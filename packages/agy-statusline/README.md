# Antigravity Status Line (`agy-statusline`)

A high-performance, real-time telemetry and live quota status line for **Google Antigravity CLI (`agy`)** on **macOS, Windows, and Linux**.

```text
Gemini 3.7 Flash │ Idle │ Context 98% left │ ~/project │ ⬡ Quota: 85% · reset 4d 12h │ ↑1.2k ↓4.8k 6.0k tok
  💡 Tip: Use /goal for complex, multi-step tasks that need deep focus.
```

---

## ✨ Key Features & Upstream Differences

Forked and enhanced from [`60ke/antigravity-statusline`](https://github.com/60ke/antigravity-statusline.git) with major cross-platform and performance upgrades:

| Feature | Original Upstream (`60ke`) | This Fork (`haiggoh`) |
| :--- | :--- | :--- |
| **Windows Support** | ❌ Broken / Unix-only | ✅ Full Windows PowerShell & Windows Terminal support |
| **Windows Locales** | ❌ Fails on non-English `netstat` | ✅ Supports international Windows output (e.g. `ABHÖREN` on German Windows) |
| **Port Discovery** | ⚠️ Slow shell `lsof`/`netstat` pipes | ✅ **Sub-millisecond direct loopback port scan** |
| **Storage Standard** | ⚠️ Pollutes `~/.antigravity/` | ✅ Clean standard paths: `~/.gemini/statusline` & `~/.gemini/cache/` |
| **Windows Installer** | ❌ None | ✅ Native PowerShell installer (`install.ps1`) |
| **Context & Quota Meter** | ✅ Basic | ✅ High-accuracy live model quota with reset countdown & token telemetry |
| **Tips Engine** | ❌ None | ✅ Smart rotating productivity tips (non-blocking, persisted cache) |

---

## 🚀 Quick Install

### macOS / Linux (Bash)

```bash
git clone https://github.com/haiggoh/antigravity-statusline.git ~/.gemini/statusline-repo
cd ~/.gemini/statusline-repo
./install.sh
```

### Windows (PowerShell)

```powershell
git clone https://github.com/haiggoh/antigravity-statusline.git "$HOME\.gemini\statusline-repo"
cd "$HOME\.gemini\statusline-repo"
.\install.ps1
```

---

## ⚙️ Manual Configuration

Add or edit the `statusLine` block in your Antigravity CLI settings:

* **macOS / Linux**: `~/.gemini/antigravity-cli/settings.json`
* **Windows**: `%USERPROFILE%\.gemini\antigravity-cli\settings.json`

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 /path/to/.gemini/statusline/status.py",
    "enabled": true
  }
}
```

*(On Windows, replace `python3` with `python`).*

---

## 📁 File Structure

```text
~/.gemini/
├── statusline/
│   ├── status.py               # Main status line renderer & loopback probe
│   └── agy-quota-cache.py      # /usage quota parser & cache updater
├── cache/
│   └── statusline/
│       ├── quota-cache.json    # Cached quota telemetry
│       └── status-state.json   # Session state cache
└── backups/                    # Automatic settings backups before changes
```

---

## 🤝 Upstream Collaboration

This fork maintains 100% upstream compatibility. Changes are structured into modular pull requests for upstream merge into `60ke/antigravity-statusline`.

---

## 📄 License

MIT © [Heiko Brantsch](https://github.com/haiggoh) & [60ke](https://github.com/60ke)
