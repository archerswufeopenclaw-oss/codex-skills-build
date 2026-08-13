# Valuation Scan: Public Contract

This directory is a portable bundle of three Codex skill roots, a terminal-receipt schema, and a provider-neutral local STDIO launcher. It does not contain a data provider, credentials, or a private execution adapter.

The workflow is a pressure screen. It is not a target-price model, full DCF, fair-value claim, or buy/sell recommendation.

## Install the skill roots

`router`, `us`, and `cn-a-ah` are independent skill roots. Users with access to this repository can copy them into their Codex skills directory. On Windows PowerShell:

```powershell
$repoRoot = (Resolve-Path .).Path
$codexRoot = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE ".codex" }
$skillRoot = Join-Path $codexRoot "skills"

New-Item -ItemType Directory -Force -Path `
  (Join-Path $skillRoot "valuation-scan-public-router"), `
  (Join-Path $skillRoot "valuation-scan-us"), `
  (Join-Path $skillRoot "valuation-scan-cn-a-ah") | Out-Null

Copy-Item -Recurse -Force "$repoRoot\valuation-scan\router\*" `
  (Join-Path $skillRoot "valuation-scan-public-router")
Copy-Item -Recurse -Force "$repoRoot\valuation-scan\us\*" `
  (Join-Path $skillRoot "valuation-scan-us")
Copy-Item -Recurse -Force "$repoRoot\valuation-scan\cn-a-ah\*" `
  (Join-Path $skillRoot "valuation-scan-cn-a-ah")
```

The same three directories can be copied to `$CODEX_HOME/skills/` on other platforms.

## Configure an execution adapter

The contracts expect a private adapter that exposes the `valuation_scan` MCP tool and returns one `valuation_scan_terminal_receipt_v2` object. Keep provider credentials in the user's local environment or local Codex configuration, never in this repository.

For a local adapter, the relevant configuration shape is:

```toml
[mcp_servers.valuation_scan]
command = "python"
args = ["C:\\path\\to\\server.py"]
cwd = "C:\\path\\to"
```

The bundled launcher reads this section from `CODEX_HOME/config.toml` by default:

```powershell
python -X utf8 -B valuation-scan/router/scripts/invoke_valuation_scan.py `
  --market US --symbol MSFT --timeout 45
```

For an alternate local config, pass `--config`. For a one-off adapter command, pass `--server-command`, repeat `--server-arg` for its arguments, and optionally pass `--server-cwd`. Do not put credentials on the command line.

The launcher only starts the user-supplied adapter, sends one bounded request, validates the terminal receipt, and prints that receipt. It does not fetch market data itself.

## Included contracts

- `router/SKILL.md`: security resolution and market routing.
- `router/scripts/invoke_valuation_scan.py`: provider-neutral bounded STDIO bridge.
- `us/SKILL.md`: single-ticker US pressure-screen contract.
- `cn-a-ah/SKILL.md`: A-share and A/H pressure-screen contract.
- `schemas/valuation_scan_terminal_receipt_v2.schema.json`: terminal-receipt shape.
- `SECURITY.md`: publication boundary and review checklist.

## Historical rebuild archive

`rebuild/` is retained as an early implementation/OpenClaw semantic-reconstruction log. It records formulas, field mappings, unresolved product decisions, and dated golden fixtures; it is not the current public contract, a live-data cache, or an execution adapter.
