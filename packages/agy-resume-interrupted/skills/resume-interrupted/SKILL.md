---
name: resume-interrupted
description: Automatically detect previously interrupted, stalled, or rate-limited Antigravity sessions and seamlessly resume context.
---

# resume-interrupted Skill

## Purpose
When a previous session crashes, exceeds Google model quotas / rate limits (`RESOURCE_EXHAUSTED`), or loses connection mid-execution, the agent's work is left incomplete.
This skill detects the unfinished session from `~/.gemini/antigravity-cli/brain/` transcripts and constructs an exact resumption plan.

## Workflow

1. **Detect Interrupted Sessions**:
   ```bash
   python3 packages/agy-resume-interrupted/bin/agy_resume_interrupted.py detect
   ```
2. **Review & Formulate Resumption**:
   ```bash
   python3 packages/agy-resume-interrupted/bin/agy_resume_interrupted.py prompt
   ```
3. **Continue Task**:
   Re-read the referenced conversation log (`.system_generated/logs/transcript.jsonl`) or artifacts, then complete the outstanding steps.
