#!/bin/sh
set -e

echo "========================================="
echo "  Portal Handover — Backend Startup"
echo "========================================="

echo "[1/4] Waiting for PostgreSQL to be ready..."
# pg_isready is installed in the Dockerfile (postgresql-client)
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" 2>/dev/null; do
  echo "      PostgreSQL not ready yet — retrying in 2s..."
  sleep 2
done
echo "      PostgreSQL is ready."

echo "[2/4] Running Alembic migrations..."
alembic upgrade head
echo "      Migrations applied."

echo "[3/4] Seeding ProductTaxonomy table..."
python seed_taxonomy.py
echo "      Taxonomy seeded."

echo "[4/4] Creating superadmin user (if not exists)..."
python create_superadmin.py
echo "      Superadmin ready."

echo "========================================="
echo "  Starting Uvicorn on 0.0.0.0:8000"
echo "========================================="
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
