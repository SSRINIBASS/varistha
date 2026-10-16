# Varistha Production Security Checklist

This checklist documents the security controls and verification gates required before deploying Varistha to a production environment.

## 1. Authentication & Authorization (RBAC)
- [x] **API Key Hashing**: All issued API keys are stored hashed with SHA-256 and salt. Raw tokens are displayed only once upon generation (`var_live_...`).
- [x] **Role Hierarchy**: Strict three-tier RBAC (`admin` > `operator` > `viewer`) enforced in FastAPI dependency middleware.
- [x] **Least Privilege for Agents**: Viewers cannot create keys, store secrets, promote agents, or approve outbound actions.
- [x] **Key Expiration & Revocation**: Keys support optional TTL (`expires_at`) and immediate revocation (`revoked_at`).

## 2. Secrets Handling & Cryptography
- [x] **Encryption at Rest**: All third-party tokens and credentials in the `secrets` table are encrypted using authenticated AES-256-GCM (`v1:<base64>`).
- [x] **Master Key Derivation**: Master symmetric encryption keys derived via HKDF-SHA256 from application `secret_key` or explicit `encryption_key`.
- [x] **Unique Nonces**: Fresh 96-bit cryptographically secure nonces (`os.urandom(12)`) generated per encryption operation to prevent replay and frequency analysis.
- [x] **Zero-Leak Metadata APIs**: Listing secrets returns only `id`, `name`, `description`, and timestamps; plaintext values are strictly omitted.
- [x] **Telemetry & Log Redaction**: OpenTelemetry span attributes and console logs automatically redact `password`, `secret`, `api_key`, `token`, and auth headers using `[REDACTED_SECRET]`.

## 3. Runtime Governance & Autonomy Guardrails
- [x] **Code-Level Autonomy Gates**: Tool permission and approval checks run in Python runtime middleware outside the model. Models cannot bypass approval via prompt overrides.
- [x] **Mandatory Outbound Approvals**: All outbound action plugins (`email-send`, `x-post`, `linkedin-post`) declare `requires_approval: true`. Runs pause with `waiting_approval` at autonomy L1 and L0.
- [x] **Untrusted Output Quarantine**: Web fetch and search plugins declare `untrusted_output: true`. Retrieved content is treated as untrusted and wrapped in structured schemas.
- [x] **Input & Output Guardrail Middleware**: Active guardrail policies inspect inputs and outputs for prompt injection markers, system instruction overrides, and schema compliance.
- [x] **PII Redaction**: Email addresses, phone numbers, and sensitive identifiers are masked before reaching external model providers or traces.

## 4. Web Fetching & SSRF Defense
- [x] **Private IP Blocking**: DNS hostnames resolved to IP addresses before sending HTTP requests in `web-fetch` and `web-scrape`.
- [x] **Reserved Subnet Denylist**: Rejection of `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, and IPv6 equivalents (`::1`, `fc00::/7`, `fe80::/10`).
- [x] **Cloud Metadata Protection**: Direct blocking of `http://169.254.169.254/` to protect AWS/GCP/Azure instance metadata and IAM credentials.
- [x] **Redirect Validation**: HTTP redirects are intercepted and re-validated against SSRF denylists before subsequent hops.
- [x] **Scheme Whitelisting**: Only `http://` and `https://` protocols permitted; `file://`, `gopher://`, `ftp://` strictly rejected.

## 5. Financial & Resource Safety Controls
- [x] **Per-Run Budget Caps**: Runs exceeding `max_usd_per_run` are automatically aborted before subsequent LLM or tool calls.
- [x] **Daily Budget Caps**: Agents whose cumulative daily cost exceeds `max_usd_per_day` cannot be triggered until budget reset.
- [x] **Global Kill Switch**: System-wide emergency killswitch halts all active and queued agent runs deterministically.

## 6. Auditability & Compliance
- [x] **Immutable Stage Transitions**: All lifecycle promotions and demotions recorded in `stage_transitions` audit table with timestamps, user IDs, and gate checklists.
- [x] **Approval Edit Diffs**: All human modifications to proposed tool payloads are captured as diffs for continuous eval calibration.
- [x] **Suppression & Opt-Out Lists**: Email plugins enforce recipient suppression lists before dispatch to ensure compliance with CAN-SPAM, GDPR, and DPDP.
- [x] **No Scraping Evasion**: Avoidance of CAPTCHA bypasses, residential proxy rotation, and ToS circumvention in all core plugins.
