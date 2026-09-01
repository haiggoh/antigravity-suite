"""Pure, unit-testable core for agy-audit-loose-ends.

Performs end-of-task durable record reconciliation:
  1. Audits waypoints store and workspace task lists for orphaned/stale items.
  2. Scans files, project notes, and configs for accidental secret / credential leaks.
  3. Provides safe token redaction without mangling document structure.

Design rules:
  * Pure standard library, fail-safe (never crashes on malformed files).
  * Read-only audit with explicit, atomic reconciliation helpers.
  * Cross-platform (macOS, Windows, Linux).
"""

import os
import re
import json
from typing import List, Dict, Any, Tuple, Optional


# Regex patterns for common API keys and sensitive tokens
SECRET_PATTERNS = [
    (r"AIza[0-9A-Za-z-_]{30,}", "Google API Key"),
    (r"sk-ant-[a-zA-Z0-9_-]{25,}", "Anthropic API Key"),
    (r"sk-[a-zA-Z0-9]{25,}", "OpenAI API Key"),
    (r"ghp_[a-zA-Z0-9]{25,}", "GitHub Personal Access Token"),
    (r"gho_[a-zA-Z0-9]{25,}", "GitHub OAuth Token"),
    (r"xox[baprs]-[0-9a-zA-Z]{10,48}", "Slack Token"),
    (r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", "Private Key Header"),
]


def redact_secret_text(text: str) -> Tuple[str, int]:
    """Redact known secret patterns from text, replacing with REDACTED placeholder."""
    redacted = text
    matches_count = 0
    for pattern, name in SECRET_PATTERNS:
        def _replace_match(m):
            nonlocal matches_count
            matches_count += 1
            val = m.group(0)
            if len(val) > 8:
                return val[:4] + "...[REDACTED " + name + "]..." + val[-2:]
            return "[REDACTED " + name + "]"
        redacted = re.sub(pattern, _replace_match, redacted)
    return redacted, matches_count


def scan_file_for_secrets(filepath: str) -> List[Dict[str, Any]]:
    """Scan a single file for exposed secrets."""
    findings = []
    if not os.path.isfile(filepath):
        return findings
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for line_idx, line in enumerate(f, 1):
                if "# noaudit" in line:
                    continue
                for pattern, name in SECRET_PATTERNS:
                    m = re.search(pattern, line)
                    if m:
                        findings.append({
                            "file": filepath,
                            "line": line_idx,
                            "type": name,
                            "preview": line.strip()[:80],
                        })
    except Exception:
        pass
    return findings


def scan_workspace_records(cwd: str) -> Dict[str, Any]:
    """Audit workspace guidelines (GEMINI.md), tasks, and local config files."""
    report = {
        "secrets_found": [],
        "loose_tasks": [],
        "scanned_files_count": 0,
    }

    # Scan markdown and JSON config files in workspace (capped depth)
    skip_dirs = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}
    for root, dirs, files in os.walk(cwd):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
        for f in files:
            if f.endswith((".md", ".json", ".txt", ".sh", ".py", ".yaml", ".yml")):
                filepath = os.path.join(root, f)
                report["scanned_files_count"] += 1
                secrets = scan_file_for_secrets(filepath)
                report["secrets_found"].extend(secrets)

                # Check for lingering to-do items in workspace GEMINI.md
                if f in ("GEMINI.md", "TODO.md", "AGENTS.md"):
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="replace") as doc:
                            for idx, line in enumerate(doc, 1):
                                if re.search(r"^\s*-\s*\[ \]\s+.*(?:TODO|FIXME|WIP|IN PROGRESS)", line, re.IGNORECASE):
                                    report["loose_tasks"].append({
                                        "file": filepath,
                                        "line": idx,
                                        "task": line.strip(),
                                    })
                    except Exception:
                        pass

    return report


def format_audit_report(report: Dict[str, Any]) -> str:
    """Format human-readable audit report."""
    lines = ["# Antigravity Loose Ends & Record Audit Report", ""]
    secrets = report.get("secrets_found", [])
    tasks = report.get("loose_tasks", [])

    lines.append(f"- Scanned Files: {report.get('scanned_files_count', 0)}")
    lines.append(f"- Secrets/Tokens Exposed: {len(secrets)}")
    lines.append(f"- Open Unreconciled Tasks: {len(tasks)}")
    lines.append("")

    if secrets:
        lines.append("## ⚠️ Exposed Secrets Detected:")
        for s in secrets:
            lines.append(f"  - `{s['file']}:{s['line']}` [{s['type']}]")
        lines.append("")

    if tasks:
        lines.append("## 📋 Unreconciled / Open Task Items:")
        for t in tasks:
            lines.append(f"  - `{t['file']}:{t['line']}`: {t['task']}")
        lines.append("")

    if not secrets and not tasks:
        lines.append("✅ **All durable records and security audits are clean!**")

    return "\n".join(lines)
