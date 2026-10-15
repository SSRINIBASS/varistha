"""Convert Bandit JSON output from stdin to GitHub Actions workflow commands and step summary."""

import json
import os
import sys


def main() -> None:
    """Parse Bandit JSON from stdin and emit GitHub Actions annotations and summary."""
    raw_input = sys.stdin.read()
    if not raw_input.strip():
        return

    try:
        data = json.loads(raw_input)
    except Exception:
        sys.stdout.write(raw_input + "\n")
        return

    results = data.get("results", [])
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")

    for issue in results:
        sev = issue.get("issue_severity", "LOW")
        filename = issue.get("filename", "")
        line = issue.get("line_number", 1)
        test_id = issue.get("test_id", "")
        text = issue.get("issue_text", "").replace("\n", " ")

        prefix = "::error" if sev in ("HIGH", "MEDIUM") else "::notice"
        msg = f"{prefix} file={filename},line={line}::[Bandit {test_id} {sev}] {text}\n"
        sys.stdout.write(msg)

    if summary_path and os.path.exists(os.path.dirname(summary_path)):
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write("\n### 🛡️ Bandit Security Scan\n")
            f.write(f"- **Total Issues Identified:** {len(results)}\n")
            if results:
                f.write("\n| Severity | File | Line | Issue |\n|---|---|---|---|\n")
                for iss in results[:20]:
                    s = iss.get("issue_severity", "LOW")
                    fn = os.path.basename(iss.get("filename", ""))
                    ln = iss.get("line_number", 1)
                    t = iss.get("issue_text", "")[:80]
                    f.write(f"| {s} | `{fn}` | {ln} | {t} |\n")


if __name__ == "__main__":
    main()
