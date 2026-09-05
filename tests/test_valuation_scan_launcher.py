from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


LAUNCHER = (
    Path(__file__).resolve().parents[1]
    / "valuation-scan"
    / "router"
    / "scripts"
    / "invoke_valuation_scan.py"
)
ADAPTER = '''\
import json
from pathlib import Path
import sys

Path(__file__).with_suffix(".started").write_text("started", encoding="utf-8")
request = json.loads(sys.stdin.readline())
receipt = {
    "schema_version": "valuation_scan_terminal_receipt_v2",
    "terminal": True,
    "execution_status": "completed",
    "valuation_status": "ready",
    "symbol": request["params"]["arguments"]["symbol"],
    "presentation": {
        "format": "markdown_v1",
        "locale": "zh-CN",
        "text": "Synthetic launcher test.",
    },
}
print(json.dumps({
    "jsonrpc": "2.0",
    "id": request["id"],
    "result": {"structuredContent": receipt},
}))
'''


class ValuationScanLauncherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="valuation-launcher-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.codex_home = self.root / "codex-home"
        self.codex_home.mkdir()
        self.config = self.codex_home / "config.toml"
        self.configured_adapter = self._write_adapter(self.root / "configured.py")
        self.runtime_adapter = self._write_adapter(
            self.codex_home / "runtimes" / "valuation-scan" / "server.py"
        )

    def _write_adapter(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(ADAPTER, encoding="utf-8")
        return path

    def _write_config(self, enabled: bool | None, *, command: bool = True) -> None:
        lines = ["[mcp_servers.valuation_scan]"]
        if enabled is not None:
            lines.append(f"enabled = {str(enabled).lower()}")
        if command:
            lines.extend(
                [
                    f"command = {json.dumps(sys.executable)}",
                    f"args = {json.dumps(['-B', str(self.configured_adapter)])}",
                ]
            )
        self.config.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _run(self, *extra: str) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["CODEX_HOME"] = str(self.codex_home)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONUTF8"] = "1"
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(LAUNCHER),
                "--market",
                "US",
                "--symbol",
                "TEST",
                "--timeout",
                "5",
                *extra,
            ],
            cwd=self.root,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=15,
            check=False,
        )

    def _assert_started(self, adapter: Path, expected: bool) -> None:
        self.assertEqual(adapter.with_suffix(".started").exists(), expected)

    def test_disabled_config_does_not_start_command_or_implicit_runtime(self) -> None:
        for command in (True, False):
            with self.subTest(command=command):
                self._write_config(False, command=command)
                completed = self._run()
                self.assertEqual(completed.returncode, 78, completed.stderr)
                self.assertEqual(completed.stdout, "")
                self.assertIn("'valuation_scan' adapter is disabled", completed.stderr)
                self.assertIn("enabled = false", completed.stderr)
                self._assert_started(self.configured_adapter, False)
                self._assert_started(self.runtime_adapter, False)

    def test_enabled_or_unspecified_config_starts_configured_adapter(self) -> None:
        for enabled in (True, None):
            with self.subTest(enabled=enabled):
                self._write_config(enabled)
                completed = self._run()
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(json.loads(completed.stdout)["symbol"], "TEST")
                self._assert_started(self.configured_adapter, True)
                self._assert_started(self.runtime_adapter, False)
                self.configured_adapter.with_suffix(".started").unlink()

    def test_explicit_command_remains_a_one_off_override_of_disabled_config(self) -> None:
        self._write_config(False)
        override = self._write_adapter(self.root / "override.py")
        completed = self._run(
            "--server-command",
            sys.executable,
            "--server-arg=-B",
            f"--server-arg={override}",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["symbol"], "TEST")
        self._assert_started(override, True)
        self._assert_started(self.configured_adapter, False)
        self._assert_started(self.runtime_adapter, False)


if __name__ == "__main__":
    unittest.main()
