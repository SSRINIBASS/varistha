# ADR 0022: Outbound and Communication Plugins (Email-Draft, Email-Send, X-Post, LinkedIn-Post)

## Status
Accepted

## Context
In accordance with `docs/SPEC.md § 5 (Phase 5: Plugin ecosystem and role packs)`, `§ 3.1 (Autonomy Levels L0-L4)`, and `§ 3.3 (Governance and Approvals)`:
1. **Outbound Approval Gating**: Outbound actions (email dispatch, social media publishing, CRM mutations) require human approval at autonomy level L1 and below. No code path may bypass this.
2. **Internal vs. Outbound Separation**: Drafting an email is an internal composition action that runs autonomously at L1, whereas sending an email or publishing a post to social networks is an outbound action strictly flagged `requires_approval: true`.
3. **Regulatory Compliance and Suppression**: Cold email touches CAN-SPAM, GDPR, and India's DPDP Act. Outbound plugins must ship with an opt-out/suppression list and safety validation.
4. **Official APIs Only**: In adherence to `docs/SPEC.md § A.12`, Varistha uses official APIs (or mock simulation for test/dry-run environments) and strictly avoids scraping evasion or Terms-of-Service circumvention.

## Decision

### 1. `email-draft` Plugin (`plugins/email-draft/`)
- Contextual email composer that creates personalized, tokenized draft emails:
  - Supports template placeholder substitution (`{{first_name}}`, `{{company}}`, `{{topic}}`, `{{call_to_action}}`).
  - Supports tone selection (`professional`, `friendly`, `persuasive`, `concise`) with contextual greetings and sign-offs.
  - Automatically generates inbox preview snippets (first 100 characters).
  - Internal action: `requires_approval: false`.

### 2. `email-send` Plugin (`plugins/email-send/`)
- Outbound transactional email sender supporting SMTP, Resend/SendGrid APIs, and dry-run simulation:
  - Enforces mandatory human approval gating (`requires_approval: true`).
  - Enforces recipient and domain suppression list checks (`RecipientSuppressedError`) to ensure CAN-SPAM, GDPR, and DPDP compliance.
  - Generates deterministic simulated delivery in test mode (`dry_run: true`).

### 3. `x-post` Plugin (`plugins/x-post/`)
- Outbound social publishing plugin for X (formerly Twitter) using official v2 API conventions:
  - Enforces mandatory human approval gating (`requires_approval: true`).
  - Strictly validates character count (1 to 280 characters).
  - Supports parent tweet ID threading (`reply_to_id`).
  - Supports deterministic mock simulation for local development and CI testing.

### 4. `linkedin-post` Plugin (`plugins/linkedin-post/`)
- Outbound professional publishing plugin for LinkedIn using Community Management UGC API conventions:
  - Enforces mandatory human approval gating (`requires_approval: true`).
  - Validates character count (1 to 3000 characters) and visibility settings (`PUBLIC`, `CONNECTIONS`).
  - Supports article preview link attachments.
  - Supports deterministic mock simulation.

### 5. Architectural Cleanliness & Schema Modularization
- Extracted LiteLLM function calling schemas to `apps/api/src/plugins/definitions.py`, keeping `PluginHost` (`host.py`) concise and well under the 300-line limit (273 lines).
- Refined runtime approval interception in `apps/api/src/runtime/adapter.py` so internal drafts are distinguished from outbound transmissions.

## Consequences
- **Positive**: Complete set of communication plugins available with explicit approval gating and compliance safeguards.
- **Positive**: Both `host.py` and `definitions.py` adhere to the < 300 lines modularity requirement.
- **Positive**: 79 plugin tests and 363 total pytest tests pass with 100% coverage, 0 pyright errors, and 0 lint warnings.
