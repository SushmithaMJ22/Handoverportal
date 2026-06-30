import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings, validate_configuration
from database import engine, Base
from routers import auth, handovers, reports, users, customers, meta

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


@app.get("/")
def read_root():
    return {"message": "Welcome to Project Handover API"}
