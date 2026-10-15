# Varistha

**Open-source control plane to build, run, monitor and govern AI agents for startups.**

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

Varistha is a self-hostable control plane where a startup installs AI employees as role packs, then runs them under real operational discipline: a registry, lifecycle stages, observability, evals, guardrails and human approvals.

## Three Pillars

1. **Build:** Declarative agent spec, role packs, plugins that toggle on and off per agent.
2. **Run:** Durable runtime, triggers (schedule, webhook, manual), approval inbox, budgets, kill switch.
3. **Govern (AgentOps):** Traces, evals, feedback, confidence signals, guardrails, lifecycle promotion.

## Quick Start

```bash
git clone https://github.com/SSRINIBASS/varistha.git
cd varistha
cp deploy/.env.example deploy/.env
docker compose -f deploy/docker-compose.yml up
```

Then open [http://localhost:3000](http://localhost:3000).

## Status

🚧 **Pre-alpha** — under active development. See the [CHANGELOG](CHANGELOG.md) for progress.

## License

Apache-2.0 — see [LICENSE](LICENSE).
