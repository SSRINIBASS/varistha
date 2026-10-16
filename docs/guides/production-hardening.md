# Production Hardening & Operations Guide

This guide details best practices for deploying, securing, and maintaining Varistha in production environments.

---

## 1. Production Architecture Topology

```
             Internet / Clients
                     |
              [ HTTPS :443 ]
                     v
          +--------------------+
          |   Reverse Proxy    |
          |  (Caddy / Nginx)   |
          +----+----------+----+
               |          |
        [ /api /healthz ] | [ / (UI) ]
               |          |
               v          v
          +---------+  +--------+
          | FastAPI |  | Next.js|
          |  (:8000)|  | (:3000)|
          +----+----+  +--------+
               |
      +--------+--------+
      |                 |
      v                 v
+------------+   +--------------+
| PostgreSQL |   | Worker Pool  |
| 16 + vector|   | (Background) |
+------------+   +------+-------+
                        |
                        v
                 +--------------+
                 |OTel Collector|
                 | (Port 4318)  |
                 +--------------+
```

---

## 2. Reverse Proxy & TLS Configuration

Never expose FastAPI or Next.js directly to the public internet. Use Caddy or Nginx for TLS termination and header sanitization.

### Recommended Caddyfile
```caddy
varistha.example.com {
    encode gzip zstd

    # API and Health endpoints
    handle /api/* {
        reverse_proxy api:8000
    }
    handle /healthz {
        reverse_proxy api:8000
    }

    # Control Plane UI
    handle {
        reverse_proxy ui:3000
    }
}
```

---

## 3. Security Configuration Checklist

### 1. Enable Mandatory Authentication
Set `AUTH_ENABLED=true` in `deploy/.env`. When enabled:
- All API routes require an authenticated API Key (`X-API-Key` or `Authorization: Bearer <key>`).
- Access is strictly governed by RBAC roles (`admin`, `operator`, `viewer`).
- Generate an initial admin key via CLI:
  ```bash
  varistha auth keys create --name "prod-ci-admin" --role admin
  ```

### 2. Configure AES-256-GCM Master Encryption Key
Ensure `SECRET_KEY` is a cryptographically secure 32-byte hex string:
```bash
openssl rand -hex 32
```
All secrets stored in the Varistha vault (`/api/v1/auth/secrets`) are encrypted at rest with AES-256-GCM using deterministic HKDF key derivation.

### 3. Untrusted Data Labeling & SSRF
Varistha automatically quarantines untrusted outputs from web scrapes and external APIs. Ensure network egress from worker containers is firewalled so that internal cloud metadata IPs (`169.254.169.254`) and private RFC 1918 subnets are inaccessible.

---

## 4. Automated Backup & Disaster Recovery

Set up a daily automated database backup cron job:

```bash
# Add to crontab (runs daily at 02:00 AM)
0 2 * * * /opt/varistha/scripts/backup_postgres.sh /var/backups/varistha >> /var/log/varistha-backup.log 2>&1
```

For complete recovery steps and migration verification, refer to the [Backup & Restore Runbook](../runbooks/backup-and-restore.md).

---

## 5. Observability & OpenTelemetry Fan-Out

To export traces to Langfuse or Grafana Tempo:

1. Launch with the OTel Collector profile:
   ```bash
   docker compose -f deploy/docker-compose.yml --profile otel up -d
   ```
2. Configure export endpoints in `deploy/.env`:
   ```bash
   OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector:4318"
   LANGFUSE_HOST="https://cloud.langfuse.com"
   LANGFUSE_AUTH_HEADER="Basic <base64(pk:sk)>"
   ```
3. See [OTel Fan-Out Documentation](../observability/otel-fanout.md) for full architecture details.

---

## 6. Emergency Incident Response

If an agent behaves unexpectedly or experiences an abnormal loop:

1. **Trip Single Agent Kill Switch**:
   ```bash
   varistha kill <agent-id-or-name>
   ```
2. **Trip Global Emergency Stop (Halts All Agents Immediately)**:
   ```bash
   varistha emergency-stop --enable
   ```
3. Verify status:
   ```bash
   varistha emergency-stop --status
   ```
