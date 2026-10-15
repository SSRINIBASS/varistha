"""Convert pip-audit JSON output from stdin to GitHub Actions workflow commands and step summary."""

import json
import os
import sys


def main() -> None:
    """Parse pip-audit JSON from stdin and emit GitHub Actions annotations and summary."""
    raw_input = sys.stdin.read()
    if not raw_input.strip():
        return

    try:
        data = json.loads(raw_input)
    except Exception:
        sys.stdout.write(raw_input + "\n")
        return

    dep_list = data if isinstance(data, list) else data.get("dependencies", [])
    vulns_found = []

    for dep in dep_list:
        name = dep.get("name", "")
        version = dep.get("version", "")
        for vuln in dep.get("vulns", []):
            vuln_id = vuln.get("id", "")
            description = vuln.get("description", "").replace("\n", " ")[:100]
            vulns_found.append((name, version, vuln_id, description))
            sys.stdout.write(
                f"::error::[pip-audit] {name}=={version} vulnerable to {vuln_id}: {description}\n"
            )

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path and os.path.exists(os.path.dirname(summary_path)):
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write("\n### 📦 Dependency Vulnerability Audit (pip-audit)\n")
            f.write(f"- **Vulnerabilities Found:** {len(vulns_found)}\n")
            if vulns_found:
                f.write("\n| Package | Version | Advisory | Description |\n|---|---|---|---|\n")
                for pkg, ver, adv, desc in vulns_found:
                    f.write(f"| `{pkg}` | `{ver}` | `{adv}` | {desc} |\n")


if __name__ == "__main__":
    main()
