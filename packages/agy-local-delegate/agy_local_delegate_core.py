"""Pure, unit-testable core for local model delegation (Apple Silicon MLX / Rapid / Ollama).

Allows Antigravity sessions to offload mechanical analysis, summaries, reviews,
or code inspections to free local LLMs running via OpenAI-compatible endpoints
(e.g., Rapid-MLX for MLX, llama.cpp / llama-server for GGUF, Ollama, LM Studio).

Features:
  * Full catalog updated to Qwen 3.8 (replacing Qwen 3.6 as default operator),
    DeepSeek R1, KAT Coder, Gemma 4, Kimi-VL, Devstral, Nemotron, and Llama Scout.
  * Live on-disk model scanner for ~/.models with size and availability reporting.
  * Bounded file context bundler with overflow protection.
  * Pure standard library (urllib.request, json, os), fail-safe.
  * Cross-platform (macOS, Windows, Linux).
"""

import os
import sys
import re
import time
import socket
import subprocess
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional, Tuple


DEFAULT_ENDPOINT = "http://127.0.0.1:8000/v1"
DEFAULT_MODELS_DIR = os.path.expanduser("~/.models")

# Comprehensive local model catalog with capabilities & on-disk directories
MODEL_CATALOG = {
    # --- Qwen 3.8 Series (Default Workhorse) ---
    "qwen-3.8-operator": {
        "description": "Fast 27B general-purpose coding & operations workhorse (Default)",
        "default_model_id": "mlx-community/Qwen3.8-27B-4bit",
        "subdir": "Qwen3.8-27B-4bit",
        "context_window": 32768,
        "is_default": True,
    },
    "qwen-3.8-thinking": {
        "description": "Qwen 3.8 reasoning model with chain-of-thought analysis",
        "default_model_id": "mlx-community/Qwen3.8-27B-4bit",
        "subdir": "Qwen3.8-27B-4bit",
        "context_window": 32768,
    },
    "qwen-3.8-8bit": {
        "description": "Qwen 3.8 27B higher-precision 8-bit operator",
        "default_model_id": "mlx-community/Qwen3.8-27B-8bit",
        "subdir": "Qwen3.8-27B-8bit",
        "context_window": 32768,
    },
    "qwen-3.8-mtp": {
        "description": "Qwen 3.8 with Multi-Token Prediction (MTP) acceleration",
        "default_model_id": "mlx-community/Qwen3.8-27B-MTP-4bit",
        "subdir": "Qwen3.8-27B-MTP-4bit",
        "context_window": 32768,
    },
    "qwen-80b-thinking": {
        "description": "Heavyweight 80B architecture and synthesis model",
        "default_model_id": "mlx-community/Qwen3-Next-80B-A3B-Thinking-4bit",
        "subdir": "qwen3-next-80b-thinking-mlx",
        "context_window": 32768,
    },

    # --- Reasoning & Architecture ---
    "deepseek-r1-architect": {
        "description": "DeepSeek R1 complex architectural reasoning and logic",
        "default_model_id": "mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit",
        "subdir": "DeepSeek-R1-Distill-Qwen-32B-4bit",
        "context_window": 65536,
    },

    # --- Specialized Coding ---
    "kat-coder-optiq": {
        "description": "KAT Coder V2.5 Dev OptiQ specialized code synthesis",
        "default_model_id": "mlx-community/KAT-Coder-V2.5-Dev-OptiQ-4bit",
        "subdir": "KAT-Coder-V2.5-Dev-OptiQ-4bit",
        "context_window": 32768,
    },
    "devstral-2-123b": {
        "description": "Heavyweight 123B code refactoring and translation engine",
        "default_model_id": "mlx-community/Devstral-2-123B-Instruct-2512-4bit",
        "subdir": "Devstral-2-123B-Instruct-2512-4bit",
        "context_window": 32768,
    },

    # --- Multimodal & Vision ---
    "gemma-4-26b": {
        "description": "Google Gemma 4 26B instruction & analysis model",
        "default_model_id": "unsloth/gemma-4-26b-a4b-it-MLX-8bit",
        "subdir": "_override_gemma-4-26b-a4b-it-MLX-8bit",
        "context_window": 8192,
    },
    "kimi-vl-thinking": {
        "description": "Kimi-VL compact multimodal vision & reasoning utility",
        "default_model_id": "mlx-community/Kimi-VL-A3B-Thinking-2506-6bit",
        "subdir": "Kimi-VL-A3B-Thinking-2506-6bit",
        "context_window": 16384,
    },

    # --- Fast Utility & Diagnostics ---
    "ministral-14b": {
        "description": "Ministral 14B fast reasoning & inspection model",
        "default_model_id": "mlx-community/Ministral-3-14B-Reasoning-2512-8bit",
        "subdir": "ministral14-reasoning-8bit",
        "context_window": 16384,
    },
    "nemotron-omni": {
        "description": "NVIDIA Nemotron 3 Nano Omni reasoning model",
        "default_model_id": "mlx-community/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-6bit",
        "subdir": "nemotron-omni-6bit",
        "context_window": 16384,
    },
    "llama-scout": {
        "description": "Llama 4 Scout fast low-latency utility & classification",
        "default_model_id": "mlx-community/Llama-4-Scout-17B-16E-Instruct-4bit",
        "subdir": "Llama-4-Scout-17B-16E-Instruct-4bit",
        "context_window": 8192,
    },
}


