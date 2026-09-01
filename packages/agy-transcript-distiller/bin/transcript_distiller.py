#!/usr/bin/env python3
"""Simple transcript distiller for Antigravity.

Usage: transcript_distiller.py <transcript.jsonl> [output.md]
If output path is omitted, distilled markdown is printed to stdout.

Current implementation: reads the JSONL transcript, extracts the "content"
field from each USER_INPUT and PLANNER_RESPONSE step, and writes them as
markdown paragraphs separated by "---".
"""
import argparse
import json
import sys
from pathlib import Path

def distill(transcript_path: Path, out_path: Path | None):
    with transcript_path.open("r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f]
    parts = []
    for step in lines:
        if step.get("type") in ("USER_INPUT", "PLANNER_RESPONSE"):
            content = step.get("content", "").strip()
            if content:
                parts.append(content)
    markdown = "\n\n---\n\n".join(parts)
    if out_path:
        out_path.write_text(markdown, encoding="utf-8")
    else:
        print(markdown)

def main():
    parser = argparse.ArgumentParser(description="Distill Antigravity transcript to markdown")
    parser.add_argument("transcript", type=Path, help="Path to transcript.jsonl")
    parser.add_argument("output", nargs="?", type=Path, help="Optional output markdown file")
    args = parser.parse_args()
    distill(args.transcript, args.output)

if __name__ == "__main__":
    main()
