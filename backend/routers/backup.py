import logging
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path

from database import get_db
from models import User, BackupRecord
from schemas import BackupOut, BackupStatus, RestoreRequest, SchedulerConfig
from core.dependencies import require_super_admin
from services.backup_service import BackupService
from services.restore_service import RestoreService
from services.backup_scheduler import scheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/backup", tags=["backup"])

backup_service = BackupService()
restore_service = RestoreService()


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
    """List all available backups."""
    try:
        backups = db.query(BackupRecord).order_by(
            BackupRecord.created_at.desc()
        ).all()
        
        # Add metadata to each backup
        result = []
        for backup in backups:
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
                import json
                backup_dict["metadata"] = json.loads(backup.metadata_json)
            result.append(BackupOut(**backup_dict))
        
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
        status = scheduler.get_status(SessionLocal)
        return status
        
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
