---
name: execute-unattended
description: Mid-run unattended execution loop. Keeps moving, wraps and switches on blockers, ensures reversibility before edits, and verifies live changes.
---

# execute-unattended — In-Run Execution Loop

## Core Principles
1. **Wrap-and-switch on gates:** The moment an unexpected gate is encountered, record the blocker (`G1:...`) and switch to the next unblocked item immediately.
2. **Reversibility before edits:** Ensure working tree is clean or take a safe backup before editing untracked files.
3. **The Ship Loop:** Verify change → bump version if applicable → commit → push → verify live.
4. **Milestone Wraps:** Emit short progress notes after each completed task without waiting for permission.
