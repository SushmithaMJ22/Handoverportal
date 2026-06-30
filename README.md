# Project Handover Documentation System

Full-stack web application for documenting project handovers from Professional Services (PS) to Technical Support.

## Tech Stack

- **Backend**: FastAPI (Python), SQLAlchemy, PostgreSQL
- **Frontend**: React (Vite), Tailwind CSS, Lucide React, Recharts
- **Infrastructure**: Docker, Nginx (Reverse Proxy + SSL)
- **Storage**: Local Filesystem (Dev) / S3-compatible (Prod)

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js (for local frontend development)
- Python 3.11+ (for local backend development)

### Quick Start with Docker

1. Clone the repository.
2. Create a `.env` file in the root (use `backend/.env.example` as a template).
3. Start the system:
   ```bash
   docker-compose up --build
   ```
4. Access the app:
   - Frontend: `http://localhost`
   - API Docs: `http://localhost/api/docs`

### Initial User Setup

The system requires a Super Admin to create other users. You can create the first user via a script or by accessing the database directly:

```python
# Inside backend container
from database import SessionLocal
from models import User, UserRole
from core.security import get_password_hash

db = SessionLocal()
admin = User(
    username="superadmin",
    email="admin@example.com",
    hashed_password=get_password_hash("securepassword"),
    role=UserRole.SUPER_ADMIN
)
db.add(admin)
db.commit()
```

## Features

- **RBAC**: Super Admin, Admin, and User roles.
- **Handover Management**: Full CRUD for handover records with document attachments.
- **Advanced Reporting**: Export stats to PDF, Excel, and CSV.
- **Product Taxonomy**: Cascading dropdowns for AVX, APV, AG, etc.
- **Search & Filter**: Server-side filtering by product, region, engineer, and date.

## Deployment

1. Set up a Linux VM with Docker installed.
2. Point your domain (e.g., `handover.example.com`) to the VM IP.
3. Update `nginx/nginx.conf` with your domain.
4. Use Certbot to generate SSL certificates in `/etc/letsencrypt`.
5. Run `docker-compose up -d`.

## Backup Strategy

Daily `pg_dump` backups are automated via a cron job inside the backend service, with optional upload to S3. See `RUNBOOK.md` for restoration steps.
