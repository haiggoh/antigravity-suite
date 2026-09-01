#!/usr/bin/env python3
"""CLI utility for Antigravity Brief Agents.

Commands:
  build     Build or refresh ~/.gemini/agent-briefing-index.md if sources changed
  cat       Print the current agent briefing index
  check     Check if index is up to date (exit code 0 if current, 1 if stale)
  prompt    Format a subagent prompt prepended with briefing directive
"""

import sys
import os
import argparse

# Add parent directory to sys.path to import core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import agy_brief_agents_core as core


def main():
    parser = argparse.ArgumentParser(description="Antigravity Subagent Briefing CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # build command
    build_p = subparsers.add_parser("build", help="Build or refresh briefing index")
    build_p.add_argument("--cwd", default=os.getcwd(), help="Target workspace path")
    build_p.add_argument("--force", action="store_true", help="Force rebuild ignoring cache")

    # cat command
    subparsers.add_parser("cat", help="Print current briefing index")

    # check command
    check_p = subparsers.add_parser("check", help="Check if briefing index is up to date")
    check_p.add_argument("--cwd", default=os.getcwd(), help="Target workspace path")

    # prompt command
    prompt_p = subparsers.add_parser("prompt", help="Wrap prompt with briefing directive")
    prompt_p.add_argument("text", help="Task prompt string")
    prompt_p.add_argument("--cwd", default=os.getcwd(), help="Target workspace path")

    args = parser.parse_args()

    if args.command == "build":
        path, rebuilt = core.build_and_save_index(args.cwd, force=args.force)
        status = "rebuilt" if rebuilt else "already current"
        print(f"[+] Briefing index ({status}): {path}")

    elif args.command == "cat":
        path = core.index_output_path()
        content = core.read_text(path)
        if content:
            print(content)
        else:
            print(f"[-] No briefing index found at {path}. Run 'build' first.", file=sys.stderr)
            sys.exit(1)

    elif args.command == "check":
        g_rules = core.scan_global_rules()
        w_rules = core.find_workspace_guidelines(args.cwd)
        home = core.get_home_dir()
        skills = core.scan_skills([
            os.path.join(home, ".gemini", "antigravity-cli", "skills"),
            os.path.join(home, ".gemini", "config", "skills"),
            os.path.join(args.cwd, "skills"),
        ])
        new_fp = core.compute_sources_fingerprint(g_rules, w_rules, skills)
        old_fp = core.read_text(core.fingerprint_path()).strip()
        if old_fp == new_fp and os.path.isfile(core.index_output_path()):
            print("[=] Briefing index is current.")
            sys.exit(0)
        else:
            print("[!] Briefing index is out of date or missing.")
            sys.exit(1)

    elif args.command == "prompt":
        formatted = core.format_subagent_prompt(args.text, args.cwd)
        print(formatted)


if __name__ == "__main__":
    main()
