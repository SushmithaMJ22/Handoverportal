import logging
from pydantic_settings import BaseSettings
from typing import Optional

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/handover_db"
    SECRET_KEY: str = "supersecretkey123changeinproduction"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    REFRESH_TOKEN_EXPIRE_DAYS: Optional[int] = 7
    S3_BUCKET_NAME: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: Optional[str] = "us-east-1"
    STORAGE_MODE: Optional[str] = "local"
    UPLOAD_DIR: Optional[str] = "./uploads"

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()


def validate_configuration() -> None:
    """
    Validate critical configuration at startup.
    Raises RuntimeError for any detected misconfiguration.
    """
    db_url = settings.DATABASE_URL.lower()

    if db_url.startswith("sqlite"):
        raise RuntimeError(
            "CONFIGURATION ERROR: DATABASE_URL is pointing to SQLite "
            f"('{settings.DATABASE_URL}'). "
            "This application requires PostgreSQL in all environments. "
            "Please set DATABASE_URL to a valid PostgreSQL URL, e.g.: "
            "postgresql://user:password@localhost:5432/handover_db"
        )

    if settings.STORAGE_MODE == "s3" and db_url.startswith("sqlite"):
        raise RuntimeError(
            "CONFIGURATION ERROR: STORAGE_MODE=s3 requires PostgreSQL but "
            "DATABASE_URL is pointing to SQLite. "
            "Both must be set correctly for production use."
        )

    if settings.STORAGE_MODE == "s3":
        missing = []
        if not settings.S3_BUCKET_NAME:
            missing.append("S3_BUCKET_NAME")
        if not settings.AWS_ACCESS_KEY_ID:
            missing.append("AWS_ACCESS_KEY_ID")
        if not settings.AWS_SECRET_ACCESS_KEY:
            missing.append("AWS_SECRET_ACCESS_KEY")
        if missing:
            raise RuntimeError(
                f"CONFIGURATION ERROR: STORAGE_MODE=s3 but the following "
                f"S3 settings are missing: {', '.join(missing)}"
            )

    logger.info(
        "Configuration validated: database=%s storage=%s",
        settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL,
        settings.STORAGE_MODE,
    )
