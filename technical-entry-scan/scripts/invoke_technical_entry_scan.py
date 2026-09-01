#!/usr/bin/env python3
"""Run one bounded technical-entry scan through a local STDIO adapter."""

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
    raise SystemExit("Python 3.11 or newer is required.") from exc


SERVER_NAME = "technical_entry_scan"
TOOL_NAME = "technical_entry_scan"
RECEIPT_VERSION = "technical_entry_scan_receipt_v1"


class ConfigurationError(ValueError):
    """Raised when no usable local execution adapter is configured."""


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
        default_server = codex_home / "runtimes" / "technical-entry-scan" / "server.py"
        if not default_server.is_file():
            raise ConfigurationError(
                f"no '{server_name}' adapter is configured; configure "
                f"{config_path} or pass --server-command"
            )
        args = [str(default_server)]
        cwd = default_server.parent
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
    if receipt.get("analysis_status") not in {"ready", "partial", "not_assessed"}:
        raise ValueError("analysis_status is invalid")
    if receipt.get("market") != "CN_A":
        raise ValueError("market is invalid")
    if not isinstance(receipt.get("symbol"), str) or not receipt["symbol"].strip():
        raise ValueError("symbol is missing")
    indicators = receipt.get("indicators")
    if not isinstance(indicators, dict) or set(indicators) != {
        "ma250",
        "free_float_turnover",
        "relative_strength",
        "chip_pressure",
    }:
        raise ValueError("four-indicator boundary is invalid")
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
        description="Run one A-share four-indicator scan through a fresh STDIO process."
    )
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--benchmark", default="000300.SH")
    parser.add_argument("--as-of")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--server-name", default=SERVER_NAME)
    parser.add_argument("--server-command")
    parser.add_argument("--server-arg", action="append", default=[])
    parser.add_argument("--server-cwd", type=Path)
    parser.add_argument("--timeout", type=int, default=45)
    parsed = parser.parse_args()
    if parsed.timeout < 1 or parsed.timeout > 300:
        parser.error("--timeout must be between 1 and 300 seconds")
    if parsed.server_cwd and not parsed.server_command:
        parser.error("--server-cwd requires --server-command")
    return parsed


def main() -> int:
    parsed = _parse_args()
    arguments: dict[str, Any] = {
        "symbol": parsed.symbol,
        "benchmark_symbol": parsed.benchmark,
    }
    if parsed.as_of:
        arguments["as_of"] = parsed.as_of

    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": TOOL_NAME, "arguments": arguments},
    }
    codex_home = _codex_home()
    config_path = parsed.config.expanduser() if parsed.config else codex_home / "config.toml"
    try:
        command, cwd, child_env = _server_command(
            config_path=config_path,
            server_name=parsed.server_name,
            override_command=parsed.server_command,
            override_args=parsed.server_arg,
            override_cwd=parsed.server_cwd.expanduser() if parsed.server_cwd else None,
        )
    except ConfigurationError as exc:
        print(f"technical-entry fallback configuration error: {exc}", file=sys.stderr)
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
        print("technical-entry fallback timed out", file=sys.stderr)
        return 124
    except OSError as exc:
        print(
            f"technical-entry fallback could not start: {type(exc).__name__}",
            file=sys.stderr,
        )
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
        print("technical-entry fallback returned no MCP response", file=sys.stderr)
        return 70
    if response.get("error"):
        print("technical-entry fallback returned an MCP protocol error", file=sys.stderr)
        return 70

    try:
        receipt = _validate_receipt((response.get("result") or {}).get("structuredContent"))
    except ValueError as exc:
        print(f"technical-entry fallback receipt invalid: {exc}", file=sys.stderr)
        return 65

    print(json.dumps(receipt, ensure_ascii=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
