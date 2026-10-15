# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.x (pre-release) | ✅ Current development |

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Report security vulnerabilities by emailing: **security@varistha.dev** (or open a GitHub Security Advisory).

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fix

You will receive a response within 48 hours. We will work with you to understand and address the issue before public disclosure.

## Security design principles

- All web/user content treated as **untrusted data** — never injected into system prompts or policies
- Tool permissions enforced in code, **outside the model**
- Outbound actions (email, posts) require human approval at L1 and below
- SSRF protection on all fetch/scrape plugins (private IP ranges blocked)
- Secrets encrypted at rest, never logged or traced
- PII redacted before telemetry export
- No scraping evasion, CAPTCHA bypass, or fake account creation

## Scope

In-scope: the Varistha API, worker, UI, CLI, built-in plugins, Docker Compose deployment.
Out-of-scope: third-party plugins installed by users, the underlying LLM providers.
