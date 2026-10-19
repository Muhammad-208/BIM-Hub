"""Transport to the desktop add-ins (Revit / Navisworks / Civil 3D / anything with an HTTP endpoint).

Default contract (see mcp-layer/BRIDGE_PROTOCOL.md):
    GET  {url}/health                         -> {"ok": true, "app": "...", "version": "...", "document": "..."}
    POST {url}/command  {"command", "args"}   -> {"ok": true, "result": ...} | {"ok": false, "error": "..."}
Per-command route overrides (config/bridges/<app>.yaml) let us talk to an existing add-in unchanged:
    <command>: {method: POST, path: "/clash/run"}   → args are sent as the JSON body (GET → query string)
Errors: HTTP >= 400 with a JSON body {error, detail} is turned into a clear BridgeError.
"""
from __future__ import annotations

import time
from typing import Any, Protocol

import httpx

from .config import BridgeConfig
from .errors import BridgeError
from .log import get_logger

log = get_logger("bimhub.bridge")


class Bridge(Protocol):
    def health(self) -> dict[str, Any]: ...
    def call(self, command: str, args: dict[str, Any] | None = None) -> Any: ...


class HttpBridge:
    def __init__(self, cfg: BridgeConfig, app: str):
        self.cfg, self.app = cfg, app
        self._client = httpx.Client(base_url=cfg.url.rstrip("/"), timeout=cfg.timeout_s)

    def health(self) -> dict[str, Any]:
        try:
            r = self._client.get("/health", timeout=5)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            raise BridgeError(self._down_msg(e)) from e

    def call(self, command: str, args: dict[str, Any] | None = None) -> Any:
        args = {k: v for k, v in (args or {}).items() if v is not None}
        route = self.cfg.map.get(command)
        last: Exception | None = None
        for attempt in range(self.cfg.retries + 1):
            try:
                if route:
                    method = route.get("method", "POST").upper()
                    if method == "GET":
                        r = self._client.get(route["path"], params=args)
                    else:
                        r = self._client.request(method, route["path"], json=args)
                else:
                    r = self._client.post("/command", json={"command": command, "args": args})
                if r.status_code >= 400:
                    raise BridgeError(self._error_from(r, command))
                body = r.json()
                if isinstance(body, dict) and "ok" in body:
                    if not body["ok"]:
                        raise BridgeError(f"{self.app} add-in error in '{command}': {body.get('error')}")
                    return body.get("result", body)
                return body
            except BridgeError:
                raise
            except httpx.ReadTimeout as e:
                # never retry a timed-out call: the add-in may still be executing it (e.g. a clash run)
                raise BridgeError(f"{self.app} did not answer '{command}' within {self.cfg.timeout_s}s "
                                  "(it may still be running — check the app before retrying)") from e
            except httpx.ConnectError as e:
                last = e
                log.warning("%s bridge attempt %d failed: %s", self.app, attempt + 1, e)
                time.sleep(0.5)
            except Exception as e:  # noqa: BLE001
                raise BridgeError(f"{self.app} bridge failed on '{command}': {e}") from e
        raise BridgeError(self._down_msg(last))

    def _error_from(self, r: httpx.Response, command: str) -> str:
        """Add-ins report handler errors as HTTP 4xx/5xx with a JSON body ({error, detail} or {error})."""
        try:
            b = r.json()
            detail = b.get("detail") or b.get("message") or ""
            return f"{self.app} add-in error in '{command}': {b.get('error', r.status_code)} {detail}".strip()
        except Exception:  # noqa: BLE001
            return f"{self.app} add-in returned HTTP {r.status_code} for '{command}'"

    def _down_msg(self, e: Exception | None) -> str:
        return (f"{self.app} is not reachable at {self.cfg.url} ({e}). "
                f"Open {self.app} with the BIM Hub add-in loaded, then retry.")


def make_bridge(cfg: BridgeConfig | None, app: str) -> Bridge:
    if cfg is None:
        raise BridgeError(f"No bridge configured for {app} in servers.yaml")
    if cfg.transport == "http":
        return HttpBridge(cfg, app)
    raise BridgeError(f"Unknown bridge transport '{cfg.transport}' for {app}")
