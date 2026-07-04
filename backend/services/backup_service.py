import os
import subprocess
import shutil
import zipfile
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path
from sqlalchemy.orm import Session
from urllib.parse import urlparse
import tempfile

from core.config import settings
from models import BackupRecord, User
from schemas import BackupMetadata

logger = logging.getLogger(__name__)

BACKUP_DIR = Path("./backups")
UPLOAD_DIR = Path(settings.UPLOAD_DIR or "./uploads")
METADATA_FILE = "metadata.json"
DATABASE_FILE = "database.sql"
UPLOADS_FOLDER = "uploads"


class BackupService:
    def __init__(self):
        self.backup_dir = BACKUP_DIR
        self.backup_dir.mkdir(exist_ok=True)
        self.max_backups = 10

    def _parse_database_url(self) -> Dict[str, str]:
        """Parse DATABASE_URL to extract connection parameters."""
        parsed = urlparse(settings.DATABASE_URL)
        return {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 5432,
            "user": parsed.username or "postgres",
            "password": parsed.password,
            "database": parsed.path[1:] if parsed.path.startswith("/") else parsed.path,
        }

    def _create_postgresql_dump(self, output_path: Path) -> bool:
        """Create PostgreSQL dump using pg_dump."""
        try:
            db_params = self._parse_database_url()
            
            # Set PGPASSWORD environment variable for pg_dump
            env = os.environ.copy()
            env["PGPASSWORD"] = db_params["password"]
            
            cmd = [
                "pg_dump",
                f"--host={db_params['host']}",
                f"--port={db_params['port']}",
                f"--username={db_params['user']}",
                f"--dbname={db_params['database']}",
                "--no-owner",
                "--no-acl",
                "--format=plain",
                "--file", str(output_path)
            ]
            
            logger.info(f"Creating PostgreSQL dump: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.returncode == 0:
                logger.info(f"PostgreSQL dump created successfully: {output_path}")
                return True
            else:
                logger.error(f"pg_dump failed: {result.stderr}")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"pg_dump command failed: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Error creating PostgreSQL dump: {str(e)}")
            return False

    def _count_uploaded_files(self, uploads_path: Path) -> int:
        """Count total files in uploads directory."""
        if not uploads_path.exists():
            return 0
        total = 0
        for root, dirs, files in os.walk(uploads_path):
            total += len(files)
        return total

    def _create_metadata(self, backup_type: str, total_files: int) -> BackupMetadata:
        """Create backup metadata."""
        return BackupMetadata(
            backup_version="1.0",
            backup_date=datetime.utcnow().isoformat(),
            application_version="1.0",
            database_version="PostgreSQL",
            includes_uploads=True,
            total_files=total_files
        )

    def _create_zip_package(
        self, 
        backup_name: str, 
        sql_file: Path, 
        uploads_source: Path,
        metadata: BackupMetadata
    ) -> Optional[Path]:
        """Create ZIP package with database dump and uploads."""
        zip_path = self.backup_dir / f"{backup_name}.zip"
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add database dump
                if sql_file.exists():
                    zipf.write(sql_file, DATABASE_FILE)
                    logger.info(f"Added database dump to ZIP: {DATABASE_FILE}")
                
                # Add uploads folder
                if uploads_source.exists():
                    for root, dirs, files in os.walk(uploads_source):
                        for file in files:
                            file_path = Path(root) / file
                            arcname = f"{UPLOADS_FOLDER}/{file_path.relative_to(uploads_source)}"
                            zipf.write(file_path, arcname)
                    logger.info(f"Added uploads folder to ZIP: {UPLOADS_FOLDER}/")
                
                # Add metadata
                metadata_json = metadata.model_dump_json()
                zipf.writestr(METADATA_FILE, metadata_json)
                logger.info(f"Added metadata to ZIP: {METADATA_FILE}")
            
            logger.info(f"ZIP package created successfully: {zip_path}")
            return zip_path
            
        except Exception as e:
            logger.error(f"Error creating ZIP package: {str(e)}")
            if zip_path.exists():
                zip_path.unlink()
            return None

    def create_backup(
        self, 
        db: Session, 
        backup_type: str = "manual",
        user_id: Optional[int] = None
    ) -> Optional[BackupRecord]:
        """Create a complete system backup."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
        backup_name = f"ProjectHandover_Backup_{timestamp}"
        
        logger.info(f"Starting {backup_type} backup: {backup_name}")
        
        # Create temporary directory for backup files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            sql_file = temp_path / DATABASE_FILE
            
            # Step 1: Create PostgreSQL dump
            if not self._create_postgresql_dump(sql_file):
                logger.error("Failed to create PostgreSQL dump")
                return None
            
            # Step 2: Count uploaded files
            total_files = self._count_uploaded_files(UPLOAD_DIR)
            
            # Step 3: Create metadata
            metadata = self._create_metadata(backup_type, total_files)
            
            # Step 4: Create ZIP package
            zip_path = self._create_zip_package(backup_name, sql_file, UPLOAD_DIR, metadata)
            if not zip_path:
                logger.error("Failed to create ZIP package")
                return None
            
            # Step 5: Get file size
            size_bytes = zip_path.stat().st_size
            
            # Step 6: Create database record
            try:
                backup_record = BackupRecord(
                    filename=f"{backup_name}.zip",
                    file_path=str(zip_path),
                    size_bytes=size_bytes,
                    status="completed",
                    backup_type=backup_type,
                    created_by=user_id,
                    metadata_json=metadata.model_dump_json()
                )
                db.add(backup_record)
                db.commit()
                db.refresh(backup_record)
                
                logger.info(f"Backup record created: ID={backup_record.id}, filename={backup_record.filename}")
                
                # Step 7: Clean up old backups if needed
                self._cleanup_old_backups(db)
                
                return backup_record
                
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to create backup record: {str(e)}")
                if zip_path.exists():
                    zip_path.unlink()
                return None

    def _cleanup_old_backups(self, db: Session):
        """Keep only the latest max_backups backups."""
        try:
            backups = db.query(BackupRecord).filter(
                BackupRecord.status == "completed"
            ).order_by(BackupRecord.created_at.desc()).all()
            
            if len(backups) > self.max_backups:
                backups_to_delete = backups[self.max_backups:]
                for backup in backups_to_delete:
                    try:
                        # Delete file
                        backup_path = Path(backup.file_path)
                        if backup_path.exists():
                            backup_path.unlink()
                            logger.info(f"Deleted old backup file: {backup.filename}")
                        
                        # Delete database record
                        db.delete(backup)
                        logger.info(f"Deleted old backup record: ID={backup.id}")
                    except Exception as e:
                        logger.error(f"Error deleting backup {backup.id}: {str(e)}")
                
                db.commit()
                logger.info(f"Cleaned up {len(backups_to_delete)} old backups")
                
        except Exception as e:
            db.rollback()
            logger.error(f"Error during backup cleanup: {str(e)}")

    def get_backup_file_path(self, backup_id: int, db: Session) -> Optional[Path]:
        """Get file path for a backup record."""
        backup = db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
        if backup and backup.status == "completed":
            return Path(backup.file_path)
        return None

    def delete_backup(self, backup_id: int, db: Session) -> bool:
        """Delete a backup and its file."""
        try:
            backup = db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
            if not backup:
                logger.error(f"Backup not found: ID={backup_id}")
                return False
            
            # Delete file
            backup_path = Path(backup.file_path)
            if backup_path.exists():
                backup_path.unlink()
                logger.info(f"Deleted backup file: {backup.filename}")
            
            # Delete database record
            db.delete(backup)
            db.commit()
            logger.info(f"Deleted backup record: ID={backup_id}")
            
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting backup {backup_id}: {str(e)}")
            return False

    def get_backup_status(self, db: Session) -> Dict:
        """Get current backup status."""
        try:
            last_backup = db.query(BackupRecord).filter(
                BackupRecord.status == "completed"
            ).order_by(BackupRecord.created_at.desc()).first()
            
            total_backups = db.query(BackupRecord).filter(
                BackupRecord.status == "completed"
            ).count()
            
            return {
                "last_backup_date": last_backup.created_at if last_backup else None,
                "last_backup_size": last_backup.size_bytes if last_backup else None,
                "total_backups": total_backups,
                "backup_location": str(self.backup_dir.absolute()),
                "scheduler_enabled": True,
                "scheduler_frequency": "weekly"
            }
        except Exception as e:
            logger.error(f"Error getting backup status: {str(e)}")
            return {
                "last_backup_date": None,
                "last_backup_size": None,
                "total_backups": 0,
                "backup_location": str(self.backup_dir.absolute()),
                "scheduler_enabled": True,
                "scheduler_frequency": "weekly"
            }
