import os
import subprocess
import zipfile
import json
import logging
from datetime import datetime
from typing import Optional, Dict
from pathlib import Path
from sqlalchemy.orm import Session
from urllib.parse import urlparse
import tempfile
import shutil

from core.config import settings
from models import BackupRecord
from schemas import BackupMetadata

logger = logging.getLogger(__name__)

BACKUP_DIR = Path("./backups")
UPLOAD_DIR = Path(settings.UPLOAD_DIR or "./uploads")
METADATA_FILE = "metadata.json"
DATABASE_FILE = "database.sql"
UPLOADS_FOLDER = "uploads"


class RestoreService:
    def __init__(self):
        self.backup_dir = BACKUP_DIR
        self.upload_dir = UPLOAD_DIR

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

    def _validate_zip_structure(self, zip_path: Path) -> bool:
        """Validate that ZIP contains required files."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                file_list = zipf.namelist()
                
                # Check for required files
                has_database = any(f.endswith(DATABASE_FILE) for f in file_list)
                has_metadata = any(f.endswith(METADATA_FILE) for f in file_list)
                
                if not has_database:
                    logger.error(f"ZIP missing {DATABASE_FILE}")
                    return False
                if not has_metadata:
                    logger.error(f"ZIP missing {METADATA_FILE}")
                    return False
                
                logger.info("ZIP structure validated successfully")
                return True
                
        except Exception as e:
            logger.error(f"Error validating ZIP structure: {str(e)}")
            return False

    def _extract_metadata(self, zip_path: Path) -> Optional[BackupMetadata]:
        """Extract and validate metadata from ZIP."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                metadata_content = zipf.read(METADATA_FILE).decode('utf-8')
                metadata_dict = json.loads(metadata_content)
                
                metadata = BackupMetadata(**metadata_dict)
                logger.info(f"Metadata extracted: version={metadata.backup_version}, date={metadata.backup_date}")
                return metadata
                
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            return None

    def _create_pre_restore_backup(self, db: Session) -> Optional[BackupRecord]:
        """Create a backup before restoring."""
        from services.backup_service import BackupService
        
        logger.info("Creating pre-restore backup...")
        backup_service = BackupService()
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = f"PreRestore_Backup_{timestamp}"
        
        return backup_service.create_backup(db, backup_type="pre_restore", user_id=None)

    def _restore_database(self, sql_file: Path) -> bool:
        """Restore PostgreSQL database from SQL dump."""
        try:
            db_params = self._parse_database_url()
            
            # Set PGPASSWORD environment variable for psql
            env = os.environ.copy()
            env["PGPASSWORD"] = db_params["password"]
            
            # Terminate all connections to the database
            logger.info("Terminating all database connections...")
            terminate_cmd = [
                "psql",
                f"--host={db_params['host']}",
                f"--port={db_params['port']}",
                f"--username={db_params['user']}",
                "postgres",
                "-c", f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '{db_params['database']}' AND pid <> pg_backend_pid();"
            ]
            
            subprocess.run(terminate_cmd, env=env, capture_output=True, check=False)
            
            # Drop existing database and recreate
            logger.info("Dropping existing database...")
            drop_cmd = [
                "psql",
                f"--host={db_params['host']}",
                f"--port={db_params['port']}",
                f"--username={db_params['user']}",
                "postgres",
                "-c", f"DROP DATABASE IF EXISTS {db_params['database']}"
            ]
            
            subprocess.run(drop_cmd, env=env, capture_output=True, check=True)
            
            logger.info("Creating new database...")
            create_cmd = [
                "psql",
                f"--host={db_params['host']}",
                f"--port={db_params['port']}",
                f"--username={db_params['user']}",
                "postgres",
                "-c", f"CREATE DATABASE {db_params['database']}"
            ]
            
            subprocess.run(create_cmd, env=env, capture_output=True, check=True)
            
            # Restore from SQL dump
            logger.info(f"Restoring database from {sql_file}...")
            restore_cmd = [
                "psql",
                f"--host={db_params['host']}",
                f"--port={db_params['port']}",
                f"--username={db_params['user']}",
                f"--dbname={db_params['database']}",
                "--file",str(sql_file)
            ]
            
            result = subprocess.run(restore_cmd, env=env, capture_output=True, text=True, check=True)
            
            if result.returncode == 0:
                logger.info("Database restored successfully")
                return True
            else:
                logger.error(f"Database restore failed: {result.stderr}")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Database restore command failed: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Error restoring database: {str(e)}")
            return False

    def _restore_uploads(self, zip_path: Path, temp_dir: Path) -> bool:
        """Restore uploaded files from ZIP."""
        try:
            # Backup existing uploads if they exist
            if self.upload_dir.exists():
                backup_upload_dir = self.upload_dir.parent / f"{self.upload_dir.name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                # Use copytree instead of move to handle Docker volume mounts
                shutil.copytree(str(self.upload_dir), str(backup_upload_dir))
                # Then remove the original directory
                shutil.rmtree(str(self.upload_dir))
                logger.info(f"Backed up existing uploads to: {backup_upload_dir}")
            
            # Create uploads directory
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract uploads from ZIP
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                for file_info in zipf.infolist():
                    if file_info.filename.startswith(UPLOADS_FOLDER + "/"):
                        # Extract file
                        extracted_path = zipf.extract(file_info.filename, temp_dir)
                        
                        # Move to correct location
                        relative_path = file_info.filename[len(UPLOADS_FOLDER) + 1:]
                        target_path = self.upload_dir / relative_path
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(extracted_path), str(target_path))
            
            logger.info("Uploads restored successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring uploads: {str(e)}")
            return False

    def restore_backup(
        self, 
        backup_id: int, 
        db: Session
    ) -> Dict[str, any]:
        """Restore system from a backup."""
        logger.info(f"Starting restore from backup ID: {backup_id}")
        
        # Get backup record
        backup = db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
        if not backup:
            logger.error(f"Backup not found: ID={backup_id}")
            return {
                "success": False,
                "error": "Backup not found"
            }
        
        if backup.status != "completed":
            logger.error(f"Backup is not in completed state: {backup.status}")
            return {
                "success": False,
                "error": f"Backup status is {backup.status}, cannot restore"
            }
        
        zip_path = Path(backup.file_path)
        if not zip_path.exists():
            logger.error(f"Backup file not found: {zip_path}")
            return {
                "success": False,
                "error": "Backup file not found"
            }
        
        # Step 1: Validate ZIP structure
        if not self._validate_zip_structure(zip_path):
            return {
                "success": False,
                "error": "Invalid backup file structure"
            }
        
        # Step 2: Extract and validate metadata
        metadata = self._extract_metadata(zip_path)
        if not metadata:
            return {
                "success": False,
                "error": "Invalid or missing metadata"
            }
        
        # Step 3: Create pre-restore backup
        pre_restore_backup = self._create_pre_restore_backup(db)
        if not pre_restore_backup:
            logger.warning("Failed to create pre-restore backup, continuing anyway...")
        
        # Step 4: Extract files to temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            sql_file = temp_path / DATABASE_FILE
            
            try:
                # Extract SQL file
                with zipfile.ZipFile(zip_path, 'r') as zipf:
                    zipf.extract(DATABASE_FILE, temp_path)
                
                # Step 5: Restore database
                if not self._restore_database(sql_file):
                    return {
                        "success": False,
                        "error": "Database restore failed"
                    }
                
                # Step 6: Restore uploads
                if not self._restore_uploads(zip_path, temp_path):
                    logger.warning("Uploads restore failed, but database was restored")
                
                logger.info(f"Restore completed successfully from backup: {backup.filename}")
                return {
                    "success": True,
                    "message": "System restored successfully",
                    "backup_filename": backup.filename,
                    "backup_date": metadata.backup_date,
                    "pre_restore_backup_id": pre_restore_backup.id if pre_restore_backup else None
                }
                
            except Exception as e:
                logger.error(f"Error during restore: {str(e)}")
                return {
                    "success": False,
                    "error": f"Restore failed: {str(e)}"
                }

    def verify_backup(self, backup_id: int, db: Session) -> Dict[str, any]:
        """Verify a backup without restoring."""
        backup = db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
        if not backup:
            return {
                "valid": False,
                "error": "Backup not found"
            }
        
        zip_path = Path(backup.file_path)
        if not zip_path.exists():
            return {
                "valid": False,
                "error": "Backup file not found"
            }
        
        # Validate structure
        if not self._validate_zip_structure(zip_path):
            return {
                "valid": False,
                "error": "Invalid backup file structure"
            }
        
        # Extract metadata
        metadata = self._extract_metadata(zip_path)
        if not metadata:
            return {
                "valid": False,
                "error": "Invalid or missing metadata"
            }
        
        return {
            "valid": True,
            "metadata": metadata.model_dump(),
            "file_size": backup.size_bytes,
            "created_at": backup.created_at
        }
