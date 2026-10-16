# Implementation Plan: Phase 6 Task 5 - Concurrency & Load Testing (10 Concurrent Agents Stable)

## Objective
Implement and verify the Phase 6 exit criterion specified in `docs/SPEC.md § 5`:
> "Exit: security checklist complete, 10 concurrent agents stable."

We will demonstrate that Varistha's Control Plane API, asynchronous SQLite/PostgreSQL connection pool, runtime execution pipeline, contextvars-based span buffering, and policy guardrails stably execute **10+ concurrent agents** without race conditions, transaction deadlocks, span leakage, or memory degradation.

---

## Deliverables

1. **`apps/api/src/runtime/tests/test_concurrency_load.py`**
   - High-concurrency automated test suite:
     - `test_ten_concurrent_agents_independent_execution`: Spawns 10 distinct agents concurrently via `asyncio.gather()`. Each executes a complete agent run with LLM call, span creation, and token/cost accumulation. Verifies all 10 runs complete successfully with unique run IDs, independent span lists, and accurate status.
     - `test_concurrent_approval_interrupts`: Spawns 10 concurrent agents triggering approval-gated outbound actions simultaneously. Verifies all 10 enter `WAITING_APPROVAL`, emit `approval.wait` spans, and generate distinct `Approval` records without database lock contention.
     - `test_concurrent_span_isolation`: Verifies that `capture_run_spans` contextvars properly isolate concurrent asyncio tasks so spans from Agent A never leak into Agent B's buffer.
     - `test_high_concurrency_burst`: Executes 25 concurrent agent trigger requests, validating database connection pooling resilience, transaction rollback safety, and sub-second p95 latencies.

2. **`scripts/load_test_concurrency.py`**
   - Standalone CLI load testing benchmark tool:
     - Asynchronously benchmarks any Varistha server endpoint using `httpx.AsyncClient`.
     - Supports arguments: `--url`, `--concurrency` (default 10), `--requests` (default 50), `--output`.
     - Measures: Total duration, throughput (req/s), latency percentiles (min, p50, p90, p95, p99, max), and error rate.
     - Produces both human-readable ANSI terminal output and JSON/Markdown summary.

3. **`docs/benchmarks/load-test-concurrency.md`**
   - Benchmark report detailing the concurrency test methodology, system specifications, latency curves, database connection performance, and exit criteria sign-off.

---

## Acceptance Criteria
- [x] 10 concurrent agents execute and complete without errors or deadlocks.
- [x] Zero cross-contamination between concurrent trace buffers.
- [x] Zero pyright, ruff, or architectural boundary errors.
- [x] Full test suite passes with >= 80% coverage.
