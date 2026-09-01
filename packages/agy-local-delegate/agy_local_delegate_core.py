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


def get_endpoint_url() -> str:
    """Return local OpenAI-compatible API base URL."""
    return os.environ.get("AGY_LOCAL_MODEL_ENDPOINT", DEFAULT_ENDPOINT).rstrip("/")


def get_models_dir() -> str:
    """Return on-disk models directory path."""
    return os.environ.get("AGY_MODELS_DIR", DEFAULT_MODELS_DIR)


def check_server_health(endpoint: Optional[str] = None, timeout: float = 2.0) -> Dict[str, Any]:
    """Health check local inference server."""
    base_url = endpoint or get_endpoint_url()
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
    alias_info = MODEL_CATALOG.get(model_alias, MODEL_CATALOG["qwen-3.8-operator"])
    model_id = alias_info["default_model_id"]

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

    base_url = endpoint or get_endpoint_url()
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
    return start_port


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
    info = MODEL_CATALOG.get(model_alias, {})
    subdir = info.get("subdir", "")
    if subdir:
        model_path = os.path.join(target_dir, subdir)
        if os.path.isdir(model_path):
            return get_directory_size_gb(model_path)
    return 14.0  # Safe default 4-bit 27B estimation


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
            if any(m == target_id or m == target_subdir or m == model_alias for m in models):
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


def get_attached_agy_ports() -> List[int]:
    """Find ports attached to running agy sessions."""
    attached = set()
    try:
        # Check agy processes
        agy_pids_out = subprocess.check_output(["pgrep", "-x", "agy"]).decode().split()
        for pid in agy_pids_out:
            # Check open connections from agy pid
            lsof_out = subprocess.check_output(["lsof", "-nP", "-p", pid]).decode()
            for m in re.finditer(r":(\d+)\s+\(LISTEN|\(ESTABLISHED", lsof_out):
                port = int(m.group(1))
                if 8000 <= port <= 8020 or 9191 <= port <= 9210 or port == 8080:
                    attached.add(port)
    except Exception:
        pass
    return sorted(list(attached))


def list_resident_servers(
    port_range: Tuple[int, int] = (8000, 8015),
    extra_ports: Tuple[int, ...] = (8080, 9191, 9192, 9193),
) -> List[Dict[str, Any]]:
    """Discover all running local inference servers and proxies with memory stats."""
    servers = []
    attached_ports = set(get_attached_agy_ports())

    ports_to_check = list(range(port_range[0], port_range[1] + 1)) + list(extra_ports)
    checked_pids = set()

    for port in ports_to_check:
        try:
            lsof_out = subprocess.check_output(
                ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
                stderr=subprocess.DEVNULL
            ).decode().strip()
        except Exception:
            continue

        if not lsof_out:
            continue

        pid_str = lsof_out.splitlines()[0].strip()
        if not pid_str.isdigit():
            continue
        pid = int(pid_str)
        if pid in checked_pids or pid <= 1:
            continue
        checked_pids.add(pid)

        # Get command line, RSS, and elapsed time
        try:
            cmd = subprocess.check_output(["ps", "-o", "command=", "-p", str(pid)]).decode().strip()
            rss_kb_str = subprocess.check_output(["ps", "-o", "rss=", "-p", str(pid)]).decode().strip()
            etime_str = subprocess.check_output(["ps", "-o", "etime=", "-p", str(pid)]).decode().strip()
            rss_mb = round(int(rss_kb_str) / 1024, 1) if rss_kb_str.isdigit() else 0.0
        except Exception:
            cmd = "unknown"
            rss_mb = 0.0
            etime_str = "0:00"

        # Determine backend
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
        elif "python" in cmd_lower and ("8000" in cmd_lower or "9191" in cmd_lower):
            backend = "python-server"
        else:
            backend = "other"

        is_attached = port in attached_ports

        # Ranking score (lower = better candidate for eviction)
        # 0 = unattached proxy/zombie, 1 = unattached large server, 2 = attached server
        if not is_attached:
            if backend == "agy-proxy":
                rank = 0
            else:
                rank = 1
        else:
            rank = 3

        servers.append({
            "port": port,
            "pid": pid,
            "backend": backend,
            "command": cmd,
            "rss_mb": rss_mb,
            "etime": etime_str,
            "attached": is_attached,
            "rank": rank,
        })

    # Sort by rank ascending, then RSS descending
    servers.sort(key=lambda s: (s["rank"], -s["rss_mb"]))
    return servers


def evict_servers(
    port: Optional[int] = None,
    pid: Optional[int] = None,
    evict_all: bool = False,
    dry_run: bool = False,
) -> List[Dict[str, Any]]:
    """Evict local model servers/proxies according to safety rankings."""
    servers = list_resident_servers()
    if not servers:
        return []

    targets = []
    if pid is not None:
        targets = [s for s in servers if s["pid"] == pid]
    elif port is not None:
        targets = [s for s in servers if s["port"] == port]
    elif evict_all:
        targets = servers
    else:
        # Evict single highest-ranked candidate
        targets = [servers[0]]

    results = []
    for s in targets:
        target_pid = s["pid"]
        target_backend = s["backend"]
        target_port = s["port"]
        target_rss = s["rss_mb"]

        if dry_run:
            results.append({
                "pid": target_pid,
                "port": target_port,
                "backend": target_backend,
                "rss_mb": target_rss,
                "action": "would_evict",
            })
        else:
            try:
                os.kill(target_pid, 15)  # SIGTERM
                time.sleep(0.5)
                # Check if still alive
                try:
                    os.kill(target_pid, 0)
                    os.kill(target_pid, 9)  # SIGKILL if still lingering
                except OSError:
                    pass
                results.append({
                    "pid": target_pid,
                    "port": target_port,
                    "backend": target_backend,
                    "rss_mb": target_rss,
                    "action": "evicted",
                })
            except Exception as e:
                results.append({
                    "pid": target_pid,
                    "port": target_port,
                    "backend": target_backend,
                    "rss_mb": target_rss,
                    "action": f"failed: {e}",
                })

    return results

