# antigravity-sync

Keep your **Google Antigravity** configuration, status line scripts, skills, rules, and tool permissions seamlessly in sync across **macOS and Windows** devices, as well as between local **CLI** and **Desktop / IDE** environments.

Modifying a shared setting, status line script, or tool permission on one machine mirrors cleanly to all your devices via a git/cloud repository template—**without clobbering machine-local account credentials, session tokens, or host paths**.

---

## Key Features

* 🔄 **Cross-OS Compatibility (macOS & Windows)**: Automatically normalizes path separators and executable commands (e.g. `python3` on macOS vs `python` on Windows, expanding `{HOME}` dynamically).
* 👤 **Account & Workspace Isolation**: Machine-local variables (such as active Google login email `heiko.brantsch@seven.one` vs `brantsch.h@gmail.com`, session tokens, and `trustedWorkspaces`) remain isolated to each host.
* 🖥️ **Cross-App Local Sync**: Mirrored after `claude-code-desktop-sync`, automatically synchronizes configuration between local CLI and Desktop / IDE app configurations on the same machine.
* 🔒 **Secure Asynchronous Sync (Git / Cloud)**: Uses Git (e.g. GitHub private repo) or cloud folder synchronization. Devices sync asynchronously whenever booted without requiring open ports or simultaneous local WiFi connectivity.
* 🛡️ **Non-Destructive & Backed Up**: Automatically creates timestamped backups in `~/.antigravity/backups/` before applying modifications.

---

## Quick Start

### 1. Install & Sync

```bash
python3 install.py
```

### 2. Dry Run Preview

To test what changes would be applied without modifying any files:

```bash
python3 install.py --dry-run
```

---

## Architecture & Transport Analysis

See [`docs/SYNC-ARCHITECTURE.md`](docs/SYNC-ARCHITECTURE.md) for a detailed security, network transport, and threat model breakdown comparing Git/Cloud remote vs. local WiFi / P2P vs. SSH VPN tunnels.

---

## Project Structure

```
antigravity-sync/
├── README.md
├── install.py                  # Standalone cross-platform installer
├── uninstall.py                # Uninstaller
├── bin/
│   └── sync_engine.py          # Cross-platform Python sync engine
├── templates/
│   └── shared-settings.json    # Shared setting template ({HOME} placeholders)
├── docs/
│   └── SYNC-ARCHITECTURE.md    # Transport & security breakdown
└── skills/
    └── antigravity-sync/       # Companion Antigravity skill
```

---

## License

MIT
