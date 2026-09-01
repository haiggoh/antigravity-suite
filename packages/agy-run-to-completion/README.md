# agy-run-to-completion

**Autonomous Multi-Step Execution & Blocker Ungating Engine for Google Antigravity (AGY)**

## Overview
A composable 6-skill suite providing structured autonomous execution, intelligent task triaging, and efficient attended blocker resolution without stalling during routine operations.

## Included Skills
1. `run-to-completion`: Continuous execution offer for multi-step plans.
2. `autopilot`: End-to-end queue processor across four phases (Kickoff, Triage, Execute, Closeout).
3. `triage-for-autonomy`: Pre-execution queue scoring (Tier 1 Do-Now, Tier 2 Heavy, Gated G1-G4/ENV/WAIT).
4. `execute-unattended`: In-run execution loop with wrap-and-switch on unexpected gates.
5. `ungate-queue`: Attended pass converting blockers into single clarifying questions sorted by cheapness.
6. `close-out-the-run`: State reconciliation and structured remaining-blocker menu.

## CLI Usage
```bash
python bin/agy_rtc.py triage GEMINI.md
python bin/agy_rtc.py ungate GEMINI.md
```
