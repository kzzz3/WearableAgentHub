"""Application configuration — file-based with env-var override.

Load order (highest priority wins):
  1. Environment variables (including .env via python-dotenv for CI)
  2. config.yaml at repo root
  3. Hard-coded defaults in this module
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CONFIG_PATH = _REPO_ROOT / "config.yaml"

# Load .env as a low-priority fallback (env vars set before process start still win)
_env_path = _REPO_ROOT / ".env"
if _env_path.exists():
    load_dotenv(_env_path, override=False)


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load YAML config file and return a flat dict of settings."""
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    # Flatten nested YAML into a single-level dict
    flat: dict[str, Any] = {}
    for section, values in raw.items():
        if isinstance(values, dict):
            for k, v in values.items():
                flat[k] = v
        else:
            flat[section] = values
    return flat


def _env(key: str, default: str = "") -> str | None:
    """Return env var value if set, otherwise None (so caller can fall through)."""
    val = os.environ.get(key)
    return val if val is not None else None


def _int_env(key: str) -> int | None:
    val = _env(key)
    return int(val) if val is not None else None


_yaml = _load_yaml(_CONFIG_PATH)


@dataclass(frozen=True)
class Settings:
    """Immutable application settings.

    Resolution order per field: env var → config.yaml → default.
    """

    # LLM
    provider_type: str = field(default_factory=lambda: (
        _env("PROVIDER_TYPE")
        or str(_yaml.get("provider_type", "openai_compatible"))
    ))
    openai_api_key: str = field(default_factory=lambda: (
        _env("OPENAI_API_KEY")
        or str(_yaml.get("api_key", ""))
    ))
    openai_base_url: str = field(default_factory=lambda: (
        _env("OPENAI_BASE_URL")
        or str(_yaml.get("base_url", "https://api.openai.com/v1"))
    ))
    openai_model: str = field(default_factory=lambda: (
        _env("OPENAI_MODEL")
        or str(_yaml.get("model", "gpt-4o"))
    ))

    # Server
    backend_port: int = field(default_factory=lambda: (
        _int_env("BACKEND_PORT")
        or int(_yaml.get("backend_port", 8000))
    ))
    frontend_port: int = field(default_factory=lambda: (
        _int_env("FRONTEND_PORT")
        or int(_yaml.get("frontend_port", 5173))
    ))

    # A2A
    a2a_base_url: str = field(default_factory=lambda: (
        _env("A2A_BASE_URL")
        or str(_yaml.get("a2a_base_url", "http://localhost:8000"))
    ))

    # x402 Payment
    x402_base_url: str = field(default_factory=lambda: (
        _env("X402_BASE_URL")
        or str(_yaml.get("x402_base_url", "http://localhost:8002"))
    ))


settings = Settings()
