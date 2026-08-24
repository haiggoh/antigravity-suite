# agy-statusline

A high-performance, cross-platform telemetry and live quota status line for **Google Antigravity (AGY)** on macOS and Windows.

---

## Origin & Upstream Architecture

* **Upstream Base**: Forked from [`60ke/antigravity-statusline`](https://github.com/60ke/antigravity-statusline.git).
* **Suite Enhancements & Custom Layers**:
  1. **Cross-Platform Compatibility**: Full support for Windows PowerShell, Windows Terminal, and macOS/Linux shells.
  2. **Encoding & Language Support**: Native UTF-8 reconfigure with support for non-English Windows netstat output (e.g. `ABHÖREN` on German Windows).
  3. **Direct Loopback Fast Scanner**: Sub-millisecond direct port scanner to discover the active local language server without shell piping overhead.
  4. **Standard Cache Path**: Cache and state files stored in `~/.gemini/cache/statusline/` instead of polluting the home root with `~/.antigravity/`.
  5. **Live Quota & Rotating Tips**: Real-time quota percentage meter, session token tracking, and non-blocking tips display.

---

## Integration

Configured in `~/.gemini/antigravity-cli/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 {HOME}/.gemini/statusline/status.py",
    "enabled": true
  }
}
```

*(Automatically adapted to `python` on Windows by `antigravity-suite` sync engine).*
