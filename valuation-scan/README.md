# Valuation Scan: Public Contract

This directory is a portable bundle of three Codex skill roots, a terminal-receipt schema, and a provider-neutral local STDIO launcher. It does not contain a data provider, credentials, or a private execution adapter.

The workflow is a pressure screen. It is not a target-price model, full DCF, fair-value claim, or buy/sell recommendation.

## Install the skill roots

`router`, `us`, and `cn-a-ah` are independent skill roots. From the repository root, copy the following public files into the skill directory used by your host. The example uses `.agents/skills`; set `$skillRoot` to your existing installation directory when updating it. Existing listed files are updated; other files are preserved. Run with PowerShell 7:

```powershell
$skillRoot = Join-Path $env:USERPROFILE '.agents/skills'
$packages = @(
    @{ Name = 'valuation-scan-public-router'; Source = 'valuation-scan/router'; Files = @(
        'SKILL.md', 'scripts/invoke_valuation_scan.py',
        'references/valuation_scan_terminal_receipt_v2.schema.json'
    ) },
    @{ Name = 'valuation-scan-us'; Source = 'valuation-scan/us'; Files = @('SKILL.md') },
    @{ Name = 'valuation-scan-cn-a-ah'; Source = 'valuation-scan/cn-a-ah'; Files = @('SKILL.md') }
)
foreach ($package in $packages) {
    foreach ($relative in $package.Files) {
        $target = Join-Path (Join-Path $skillRoot $package.Name) $relative
        New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null
        Copy-Item -LiteralPath (Join-Path $package.Source $relative) -Destination $target -Force
    }
}
```

The same listed files can be copied on other platforms. Preserve their relative paths so the router's schema link remains valid. This file allowlist excludes local caches and research artifacts.

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

`enabled = false` in the selected MCP section stops configuration-based execution, including the implicit local runtime fallback, with exit code 78. An explicit `--server-command` is still a separate one-off override; the skill must not supply it automatically to bypass a disabled server.

The launcher only starts the user-supplied adapter, sends one bounded request, validates the terminal receipt, and prints that receipt. It does not fetch market data itself.

## Included contracts

- `router/SKILL.md`: security resolution and market routing.
- `router/scripts/invoke_valuation_scan.py`: provider-neutral bounded STDIO bridge.
- `us/SKILL.md`: single-ticker US pressure-screen contract.
- `cn-a-ah/SKILL.md`: A-share and A/H pressure-screen contract.
- `router/references/valuation_scan_terminal_receipt_v2.schema.json`: terminal-receipt shape, bundled with the router.
- `schemas/valuation_scan_terminal_receipt_v2.schema.json`: identical copy retained at the previously documented repository path; update both copies together.
- `SECURITY.md`: publication boundary and review checklist.

## Historical rebuild archive

`rebuild/` is retained as an early implementation/OpenClaw semantic-reconstruction log. It records formulas, field mappings, unresolved product decisions, and dated golden fixtures; it is not the current public contract, a live-data cache, or an execution adapter.
