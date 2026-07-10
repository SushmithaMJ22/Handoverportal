import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def get_windows_documents_folder() -> Path:
    """
    Get the current Windows user's Documents folder.
    Works both in Windows and inside Docker container.
    """
    try:
        # Try to get from environment variable (set by Docker)
        if "USERPROFILE" in os.environ:
            user_profile = Path(os.environ["USERPROFILE"])
            documents_folder = user_profile / "Documents"
            if documents_folder.exists():
                logger.info(f"Using Documents folder from USERPROFILE: {documents_folder}")
                return documents_folder
        
        # Fallback to HOME environment variable
        if "HOME" in os.environ:
            home = Path(os.environ["HOME"])
            # On Windows, HOME might point to user profile
            # On Linux, this would be /home/user
            if os.name == 'nt':
                documents_folder = home / "Documents"
            else:
                # Inside Docker container, use the mounted path
                documents_folder = Path("/host/Documents")
            
            if documents_folder.exists():
                logger.info(f"Using Documents folder from HOME: {documents_folder}")
                return documents_folder
        
        # Final fallback for Docker container
        docker_documents = Path("/host/Documents")
        if docker_documents.exists():
            logger.info(f"Using Docker mounted Documents folder: {docker_documents}")
            return docker_documents
        
        # If nothing works, raise an error
        raise RuntimeError("Could not detect Windows Documents folder")
        
    except Exception as e:
        logger.error(f"Error detecting Documents folder: {str(e)}")
        raise RuntimeError(f"Failed to detect Windows Documents folder: {str(e)}")


def get_project_handover_folder() -> Path:
    """
    Get the Project Handover folder in Documents.
    Creates it if it doesn't exist.
    """
    try:
        documents = get_windows_documents_folder()
        project_handover = documents / "Project Handover"
        
        # Create folder if it doesn't exist
        project_handover.mkdir(parents=True, exist_ok=True)
        logger.info(f"Project Handover folder: {project_handover}")
        
        return project_handover
        
    except Exception as e:
        logger.error(f"Error creating Project Handover folder: {str(e)}")
        raise


def get_backup_folder() -> Path:
    """
    Get the Backup folder in Project Handover.
    Creates it if it doesn't exist.
    """
    try:
        project_handover = get_project_handover_folder()
        backup_folder = project_handover / "Backups"
        
        # Create folder if it doesn't exist
        backup_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Backup folder: {backup_folder}")
        
        return backup_folder
        
    except Exception as e:
        logger.error(f"Error creating Backup folder: {str(e)}")
        raise


def get_uploads_folder() -> Path:
    """
    Get the Uploads folder in Project Handover.
    Creates it if it doesn't exist.
    """
    try:
        project_handover = get_project_handover_folder()
        uploads_folder = project_handover / "Uploads"
        
        # Create folder if it doesn't exist
        uploads_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Uploads folder: {uploads_folder}")
        
        return uploads_folder
        
    except Exception as e:
        logger.error(f"Error creating Uploads folder: {str(e)}")
        raise


def get_docker_backup_path() -> str:
    """
    Get the Docker internal path for backups.
    This should match the volume mount in docker-compose.yml.
    """
    return "/app/backups"


def get_docker_uploads_path() -> str:
    """
    Get the Docker internal path for uploads.
    This should match the volume mount in docker-compose.yml.
    """
    return "/app/uploads"


def initialize_user_data_folders() -> dict:
    """
    Initialize all user data folders and return their paths.
    This should be called on application startup.
    
    Returns:
        dict: {
            "windows_backup_path": Path,
            "windows_uploads_path": Path,
            "docker_backup_path": str,
            "docker_uploads_path": str
        }
    """
    try:
        windows_backup = get_backup_folder()
        windows_uploads = get_uploads_folder()
        
        logger.info("User data folders initialized successfully")
        
        return {
            "windows_backup_path": str(windows_backup),
            "windows_uploads_path": str(windows_uploads),
            "docker_backup_path": get_docker_backup_path(),
            "docker_uploads_path": get_docker_uploads_path()
        }
        
    except Exception as e:
        logger.error(f"Error initializing user data folders: {str(e)}")
        raise
