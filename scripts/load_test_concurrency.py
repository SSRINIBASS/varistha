# ruff: noqa: T201
"""CLI load testing and benchmark script for Varistha concurrent agent execution."""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from typing import Any

import httpx


def _make_benchmark_agent_spec(name: str) -> dict[str, Any]:
    """Generate agent spec for load testing."""
    return {
        "apiVersion": "varistha/v1",
        "kind": "Agent",
        "metadata": {
            "name": name,
            "owner": "benchmark@varistha.io",
            "stage": "prototype",
            "version": "1.0.0",
        },
        "spec": {
            "role": "Load test worker for latency and throughput measurement",
            "model": {
                "primary": "gpt-4o",
                "fallback": "ollama/llama3",
            },
            "instructions": "Respond immediately to verify concurrent control plane throughput.",
            "plugins": [{"name": "web-fetch", "enabled": True}],
            "autonomy": "L1",
            "guardrails": {
                "input": ["injection-scan"],
                "output": ["schema-valid"],
            },
            "budget": {
                "max_usd_per_run": 0.50,
                "max_usd_per_day": 10.00,
            },
        },
    }


async def run_benchmark(
    base_url: str,
    concurrency: int,
    total_requests: int,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Execute asynchronous load test against Varistha API."""
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    limits = httpx.Limits(
        max_connections=concurrency * 2,
        max_keepalive_connections=concurrency,
    )
    async with httpx.AsyncClient(
        base_url=base_url,
        headers=headers,
        limits=limits,
        timeout=30.0,
    ) as client:
        # 1. Health check
        try:
            health = await client.get("/health")
            if health.status_code != 200:
                print(
                    f"[!] Target at {base_url} returned health status {health.status_code}",
                    file=sys.stderr,
                )
                return {"error": f"Health check failed with {health.status_code}"}
        except Exception as exc:
            print(f"[!] Unable to connect to {base_url}: {exc}", file=sys.stderr)
            return {"error": str(exc)}

        # 2. Register benchmark agent
        agent_slug = f"load-benchmark-{int(time.time())}"
        reg_resp = await client.post("/api/v1/agents", json=_make_benchmark_agent_spec(agent_slug))
        if reg_resp.status_code not in (200, 201):
            print(f"[!] Failed to register benchmark agent: {reg_resp.text}", file=sys.stderr)
            return {"error": f"Agent registration failed: {reg_resp.status_code}"}

        agent_id = reg_resp.json()["id"]
        print(f"[*] Registered benchmark agent '{agent_slug}' ({agent_id})")
        print(f"[*] Launching {total_requests} runs with concurrency {concurrency}...")

        sem = asyncio.Semaphore(concurrency)
        latencies: list[float] = []
        errors: int = 0

        async def _single_run(index: int) -> None:
            nonlocal errors
            async with sem:
                start = time.perf_counter()
                try:
                    resp = await client.post(
                        f"/api/v1/agents/{agent_id}/runs",
                        json={"input": {"task": f"benchmark-request-{index}"}},
                    )
                    latency = time.perf_counter() - start
                    if resp.status_code == 200 and resp.json().get("status") == "COMPLETED":
                        latencies.append(latency)
                    else:
                        errors += 1
                except Exception:
                    errors += 1

        overall_start = time.perf_counter()
        await asyncio.gather(*[_single_run(i) for i in range(total_requests)])
        total_duration = time.perf_counter() - overall_start

    successful = len(latencies)
    throughput = round(successful / total_duration, 2) if total_duration > 0 else 0.0

    latencies_ms = [round(lat * 1000.0, 2) for lat in sorted(latencies)]
    min_lat = min(latencies_ms) if latencies_ms else 0.0
    max_lat = max(latencies_ms) if latencies_ms else 0.0
    mean_lat = round(statistics.mean(latencies_ms), 2) if latencies_ms else 0.0

    def _pct(p: float) -> float:
        if not latencies_ms:
            return 0.0
        k = (len(latencies_ms) - 1) * p
        f = int(k)
        c = f + 1
        if c < len(latencies_ms):
            return round(latencies_ms[f] + (k - f) * (latencies_ms[c] - latencies_ms[f]), 2)
        return latencies_ms[f]

    stats = {
        "concurrency": concurrency,
        "total_requests": total_requests,
        "successful_requests": successful,
        "failed_requests": errors,
        "total_duration_sec": round(total_duration, 3),
        "throughput_req_per_sec": throughput,
        "latency_ms": {
            "min": min_lat,
            "mean": mean_lat,
            "p50": _pct(0.50),
            "p90": _pct(0.90),
            "p95": _pct(0.95),
            "p99": _pct(0.99),
            "max": max_lat,
        },
    }
    return stats


def main() -> None:
    """Parse CLI flags and run concurrency benchmark."""
    parser = argparse.ArgumentParser(description="Varistha Concurrency Benchmark")
    parser.add_argument("--url", default="http://localhost:8000", help="Target API URL")
    parser.add_argument("-c", "--concurrency", type=int, default=10, help="Concurrent workers")
    parser.add_argument("-n", "--requests", type=int, default=50, help="Total requests to dispatch")
    parser.add_argument("--api-key", default=None, help="Optional X-API-Key auth token")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    results = asyncio.run(
        run_benchmark(
            base_url=args.url.rstrip("/"),
            concurrency=args.concurrency,
            total_requests=args.requests,
            api_key=args.api_key,
        )
    )

    if args.json:
        print(json.dumps(results, indent=2))
        return

    if "error" in results:
        print(f"\n[FAIL] Benchmark failed: {results['error']}")
        sys.exit(1)

    print("\n" + "=" * 50)
    print(" Varistha Concurrency Benchmark Results")
    print("=" * 50)
    print(f" Concurrency Level:    {results['concurrency']}")
    print(f" Total Requests:       {results['total_requests']}")
    print(f" Successful:           {results['successful_requests']}")
    print(f" Failed:               {results['failed_requests']}")
    print(f" Total Duration:       {results['total_duration_sec']}s")
    print(f" Throughput:           {results['throughput_req_per_sec']} req/sec")
    print("-" * 50)
    print(" Latency Percentiles (ms):")
    lats = results["latency_ms"]
    print(f"   Min:   {lats['min']} ms")
    print(f"   Mean:  {lats['mean']} ms")
    print(f"   p50:   {lats['p50']} ms")
    print(f"   p90:   {lats['p90']} ms")
    print(f"   p95:   {lats['p95']} ms")
    print(f"   p99:   {lats['p99']} ms")
    print(f"   Max:   {lats['max']} ms")
    print("=" * 50)


if __name__ == "__main__":
    main()
