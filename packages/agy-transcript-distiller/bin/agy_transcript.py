#!/usr/bin/env python3
"""CLI utility for agy-transcript-distiller (v0.8.0).

Commands:
  distill     Distill a transcript file or conversation ID into a Markdown capsule
  latest      Distill the most recent session in ~/.gemini/antigravity-cli/brain
  list        List all available sessions in brain
  bundle      Bundle multiple sessions into a combined document
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import agy_transcript_distiller_core as core


def main():
    parser = argparse.ArgumentParser(description="Antigravity Transcript Distiller (v0.8.0)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # distill command
    dist_p = subparsers.add_parser("distill", help="Distill transcript to markdown")
    dist_p.add_argument("target", help="Path to transcript.jsonl OR conversation UUID")
    dist_p.add_argument("output", nargs="?", help="Optional destination markdown file")
    dist_p.add_argument("--thinking", action="store_true", help="Include model thinking CoT")

    # latest command
    lat_p = subparsers.add_parser("latest", help="Distill newest session in brain")
    lat_p.add_argument("output", nargs="?", help="Optional destination markdown file")
    lat_p.add_argument("--thinking", action="store_true", help="Include model thinking CoT")

    # list command
    subparsers.add_parser("list", help="List all distillable sessions")

    # bundle command
    bun_p = subparsers.add_parser("bundle", help="Bundle multiple sessions chronologically")
    bun_p.add_argument("sessions", nargs="+", help="Conversation UUIDs to bundle")
    bun_p.add_argument("-o", "--output", help="Destination markdown file")

    args = parser.parse_args()

    if args.command == "distill":
        path = args.target
        cid = ""
        if not os.path.isfile(path):
            brain = core.get_brain_dir()
            candidate = os.path.join(brain, args.target, ".system_generated", "logs", "transcript.jsonl")
            if os.path.isfile(candidate):
                path = candidate
                cid = args.target
            else:
                print(f"[-] Transcript not found: {args.target}", file=sys.stderr)
                sys.exit(1)

        result = core.distill_transcript(path, conversation_id=cid, include_thinking=args.thinking)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"[+] Distilled capsule written to {args.output}")
        else:
            print(result)

    elif args.command == "latest":
        sessions = core.find_available_sessions()
        if not sessions:
            print("[-] No sessions found in brain.", file=sys.stderr)
            sys.exit(1)

        latest = sessions[0]
        result = core.distill_transcript(
            latest["transcript_path"],
            conversation_id=latest["conversation_id"],
            include_thinking=args.thinking,
        )
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"[+] Distilled latest capsule ({latest['conversation_id']}) written to {args.output}")
        else:
            print(result)

    elif args.command == "list":
        sessions = core.find_available_sessions()
        if not sessions:
            print("[=] No sessions found in brain.")
            return

        print(f"Available Antigravity Sessions ({len(sessions)}):\n")
        for s in sessions:
            kb = s["size_bytes"] // 1024
            print(f"- `{s['conversation_id']}` ({kb} KB) · {s['timestamp']}")

    elif args.command == "bundle":
        out_file = args.output
        session_list = args.sessions
        if out_file and out_file in session_list:
            session_list.remove(out_file)

        result = core.bundle_sessions(session_list)
        if out_file:
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"[+] Multi-session bundle written to {out_file}")
        else:
            print(result)


if __name__ == "__main__":
    main()
