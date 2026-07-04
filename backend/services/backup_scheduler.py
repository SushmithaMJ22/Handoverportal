import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session

from core.config import settings
from models import BackupRecord
from services.backup_service import BackupService

logger = logging.getLogger(__name__)


class BackupScheduler:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(BackupScheduler, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.enabled = True
        self.frequency_days = 7  # Default: weekly
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.backup_service = BackupService()
        
        logger.info("BackupScheduler initialized")
    
    def start(self, db_factory):
        """Start the backup scheduler in a background thread."""
        if self._running:
            logger.warning("Backup scheduler is already running")
            return
        
        if not self.enabled:
            logger.info("Backup scheduler is disabled")
            return
        
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_scheduler,
            args=(db_factory,),
            daemon=True
        )
        self._thread.start()
        logger.info("Backup scheduler started")
    
    def stop(self):
        """Stop the backup scheduler."""
        if not self._running:
            return
        
        logger.info("Stopping backup scheduler...")
        self._stop_event.set()
        self._running = False
        
        if self._thread:
            self._thread.join(timeout=5)
        
        logger.info("Backup scheduler stopped")
    
    def _run_scheduler(self, db_factory):
        """Main scheduler loop."""
        logger.info("Backup scheduler thread started")
        
        while not self._stop_event.is_set():
            try:
                # Check if backup is needed
                if self._should_run_backup(db_factory):
                    logger.info("Running scheduled backup...")
                    db = db_factory()
                    try:
                        backup = self.backup_service.create_backup(
                            db=db,
                            backup_type="automatic",
                            user_id=None
                        )
                        if backup:
                            logger.info(f"Scheduled backup completed: {backup.filename}")
                        else:
                            logger.error("Scheduled backup failed")
                    finally:
                        db.close()
                
                # Sleep for 1 hour before next check
                self._stop_event.wait(timeout=3600)  # 1 hour
                
            except Exception as e:
                logger.error(f"Error in backup scheduler: {str(e)}")
                # Sleep for 5 minutes on error before retrying
                self._stop_event.wait(timeout=300)  # 5 minutes
        
        logger.info("Backup scheduler thread stopped")
    
    def _should_run_backup(self, db_factory) -> bool:
        """Check if a backup should be run based on schedule."""
        if not self.enabled:
            return False
        
        db = db_factory()
        try:
            # Get last successful backup
            last_backup = db.query(BackupRecord).filter(
                BackupRecord.status == "completed",
                BackupRecord.backup_type == "automatic"
            ).order_by(BackupRecord.created_at.desc()).first()
            
            if not last_backup:
                logger.info("No previous automatic backup found, running first backup")
                return True
            
            # Check if enough time has passed
            now = datetime.now(timezone.utc)
            # Ensure last_backup.created_at is timezone-aware
            if last_backup.created_at.tzinfo is None:
                last_backup.created_at = last_backup.created_at.replace(tzinfo=timezone.utc)
            time_since_last = now - last_backup.created_at
            if time_since_last >= timedelta(days=self.frequency_days):
                logger.info(f"Time since last backup: {time_since_last.days} days, threshold: {self.frequency_days} days")
                return True
            
            logger.debug(f"Backup not needed yet. Last backup was {time_since_last.days} days ago")
            return False
            
        finally:
            db.close()
    
    def set_frequency(self, days: int):
        """Set backup frequency in days."""
        if days < 1:
            logger.warning(f"Invalid frequency: {days} days, must be at least 1")
            return
        
        self.frequency_days = days
        logger.info(f"Backup frequency set to {days} days")
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the scheduler."""
        self.enabled = enabled
        logger.info(f"Backup scheduler {'enabled' if enabled else 'disabled'}")
    
    def get_status(self, db_factory) -> dict:
        """Get scheduler status."""
        db = db_factory()
        try:
            last_backup = db.query(BackupRecord).filter(
                BackupRecord.status == "completed",
                BackupRecord.backup_type == "automatic"
            ).order_by(BackupRecord.created_at.desc()).first()
            
            next_backup = None
            if last_backup:
                # Ensure created_at is timezone-aware
                if last_backup.created_at.tzinfo is None:
                    last_backup.created_at = last_backup.created_at.replace(tzinfo=timezone.utc)
                next_backup = last_backup.created_at + timedelta(days=self.frequency_days)
            
            return {
                "enabled": self.enabled,
                "running": self._running,
                "frequency_days": self.frequency_days,
                "last_automatic_backup": last_backup.created_at if last_backup else None,
                "next_scheduled_backup": next_backup
            }
        finally:
            db.close()


# Global scheduler instance
scheduler = BackupScheduler()
