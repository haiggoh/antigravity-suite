---
name: get-antigravity
description: Package hub & updater for Antigravity suite. Provides /get-antigravity slash command to update or list packages.
---

# Get Antigravity Skill

Use the `/get-antigravity` slash command to run the `get-antigravity` CLI wrapper.

## Usage
- `/get-antigravity` – updates the entire Antigravity suite (default).
- `/get-antigravity --list` – lists available packages.
- `/get-antigravity --install <pkg>` – installs a specific package.
- `/get-antigravity --update` – explicitly updates all packages.

The skill invokes the binary `packages/get-antigravity/bin/get-antigravity` located in the suite.