def resolve_model_reference(model: str, models_dir: Optional[str] = None) -> Dict[str, Any]:
    """Resolve a catalog alias, model ID, or local path without losing custom values."""
    requested = (model or "qwen-3.8-operator").strip()
    info = MODEL_CATALOG.get(requested)
    target_dir = models_dir or get_models_dir()

    if info:
        subdir = info.get("subdir", "")
        local_path = os.path.join(target_dir, subdir) if subdir else ""
        installed = bool(local_path and os.path.isdir(local_path))
        return {
            "requested": requested,
            "alias": requested,
            "model_id": info["default_model_id"],
            "subdir": subdir,
            "local_path": local_path if installed else "",
            "serve_arg": local_path if installed else info["default_model_id"],
            "installed": installed,
        }

    expanded = os.path.abspath(os.path.expanduser(requested)) if requested.startswith(("~", ".", "/")) else requested
    is_local = os.path.isdir(expanded)
    model_id = os.path.basename(expanded.rstrip(os.sep)) if is_local else requested
    return {
        "requested": requested,
        "alias": requested,
        "model_id": model_id,
        "subdir": os.path.basename(expanded.rstrip(os.sep)) if is_local else "",
        "local_path": expanded if is_local else "",
        "serve_arg": expanded if is_local else requested,
        "installed": is_local,
    }


def _normalized_model_names(value: str) -> set:
    """Return conservative normalized forms used to compare served model names."""
    if not value:
        return set()
    raw = str(value).strip().rstrip("/")
    forms = {raw.casefold(), os.path.basename(raw).casefold()}
    # Rapid-MLX aliases commonly differ only in punctuation/case from HF IDs.
    for item in list(forms):
        forms.add(re.sub(r"[^a-z0-9]+", "", item))
    return {item for item in forms if item}


def model_names_match(served: str, requested: str) -> bool:
    """Conservatively compare an API model name with an alias/ID/path."""
    if not served or str(served).casefold() == "default":
        return False
    resolved = resolve_model_reference(requested)
    candidates = {
        requested,
        resolved.get("alias", ""),
        resolved.get("model_id", ""),
        resolved.get("subdir", ""),
        resolved.get("local_path", ""),
        resolved.get("serve_arg", ""),
    }
    served_forms = _normalized_model_names(served)
    return any(served_forms & _normalized_model_names(candidate) for candidate in candidates if candidate)


def find_matching_model_server(
    model: str,
    start_port: int = 8000,
    end_port: int = 8015,
) -> Optional[Dict[str, Any]]:
    """Return an active server only when it advertises the requested model."""
    for server in find_active_model_servers(start_port, end_port):
        for served_model in server.get("models", []):
            if model_names_match(served_model, model):
                result = dict(server)
                result["matched_model"] = served_model
                return result
    return None


def get_server_model(endpoint: str, requested: Optional[str] = None, timeout: float = 2.0) -> Optional[str]:
    """Return the requested matching model, or the first advertised model."""
    health = check_server_health(endpoint, timeout=timeout)
    if not health.get("online"):
        return None
    models = [m for m in health.get("available_models", []) if m]
    if requested:
        for model in models:
            if model_names_match(model, requested):
                return model
    return models[0] if models else None


