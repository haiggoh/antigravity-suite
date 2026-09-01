---
name: local-delegate
description: Offload heavy file analysis, code reviews, or text transformations to free local MLX models on Apple Silicon (e.g. Qwen 3.6, DeepSeek R1, Gemma 4, Devstral).
---

# local-delegate Skill

## Purpose
Delegate mechanical tasks, deep file reviews, log parsing, or text transformations to free local MLX / OpenAI-compatible models running on Apple Silicon.

## Available Model Aliases
* **`qwen-3.6-operator`** *(Default)*: Fast, capable 27B coding and operations model.
* **`qwen-3.6-thinking`**: Deep reasoning model with chain-of-thought analysis.
* **`deepseek-r1-architect`**: Complex architectural reasoning and algorithmic design.
* **`gemma-4-26b`**: Google Gemma 4 26B instruction model.
* **`devstral-2-123b`**: Heavyweight 123B code refactoring engine.
* **`llama-scout`**: Fast, lightweight inspection utility.

## How to Delegate
```bash
python3 packages/agy-local-delegate/bin/agy_local_delegate.py dispatch \
  --model qwen-3.6-operator \
  --prompt "Analyze the provided source file for logic errors" \
  --files path/to/file.py
```
