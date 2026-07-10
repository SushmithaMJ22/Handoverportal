import os
import subprocess
import shutil
import zipfile
import json
import logging
import hashlib
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

# Use Docker internal paths for backup storage
BACKUP_DIR = Path(settings.BACKUP_DIR or "/app/backups")
UPLOAD_DIR = Path(settings.LOCAL_UPLOADS_DIR or "/app/uploads_host")
METADATA_FILE = "backup_metadata.json"
DATABASE_FILE = "database.sql"
UPLOADS_FOLDER = "uploads"
CHECKSUM_FILE = "checksum.sha256"


class BackupService:
    def __init__(self):
        self.backup_dir = BACKUP_DIR
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
                "--clean",
                "--if-exists",
                "--format=plain",
                "--exclude-table-data=backup_records",
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

    def _create_metadata(self, backup_type: str, total_files: int, created_by: Optional[int] = None) -> Dict:
        """Create backup metadata as dictionary."""
        metadata = {
            "backup_version": "1.0",
            "backup_date": datetime.utcnow().isoformat(),
            "backup_type": backup_type,
            "application_version": "1.0",
            "database_version": "PostgreSQL",
            "includes_uploads": True,
            "total_files": total_files,
            "created_by": created_by
        }
        return metadata

    def _calculate_checksum(self, sql_file: Path) -> str:
        """Calculate SHA256 checksum of database.sql file."""
        sha256_hash = hashlib.sha256()
        with open(sql_file, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _create_zip_package(
        self, 
        backup_name: str, 
        sql_file: Path, 
        uploads_source: Path,
        metadata: Dict
    ) -> Optional[Path]:
        """Create ZIP package with database dump, uploads, metadata, and checksum."""
        zip_path = self.backup_dir / f"{backup_name}.zip"
        
        try:
            # Calculate checksum of database.sql before adding to ZIP
            checksum = self._calculate_checksum(sql_file)
            logger.info(f"Calculated checksum for database.sql: {checksum}")
            
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
                metadata_json = json.dumps(metadata, indent=2)
                zipf.writestr(METADATA_FILE, metadata_json)
                logger.info(f"Added metadata to ZIP: {METADATA_FILE}")
                
                # Add checksum
                zipf.writestr(CHECKSUM_FILE, checksum)
                logger.info(f"Added checksum to ZIP: {CHECKSUM_FILE}")
            
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
        import time
        start_time = time.time()
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = f"ProjectHandover_Backup_{timestamp}"
        
        logger.info(f"Starting {backup_type} backup: {backup_name} initiated by user_id={user_id}")
        
        # Ensure backup directory exists
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Backup directory ensured: {self.backup_dir}")
        except Exception as e:
            logger.error(f"Failed to create backup directory {self.backup_dir}: {str(e)}")
            raise Exception(f"Cannot create backup directory {self.backup_dir}. Please check permissions and path configuration.")
        
        # Create temporary directory for backup files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            sql_file = temp_path / DATABASE_FILE
            
            # Step 1: Create PostgreSQL dump
            logger.info("Step 1/5: Creating PostgreSQL dump...")
            if not self._create_postgresql_dump(sql_file):
                logger.error("Failed to create PostgreSQL dump")
                return None
            logger.info(f"PostgreSQL dump created: {sql_file}")
            
            # Step 2: Count uploaded files
            logger.info("Step 2/5: Counting uploaded files...")
            total_files = self._count_uploaded_files(UPLOAD_DIR)
            logger.info(f"Found {total_files} files in uploads directory")
            
            # Step 3: Create metadata
            logger.info("Step 3/5: Creating backup metadata...")
            metadata = self._create_metadata(backup_type, total_files, user_id)
            logger.info(f"Metadata created: backup_type={backup_type}, total_files={total_files}")
            
            # Step 4: Create ZIP package
            logger.info("Step 4/5: Creating ZIP package...")
            zip_path = self._create_zip_package(backup_name, sql_file, UPLOAD_DIR, metadata)
            if not zip_path:
                logger.error("Failed to create ZIP package")
                return None
            logger.info(f"ZIP package created: {zip_path}")
            
            # Step 5: Get file size
            size_bytes = zip_path.stat().st_size
            logger.info(f"Backup file size: {size_bytes} bytes")
            
            # Step 6: Create database record
            logger.info("Step 5/5: Creating database record...")
            try:
                backup_record = BackupRecord(
                    filename=f"{backup_name}.zip",
                    file_path=str(zip_path),
                    size_bytes=size_bytes,
                    status="completed",
                    backup_type=backup_type,
                    created_by=user_id,
                    metadata_json=json.dumps(metadata)
                )
                db.add(backup_record)
                db.commit()
                db.refresh(backup_record)
                
                elapsed_time = time.time() - start_time
                logger.info(f"Backup record created: ID={backup_record.id}, filename={backup_record.filename}")
                logger.info(f"{backup_type} backup completed successfully in {elapsed_time:.2f} seconds")
                
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
        logger.info(f"Deleting backup: ID={backup_id}")
        try:
            backup = db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
            if not backup:
                logger.error(f"Backup not found: ID={backup_id}")
                return False
            
            logger.info(f"Backup found: {backup.filename}, type={backup.backup_type}")
            
            # Delete file
            backup_path = Path(backup.file_path)
            if backup_path.exists():
                backup_path.unlink()
                logger.info(f"Deleted backup file: {backup.filename} from {backup_path}")
            else:
                logger.warning(f"Backup file does not exist: {backup_path}")
            
            # Delete database record
            db.delete(backup)
            db.commit()
            logger.info(f"Deleted backup record: ID={backup_id}, filename={backup.filename}")
            
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting backup {backup_id}: {str(e)}")
            return False

    def get_backup_status(self, db: Session) -> Dict:
        """Get current backup status."""
        try:
            # Count only backups with existing ZIP files (same as Backup History)
            # Include all backup types: manual, automatic, and pre_restore
            completed_backups = db.query(BackupRecord).filter(
                BackupRecord.status == "completed"
            ).all()
            
            # Filter to only include backups with existing ZIP files
            valid_backups = []
            for backup in completed_backups:
                backup_path = Path(backup.file_path)
                if backup_path.exists():
                    valid_backups.append(backup)
                else:
                    logger.warning(f"Backup record has missing ZIP file: {backup.filename} (ID={backup.id})")
            
            total_backups = len(valid_backups)
            
            # Get last backup from valid backups
            last_backup = None
            if valid_backups:
                last_backup = max(valid_backups, key=lambda x: x.created_at)
            
            return {
                "last_backup_date": last_backup.created_at if last_backup else None,
                "last_backup_size": last_backup.size_bytes if last_backup else None,
                "total_backups": total_backups,
                "backup_location": settings.BACKUP_DIR_HOST or settings.BACKUP_DIR or "C:\\ProjectHandover\\Backups",
                "scheduler_enabled": True,
                "scheduler_frequency": "weekly"
            }
        except Exception as e:
            logger.error(f"Error getting backup status: {str(e)}")
            return {
                "last_backup_date": None,
                "last_backup_size": None,
                "total_backups": 0,
                "backup_location": settings.BACKUP_DIR_HOST or settings.BACKUP_DIR or "C:\\ProjectHandover\\Backups",
                "scheduler_enabled": True,
                "scheduler_frequency": "weekly"
            }

    def sync_backup_history(self, db: Session) -> int:
        """
        Synchronize backup history with the filesystem.
        Scans the backup folder and creates BackupRecord entries for any ZIP files
        that don't have corresponding database records.
        Also removes database records for ZIP files that no longer exist.
        
        This method is idempotent - running it multiple times will not create duplicates.
        
        Returns:
            int: Number of new backup records created
        """
        try:
            logger.info("Synchronizing backup history...")
            logger.info(f"Backup directory path: {self.backup_dir}")
            logger.info(f"Backup directory exists: {self.backup_dir.exists()}")
            
            # Ensure backup directory exists
            if not self.backup_dir.exists():
                logger.warning(f"Backup directory does not exist: {self.backup_dir}")
                logger.info("Creating backup directory...")
                try:
                    self.backup_dir.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Backup directory created: {self.backup_dir}")
                except Exception as e:
                    logger.error(f"Failed to create backup directory: {str(e)}")
                    return 0
            
            # Scan for ZIP files
            backup_files = list(self.backup_dir.glob("*.zip"))
            logger.info(f"Found {len(backup_files)} backup files in filesystem")
            
            if backup_files:
                logger.info(f"Backup files: {[f.name for f in backup_files]}")
            else:
                logger.warning("No backup files found in backup directory")
            
            # Get set of existing ZIP filenames
            existing_zip_filenames = {zip_path.name for zip_path in backup_files}
            
            # Step 1: Remove stale database records (ZIP files no longer exist)
            # Preserve all backup types since they are now displayed in history
            all_db_records = db.query(BackupRecord).filter(
                BackupRecord.status == "completed"
            ).all()
            
            logger.info(f"Found {len(all_db_records)} database records")
            
            stale_records_removed = 0
            for record in all_db_records:
                if record.filename not in existing_zip_filenames:
                    logger.info(f"Removing stale database record: {record.filename} (ID={record.id}, type={record.backup_type})")
                    db.delete(record)
                    stale_records_removed += 1
            
            if stale_records_removed > 0:
                db.commit()
                logger.info(f"Removed {stale_records_removed} stale database records")
            
            # Step 2: Create new database records for ZIP files without entries
            new_records_created = 0
            skipped_existing = 0
            errors = 0
            
            for zip_path in backup_files:
                # Check if database record already exists
                existing = db.query(BackupRecord).filter(
                    BackupRecord.filename == zip_path.name
                ).first()
                
                if existing:
                    logger.info(f"Skipped existing: {zip_path.name} (ID={existing.id})")
                    skipped_existing += 1
                    continue
                
                # Extract metadata from ZIP
                metadata = None
                backup_type = "manual"
                created_at = None
                created_by = None
                
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zipf:
                        if METADATA_FILE in zipf.namelist():
                            metadata_content = zipf.read(METADATA_FILE).decode('utf-8')
                            metadata = json.loads(metadata_content)
                            backup_type = metadata.get('backup_type', 'manual')
                            created_at = metadata.get('backup_date')
                            created_by = metadata.get('created_by')
                except Exception as e:
                    logger.warning(f"Could not read metadata from {zip_path.name}: {str(e)}")
                
                # Get file size
                size_bytes = zip_path.stat().st_size
                
                # Create backup record
                try:
                    backup_record = BackupRecord(
                        filename=zip_path.name,
                        file_path=str(zip_path),
                        size_bytes=size_bytes,
                        status="completed",
                        backup_type=backup_type,
                        created_by=created_by,
                        metadata_json=json.dumps(metadata) if metadata else None
                    )
                    
                    # Parse created_at from metadata if available
                    if created_at:
                        try:
                            from datetime import datetime
                            backup_record.created_at = datetime.fromisoformat(created_at)
                        except Exception as e:
                            logger.warning(f"Could not parse created_at from metadata: {str(e)}")
                    
                    db.add(backup_record)
                    db.commit()
                    db.refresh(backup_record)
                    
                    new_records_created += 1
                    logger.info(f"Imported new: {zip_path.name} (ID={backup_record.id}, type={backup_type})")
                    
                except Exception as e:
                    db.rollback()
                    errors += 1
                    logger.error(f"Failed to create backup record for {zip_path.name}: {str(e)}")
            
            logger.info(f"Synchronization completed. Stale removed: {stale_records_removed}, Existing: {skipped_existing}, Imported: {new_records_created}, Errors: {errors}")
            return new_records_created
            
        except Exception as e:
            logger.error(f"Error synchronizing backup history: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return 0
