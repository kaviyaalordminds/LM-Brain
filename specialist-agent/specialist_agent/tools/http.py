"""
Specialist Agent — HTTP Tool

Safe HTTP request tool for specialist agents.
Supports GET and POST; returns structured responses.
NETWORK permission is required.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from specialist_agent.permissions.policy import Permission
from specialist_agent.tools.base import BaseTool, ToolCapability, ToolResult

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 30


class HttpTool(BaseTool):
    """
    HTTP client tool using stdlib urllib (no external dependencies).

    Supports: GET | POST
    """

    def __init__(self, timeout: int = _DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout

    @property
    def name(self) -> str:
        return "http"

    @property
    def capability(self) -> ToolCapability:
        return ToolCapability.HTTP

    @property
    def description(self) -> str:
        return "HTTP GET/POST requests to external services."

    @property
    def permission_level(self) -> str:
        return Permission.NETWORK.value

    def execute(
        self,
        method: str = "GET",
        url: str = "",
        headers: dict[str, str] | None = None,
        body: dict[str, Any] | str | None = None,
        **kwargs: Any,
    ) -> ToolResult:
        """
        Execute an HTTP request.

        Parameters
        ----------
        method  : HTTP method (GET | POST).
        url     : Target URL.
        headers : Optional HTTP headers.
        body    : Optional request body (dict is JSON-serialised).
        """
        if not url.strip():
            return ToolResult(success=False, error="'url' is required.")

        method = method.upper()
        if method not in {"GET", "POST"}:
            return ToolResult(success=False, error=f"Unsupported HTTP method: {method}")

        try:
            req_headers = headers or {}
            encoded_body = None
            if body is not None:
                if isinstance(body, dict):
                    encoded_body = json.dumps(body).encode("utf-8")
                    req_headers.setdefault("Content-Type", "application/json")
                else:
                    encoded_body = str(body).encode("utf-8")

            req = urllib.request.Request(
                url,
                data=encoded_body,
                headers=req_headers,
                method=method,
            )

            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                status = resp.status
                raw = resp.read().decode("utf-8", errors="replace")
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    data = raw
                return ToolResult(
                    success=True,
                    output=data,
                    metadata={"status": status, "url": url, "method": method},
                )

        except urllib.error.HTTPError as exc:
            return ToolResult(
                success=False,
                error=f"HTTP {exc.code}: {exc.reason}",
                metadata={"status": exc.code, "url": url},
            )
        except urllib.error.URLError as exc:
            return ToolResult(success=False, error=f"URL error: {exc.reason}")
        except Exception as exc:  # noqa: BLE001
            return ToolResult(success=False, error=f"HTTP tool error: {exc}")
