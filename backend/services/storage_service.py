import os
import shutil
import boto3
from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse
from core.config import settings

class StorageService:
    def __init__(self):
        self.mode = settings.STORAGE_MODE
        if self.mode == "s3":
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            self.bucket = settings.S3_BUCKET_NAME

    async def save_file(self, file: UploadFile, sub_dir: str) -> str:
        if self.mode == "local":
            upload_path = os.path.join(settings.UPLOAD_DIR, sub_dir)
            os.makedirs(upload_path, exist_ok=True)
            file_path = os.path.join(upload_path, file.filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            return file_path
        else:
            # S3 logic
            key = f"{sub_dir}/{file.filename}"
            try:
                self.s3.upload_fileobj(file.file, self.bucket, key)
                return key
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(e)}")

    def delete_file(self, file_path: str):
        if self.mode == "local":
            if os.path.exists(file_path):
                os.remove(file_path)
        else:
            try:
                self.s3.delete_object(Bucket=self.bucket, Key=file_path)
            except Exception:
                pass

    def get_file_response(self, file_path: str, filename: str):
        if self.mode == "local":
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="File not found")
            return FileResponse(file_path, filename=filename)
        else:
            # Generate pre-signed URL for S3
            try:
                url = self.s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket, 'Key': file_path},
                    ExpiresIn=3600
                )
                return {"url": url}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to generate S3 URL: {str(e)}")

storage_service = StorageService()
