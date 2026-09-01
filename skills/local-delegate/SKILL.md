---
name: local-delegate
description: Offload heavy file analysis, code reviews, or text transformations to free local MLX models on Apple Silicon (e.g. Qwen 3.8, DeepSeek R1, KAT Coder, Gemma 4, Devstral).
---

# local-delegate Skill

## Purpose
Delegate mechanical tasks, deep file reviews, log parsing, or code transformations to free local Apple Silicon MLX models via OpenAI-compatible endpoints with zero quota consumption.

## Available Model Profiles
* **`qwen-3.8-operator`** *(Default)*: Fast, capable 27B coding and operations workhorse.
* **`qwen-3.8-thinking`**: Qwen 3.8 deep reasoning model with chain-of-thought analysis.
* **`qwen-3.8-8bit`**: Higher-precision 8-bit Qwen 3.8 operator.
* **`qwen-3.8-mtp`**: Accelerated Multi-Token Prediction operator.
* **`deepseek-r1-architect`**: Complex architectural reasoning and algorithmic design.
* **`kat-coder-optiq`**: Specialized KAT Coder V2.5 code generation engine.
* **`gemma-4-26b`**: Google Gemma 4 26B instruction model.
* **`kimi-vl-thinking`**: Multimodal vision & reasoning utility model.
* **`devstral-2-123b`**: Heavyweight 123B code refactoring engine.
* **`ministral-14b`**: Fast reasoning & inspection model.
* **`nemotron-omni`**: NVIDIA Nemotron 3 Nano Omni multimodal model.
* **`llama-scout`**: Lightweight inspection utility.

## Scanning Local Models
Scan your local on-disk models (`~/.models`) to check what is installed and verified:
```bash
python3 packages/agy-local-delegate/bin/agy_local_delegate.py scan
```

## How to Delegate
```bash
python3 packages/agy-local-delegate/bin/agy_local_delegate.py dispatch \
  --model qwen-3.8-operator \
  --prompt "Analyze the provided source file for logic errors" \
  --files path/to/file.py
```
