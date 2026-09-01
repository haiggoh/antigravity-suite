---
name: local-delegate
description: Offload heavy file analysis, code reviews, or text transformations to free local MLX models on Apple Silicon (Qwen 3.8, DeepSeek R1, KAT Coder, Gemma 4, Devstral). Also enables running local models as the primary AGY engine via agy-local-mode.
---

# local-delegate Skill

## Purpose
Two complementary modes of local model use:

1. **Delegate mode**: Dispatch specific sub-tasks to a local model from within a cloud AGY session (zero quota consumed for the delegated work).
2. **Local engine mode** (`agy-local-mode`): Boot AGY with a local Qwen 3.8 / MLX model as the *primary engine* — useful when cloud quota has run out.

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

### Dispatch a Task
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

### Quick Start

```bash
# 1. Start your local model server (Rapid-MLX default on port 8000)
~/.venvs/rapid-mlx-0.12.18/bin/rapid-mlx --model ~/.models/Qwen3.8-27B-4bit

# 2. In another terminal, launch AGY in local mode:
agy-local-mode

# Or with a specific model/upstream:
agy-local-mode --model mlx-community/Qwen3.8-27B-4bit \
               --upstream http://127.0.0.1:8000/v1
```

### Manual Proxy Control
```bash
# Start proxy only (useful for scripting):
python3 packages/agy-local-delegate/bin/agy_local_proxy.py \
  --port 9191 \
  --upstream http://127.0.0.1:8000/v1 \
  --model mlx-community/Qwen3.8-27B-4bit

# Then in another shell:
GOOGLE_GEMINI_BASE_URL=http://127.0.0.1:9191 agy
```

### Environment Variables
| Variable | Default | Description |
|---|---|---|
| `AGY_LOCAL_PROXY_PORT` | `9191` | Proxy listen port |
| `AGY_LOCAL_MODEL_ENDPOINT` | `http://127.0.0.1:8000/v1` | Upstream OpenAI-compatible URL |
| `AGY_LOCAL_MODEL_ID` | `mlx-community/Qwen3.8-27B-4bit` | Model ID sent to upstream |
| `AGY_LOCAL_PROXY_TIMEOUT` | `180` | Seconds before upstream timeout |
| `AGY_LOCAL_PROXY_DEBUG` | *(unset)* | Set to any value for verbose logging |
