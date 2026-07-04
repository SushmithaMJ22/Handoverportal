FROM python:3.11-slim

WORKDIR /app

# Install postgresql-client for pg_dump and pg_isready
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer-cached)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Create backup directory
RUN mkdir -p /app/backups

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
