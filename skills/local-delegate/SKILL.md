---
name: local-delegate
description: Offload heavy file analysis, code reviews, or text transformations to free local MLX models on Apple Silicon (e.g. Qwen 3.6, DeepSeek R1, Gemma 4, Devstral).
---

# Local Agent Delegation Skill

Use this skill to delegate bulk tasks, file summaries, code reviews, or reasoning steps to free local MLX models running on your Apple Silicon Mac.

## Available Local Models
* **`qwen-3.6-operator`** *(Default)*: Fast, capable general-purpose 27B model.
* **`qwen-3.6-thinking`**: Qwen 3.6 with deep thinking reasoning.
* **`deepseek-r1-architect`**: DeepSeek R1 reasoning & architecture model.
* **`gemma-4-26b`**: Google Gemma 4 26B model.
* **`devstral-2-123b`**: Heavyweight 123B coding model.
* **`llama-scout`**: Fast low-latency utility model.

## How to Delegate Work

Run the `local-agent-dispatch.py` (or `local-agent`) bridge tool via shell execution:

```bash
python3 /Users/bra0002h/ClaudeWorkspace/local-agents/bin/local-agent-dispatch.py --model qwen-3.6-operator --prompt "Analyze the provided file" --files path/to/file.txt
```

### Options:
* `--model <alias>`: Select model alias from list above.
* `--prompt "<text>"`: Detailed prompt or task specification.
* `--files <file1> <file2>`: Optional file attachments to include as context.
