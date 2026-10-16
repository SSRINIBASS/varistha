#!/usr/bin/env bash
# =============================================================================
# Varistha PostgreSQL & pgvector Automated Backup Utility
# =============================================================================

set -euo pipefail

BACKUP_DIR="${1:-./backups}"
POSTGRES_USER="${POSTGRES_USER:-varistha}"
POSTGRES_DB="${POSTGRES_DB:-varistha}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/varistha_backup_${TIMESTAMP}.dump"
CHECKSUM_FILE="${BACKUP_FILE}.sha256"

mkdir -p "$BACKUP_DIR"

echo "[*] Initiating Varistha PostgreSQL backup..."
echo "[*] Database: ${POSTGRES_DB}"
echo "[*] Destination: ${BACKUP_FILE}"

# Execute custom format pg_dump
if command -v docker &> /dev/null && docker ps --format '{{.Names}}' | grep -q 'varistha-postgres'; then
    echo "[*] Dumping via docker compose exec..."
    docker compose exec -T postgres pg_dump \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        -Fc \
        --blobs \
        > "$BACKUP_FILE"
elif command -v pg_dump &> /dev/null; then
    echo "[*] Dumping via local pg_dump..."
    pg_dump \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        -Fc \
        --blobs \
        -f "$BACKUP_FILE"
else
    echo "[!] Error: Neither running docker container nor local pg_dump found." >&2
    exit 1
fi

# Generate SHA-256 Checksum
if command -v sha256sum &> /dev/null; then
    sha256sum "$BACKUP_FILE" > "$CHECKSUM_FILE"
elif command -v shasum &> /dev/null; then
    shasum -a 256 "$BACKUP_FILE" > "$CHECKSUM_FILE"
fi

echo "[+] Backup successfully completed:"
echo "    Dump:     ${BACKUP_FILE}"
echo "    Checksum: ${CHECKSUM_FILE}"
