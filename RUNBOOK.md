# Project Handover System - Runbook

## Disaster Recovery Plan

| Scenario | RTO | RPO | Action |
|----------|-----|-----|--------|
| App server crash | < 30 min | < 24 hrs | Redeploy container; DB intact |
| DB corruption | < 2 hrs | < 24 hrs | Restore latest pg_dump from S3 |
| Full server loss | < 4 hrs | < 24 hrs | Provision new VM; restore DB + files |

## Database Restore Steps

1. **Identify the latest backup**:
   Check S3 bucket `backups/` or local backup storage.

2. **Download and decompress**:
   ```bash
   gunzip backup_YYYYMMDD.sql.gz
   ```

3. **Restore to PostgreSQL**:
   ```bash
   psql -h <db_host> -U <db_user> -d <db_name> -f backup_YYYYMMDD.sql
   ```

## Monthly Restore Drill

1. Create a staging database: `handover_db_staging`.
2. Follow the restore steps above using the latest production backup.
3. Verify data integrity by logging in with a test admin account.
4. Check if files are accessible (if stored locally, sync from production; if S3, pre-signed URLs should work).

## Monitoring & Backups

- Backups are scheduled via cron at 02:00 UTC daily.
- Retention: 30 daily backups, weekly backups for 3 months.
- Logs are available in the `backend` container logs.
