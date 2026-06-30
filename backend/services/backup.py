import os
import subprocess
from datetime import datetime
import boto3
from core.config import settings

def run_backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_{timestamp}.sql.gz"
    
    # Run pg_dump
    # Note: Assumes DATABASE_URL is in a format pg_dump can use or split it
    # For simplicity in this script, we use environment variables
    db_host = os.getenv("DB_HOST", "localhost")
    db_user = os.getenv("DB_USER", "user")
    db_name = os.getenv("DB_NAME", "handover_db")
    
    try:
        cmd = f"pg_dump -h {db_host} -U {db_user} {db_name} | gzip > {backup_file}"
        subprocess.run(cmd, shell=True, check=True)
        
        # Upload to S3 if configured
        if settings.STORAGE_MODE == "s3":
            s3 = boto3.client('s3')
            s3.upload_file(backup_file, settings.S3_BUCKET_NAME, f"backups/{backup_file}")
            print(f"Backup uploaded to S3: {backup_file}")
            
        print(f"Backup completed successfully: {backup_file}")
        
    except Exception as e:
        print(f"Backup failed: {str(e)}")

if __name__ == "__main__":
    run_backup()
