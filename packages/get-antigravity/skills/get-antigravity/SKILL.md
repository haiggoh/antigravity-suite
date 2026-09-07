---
name: get-antigravity
description: Package hub, skip-list manager, and distribution updater for the Antigravity suite. Use to inspect available packages, view version drift, manage skips, and perform selective or bulk package updates.
---

# Get Antigravity Skill

The `get-antigravity` package hub manages the distribution, versioning, drift detection, and synchronization of all Google Antigravity (AGY) packages, skills, rules, and CLI tools.

## Key Capabilities
1. **Catalog Inspection**: Discover all installed vs available packages across the suite.
2. **Execution Planning (`plan`)**: Preview pending installs, version updates, and active skips.
3. **Execution Application (`apply`)**: Safely run installation and deployment with automatic verification.
4. **Selective Sync**: Filter installs or updates using `--only <pkg1,pkg2>` or `--category <system|tools|ai>`.
5. **Persistent Skip List**: Mark specific packages to skip install, update, or both (`~/.gemini/.agy-skip.json`).
6. **Version Drift Checking**: Compare installed versions against remote releases.

---

## Slash Commands & CLI Invocations

### Overview & Planning
- `/get-antigravity` or `get-antigravity plan` – previews missing or outdated packages.
- `get-antigravity list` – displays a table of all packages, versions, categories, and skip states.
- `get-antigravity list --json` – outputs catalog metadata in JSON format.

### Synchronizing & Applying Updates
- `get-antigravity apply` – applies all pending package installations and updates.
- `get-antigravity apply --only agy-local-delegate` – selectively installs/updates a specific package.
- `get-antigravity apply --category system` – updates packages within a specific category.
- `get-antigravity apply --no-workspace-sync` – updates packages without running workspace git pull.

### Managing Skip Lists
- `get-antigravity skip <pkg>` – skips both install and update for `<pkg>`.
- `get-antigravity skip <pkg> --action install` – skips automatic install of missing `<pkg>`.
- `get-antigravity skip <pkg> --action update` – skips version updates for `<pkg>`.
- `get-antigravity unskip <pkg>` – removes `<pkg>` from skip list.
- `get-antigravity skips` – lists all currently skipped packages.
