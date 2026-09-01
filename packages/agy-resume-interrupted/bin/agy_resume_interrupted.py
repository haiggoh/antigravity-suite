#!/usr/bin/env python3
"""CLI utility for Antigravity Resume Interrupted.

Commands:
  detect    Detect if the most recent prior session was interrupted
  list      List all detected interrupted sessions in brain
  prompt    Output resumption prompt for recommended or specific session ID
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import agy_resume_core as core


def main():
    parser = argparse.ArgumentParser(description="Antigravity Interrupted Session Detector")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # detect command
    subparsers.add_parser("detect", help="Check for recent interrupted session")

    # list command
    list_p = subparsers.add_parser("list", help="List all interrupted sessions")
    list_p.add_argument("--limit", type=int, default=10, help="Max candidates to show")

    # prompt command
    prompt_p = subparsers.add_parser("prompt", help="Generate resumption prompt")
    prompt_p.add_argument("--id", help="Optional specific conversation ID")

    args = parser.parse_args()

    if args.command == "detect":
        rec = core.get_recommended_resume()
        if rec:
            print(f"[!] Interrupted session detected: {rec['conversation_id']} ({rec['reason']})")
            print(f"    Last prompt: {rec['last_user_prompt'][:100]}")
            sys.exit(0)
        else:
            print("[=] No interrupted sessions found.")
            sys.exit(1)

    elif args.command == "list":
        candidates = core.find_interrupted_sessions(limit=args.limit)
        if not candidates:
            print("[=] No interrupted sessions found.")
            return
        print(f"Found {len(candidates)} interrupted session(s):\n")
        for c in candidates:
            print(f"- ID: {c['conversation_id']}")
            print(f"  Reason: {c['reason']} | Turns: {c['turn_count']}")
            print(f"  Prompt: {c['last_user_prompt'][:90]}")
            print()

    elif args.command == "prompt":
        if args.id:
            brain_dir = core.get_brain_dir()
            transcript_path = os.path.join(brain_dir, args.id, ".system_generated", "logs", "transcript.jsonl")
            analysis = core.analyze_transcript(transcript_path, args.id)
            if not analysis:
                print(f"[-] Session {args.id} not found or not interrupted.", file=sys.stderr)
                sys.exit(1)
            print(core.format_resumption_prompt(analysis))
        else:
            rec = core.get_recommended_resume()
            if rec:
                print(core.format_resumption_prompt(rec))
            else:
                print("[-] No interrupted session to resume.", file=sys.stderr)
                sys.exit(1)


if __name__ == "__main__":
    main()
