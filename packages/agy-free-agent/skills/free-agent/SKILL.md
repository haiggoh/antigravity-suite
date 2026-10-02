---
name: local-delegate
description: Use when planning or decomposing ANY multi-step task involving reading, searching, summarizing, transforming, drafting, reviewing, or editing across files. Routes bulk/mechanical legwork to a free local model (by default `qwen-3.8-operator` on Apple Silicon) instead of burning cloud quota, keeping orchestration and judgment on cloud. Automatically runs RAM preflight before execution.
---

# local-delegate Skill

## Core Principle: Decide Upfront at Decomposition (Fixing the Catch-22)
The biggest quota saving is **$0 local compute**. The old trap was classifying tasks as either "too trivial to offload" or "too difficult to offload" — resulting in 100% cloud execution.

**The Fix**:
1. **Decide UPFRONT at decomposition** — annotate each planned step before burning cloud tokens:
   - `local:operator` — delegated to local Apple Silicon MLX compute ($0 per token).
   - `cloud:<reason>` — kept on cloud with specific justification (`cloud:frontier-reasoning`, `cloud:final-verification`, `cloud:not-worth-offloading`).
2. **Default to `operator`**: Bulk file inspections, log parsing, code reviews, formatting, boilerplate, and transformations default to `qwen-3.8-operator`.
3. **Keep Judgment on Cloud, Delegate Legwork**: Cloud agent coordinates, evaluates, and verifies.
4. **Mandatory RAM Preflight**: Every local dispatch verifies memory headroom before execution to prevent unified memory freeze.

---

## Mode 1: Delegate (from within a cloud session)

### Available Model Profiles
* **`qwen-3.8-operator`** *(Default)*: Fast 27B coding and operations workhorse.
* **`qwen-3.8-thinking`**: Deep chain-of-thought analysis.
* **`qwen-3.8-8bit`**: Higher-precision 8-bit operator.
* **`qwen-3.8-mtp`**: Multi-Token Prediction accelerated.
* **`deepseek-r1-architect`**: Complex architectural reasoning.
* **`kat-coder-optiq`**: KAT Coder V2.5 specialized code synthesis.
* **`gemma-4-26b`**: Google Gemma 4 26B.
* **`kimi-vl-thinking`**: Multimodal vision & reasoning.
* **`devstral-2-123b`**: Heavyweight 123B code refactoring.
* **`ministral-14b`**: Fast inspection.
* **`nemotron-omni`**: NVIDIA Nemotron multimodal.
* **`llama-scout`**: Lightweight classification.

### Scan Installed Models
```bash
python3 packages/agy-local-delegate/bin/agy_local_delegate.py scan
```

### Dispatch a Task (RAM Preflight Enforced Automatically)
```bash
python3 packages/agy-local-delegate/bin/agy_local_delegate.py dispatch \
  --model qwen-3.8-operator \
  --prompt "Analyze this file for logic errors" \
  --files path/to/file.py
```

---

## Mode 2: Local Engine (full AGY session on local model)

### Architecture
```
AGY CLI ──(Gemini API format)──► agy-local-proxy:9191
                                    │
                              Gemini → OpenAI translation
                                    │
                         ──(OpenAI format)──► Rapid-MLX:8000
                                                  │
                                            Qwen 3.8 27B
```

AGY speaks the Gemini API protocol natively. Rapid-MLX (for MLX models) and llama.cpp / llama-server (for GGUF models) speak OpenAI-compatible REST APIs. The proxy (`agy_local_proxy.py`) bridges the two with zero dependencies.

> **No model allowlist**: Unlike Claude Code's strict model allowlist, AGY uses `GOOGLE_GEMINI_BASE_URL` to redirect traffic, so **no spoofing required** — the local model can identify as itself.

### Quick Start & Interactive Model Selection (`agy-csl`)

```bash
# 1. Start your local model server (Rapid-MLX default on port 8000)
~/.venvs/rapid-mlx-0.12.18/bin/rapid-mlx --model ~/.models/Qwen3.8-27B-4bit

# 2. Interactive model selection menu:
agy-csl
# or:
agy-local-mode

# 3. Direct launch with a specific model profile:
agy-local-mode --model qwen-3.8-operator
agy-local-mode --model deepseek-r1-architect
```

---

## Mode 3: Safe Eviction & RAM Management (`agy-evict`)

When multiple inference servers or proxies hold Apple Silicon memory:
```bash
# Inspect resident servers, RSS memory, uptime, and safety ranks:
agy-evict --status

# Preview eviction without killing anything:
agy-evict --dry-run

# Evict single highest-ranked candidate safely (preserves attached AGY sessions):
agy-evict

# Evict all resident local model servers:
agy-evict --all
```

---

### Environment Variables
| Variable | Default | Description |
|---|---|---|
| `AGY_LOCAL_PROXY_PORT` | `9191` | Proxy listen port |
| `AGY_LOCAL_MODEL_ENDPOINT` | `http://127.0.0.1:8000/v1` | Upstream OpenAI-compatible URL |
| `AGY_LOCAL_MODEL_ID` | `mlx-community/Qwen3.8-27B-4bit` | Model ID sent to upstream |
| `AGY_LOCAL_PROXY_TIMEOUT` | `180` | Seconds before upstream timeout |
| `AGY_LOCAL_PROXY_DEBUG` | *(unset)* | Set to any value for verbose logging |
| `AGY_SKIP_RAM_PREFLIGHT` | `0` | Set `1` to bypass RAM preflight safety check |

