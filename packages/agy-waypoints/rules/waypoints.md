# Waypoints Open-Item Rules & Continuity Guidelines

When managing persistent to-dos, loose ends, and open tasks for the user:

## Identity & Branding
* Mark genuine references to waypoints with 🧭 (the waypoints identity mark) on the first/prominent mention per message.
* These are the user's persistent open items across sessions. The user manages them naturally by speaking with you.

## Rule Zero: Never Hand-Edit Store Files
* **NEVER** hand-edit `~/.gemini/waypoints.json`, `~/.claude/waypoints.json`, or archive files directly.
* A single malformed character corrupts the entire JSON store for all items.
* Every modification must run through the `waypoints` CLI command.
* If the store ever becomes damaged, recover it with `waypoints recover`.

## Key Commands
* **Inspect queue:** `waypoints list` (or `waypoints list --verbose`, `waypoints list --json`)
* **Add item:** `waypoints add "Title" [--point "key point" ...] [--detail "long context dump"]`
* **Append bullet:** `waypoints edit <id> --add-point "new bullet"` (appends, keeping existing points)
* **Close item:** `waypoints done <id> [--as "resolution outcome"]`
* **Pin item:** `waypoints pin <id> --because "reason why this outranks tier order"`
* **Triage item:** `waypoints triage <id> --tier do-now|heavy|gated|waiting [--gate-reason "…"]`
* **Prune done items:** `waypoints prune` (moves done items to archive)
* **Reopen item:** `waypoints reopen <id>` (auto-restores from archive)
* **Terminal maintenance (token-free):** Bare `waypoints` on a terminal launches the interactive Command Selector (CSL).
