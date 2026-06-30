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