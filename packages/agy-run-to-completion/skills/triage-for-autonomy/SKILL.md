---
name: triage-for-autonomy
description: Score any queue into Tier 1 (Do Now), Tier 2 (Heavy), and Gated tasks, recording a gate reason per blocked item ordered by cheapness of resolution.
---

# triage-for-autonomy — Pre-Execution Queue Scoring

## Tiers
- **Tier 1 (Do-Now):** Fully actionable, clear requirements, no human in the loop needed.
- **Tier 2 (Heavy):** Autonomous but complex or long-running.
- **Gated:** Blocked on a specific requirement or human decision.

## Blocker Taxonomy (Ordered by Cheapness to Release)
- **`G1` (One decision / choice):** Resolved by one clarifying answer.
- **`G2` (Setup script):** Resolved by running a bundled command.
- **`G3` (Custom setup):** Requires multi-step configuration.
- **`G4` (Human GUI driver):** Attended interaction required throughout.
- **`ENV` (Precondition):** External condition (network/service running).
- **`WAIT` (Dependency):** Self-releasing upon prerequisite task completion.
- **`EXT` (External):** Waiting on upstream PR or external third party.
