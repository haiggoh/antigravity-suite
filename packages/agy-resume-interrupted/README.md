# agy-resume-interrupted

**Interrupted Session Detector & Continuity Resumer for Google Antigravity (AGY)**

## Problem
Sessions that hit rate limits (429 / `RESOURCE_EXHAUSTED`), tool crashes, or abrupt disconnections leave unfinished tasks without explicit state markers.

## Solution
`agy-resume-interrupted` parses AGY transcripts (`transcript.jsonl`), identifies stalled turns or error cutoffs, and formats a clean resumption summary and prompt.

## Features
- **Accurate Detection**: Identifies rate limits, API rejections, stalled turns, and tool exceptions.
- **Fail-Safe & Standard Library**: Requires no external dependencies.
- **CLI & Skill**: Provides `bin/agy_resume_interrupted.py` and `skills/resume-interrupted`.
