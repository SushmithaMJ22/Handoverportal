import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings, validate_configuration
from database import engine, Base
from routers import auth, handovers, reports, users, customers, meta, backup
from services.backup_scheduler import scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

# Validate configuration before anything else starts
validate_configuration()

# Create database tables (idempotent; real schema management done via Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Project Handover System", redirect_slashes=False)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(customers.router)
app.include_router(handovers.router)
app.include_router(reports.router)
app.include_router(meta.router)
app.include_router(backup.router)


@app.on_event("startup")
def startup_event():
    """Start the backup scheduler on application startup."""
    from database import SessionLocal
    
    # Log configuration paths
    logging.info(f"Windows Backup Path: {settings.BACKUP_DIR_HOST}")
    logging.info(f"Windows Uploads Path: {settings.UPLOADS_DIR_HOST}")
    logging.info(f"Docker Backup Path: {settings.BACKUP_DIR}")
    logging.info(f"Docker Uploads Path: {settings.LOCAL_UPLOADS_DIR}")
    
    # Ensure Docker internal directories exist
    try:
        Path(settings.BACKUP_DIR).mkdir(parents=True, exist_ok=True)
        Path(settings.LOCAL_UPLOADS_DIR).mkdir(parents=True, exist_ok=True)
        logging.info("Docker internal directories ensured")
    except Exception as e:
        logging.error(f"Failed to create Docker internal directories: {str(e)}")
        # Continue anyway - Docker volumes should handle this
    
    # Synchronize backup history from filesystem
    try:
        db = SessionLocal()
        try:
            from services.backup_service import BackupService
            backup_service = BackupService()
            backup_service.sync_backup_history(db)
            logging.info("Backup history synchronized from filesystem")
        finally:
            db.close()
    except Exception as e:
        logging.error(f"Error synchronizing backup history: {str(e)}")
        # Continue anyway - this is not critical
    
    scheduler.start(SessionLocal)
    logging.info("Backup scheduler started on application startup")


@app.on_event("shutdown")
def shutdown_event():
    """Stop the backup scheduler on application shutdown."""
    scheduler.stop()
    logging.info("Backup scheduler stopped on application shutdown")


@app.get("/")
def read_root():
    return {"message": "Welcome to Project Handover API"}
