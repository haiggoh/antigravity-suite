---
name: antigravity-sync
description: Manage and trigger Antigravity settings and plugin synchronization across macOS, Windows, and local Desktop applications.
---

# Antigravity Sync Skill

This skill allows Antigravity agents to check sync status, perform on-demand syncs, or manage shared configuration templates across macOS and Windows devices.

## Usage

* **Run Sync**: Executes `bin/sync_engine.py` to merge shared configuration settings into the active host environment.
* **Check Status**: Inspects `~/.gemini/antigravity-cli/settings.json` and compares against `templates/shared-settings.json`.

## Engine Path
`bin/sync_engine.py`
