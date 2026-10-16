"""Utility script to query GitHub Actions workflow runs."""

from __future__ import annotations

import json
import sys
import urllib.request

url = "https://api.github.com/repos/SSRINIBASS/varistha/actions/runs?per_page=10"
req = urllib.request.Request(url, headers={"User-Agent": "Varistha-CI-Checker"})

try:
    with urllib.request.urlopen(req) as resp:  # noqa: S310
        data = json.loads(resp.read().decode())
        runs = data.get("workflow_runs", [])
        for r in runs:
            run_id = r["id"]
            name = r["name"]
            branch = r["head_branch"]
            sha = r["head_sha"][:7]
            status = r["status"]
            conclusion = r["conclusion"]
            print(f"{run_id}: {name} on {branch} ({sha}) - {status}/{conclusion}")  # noqa: T201
except Exception as e:
    print(f"Error fetching runs: {e}", file=sys.stderr)  # noqa: T201
