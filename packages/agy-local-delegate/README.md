# agy-local-delegate

Local Apple Silicon model delegation and full AGY local-engine launcher.

## Full local session

One-time AGY provider setup is required in `~/.gemini/antigravity-cli/settings.json`:

```json
{
  "modelProvider": "gemini"
}
```

Preserve any other existing settings in that file. Then run:

```bash
agy-local-mode                         # default qwen-3.8-operator
agy-csl                                # interactive model picker
agy-local-mode --model qwen-3.8-operator
```

The launcher:

- preserves a 16 GB RAM floor unless `AGY_SKIP_RAM_PREFLIGHT=1`;
- reuses only a server advertising the requested model;
- otherwise starts `rapid-mlx serve` on a free port in 8000-8015;
- starts its proxy on a free port in 9191-9205 without killing other listeners;
- runs a real Gemini-proxy inference smoke test before launching AGY;
- sets a loopback-only dummy `GEMINI_API_KEY` and `GOOGLE_GEMINI_BASE_URL`;
- cleans up only processes that it started.

Useful overrides:

- `AGY_RAPID_MLX_BIN=/path/to/rapid-mlx`
- `AGY_LOCAL_MODEL_ENDPOINT=http://127.0.0.1:8000/v1`
- `AGY_LOCAL_PROXY_PORT=9195`
- `AGY_LOCAL_SERVER_STARTUP_TIMEOUT=900`
- `AGY_LOCAL_SKIP_SMOKE=1` (diagnostics only; not recommended)
- `AGY_LOCAL_PROXY_DEBUG=1`

## Direct task delegation

```bash
python3 bin/agy_local_delegate.py scan
python3 bin/agy_local_delegate.py dispatch \
  --model qwen-3.8-operator \
  --prompt "Review this file" \
  --files path/to/file.py
```

## Safe server eviction

`agy-evict` protects model servers attached to active AGY or Claude Code
clients. Claude attachment is determined from each local client's loopback
`ANTHROPIC_BASE_URL`. AGY proxy attachment also protects the proxy's upstream
model server.

Attached servers are protected for default, `--all`, `--port`, and `--pid`
operations. Deliberate termination requires an explicit target together with
`--force-attached`.

```bash
agy-evict --status
agy-evict --dry-run
agy-evict --port 8001
agy-evict --port 8001 --force-attached
```
