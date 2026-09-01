---
name: autopilot
description: End-to-end unattended queue execution. Triages open tasks, executes autonomous tiers, handles blockers, and closes out with clean state reconciliation.
---

# autopilot — Autonomous Queue Clearing

## Purpose
Execute all possible autonomous work across a standing queue (`GEMINI.md`, waypoints, or project task lists) while the user is away.

## 4-Phase Lifecycle

```text
1. Kickoff  → Clarify execution scope, destructive permissions, and resource constraints ONCE.
2. Triage   → Score queue into Tier 1 (Do Now), Tier 2 (Heavy), and Gated (G1-G4/ENV/WAIT).
3. Execute  → Run Tier 1/2 tasks, wrap-and-switch on gates, re-poll self-releasing blocks.
4. Closeout → Reconcile durable records, working tree clean, output structured gated menu.
```
