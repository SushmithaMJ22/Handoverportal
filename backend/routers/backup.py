import logging
import json
import zipfile
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path

from database import get_db
from models import User, BackupRecord
from schemas import BackupOut, BackupStatus, RestoreRequest, RestoreByFilenameRequest, SchedulerConfig
from core.dependencies import require_super_admin
from services.backup_service import BackupService
from services.restore_service import RestoreService
from services.backup_scheduler import scheduler
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/backup", tags=["backup"])

backup_service = BackupService()
restore_service = RestoreService()

BACKUP_DIR = Path(settings.BACKUP_DIR or "/app/backups")
METADATA_FILE = "backup_metadata.json"
DATABASE_FILE = "database.sql"
CHECKSUM_FILE = "checksum.sha256"


@router.post("/create", response_model=BackupOut)
def create_backup(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Create a manual system backup."""
    try:
        logger.info(f"Manual backup requested by user: {current_user.username}")
        
        backup = backup_service.create_backup(
            db=db,
            backup_type="manual",
            user_id=current_user.id
        )
        
        if not backup:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create backup"
            )
        
        logger.info(f"Manual backup created successfully: {backup.filename}")
        
        # Construct response with proper metadata serialization
        import json
        backup_dict = {
            "id": backup.id,
            "filename": backup.filename,
            "file_path": backup.file_path,
            "size_bytes": backup.size_bytes,
            "status": backup.status,
            "backup_type": backup.backup_type,
            "created_at": backup.created_at,
            "created_by": backup.created_by,
            "metadata": None
        }
        if backup.metadata_json:
            backup_dict["metadata"] = json.loads(backup.metadata_json)
        
        return BackupOut(**backup_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating backup: {str(e)}"
        )


@router.get("/list", response_model=List[BackupOut])
def list_backups(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """List all available backups from database records."""
    try:
        # Query database for backup records (single source of truth)
        # Include all backup types: manual, automatic, and pre_restore
        backups = db.query(BackupRecord).filter(
            BackupRecord.status == "completed"
        ).all()
        
        # Build result from database records
        result = []
        for backup in backups:
            # Verify ZIP file exists
            backup_path = Path(backup.file_path)
            if not backup_path.exists():
                logger.warning(f"Backup record has missing ZIP file: {backup.filename} (ID={backup.id})")
                continue
            
            # Parse metadata
            metadata = None
            if backup.metadata_json:
                try:
                    metadata = json.loads(backup.metadata_json)
                except Exception as e:
                    logger.warning(f"Could not parse metadata for {backup.filename}: {str(e)}")
            
            backup_dict = {
                "id": backup.id,
                "filename": backup.filename,
                "file_path": backup.file_path,
                "size_bytes": backup.size_bytes,
                "status": backup.status,
                "backup_type": backup.backup_type,
                "created_at": backup.created_at,
                "created_by": backup.created_by,
                "metadata": metadata
            }
            result.append(BackupOut(**backup_dict))
        
        # Sort by created_at (newest first)
        # Normalize datetime objects to handle timezone-aware and timezone-naive
        def normalize_datetime(dt):
            if dt is None:
                return None
            if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
                # Make timezone-aware datetime naive for comparison
                return dt.replace(tzinfo=None)
            return dt
        
        result.sort(key=lambda x: normalize_datetime(x.created_at) or "", reverse=True)
        
        logger.info(f"Listed {len(result)} backups from database")
        return result
        
    except Exception as e:
        logger.error(f"Error listing backups: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing backups: {str(e)}"
        )


@router.get("/status", response_model=BackupStatus)
def get_backup_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Get current backup status."""
    try:
        status_dict = backup_service.get_backup_status(db)
        
        # Add scheduler status
        from database import SessionLocal
        scheduler_status = scheduler.get_status(SessionLocal)
        status_dict["scheduler_enabled"] = scheduler_status["enabled"]
        status_dict["next_scheduled_backup"] = scheduler_status["next_scheduled_backup"]
        
        return BackupStatus(**status_dict)
        
    except Exception as e:
        logger.error(f"Error getting backup status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting backup status: {str(e)}"
        )


@router.get("/download/{backup_id}")
def download_backup(
    backup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Download a backup file."""
    try:
        backup_path = backup_service.get_backup_file_path(backup_id, db)
        
        if not backup_path or not backup_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup file not found"
            )
        
        logger.info(f"Backup download requested: {backup_path.name} by {current_user.username}")
        
        return FileResponse(
            path=str(backup_path),
            filename=backup_path.name,
            media_type="application/zip"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading backup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading backup: {str(e)}"
        )


@router.delete("/{backup_id}")
def delete_backup(
    backup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Delete a backup."""
    try:
        logger.info(f"Backup deletion requested: ID={backup_id} by {current_user.username}")
        
        success = backup_service.delete_backup(backup_id, db)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup not found or deletion failed"
            )
        
        logger.info(f"Backup deleted successfully: ID={backup_id}")
        return {"message": "Backup deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting backup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting backup: {str(e)}"
        )


@router.post("/restore")
def restore_backup(
    request: RestoreRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Restore system from a backup."""
    try:
        logger.info(f"Restore requested: backup_id={request.backup_id} by {current_user.username}")
        
        result = restore_service.restore_backup(request.backup_id, db)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Restore failed")
            )
        
        logger.info(f"Restore completed successfully: {result}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring backup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error restoring backup: {str(e)}"
        )


@router.get("/verify/{backup_id}")
def verify_backup(
    backup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Verify a backup without restoring."""
    try:
        result = restore_service.verify_backup(backup_id, db)
        return result
        
    except Exception as e:
        logger.error(f"Error verifying backup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying backup: {str(e)}"
        )


@router.get("/scheduler/status")
def get_scheduler_status(
    current_user: User = Depends(require_super_admin)
):
    """Get scheduler status."""
    try:
        from database import SessionLocal
        scheduler_status = scheduler.get_status(SessionLocal)
        return scheduler_status
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting scheduler status: {str(e)}"
        )


@router.put("/scheduler/config")
def update_scheduler_config(
    config: SchedulerConfig,
    current_user: User = Depends(require_super_admin)
):
    """Update scheduler configuration."""
    try:
        logger.info(f"Scheduler config update by {current_user.username}: enabled={config.enabled}, frequency={config.frequency}")
        
        scheduler.set_enabled(config.enabled)
        
        # Convert frequency string to days
        frequency_map = {
            "daily": 1,
            "weekly": 7,
            "monthly": 30
        }
        days = frequency_map.get(config.frequency, 7)
        scheduler.set_frequency(days)
        
        return {
            "message": "Scheduler configuration updated",
            "enabled": config.enabled,
            "frequency": config.frequency
        }
        
    except Exception as e:
        logger.error(f"Error updating scheduler config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating scheduler config: {str(e)}"
        )


@router.post("/restore-by-filename")
def restore_backup_by_filename(
    request: RestoreByFilenameRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Restore system from a backup by filename (for files without database records)."""
    try:
        filename = request.filename
        
        # Validate filename is not empty
        if not filename or not filename.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename cannot be empty"
            )
        
        logger.info(f"Restore requested by filename: {filename} by {current_user.username}")
        
        zip_path = BACKUP_DIR / filename
        
        # Check if backup file exists
        if not zip_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backup file not found: {filename}"
            )
        
        # Create a temporary backup record for the restore
        import tempfile
        from services.backup_service import BackupService
        
        # First, create a database record for this backup if it doesn't exist
        db_backup = db.query(BackupRecord).filter(
            BackupRecord.filename == filename
        ).first()
        
        backup_id = None
        created_record = False
        
        if not db_backup:
            # Extract metadata
            metadata = None
            size_bytes = zip_path.stat().st_size
            
            try:
                with zipfile.ZipFile(zip_path, 'r') as zipf:
                    if METADATA_FILE in zipf.namelist():
                        metadata_content = zipf.read(METADATA_FILE).decode('utf-8')
                        metadata = json.loads(metadata_content)
            except Exception as e:
                logger.warning(f"Could not read metadata from {filename}: {str(e)}")
            
            backup_type = metadata.get('backup_type', 'manual') if metadata else 'manual'
            
            db_backup = BackupRecord(
                filename=filename,
                file_path=str(zip_path),
                size_bytes=size_bytes,
                status="completed",
                backup_type=backup_type,
                created_by=current_user.id,
                metadata_json=json.dumps(metadata) if metadata else None
            )
            db.add(db_backup)
            db.flush()  # Get the ID but don't commit yet
            db.refresh(db_backup)
            backup_id = db_backup.id
            created_record = True
        else:
            backup_id = db_backup.id
        
        try:
            # Now restore using the backup ID
            result = restore_service.restore_backup(backup_id, db)
            
            if not result.get("success"):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.get("error", "Restore failed")
                )
            
            # Only commit the database record if restore succeeded
            if created_record:
                db.commit()
                logger.info(f"Backup record created and committed: {filename}")
            
            logger.info(f"Restore completed successfully: {result}")
            return result
            
        except Exception as restore_error:
            # Rollback if restore failed and we created a new record
            if created_record:
                db.rollback()
                logger.warning(f"Restore failed, rolled back database record for {filename}")
            raise restore_error
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring backup by filename: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error restoring backup: {str(e)}"
        )
