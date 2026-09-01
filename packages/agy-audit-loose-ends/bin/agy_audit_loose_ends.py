#!/usr/bin/env python3
"""CLI utility for Antigravity Audit Loose Ends.

Commands:
  scan      Scan current workspace or target directory for secrets & open items
  redact    Safely redact secrets in a specific file
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import agy_audit_core as core


def main():
    parser = argparse.ArgumentParser(description="Antigravity Audit Loose Ends CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # scan command
    scan_p = subparsers.add_parser("scan", help="Scan workspace for loose ends & secrets")
    scan_p.add_argument("--cwd", default=os.getcwd(), help="Target workspace path")

    # redact command
    redact_p = subparsers.add_parser("redact", help="Redact secret occurrences in file")
    redact_p.add_argument("file", help="Path to file to redact")

    args = parser.parse_args()

    if args.command == "scan":
        report = core.scan_workspace_records(args.cwd)
        print(core.format_audit_report(report))
        if report["secrets_found"] or report["loose_tasks"]:
            sys.exit(1)
        sys.exit(0)

    elif args.command == "redact":
        target = os.path.abspath(args.file)
        if not os.path.isfile(target):
            print(f"[-] File not found: {target}", file=sys.stderr)
            sys.exit(1)
        content = ""
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        redacted, count = core.redact_secret_text(content)
        if count == 0:
            print("[=] No secrets detected in file.")
        else:
            with open(target, "w", encoding="utf-8") as f:
                f.write(redacted)
            print(f"[+] Redacted {count} secret match(es) in {target}")


if __name__ == "__main__":
    main()
