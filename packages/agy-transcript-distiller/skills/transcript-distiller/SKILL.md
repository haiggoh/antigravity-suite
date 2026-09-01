---
name: agy-transcript-distiller
description: Distills Antigravity transcript JSONL into clean markdown capsules.
---

# Transcript Distiller Skill

Provides a simple way to turn raw `transcript.jsonl` files into readable markdown.

## Usage
- Run the CLI `packages/agy-transcript-distiller/bin/transcript_distiller.py <transcript.jsonl> [output.md]`.
- The skill can be invoked via the `/transcript-distill` slash command (future).

The script extracts the `content` fields from user and planner steps and separates them with `---` sections for easy reading.
