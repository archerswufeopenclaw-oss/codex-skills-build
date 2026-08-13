#!/usr/bin/env python3
"""Run one bounded valuation-scan request through a local STDIO adapter.

The script is a provider-neutral launcher, not a data-acquisition adapter. It
starts a user-configured STDIO server as a fresh child process, makes one
``tools/call`` request, validates the terminal receipt, prints only that
receipt as JSON, and exits. Credentials stay in the user's local environment
or configuration and are never printed by this wrapper.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

try:
    import tomllib
except ModuleNotFoundError as exc:  # pragma: no cover - Python < 3.11
    raise SystemExit("Python 3.11 or newer is required for the fallback.") from exc


SERVER_NAME = "valuation_scan"
RECEIPT_VERSION = "valuation_scan_terminal_receipt_v2"


class ConfigurationError(ValueError):
    """Raised when no usable local valuation-scan adapter is configured."""


def _codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME", "").strip()
    return Path(configured).expanduser() if configured else Path.home() / ".codex"


def _server_command(
    *,
    config_path: Path,
    server_name: str,
    override_command: str | None,
    override_args: list[str],
    override_cwd: Path | None,
) -> tuple[list[str], Path, dict[str, str]]:
    codex_home = _codex_home()
    child_env = dict(os.environ)
    # MCP JSON-RPC is UTF-8. This also prevents Python children on Windows
    # from using the system code page for diagnostic output.
    child_env["PYTHONUTF8"] = "1"

    if override_command:
        cwd = override_cwd or Path.cwd()
        if not cwd.is_dir():
            raise ConfigurationError(f"server cwd does not exist: {cwd}")
        return [override_command, *override_args], cwd, child_env

    config: dict[str, Any] = {}
    if config_path.is_file():
        try:
            with config_path.open("rb") as stream:
                config = tomllib.load(stream)
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise ConfigurationError(
                f"could not read config {config_path}: {type(exc).__name__}"
            ) from exc

    server = ((config.get("mcp_servers") or {}).get(server_name) or {})
    command = str(server.get("command") or "").strip()
    args = [str(value) for value in (server.get("args") or [])]
    cwd_text = str(server.get("cwd") or "").strip()
    child_env.update(
        {str(key): str(value) for key, value in (server.get("env") or {}).items()}
    )
    child_env["PYTHONUTF8"] = "1"

    if not command:
        command = sys.executable
        default_server = codex_home / "runtimes" / "valuation-scan" / "server.py"
        if not default_server.is_file():
            raise ConfigurationError(
                f"no '{server_name}' adapter is configured; configure "
                f"{config_path} or pass --server-command"
            )
        args = [str(default_server)]
        cwd = Path(cwd_text) if cwd_text else codex_home / "runtimes" / "valuation-scan"
    else:
        cwd = Path(cwd_text) if cwd_text else Path.cwd()

    if not cwd.is_dir():
        raise ConfigurationError(f"server cwd does not exist: {cwd}")
    return [command, *args], cwd, child_env


def _validate_receipt(receipt: Any) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise ValueError("structuredContent is not an object")
    if receipt.get("schema_version") != RECEIPT_VERSION:
        raise ValueError("receipt schema version is invalid")
    if receipt.get("terminal") is not True:
        raise ValueError("receipt is not terminal")
    if receipt.get("execution_status") not in {"completed", "failed", "rejected"}:
        raise ValueError("execution_status is invalid")
    if not isinstance(receipt.get("valuation_status"), str) or not receipt["valuation_status"].strip():
        raise ValueError("valuation_status is missing")
    if not isinstance(receipt.get("symbol"), str) or not receipt["symbol"].strip():
        raise ValueError("symbol is missing")
    presentation = receipt.get("presentation")
    if not isinstance(presentation, dict):
        raise ValueError("presentation is missing")
    text = presentation.get("text")
    if (
        presentation.get("format") not in {"plain_text_v1", "markdown_v1"}
        or presentation.get("locale") != "zh-CN"
        or not isinstance(text, str)
        or not text.strip()
        or len(text) > 3500
    ):
        raise ValueError("presentation boundary is invalid")
    return receipt


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one valuation scan through a fresh local STDIO process."
    )
    parser.add_argument("--market", required=True, choices=("US", "CN_A", "CN_AH"))
    parser.add_argument("--symbol")
    parser.add_argument("--query", dest="requested_query")
    parser.add_argument("--h-symbol")
    parser.add_argument(
        "--config",
        type=Path,
        help="Alternate Codex TOML config containing mcp_servers.valuation_scan.",
    )
    parser.add_argument(
        "--server-name",
        default=SERVER_NAME,
        help=f"MCP config section to use (default: {SERVER_NAME}).",
    )
    parser.add_argument(
        "--server-command",
        help="One-off local adapter command; overrides the config file.",
    )
    parser.add_argument(
        "--server-arg",
        action="append",
        default=[],
        help="Argument for --server-command; repeat for multiple arguments.",
    )
    parser.add_argument(
        "--server-cwd",
        type=Path,
        help="Working directory for --server-command.",
    )
    parser.add_argument(
        "--refresh",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Record the requested refresh policy; the current runtime always fetches live.",
    )
    parser.add_argument("--timeout", type=int, default=120)
    parsed = parser.parse_args()
    if not (parsed.symbol or parsed.requested_query):
        parser.error("one of --symbol or --query is required")
    if parsed.timeout < 1 or parsed.timeout > 300:
        parser.error("--timeout must be between 1 and 300 seconds")
    if parsed.server_cwd and not parsed.server_command:
        parser.error("--server-cwd requires --server-command")
    return parsed


def main() -> int:
    parsed = _parse_args()
    arguments: dict[str, Any] = {
        "market": parsed.market,
        "refresh": parsed.refresh,
    }
    if parsed.symbol:
        arguments["symbol"] = parsed.symbol
    if parsed.requested_query:
        arguments["requested_query"] = parsed.requested_query
    if parsed.h_symbol:
        arguments["h_symbol"] = parsed.h_symbol

    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "valuation_scan", "arguments": arguments},
    }
    codex_home = _codex_home()
    config_path = (
        parsed.config.expanduser()
        if parsed.config
        else codex_home / "config.toml"
    )
    try:
        command, cwd, child_env = _server_command(
            config_path=config_path,
            server_name=parsed.server_name,
            override_command=parsed.server_command,
            override_args=parsed.server_arg,
            override_cwd=parsed.server_cwd.expanduser() if parsed.server_cwd else None,
        )
    except ConfigurationError as exc:
        print(f"valuation-scan fallback configuration error: {exc}", file=sys.stderr)
        return 78
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            env=child_env,
            input=json.dumps(request, ensure_ascii=True) + "\n",
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=parsed.timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print("valuation-scan fallback timed out", file=sys.stderr)
        return 124
    except OSError as exc:
        print(f"valuation-scan fallback could not start: {type(exc).__name__}", file=sys.stderr)
        return 126

    response = None
    for line in (completed.stdout or "").splitlines():
        try:
            candidate = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict) and candidate.get("id") == 1:
            response = candidate
    if response is None:
        print("valuation-scan fallback returned no MCP response", file=sys.stderr)
        return 70
    if response.get("error"):
        print("valuation-scan fallback returned an MCP protocol error", file=sys.stderr)
        return 70

    try:
        receipt = _validate_receipt(
            ((response.get("result") or {}).get("structuredContent"))
        )
    except ValueError as exc:
        print(f"valuation-scan fallback receipt invalid: {exc}", file=sys.stderr)
        return 65

    # ASCII JSON avoids Windows console-codepage corruption. JSON consumers
    # reconstruct the original Chinese presentation from \u escapes.
    print(json.dumps(receipt, ensure_ascii=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
