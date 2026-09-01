---
name: ungate-queue
description: Attended pass walking the blocked pile with the user, cheapest gate first, turning each gate reason into the single question that releases it.
---

# ungate-queue — Attended Blocker Resolution

## Purpose
Spends human attention efficiently to release gates for future autonomous runs.

## Method
1. Sort gated items by cheapness rank (`G1` → `G2` → `G3` → `G4` → `ENV`).
2. Ask the single smallest question whose answer unblocks the item.
3. Record the answer directly onto the task item.
4. Promote released items into the autonomous queue.
