"""Studio settings in %APPDATA%/BIMHub/studio.json (per user, never inside a project folder).

auth_mode:
  subscription  → the user's own Claude Code login (claude auth login). For the user's personal use.
  api_key       → ANTHROPIC_API_KEY given to the engine. Required for distributing the app / SaaS.
The API key is stored with the OS keyring when available, else in the settings file (user-only folder).
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

KEYRING_SERVICE = "BIMHub-Studio"


def settings_dir() -> Path:
    base = os.environ.get("BIMHUB_STUDIO_HOME") or os.environ.get("APPDATA") or str(Path.home() / ".config")
    d = Path(base) / "BIMHub"
    d.mkdir(parents=True, exist_ok=True)
    return d


@dataclass
class StudioSettings:
    hub_root: str = ""                         # used by the packaged app (sidecar); empty → BIMHUB_ROOT / default
    auth_mode: str = "subscription"            # subscription | api_key
    claude_path: str = ""                      # empty → find `claude` on PATH
    model: str = ""                            # empty → Claude Code default
    permission_mode: str = "dontAsk"           # headless: only pre-approved tools run
    allowed_tools: list[str] = field(default_factory=lambda: [
        "mcp__bimhub", "mcp__revit", "mcp__navisworks", "mcp__civil3d", "mcp__sd-agent",
        "Read", "Grep", "Glob"])
    max_budget_usd: float = 0.0                # API mode only; 0 = no cap
    language: str = "ar-EG"                    # reply language hint added to prompts
    _api_key_inline: str = ""                  # fallback storage when keyring is unavailable

    @classmethod
    def load(cls) -> "StudioSettings":
        f = settings_dir() / "studio.json"
        if f.is_file():
            data = json.loads(f.read_text(encoding="utf-8"))
            known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
            return cls(**known)
        return cls()

    def save(self) -> None:
        (settings_dir() / "studio.json").write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    def public(self) -> dict:
        d = asdict(self)
        d.pop("_api_key_inline", None)
        d["api_key_set"] = bool(self.get_api_key())
        return d

    # API key
    def set_api_key(self, key: str) -> None:
        try:
            import keyring
            keyring.set_password(KEYRING_SERVICE, "anthropic", key)
            self._api_key_inline = ""
        except Exception:  # noqa: BLE001 — no keyring backend
            self._api_key_inline = key
        self.save()

    def get_api_key(self) -> str:
        if os.environ.get("ANTHROPIC_API_KEY"):
            return os.environ["ANTHROPIC_API_KEY"]
        try:
            import keyring
            k = keyring.get_password(KEYRING_SERVICE, "anthropic")
            if k:
                return k
        except Exception:  # noqa: BLE001
            pass
        return self._api_key_inline
