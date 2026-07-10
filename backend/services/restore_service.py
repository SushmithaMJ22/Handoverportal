import os
import subprocess
import zipfile
import json
import logging
import hashlib
import time
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from urllib.parse import urlparse
import tempfile
import shutil

from core.config import settings
from models import BackupRecord
from schemas import BackupMetadata

logger = logging.getLogger(__name__)

# Use Docker internal paths for backup storage
BACKUP_DIR = Path(settings.BACKUP_DIR or "/app/backups")
UPLOAD_DIR = Path(settings.LOCAL_UPLOADS_DIR or "/app/uploads_host")
METADATA_FILE = "backup_metadata.json"
DATABASE_FILE = "database.sql"
UPLOADS_FOLDER = "uploads"
CHECKSUM_FILE = "checksum.sha256"


class RestoreService:
    def __init__(self):
        self.backup_dir = BACKUP_DIR
        self.upload_dir = UPLOAD_DIR

    def _dispose_sqlalchemy_connections(self):
        """
        Dispose all SQLAlchemy engine connections before restore.
        This ensures no active connections exist when psql modifies the database.
        """
        try:
            from database import engine
            logger.info("Disposing SQLAlchemy engine connections...")
            engine.dispose()
            logger.info("SQLAlchemy engine connections disposed successfully")
        except Exception as e:
            logger.warning(f"Failed to dispose SQLAlchemy engine: {str(e)}")

    def _verify_database_connection(self, max_retries: int = 5, retry_delay: int = 2) -> bool:
        """
        Verify database connection is available after restore.
        Retry connection if PostgreSQL is temporarily unavailable.
        
        Args:
            max_retries: Maximum number of connection attempts
            retry_delay: Seconds to wait between retries
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            from database import engine
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Attempting database connection (attempt {attempt + 1}/{max_retries})...")
                    with engine.connect() as conn:
                        result = conn.execute(text("SELECT 1"))
                        if result.fetchone():
                            logger.info("Database connection verified successfully")
                            return True
                except Exception as e:
                    logger.warning(f"Connection attempt {attempt + 1} failed: {str(e)}")
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        logger.error("All connection attempts failed")
                        return False
            
            return False
        except Exception as e:
            logger.error(f"Error verifying database connection: {str(e)}")
            return False

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
                
                # Check for required files (exact match)
                has_database = DATABASE_FILE in file_list
                has_metadata = METADATA_FILE in file_list
                has_checksum = CHECKSUM_FILE in file_list
                
                if not has_database:
                    logger.error(f"ZIP missing {DATABASE_FILE}")
                    return False
                if not has_metadata:
                    logger.error(f"ZIP missing {METADATA_FILE}")
                    return False
                if not has_checksum:
                    logger.error(f"ZIP missing {CHECKSUM_FILE}")
                    return False
                
                logger.info("ZIP structure validated successfully")
                return True
                
        except Exception as e:
            logger.error(f"Error validating ZIP structure: {str(e)}")
            return False

    def _verify_checksum(self, zip_path: Path) -> bool:
        """Verify SHA256 checksum of database.sql file inside the ZIP."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                stored_checksum = zipf.read(CHECKSUM_FILE).decode('utf-8').strip()
                
                # Read database.sql from ZIP and calculate its checksum
                database_content = zipf.read(DATABASE_FILE)
                sha256_hash = hashlib.sha256()
                sha256_hash.update(database_content)
                calculated_checksum = sha256_hash.hexdigest()
            
            if stored_checksum == calculated_checksum:
                logger.info("Checksum verification successful")
                return True
            else:
                logger.error(f"Checksum mismatch: stored={stored_checksum}, calculated={calculated_checksum}")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying checksum: {str(e)}")
            return False

    def _extract_metadata(self, zip_path: Path) -> Optional[Dict]:
        """Extract and validate metadata from ZIP."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                metadata_content = zipf.read(METADATA_FILE).decode('utf-8')
                metadata_dict = json.loads(metadata_content)
                
                logger.info(f"Metadata extracted: version={metadata_dict.get('backup_version')}, date={metadata_dict.get('backup_date')}")
                return metadata_dict
                
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

    def _sanitize_sql_file(self, sql_file: Path, temp_dir: Path) -> Path:
        """
        Sanitize SQL file to remove unsupported PostgreSQL configuration statements.
        
        This is required for cross-version compatibility between PostgreSQL versions 14, 15, 16, and 17.
        Newer PostgreSQL versions may include SET statements for configuration parameters that don't exist
        in older versions, causing restore failures.
        
        Args:
            sql_file: Path to the original SQL file
            temp_dir: Temporary directory for the sanitized file
            
        Returns:
            Path to the sanitized SQL file
        """
        sanitized_file = temp_dir / "database_sanitized.sql"
        
        # Patterns of unsupported SET statements to remove
        # These are configuration parameters that may not exist in all PostgreSQL versions
        unsupported_patterns = [
            r"SET\s+transaction_timeout\s*=\s*[^;]+;",
            r"SET\s+idle_in_transaction_session_timeout\s*=\s*[^;]+;",
            r"SET\s+lock_timeout\s*=\s*[^;]+;",
            r"SET\s+statement_timeout\s*=\s*[^;]+;",
            r"SET\s+client_encoding\s*=\s*[^;]+;",
            r"SET\s+search_path\s*=\s*[^;]+;",
            r"SET\s+default_transaction_read_only\s*=\s*[^;]+;",
            r"SET\s+default_transaction_isolation\s*=\s*[^;]+;",
            r"SET\s+timezone\s*=\s*[^;]+;",
            r"SET\s+datestyle\s*=\s*[^;]+;",
            r"SET\s+intervalstyle\s*=\s*[^;]+;",
            r"SET\s+extra_float_digits\s*=\s*[^;]+;",
            r"SET\s+application_name\s*=\s*[^;]+;",
        ]
        
        removed_count = 0
        
        try:
            with open(sql_file, 'r', encoding='utf-8') as infile, \
                 open(sanitized_file, 'w', encoding='utf-8') as outfile:
                
                for line in infile:
                    line_stripped = line.strip()
                    removed = False
                    
                    # Check if line matches any unsupported pattern
                    for pattern in unsupported_patterns:
                        import re
                        if re.match(pattern, line_stripped, re.IGNORECASE):
                            logger.info(f"Removed unsupported statement: {line_stripped}")
                            removed = True
                            removed_count += 1
                            break
                    
                    # Only write the line if it wasn't removed
                    if not removed:
                        outfile.write(line)
            
            logger.info(f"SQL sanitization complete. Removed {removed_count} unsupported statements.")
            return sanitized_file
            
        except Exception as e:
            logger.error(f"Error sanitizing SQL file: {str(e)}")
            # If sanitization fails, return the original file
            return sql_file

    def _restore_database(self, sql_file: Path) -> bool:
        """Restore PostgreSQL database from SQL dump without dropping the database."""
        try:
            db_params = self._parse_database_url()
            
            # Set PGPASSWORD environment variable for psql
            env = os.environ.copy()
            env["PGPASSWORD"] = db_params["password"]
            
            # Restore from SQL dump directly
            # The SQL dump contains DROP TABLE IF EXISTS statements, so we don't need to drop the database
            # This preserves the database connection for the FastAPI application
            logger.info(f"Restoring database from {sql_file}...")
            restore_cmd = [
                "psql",
                f"--host={db_params['host']}",
                f"--port={db_params['port']}",
                f"--username={db_params['user']}",
                f"--dbname={db_params['database']}",
                "--file", str(sql_file),
                "--set", "ON_ERROR_STOP=on"
            ]
            
            # Log command without password
            cmd_for_log = " ".join(restore_cmd)
            logger.info(f"Executing psql command: {cmd_for_log}")
            
            result = subprocess.run(restore_cmd, env=env, capture_output=True, text=True, check=False)
            
            # Log detailed output
            logger.info(f"psql exit code: {result.returncode}")
            if result.stdout:
                logger.info(f"psql stdout:\n{result.stdout}")
            if result.stderr:
                logger.info(f"psql stderr:\n{result.stderr}")
            
            if result.returncode == 0:
                logger.info("Database restored successfully")
                return True
            else:
                logger.error(f"Database restore failed with exit code {result.returncode}")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Database restore command failed with CalledProcessError")
            logger.error(f"Exit code: {e.returncode}")
            if e.stdout:
                logger.error(f"stdout:\n{e.stdout}")
            if e.stderr:
                logger.error(f"stderr:\n{e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Error restoring database: {str(e)}")
            return False

    def _restore_uploads(self, zip_path: Path, temp_dir: Path) -> bool:
        """Restore uploaded files from ZIP."""
        try:
            # Clear existing uploads directory contents without removing the directory itself
            # This avoids "device busy" errors on Docker volume mounts
            if self.upload_dir.exists():
                logger.info(f"Clearing existing uploads directory: {self.upload_dir}")
                for item in self.upload_dir.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(str(item))
                logger.info("Existing uploads directory cleared")
            
            # Ensure uploads directory exists
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
        import time
        start_time = time.time()
        
        logger.info(f"Starting restore from backup ID: {backup_id}")
        
        # Get backup record
        backup = db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
        if not backup:
            logger.error(f"Backup not found: ID={backup_id}")
            return {
                "success": False,
                "error": "Backup not found"
            }
        
        logger.info(f"Backup found: {backup.filename}, type={backup.backup_type}, status={backup.status}")
        
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
        
        logger.info(f"Backup file verified: {zip_path}")
        
        # Step 1: Validate ZIP structure
        logger.info("Step 1/9: Validating ZIP structure...")
        if not self._validate_zip_structure(zip_path):
            return {
                "success": False,
                "error": "Invalid backup file structure"
            }
        logger.info("ZIP structure validated")
        
        # Step 2: Verify checksum
        logger.info("Step 2/9: Verifying checksum...")
        if not self._verify_checksum(zip_path):
            return {
                "success": False,
                "error": "Backup file is corrupted (checksum mismatch)"
            }
        logger.info("Checksum verified")
        
        # Step 3: Extract and validate metadata
        logger.info("Step 3/9: Extracting metadata...")
        metadata = self._extract_metadata(zip_path)
        if not metadata:
            return {
                "success": False,
                "error": "Invalid or missing metadata"
            }
        logger.info(f"Metadata extracted: version={metadata.get('backup_version')}, date={metadata.get('backup_date')}")
        
        # Step 4: Create pre-restore backup
        logger.info("Step 4/9: Creating pre-restore backup...")
        pre_restore_backup = self._create_pre_restore_backup(db)
        if not pre_restore_backup:
            logger.warning("Failed to create pre-restore backup, continuing anyway...")
        else:
            logger.info(f"Pre-restore backup created: {pre_restore_backup.filename}")
        
        # Step 5: Dispose SQLAlchemy connections before restore
        logger.info("Step 5/9: Closing database connections before restore...")
        db.close()
        self._dispose_sqlalchemy_connections()
        logger.info("Database connections closed and disposed")
        
        # Step 6: Extract files to temporary directory
        logger.info("Step 6/9: Extracting files to temporary directory...")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            sql_file = temp_path / DATABASE_FILE
            
            try:
                # Extract SQL file
                logger.info("Extracting SQL file from ZIP...")
                with zipfile.ZipFile(zip_path, 'r') as zipf:
                    zipf.extract(DATABASE_FILE, temp_path)
                logger.info(f"SQL file extracted: {sql_file}")
                
                # Step 7: Sanitize SQL for cross-version compatibility
                logger.info("Step 7/9: Sanitizing SQL for PostgreSQL version compatibility...")
                sanitized_sql_file = self._sanitize_sql_file(sql_file, temp_path)
                logger.info("SQL sanitization completed")
                
                # Step 8: Restore database
                logger.info("Step 8/9: Restoring database...")
                if not self._restore_database(sanitized_sql_file):
                    # If restore fails, attempt to restore pre-restore backup
                    if pre_restore_backup:
                        logger.error("Database restore failed, attempting to restore pre-restore backup...")
                        self._restore_from_pre_restore_backup(pre_restore_backup)
                    return {
                        "success": False,
                        "error": "Database restore failed"
                    }
                logger.info("Database restored successfully")
                
                # Step 9: Verify database connection after restore
                logger.info("Step 9/9: Verifying database connection after restore...")
                if not self._verify_database_connection():
                    logger.error("Database connection verification failed after restore")
                    return {
                        "success": False,
                        "error": "Database restore completed but connection verification failed"
                    }
                logger.info("Database connection verified")
                
                # Step 10: Restore uploads
                logger.info("Restoring uploads...")
                if not self._restore_uploads(zip_path, temp_path):
                    logger.warning("Uploads restore failed, but database was restored")
                else:
                    logger.info("Uploads restored successfully")
                
                # Step 11: Reconcile backup metadata with filesystem
                logger.info("Reconciling backup metadata with filesystem...")
                try:
                    from database import SessionLocal
                    from services.backup_service import BackupService
                    
                    # Create new database session for reconciliation
                    reconcile_db = SessionLocal()
                    try:
                        backup_service = BackupService()
                        new_records = backup_service.sync_backup_history(reconcile_db)
                        logger.info(f"Backup reconciliation completed: {new_records} new records synchronized")
                    finally:
                        reconcile_db.close()
                except Exception as e:
                    logger.error(f"Error during backup reconciliation: {str(e)}")
                    # Non-critical error, don't fail the restore
                
                elapsed_time = time.time() - start_time
                logger.info(f"Restore completed successfully from backup: {backup.filename} in {elapsed_time:.2f} seconds")
                return {
                    "success": True,
                    "message": "System restored successfully",
                    "backup_filename": backup.filename,
                    "backup_date": metadata.get('backup_date'),
                    "pre_restore_backup_id": pre_restore_backup.id if pre_restore_backup else None,
                    "elapsed_time": elapsed_time
                }
                
            except Exception as e:
                logger.error(f"Error during restore: {str(e)}")
                # If restore fails, attempt to restore pre-restore backup
                if pre_restore_backup:
                    logger.error("Restore failed, attempting to restore pre-restore backup...")
                    self._restore_from_pre_restore_backup(pre_restore_backup)
                return {
                    "success": False,
                    "error": f"Restore failed: {str(e)}"
                }

    def _restore_from_pre_restore_backup(self, pre_restore_backup: BackupRecord):
        """Restore from pre-restore backup if main restore fails."""
        try:
            logger.info(f"Restoring from pre-restore backup: {pre_restore_backup.filename}")
            zip_path = Path(pre_restore_backup.file_path)
            
            if not zip_path.exists():
                logger.error("Pre-restore backup file not found")
                return
            
            # Dispose connections before restore
            logger.info("Disposing connections before pre-restore backup restore...")
            self._dispose_sqlalchemy_connections()
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                sql_file = temp_path / DATABASE_FILE
                
                with zipfile.ZipFile(zip_path, 'r') as zipf:
                    zipf.extract(DATABASE_FILE, temp_path)
                
                # Sanitize SQL
                sanitized_sql_file = self._sanitize_sql_file(sql_file, temp_path)
                
                if self._restore_database(sanitized_sql_file):
                    logger.info("Pre-restore backup restored successfully")
                    # Verify connection after restore
                    if self._verify_database_connection():
                        logger.info("Database connection verified after pre-restore backup restore")
                    else:
                        logger.warning("Connection verification failed after pre-restore backup restore")
                    
                    # Reconcile backup metadata with filesystem
                    logger.info("Reconciling backup metadata after pre-restore backup restore...")
                    try:
                        from database import SessionLocal
                        from services.backup_service import BackupService
                        
                        reconcile_db = SessionLocal()
                        try:
                            backup_service = BackupService()
                            new_records = backup_service.sync_backup_history(reconcile_db)
                            logger.info(f"Backup reconciliation completed: {new_records} new records synchronized")
                        finally:
                            reconcile_db.close()
                    except Exception as e:
                        logger.error(f"Error during backup reconciliation: {str(e)}")
                else:
                    logger.error("Failed to restore pre-restore backup")
                    
        except Exception as e:
            logger.error(f"Error restoring pre-restore backup: {str(e)}")

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
        
        # Verify checksum
        if not self._verify_checksum(zip_path):
            return {
                "valid": False,
                "error": "Backup file is corrupted (checksum mismatch)"
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
            "metadata": metadata,
            "file_size": backup.size_bytes,
            "created_at": backup.created_at
        }
