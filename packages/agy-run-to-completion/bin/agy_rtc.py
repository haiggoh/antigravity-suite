#!/usr/bin/env python3
"""CLI utility for Antigravity Run To Completion & Autopilot.

Commands:
  triage    Score and partition tasks in a file into Do-Now, Heavy, and Gated
  ungate    Generate clarifying questions for gated tasks sorted by cheapness
  closeout  Generate end-of-run closeout summary
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import agy_rtc_core as core


def main():
    parser = argparse.ArgumentParser(description="Antigravity Autonomous Task Triage & Execution CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # triage command
    triage_p = subparsers.add_parser("triage", help="Triage task items from file")
    triage_p.add_argument("file", help="Path to markdown task list file (e.g. GEMINI.md)")

    # ungate command
    ungate_p = subparsers.add_parser("ungate", help="Format ungate questions for blocked items")
    ungate_p.add_argument("file", help="Path to markdown task list file")

    args = parser.parse_args()

    if args.command in ("triage", "ungate"):
        target = os.path.abspath(args.file)
        if not os.path.isfile(target):
            print(f"[-] File not found: {target}", file=sys.stderr)
            sys.exit(1)

        with open(target, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        result = core.triage_task_list(lines)
        if args.command == "triage":
            print(core.format_triage_summary(result))
        else:
            print(core.format_ungate_questions(result["gated"]))


if __name__ == "__main__":
    main()
