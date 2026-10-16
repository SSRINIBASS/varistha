# Plan: Phase 6 Task 2 — Secrets Handling Review & Transparent Encryption at Rest

## Context & Spec Reference
- `docs/SPEC.md § 4.1`: "Secrets: encrypted in Postgres for v0, OpenBao or Infisical adapter later | env vars"
- `docs/SPEC.md § 4.2`: "`secrets`, `api_keys`, `audit_log`..."
- `docs/SPEC.md § 5 (Phase 6)`: "secrets handling review, threat-model pass (prompt injection, SSRF in fetch plugins, credential leakage)"
- `AGENTS.md`: "Never log or trace secrets. Redact PII before export. Secrets are encrypted at rest."

## Architecture & Design Decisions
1. **Authenticated AES-256-GCM Encryption (`shared/crypto.py`)**:
   - Master key derived deterministically using HKDF-SHA256 from `settings.secret_key` and salt `"varistha-secrets-v1"`, or explicit 32-byte `settings.encryption_key`.
   - Each encryption creates a fresh cryptographically random 12-byte IV/nonce (`secrets.token_bytes(12)`).
   - Ciphertext format: `v1:<base64(nonce + tag + ciphertext)>`.
   - Authenticated encryption detects any tampering or bit flips.
2. **Database Model & Migration**:
   - `shared/db/models/secrets.py`: `Secret` model with `id`, `name`, `encrypted_value`, `description`, `created_at`, `updated_at`.
   - Migration `0007_secrets_vault.py`.
   - Update `shared/tests/test_migrations.py`.
3. **Secrets Management Service & Endpoints**:
   - `identity/secrets_service.py`: `store_secret`, `resolve_secret`, `list_secret_metadata`, `delete_secret`.
   - `identity/router.py`: REST routes for admin management of secrets vault (`POST /secrets`, `GET /secrets`, `DELETE /secrets/{name}`).
   - API responses NEVER return secret values in listings or traces.
4. **Testing**:
   - `shared/tests/test_crypto.py`: AES-256-GCM roundtrip, tampering resistance, nonce entropy.
   - `identity/tests/test_secrets.py`: Secret storage, retrieval, RBAC enforcement (admin vs operator vs viewer).
