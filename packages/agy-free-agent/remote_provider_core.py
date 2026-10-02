#!/usr/bin/env python3
"""Shared core for the remote lane of agy-free-agent (NVIDIA NIM integration).

Privacy posture: the remote lane is DISABLED by default.
Nothing in this module makes a network call on its own unless explicitly selected.
Currently configured ONLY for NVIDIA NIM as requested.
"""

import os
import sys
from dataclasses import dataclass, field

SCHEMA_VERSION = 1

LOCAL = "local"
RENEWING_FREE = "renewing_free"
TRIAL = "trial"
PAID = "paid"
UNKNOWN = "unknown"

@dataclass(frozen=True)
class Provider:
    id: str
    display: str
    tier: str
    base_url: str
    chat_path: str
    models_path: str
    key_env: str
    extra_env: tuple = ()
    static_headers: dict = field(default_factory=dict)
    default_models: tuple = ()
    notes: str = ""

    def auth_headers(self):
        key = os.environ.get(self.key_env, "")
        return {"Authorization": "Bearer " + key, **self.static_headers}


PROVIDERS = {
    "nvidia": Provider(
        id="nvidia",
        display="NVIDIA NIM",
        tier=RENEWING_FREE,
        base_url="https://integrate.api.nvidia.com/v1",
        chat_path="/chat/completions",
        models_path="/models",
        key_env="NVIDIA_API_KEY",
        default_models=("meta/llama-3.1-70b-instruct", "nvidia/neva-22b"),
        notes="NVIDIA NIM API integration for free-agent remote dispatch.",
    ),
}

def get(provider_id: str):
    return PROVIDERS.get(provider_id)
