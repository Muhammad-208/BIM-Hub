"""Typed access to config/hub.yaml and config/servers.yaml."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .errors import ConfigError
from .paths import HubPaths


def load_yaml(path: Path) -> Any:
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError as e:
        raise ConfigError(f"Missing config file: {path}") from e


@dataclass
class BridgeConfig:
    transport: str = "http"
    url: str = "http://127.0.0.1:8765"
    timeout_s: float = 60
    retries: int = 1
    map: dict[str, dict[str, str]] = field(default_factory=dict)  # tool -> {method, path}


@dataclass
class ServerConfig:
    name: str
    kind: str                      # native | external
    description: str = ""
    module: str | None = None      # native
    command: str | None = None     # external
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    bridge: BridgeConfig | None = None


def load_servers(paths: HubPaths) -> dict[str, ServerConfig]:
    raw = load_yaml(paths.config / "servers.yaml").get("servers", {}) or {}
    out: dict[str, ServerConfig] = {}
    for name, s in raw.items():
        kind = s.get("kind", "native")
        if kind not in ("native", "external"):
            raise ConfigError(f"servers.yaml: '{name}' has unknown kind '{kind}'")
        bridge = None
        if s.get("bridge"):
            b = dict(s["bridge"])
            mp = b.pop("map", None)
            mapping = load_yaml(paths.config / mp) if mp else {}
            bridge = BridgeConfig(**b, map=mapping or {})
        out[name] = ServerConfig(
            name=name, kind=kind, description=s.get("description", ""),
            module=s.get("module"), command=s.get("command"),
            args=list(s.get("args", [])), env=dict(s.get("env", {})), bridge=bridge,
        )
    return out


def load_hub_settings(paths: HubPaths) -> dict[str, Any]:
    return load_yaml(paths.config / "hub.yaml")
