# Antigravity Sync Architecture & Transport Analysis

This document evaluates sync transport mechanisms for synchronizing Google Antigravity configurations, status lines, skills, rules, and MCP servers across multiple devices (e.g. macOS and Windows) and multiple local applications (e.g. Antigravity CLI and Antigravity Desktop / IDE).

---

## 1. Transport Mechanisms Evaluated

| Mechanism | Description | Security | Asynchronous / Offline | Multi-Account Support | Setup Overhead |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Git Remote** *(Recommended)* | Private GitHub/GitLab repo as declarative source of truth | 🔒 High (SSH/OAuth) | ✅ Excellent (Pull/Push anytime) | ✅ Isolated per host | Low |
| **Cloud Drive** *(Google Drive / iCloud)* | Watch directory in cloud folder | 🔒 High (OS-level auth) | ✅ Excellent | ✅ Isolated per host | Minimal |
| **Local WiFi / LAN P2P** | Direct mDNS / TCP socket on local network | ⚠️ Medium (Firewall/mDNS) | ❌ Requires both devices online on same WiFi | ⚠️ Complex conflict resolution | Medium |
| **Tailscale / VPN SSH** | Direct encrypted tunnel between hosts | 🔒 High (Wireguard) | ❌ Requires receiving host powered on | ✅ High | High |

---

## 2. Why Git / Cloud Remote Wins

### Security & Threat Model
* **Zero Open Ports**: WiFi P2P or local sockets require open network ports listening on your machine. Git over SSH/HTTPS or Cloud Drive uses outgoing HTTPS/SSH requests only.
* **Authentication**: Credentials remain secured via GitHub SSH keys or OS Google Drive auth. No unauthenticated local network broadcasts.

### Offline & Asynchronous Capability
* When working on your Mac away from home (or at the office under `heiko.brantsch@seven.one`), you can push settings or plugin updates.
* Your Windows PC (running `brantsch.h@gmail.com`) automatically pulls and applies these updates the next time you turn it on—**no requirement for both machines to be online or connected to the same WiFi network simultaneously**.

### Multi-Account & Multi-OS Isolation
* **OS Path Normalization**: macOS paths (`~/.gemini/statusline/status.py`) and Windows paths (`%USERPROFILE%\.gemini\statusline\status.py`) are expanded dynamically by the sync engine.
* **Account Isolation**: Machine-local keys (such as active Google login tokens, `email`, and `trustedWorkspaces`) are preserved locally and explicitly excluded from synced templates.

---

## 3. Dual-Layer Sync Engine Design

`antigravity-sync` implements two complementary sync layers:

1. **Cross-Device Layer (Machine <─> Git/Cloud Remote <─> Machine)**:
   - Syncs declarative settings, status line scripts, custom rules, skills, and MCP server templates.
   - Preserves local account identity and machine-specific file paths.

2. **Cross-App Layer (CLI <─> Desktop / IDE on Same Host)**:
   - Mirrored after `claude-code-desktop-sync`, automatically keeping local Antigravity CLI configs in sync with local Antigravity Desktop / IDE files.