def smoke_test_gemini_proxy(
    base_url: str,
    timeout: float = 60.0,
    prompt: str = "Reply with the single word LOCAL.",
) -> Dict[str, Any]:
    """Run one non-streaming inference request through the Gemini proxy."""
    url = f"{base_url.rstrip('/')}/v1beta/models/local:generateContent"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 8},
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": "local"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        parts = body.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
        has_function_call = any(isinstance(part, dict) and "functionCall" in part for part in parts)
        if not text and not has_function_call:
            return {"success": False, "error": "Proxy returned no text or function call"}
        return {"success": True, "reply": text, "response": body}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def get_endpoint_url() -> str:
    """Return local OpenAI-compatible API base URL."""
    return os.environ.get("AGY_LOCAL_MODEL_ENDPOINT", DEFAULT_ENDPOINT).rstrip("/")


def get_models_dir() -> str:
    """Return on-disk models directory path."""
    return os.environ.get("AGY_MODELS_DIR", DEFAULT_MODELS_DIR)


def check_server_health(endpoint: Optional[str] = None, timeout: float = 2.0) -> Dict[str, Any]:
    """Health check local inference server."""
    base_url = (endpoint or get_endpoint_url()).rstrip("/")
    models_url = f"{base_url}/models"
    try:
        req = urllib.request.Request(models_url, headers={"User-Agent": "Antigravity-Local-Delegate"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("id") for m in data.get("data", [])]
                return {"online": True, "endpoint": base_url, "available_models": models}
    except Exception as e:
        return {"online": False, "endpoint": base_url, "error": str(e)}
    return {"online": False, "endpoint": base_url, "error": "Unknown status"}


def get_directory_size_gb(path: str) -> float:
    """Compute approximate disk size in gigabytes."""
    total_bytes = 0
    try:
        for root, _, files in os.walk(path):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    total_bytes += os.path.getsize(fp)
                except Exception:
                    pass
    except Exception:
        pass
    return round(total_bytes / (1024 ** 3), 1)


def scan_local_models_dir(models_dir: Optional[str] = None) -> Dict[str, Any]:
    """Scan the local model directory on disk and report available models."""
    target_dir = models_dir or get_models_dir()
    installed_catalog = []
    unregistered_models = []

    if not os.path.isdir(target_dir):
        return {
            "models_dir": target_dir,
            "exists": False,
            "installed_catalog": [],
            "unregistered_models": [],
        }

    disk_dirs = set(os.listdir(target_dir))

    # Check catalog entries
    for alias, info in MODEL_CATALOG.items():
        subdir = info.get("subdir", "")
        is_installed = subdir in disk_dirs if subdir else False
        size_gb = 0.0
        if is_installed:
            model_full_path = os.path.join(target_dir, subdir)
            size_gb = get_directory_size_gb(model_full_path)
            installed_catalog.append({
                "alias": alias,
                "description": info["description"],
                "subdir": subdir,
                "size_gb": size_gb,
                "installed": True,
            })

    # Check for models on disk that are not registered in catalog
    catalog_subdirs = {info.get("subdir") for info in MODEL_CATALOG.values() if info.get("subdir")}
    for item in sorted(disk_dirs):
        full_item_path = os.path.join(target_dir, item)
        if os.path.isdir(full_item_path) and not item.startswith("."):
            if item not in catalog_subdirs:
                size_gb = get_directory_size_gb(full_item_path)
                unregistered_models.append({
                    "name": item,
                    "size_gb": size_gb,
                    "path": full_item_path,
                })

    return {
        "models_dir": target_dir,
        "exists": True,
        "installed_catalog": installed_catalog,
        "unregistered_models": unregistered_models,
    }


def bundle_file_attachments(filepaths: List[str], max_total_chars: int = 150000) -> str:
    """Read attached files and format as bounded markdown context."""
    if not filepaths:
        return ""
    
    sections = ["\n\n--- ATTACHED FILE CONTEXT ---"]
    current_chars = 0

    for path in filepaths:
        norm_path = os.path.abspath(path)
        if not os.path.isfile(norm_path):
            sections.append(f"\n[Warning: File not found: {path}]")
            continue
        try:
            with open(norm_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            if current_chars + len(content) > max_total_chars:
                allowed = max(0, max_total_chars - current_chars)
                content = content[:allowed] + "\n... [Context truncated to prevent overflow] ..."
            sections.append(f"\n### File: `{path}`\n```\n{content}\n```")
            current_chars += len(content)
            if current_chars >= max_total_chars:
                break
        except Exception as e:
            sections.append(f"\n[Error reading file {path}: {e}]")

    return "\n".join(sections)


def build_chat_payload(
    prompt: str,
    model_alias: str = "qwen-3.8-operator",
    files: Optional[List[str]] = None,
    system_instruction: str = "You are a specialized local AI assistant. Provide concise, accurate responses.",
    temperature: float = 0.2,
    max_tokens: int = 4096,
) -> Dict[str, Any]:
    """Construct OpenAI-compatible chat completion request payload."""
    resolved = resolve_model_reference(model_alias)
    model_id = resolved["model_id"]

    context_text = bundle_file_attachments(files or [])
    full_user_content = prompt + context_text

    return {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": full_user_content},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }


def dispatch_local_prompt(
    prompt: str,
    model_alias: str = "qwen-3.8-operator",
    files: Optional[List[str]] = None,
    endpoint: Optional[str] = None,
    timeout: float = 120.0,
    skip_ram_preflight: bool = False,
) -> Dict[str, Any]:
    """Send prompt to local model endpoint and return parsed response."""
    # 1. Mandatory RAM Preflight Check (prevent unified memory freeze)
    if not skip_ram_preflight and os.environ.get("AGY_SKIP_RAM_PREFLIGHT", "0") != "1":
        preflight = ram_preflight_check(model_alias)
        if not preflight.get("fits", True):
            return {
                "success": False,
                "error": f"RAM preflight safety check failed: {preflight.get('message')}",
                "hint": "Free resident memory with 'agy-evict' or bypass with AGY_SKIP_RAM_PREFLIGHT=1.",
                "preflight": preflight,
            }

    base_url = (endpoint or get_endpoint_url()).rstrip("/")
    completions_url = f"{base_url}/chat/completions"
    payload = build_chat_payload(prompt, model_alias=model_alias, files=files)

    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        completions_url,
        data=data_bytes,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Antigravity-Local-Delegate",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            choices = body.get("choices", [])
            reply = choices[0]["message"]["content"] if choices else ""
            usage = body.get("usage", {})
            return {
                "success": True,
                "reply": reply,
                "model": payload["model"],
                "usage": usage,
            }
    except urllib.error.URLError as e:
        return {
            "success": False,
            "error": f"Local model server unreachable at {base_url}: {e.reason}",
            "hint": "Start your local MLX / Rapid / llama.cpp / Ollama server on port 8000.",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Local inference error: {str(e)}",
        }


def get_available_system_ram_gb() -> Tuple[float, float]:
    """Return (available_ram_gb, total_ram_gb).

    Cross-platform memory detection (macOS vm_stat, Linux /proc/meminfo, Windows GlobalMemoryStatusEx).
    """
    # 1. macOS
    if sys.platform == "darwin":
        try:
            # Total RAM via sysctl
            tot_bytes = int(subprocess.check_output(["sysctl", "-n", "hw.memsize"]).strip())
            tot_gb = tot_bytes / (1024 ** 3)

            # Available RAM via vm_stat
            vm_out = subprocess.check_output(["vm_stat"]).decode("utf-8")
            page_size = 4096
            m_ps = re.search(r"page size of (\d+) bytes", vm_out)
            if m_ps:
                page_size = int(m_ps.group(1))

            pages_free = 0
            pages_inactive = 0
            pages_purgeable = 0
            pages_speculative = 0

            for line in vm_out.splitlines():
                if "Pages free:" in line:
                    pages_free = int(re.sub(r"[^0-9]", "", line))
                elif "Pages inactive:" in line:
                    pages_inactive = int(re.sub(r"[^0-9]", "", line))
                elif "Pages purgeable:" in line:
                    pages_purgeable = int(re.sub(r"[^0-9]", "", line))
                elif "Pages speculative:" in line:
                    pages_speculative = int(re.sub(r"[^0-9]", "", line))

            avail_bytes = (pages_free + pages_inactive + pages_purgeable + pages_speculative) * page_size
            avail_gb = avail_bytes / (1024 ** 3)
            return (round(avail_gb, 1), round(tot_gb, 1))
        except Exception:
            pass

    # 2. Linux
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/meminfo", "r") as f:
                info = f.read()
            m_avail = re.search(r"MemAvailable:\s+(\d+)\s+kB", info)
            m_tot = re.search(r"MemTotal:\s+(\d+)\s+kB", info)
            if m_avail and m_tot:
                avail_gb = int(m_avail.group(1)) / (1024 ** 2)
                tot_gb = int(m_tot.group(1)) / (1024 ** 2)
                return (round(avail_gb, 1), round(tot_gb, 1))
        except Exception:
            pass

    # Fallback (approximate 32GB total, 16GB available)
    return (16.0, 32.0)


def find_free_port(start_port: int = 8000, max_port: int = 8050) -> int:
    """Find the first available TCP port in the given range."""
    for port in range(start_port, max_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return 0


def find_active_model_servers(start_port: int = 8000, end_port: int = 8015) -> List[Dict[str, Any]]:
    """Scan port range for active OpenAI-compatible model servers."""
    active = []
    for port in range(start_port, end_port + 1):
        url = f"http://127.0.0.1:{port}/v1"
        health = check_server_health(url, timeout=0.8)
        if health.get("online"):
            active.append({
                "port": port,
                "endpoint": url,
                "models": health.get("available_models", []),
            })
    return active


def get_model_weights_size_gb(model_alias: str, models_dir: Optional[str] = None) -> float:
    """Estimate on-disk weight size in GB for a registered model alias."""
    target_dir = models_dir or get_models_dir()
    resolved = resolve_model_reference(model_alias, models_dir=target_dir)
    model_path = resolved.get("local_path", "")
    if model_path and os.path.isdir(model_path):
        return get_directory_size_gb(model_path)
    return 14.0  # Conservative fallback when weights are not available locally.


def ram_preflight_check(
    model_alias: str = "qwen-3.8-operator",
    floor_gb: float = 16.0,
    overhead_gb: float = 6.0,
    models_dir: Optional[str] = None,
    scan_ports: bool = True,
) -> Dict[str, Any]:
    """Perform RAM preflight check to ensure model safely fits before launching.

    Deliberately checks:
    1. Is the model already served on an active port? (No new RAM needed)
    2. Do disk weights + runtime overhead fit within available RAM while preserving a floor?
    """
    # 1. Question 0: Already served?
    if scan_ports:
        target_info = MODEL_CATALOG.get(model_alias, {})
        target_id = target_info.get("default_model_id", "")
        target_subdir = target_info.get("subdir", "")

        active_servers = find_active_model_servers(start_port=8000, end_port=8015)
        for s in active_servers:
            models = s.get("models", [])
            if any(model_names_match(m, model_alias) or m == target_id or m == target_subdir or m == model_alias for m in models):
                return {
                    "fits": True,
                    "already_served": True,
                    "served_port": s["port"],
                    "endpoint": s["endpoint"],
                    "model_alias": model_alias,
                    "message": f"Model {model_alias} is ALREADY running on port {s['port']} — reusing without loading new weights.",
                }

    # 2. Question 1: Does it fit in RAM?
    avail_gb, total_gb = get_available_system_ram_gb()
    weights_gb = get_model_weights_size_gb(model_alias, models_dir=models_dir)
    need_gb = round(weights_gb + overhead_gb, 1)
    fits = (avail_gb - need_gb) >= floor_gb

    return {
        "fits": fits,
        "already_served": False,
        "served_port": None,
        "endpoint": None,
        "model_alias": model_alias,
        "weights_gb": weights_gb,
        "overhead_gb": overhead_gb,
        "need_gb": need_gb,
        "available_gb": avail_gb,
        "total_gb": total_gb,
        "floor_gb": floor_gb,
        "remaining_after_load_gb": round(avail_gb - need_gb, 1),
        "message": (
            f"Clear: needs ~{need_gb} GB (weights {weights_gb} + {overhead_gb} GB overhead); "
            f"{avail_gb} GB available, {floor_gb} GB floor kept."
            if fits else
            f"Tight: needs ~{need_gb} GB (weights {weights_gb} + {overhead_gb} GB overhead); "
            f"only {avail_gb} GB available (would breach {floor_gb} GB floor)."
        ),
    }


def _loopback_port_from_env(command: str, variable: str) -> Optional[int]:
    """Extract a loopback endpoint port from one process-environment line."""
    pattern = (
        rf"(?:^|\s){re.escape(variable)}="
        r"https?://(?:localhost|127\.0\.0\.1):(\d+)(?:/|\s|$)"
    )
    match = re.search(pattern, command)
    return int(match.group(1)) if match else None


def _add_attached_owner(
    attached: Dict[int, List[str]],
    port: int,
    owner: str,
) -> None:
    owners = attached.setdefault(port, [])
    if owner not in owners:
        owners.append(owner)


def get_attached_client_ports() -> Tuple[Dict[int, List[str]], bool]:
    """Return local inference/proxy ports attached to AGY or Claude clients.

    Claude Code's loopback ANTHROPIC_BASE_URL is authoritative. AGY's
    GOOGLE_GEMINI_BASE_URL identifies its proxy; an attached proxy's /health
    response is used to protect the upstream model server as well.

    The boolean reports whether client inspection was reliable. Callers must
    fail closed when it is false.
    """
    attached: Dict[int, List[str]] = {}

    try:
        result = subprocess.run(
            ["ps", "eww", "-axo", "pid=,command="],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return attached, False

    for line in result.stdout.splitlines():
        is_claude = bool(
            re.search(r"(?:^|\s)(?:\S*/)?claude(?:\s|$)", line)
        )
        is_agy = bool(
            re.search(r"(?:^|\s)(?:\S*/)?agy(?:\s|$)", line)
        )

        if is_claude:
            port = _loopback_port_from_env(line, "ANTHROPIC_BASE_URL")
            if port is not None:
                _add_attached_owner(attached, port, "Claude Code")

        if is_agy:
            port = _loopback_port_from_env(
                line,
                "GOOGLE_GEMINI_BASE_URL",
            )
            if port is not None:
                _add_attached_owner(attached, port, "AGY")

    reliable = True

    # An AGY client attaches to the Gemini proxy. Protect the proxy's upstream
    # model server too, because killing it would still terminate inference.
    for proxy_port, owners in list(attached.items()):
        if "AGY" not in owners or not 9191 <= proxy_port <= 9205:
            continue

        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{proxy_port}/health",
                timeout=2,
            ) as response:
                health = json.loads(response.read().decode("utf-8"))
            upstream = str(health.get("upstream", ""))
            match = re.search(
                r"https?://(?:localhost|127\.0\.0\.1):(\d+)",
                upstream,
            )
            if not match:
                reliable = False
                continue
            _add_attached_owner(
                attached,
                int(match.group(1)),
                "AGY",
            )
        except Exception:
            # We know an AGY client targets this proxy but cannot establish its
            # upstream. Protect all discovered servers rather than guessing.
            reliable = False

    return attached, reliable


def get_attached_agy_ports() -> List[int]:
    """Backward-compatible view of ports attached to AGY clients."""
    attached, _ = get_attached_client_ports()
    return sorted(
        port
        for port, owners in attached.items()
        if "AGY" in owners
    )


def _listener_pid(port: int) -> Optional[int]:
    try:
        output = subprocess.check_output(
            [
                "lsof", "-nP", f"-iTCP:{port}",
                "-sTCP:LISTEN", "-t",
            ],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        return None

    first = output.splitlines()[0].strip() if output else ""
    return int(first) if first.isdigit() else None


def _process_command(pid: int) -> str:
    try:
        return subprocess.check_output(
            ["ps", "-o", "command=", "-p", str(pid)],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        return ""


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def list_resident_servers(
    port_range: Tuple[int, int] = (8000, 8015),
    extra_ports: Tuple[int, ...] = (
        8080,
        9191, 9192, 9193, 9194, 9195,
        9196, 9197, 9198, 9199, 9200,
        9201, 9202, 9203, 9204, 9205,
    ),
) -> List[Dict[str, Any]]:
    """Discover local inference servers and protect attached clients."""
    servers = []
    attached_map, inspection_reliable = get_attached_client_ports()

    ports_to_check = list(dict.fromkeys(
        list(range(port_range[0], port_range[1] + 1))
        + list(extra_ports)
    ))
    checked_pids = set()

    for port in ports_to_check:
        pid = _listener_pid(port)
        if pid is None or pid <= 1 or pid in checked_pids:
            continue
        checked_pids.add(pid)

        cmd = _process_command(pid)
        try:
            rss_raw = subprocess.check_output(
                ["ps", "-o", "rss=", "-p", str(pid)],
                stderr=subprocess.DEVNULL,
            ).decode().strip()
            etime = subprocess.check_output(
                ["ps", "-o", "etime=", "-p", str(pid)],
                stderr=subprocess.DEVNULL,
            ).decode().strip()
            rss_mb = (
                round(int(rss_raw) / 1024, 1)
                if rss_raw.isdigit()
                else 0.0
            )
        except Exception:
            rss_mb = 0.0
            etime = "unknown"

        cmd_lower = cmd.lower()
        if "rapid-mlx" in cmd_lower:
            backend = "rapid-mlx"
        elif "llama-server" in cmd_lower or "llama.cpp" in cmd_lower:
            backend = "llama.cpp"
        elif "mlx_lm.server" in cmd_lower:
            backend = "mlx-lm"
        elif "vllm" in cmd_lower:
            backend = "vllm-mlx"
        elif "agy_local_proxy.py" in cmd_lower:
            backend = "agy-proxy"
        elif "python" in cmd_lower:
            backend = "python-server"
        else:
            backend = "other"

        owners = list(attached_map.get(port, []))
        if not inspection_reliable:
            owners = owners or ["unknown client (inspection failed)"]

        attached = bool(owners)
        rank = 3 if attached else (0 if backend == "agy-proxy" else 1)

        servers.append({
            "port": port,
            "pid": pid,
            "backend": backend,
            "command": cmd,
            "rss_mb": rss_mb,
            "etime": etime,
            "attached": attached,
            "attached_clients": owners,
            "attachment_inspection_reliable": inspection_reliable,
            "rank": rank,
        })

    servers.sort(key=lambda server: (
        server["rank"],
        -server["rss_mb"],
    ))
    return servers


def evict_servers(
    port: Optional[int] = None,
    pid: Optional[int] = None,
    evict_all: bool = False,
    dry_run: bool = False,
    force_attached: bool = False,
    term_wait: float = 8.0,
) -> List[Dict[str, Any]]:
    """Evict eligible servers while protecting attached clients by default."""
    servers = list_resident_servers()
    if not servers:
        return []

    if pid is not None:
        selected = [server for server in servers if server["pid"] == pid]
    elif port is not None:
        selected = [server for server in servers if server["port"] == port]
    elif evict_all:
        selected = list(servers)
    else:
        unattached = [
            server for server in servers if not server["attached"]
        ]
        selected = unattached[:1] if unattached else servers[:1]

    results = []

    for server in selected:
        result = {
            "pid": server["pid"],
            "port": server["port"],
            "backend": server["backend"],
            "rss_mb": server["rss_mb"],
            "attached": server["attached"],
            "attached_clients": server.get("attached_clients", []),
        }

        if server["attached"] and not force_attached:
            result["action"] = "protected_attached"
            results.append(result)
            continue

        if dry_run:
            result["action"] = "would_evict"
            results.append(result)
            continue

        target_pid = server["pid"]
        target_port = server["port"]
        original_command = server["command"]

        # Revalidate both listener ownership and process identity immediately
        # before signaling. PID reuse or port handoff must fail closed.
        if (
            _listener_pid(target_port) != target_pid
            or not original_command
            or _process_command(target_pid) != original_command
        ):
            result["action"] = "skipped_identity_changed"
            results.append(result)
            continue

        try:
            os.kill(target_pid, 15)
        except Exception as exc:
            result["action"] = f"failed_term: {exc}"
            results.append(result)
            continue

        deadline = time.monotonic() + max(0.0, term_wait)
        while _pid_alive(target_pid) and time.monotonic() < deadline:
            time.sleep(0.2)

        if not _pid_alive(target_pid):
            result["action"] = "evicted_term"
            results.append(result)
            continue

        # Escalate only if the same PID still owns the same listener and has
        # the same command identity. Never SIGKILL a changed/reused process.
        if (
            _listener_pid(target_port) != target_pid
            or _process_command(target_pid) != original_command
        ):
            result["action"] = "term_sent_identity_changed_no_kill"
            results.append(result)
            continue

        try:
            os.kill(target_pid, 9)
            result["action"] = "evicted_kill"
        except Exception as exc:
            result["action"] = f"failed_kill: {exc}"
        results.append(result)

    return results
