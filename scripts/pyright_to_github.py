"""Convert Pyright JSON output from stdin to GitHub Actions workflow commands and step summary."""

import json
import os
import sys


def main() -> None:
    """Parse Pyright JSON from stdin and emit GitHub Actions annotations and summary."""
    raw_input = sys.stdin.read()
    if not raw_input.strip():
        return

    try:
        data = json.loads(raw_input)
    except Exception:
        sys.stdout.write(raw_input + "\n")
        return

    diagnostics = data.get("generalDiagnostics", [])
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")

    error_count = 0
    warning_count = 0

    for d in diagnostics:
        severity = d.get("severity", "information")
        file_path = d.get("file", "")
        range_info = d.get("range", {}).get("start", {})
        line = range_info.get("line", 0) + 1
        col = range_info.get("character", 0) + 1
        message = d.get("message", "").replace("\n", " ")

        if severity == "error":
            error_count += 1
            cmd = f"::error file={file_path},line={line},col={col}::[Pyright] {message}\n"
            sys.stdout.write(cmd)
        elif severity == "warning":
            warning_count += 1
            cmd = f"::warning file={file_path},line={line},col={col}::[Pyright] {message}\n"
            sys.stdout.write(cmd)

    if summary_path and os.path.exists(os.path.dirname(summary_path)):
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write("\n### 🔍 Pyright Type Check\n")
            f.write(f"- **Errors:** {error_count}\n")
            f.write(f"- **Warnings:** {warning_count}\n")
            if diagnostics:
                f.write("\n| Severity | File | Line | Message |\n|---|---|---|---|\n")
                for d in diagnostics[:20]:
                    s = d.get("severity", "info")
                    fp = os.path.basename(d.get("file", ""))
                    ln = d.get("range", {}).get("start", {}).get("line", 0) + 1
                    msg = d.get("message", "").replace("\n", " ")[:80]
                    f.write(f"| {s} | `{fp}` | {ln} | {msg} |\n")


if __name__ == "__main__":
    main()
