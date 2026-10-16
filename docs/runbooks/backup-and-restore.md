# Varistha Production Runbook: Backup & Disaster Recovery

This runbook defines the operational procedures for backing up, verifying, and restoring the Varistha Control Plane database and encrypted secrets vault.

---

## 1. Scope and Architecture

A complete Varistha backup consists of two interdependent components:

1. **Relational Database (`PostgreSQL 16 + pgvector`)**:
   - Contains: Agent specs, immutable version history, stage transitions, runs, spans, approvals, budgets, feedback, evals, API keys, and encrypted secrets vault.
   - Storage format: PostgreSQL Custom Dump format (`-Fc`), preserving table structures, schemas, foreign keys, triggers, and pgvector embeddings.
2. **Master Encryption Key (`SECRET_KEY` or `VARISTHA_ENCRYPTION_KEY`)**:
   - The master key from which the 256-bit AES-GCM symmetric encryption key is derived via HKDF-SHA256.
   - **CRITICAL**: The database dump contains encrypted ciphertexts (`v1:<base64>`). Without the matching master encryption key, vault secrets **cannot be recovered**.

---

## 2. Environment Variables

Ensure the following variables from your `.env` file are identified:

```bash
# PostgreSQL Credentials
POSTGRES_DB=varistha
POSTGRES_USER=varistha
POSTGRES_PASSWORD=your_production_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Master Encryption Key (KEEP SECURE)
SECRET_KEY=your_production_master_secret
VARISTHA_ENCRYPTION_KEY=optional_explicit_32_byte_key
```

---

## 3. Backup Procedure

### Method A: Via Docker Compose (Recommended)

Run the backup directly against the running `varistha-postgres` container:

```bash
# 1. Create a timestamped backup directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"

# 2. Execute pg_dump inside container using custom compressed format
docker compose exec -T postgres pg_dump \
  -U varistha \
  -d varistha \
  -Fc \
  --blobs \
  --verbose > "$BACKUP_DIR/varistha_backup_${TIMESTAMP}.dump"

# 3. Generate SHA-256 checksum for tamper evidence
sha256sum "$BACKUP_DIR/varistha_backup_${TIMESTAMP}.dump" > "$BACKUP_DIR/varistha_backup_${TIMESTAMP}.sha256"

echo "Backup completed: $BACKUP_DIR/varistha_backup_${TIMESTAMP}.dump"
```

### Method B: Native `pg_dump` Command

If running PostgreSQL outside Docker:

```bash
pg_dump \
  -h localhost \
  -p 5432 \
  -U varistha \
  -d varistha \
  -Fc \
  --blobs \
  -f "varistha_backup_${TIMESTAMP}.dump"
```

---

## 4. Restoration Procedure

### Step 1: Pre-Restoration Verification
1. Verify checksum integrity of the backup file:
   ```bash
   sha256sum -c "varistha_backup_${TIMESTAMP}.sha256"
   ```
2. Verify the master encryption key in `.env` matches the key used when the backup was created:
   ```bash
   echo "Checking master key presence..."
   grep -E "^(SECRET_KEY|VARISTHA_ENCRYPTION_KEY)=" .env
   ```

### Step 2: Stop Application Containers
To avoid race conditions or dirty writes during restoration, stop the API and worker services:

```bash
docker compose stop api worker ui
```

### Step 3: Restore Database Schema & Data

Restore the database using `pg_restore` with clean replacement:

```bash
# Drop active connections, clean existing objects, and restore
docker compose exec -T postgres pg_restore \
  -U varistha \
  -d varistha \
  --clean \
  --if-exists \
  --no-owner \
  --no-privileges \
  --verbose < "$BACKUP_DIR/varistha_backup_${TIMESTAMP}.dump"
```

*Note: If restoring into a brand-new, empty PostgreSQL instance, ensure the `pgvector` extension is installed before restoration:*
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Step 4: Verify Alembic Migration Status

Verify that the restored database is in sync with the application migration head:

```bash
uv run alembic current
uv run alembic check
```

If the database is behind, apply outstanding migrations:
```bash
uv run alembic upgrade head
```

### Step 5: Restart Application Services

```bash
docker compose start api worker ui
docker compose ps
```

---

## 5. Post-Restoration Data Integrity Verification

Run the following checks to confirm complete recovery:

### 1. Health & Readiness Check
```bash
curl -f http://localhost:8000/health
# Expected: {"status":"healthy"}
```

### 2. Verify Core Entities
```bash
# Check agents list
curl -s http://localhost:8000/api/v1/agents | jq '.total'

# Check approvals list
curl -s http://localhost:8000/api/v1/approvals | jq '.total'
```

### 3. Verify Secrets Vault Decryption
Test that stored secrets can be decrypted with the active master key:

```bash
# Query a known secret through the API (Admin role required)
curl -s -H "X-API-Key: $ADMIN_API_KEY" http://localhost:8000/api/v1/auth/secrets
```

If the master key is incorrect or missing, the API will return HTTP 500 with a typed `DecryptionError` indicating ciphertext tamper or key mismatch.

---

## 6. Disaster Recovery Scenarios

| Scenario | Recovery Action |
| :--- | :--- |
| **Accidental Data Deletion** | Stop API, restore from latest hourly/daily dump via Step 3, restart API. |
| **Hardware / Host Failure** | Provision new host, copy `.env` (including `SECRET_KEY`), restore dump via `pg_restore`, run `docker compose up -d`. |
| **Master Key Loss** | **IRREVERSIBLE for secrets**. Database rows, specs, and traces are intact, but `secrets` table must be purged and re-populated with fresh API credentials. |
| **Key Rotation** | Export all secrets into memory using old key, update `.env` with new key, re-encrypt and update database rows. |

---

## 7. Automated Daily Backups (Cron Example)

Place the following script in `/etc/cron.daily/varistha-backup`:

```bash
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/var/backups/varistha"
RETENTION_DAYS=14
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Perform backup
docker exec -t varistha-postgres pg_dump -U varistha -d varistha -Fc > "$BACKUP_DIR/varistha_${TIMESTAMP}.dump"
sha256sum "$BACKUP_DIR/varistha_${TIMESTAMP}.dump" > "$BACKUP_DIR/varistha_${TIMESTAMP}.sha256"

# Rotate backups older than retention window
find "$BACKUP_DIR" -type f -name "varistha_*.dump" -mtime +"$RETENTION_DAYS" -delete
find "$BACKUP_DIR" -type f -name "varistha_*.sha256" -mtime +"$RETENTION_DAYS" -delete
```
