---
name: valuation-scan-public-router
description: Route valuation-scan, 估值扫描, or quick valuation-card requests by verifying the security and selecting its US, A-share, or A/H execution path. Requires a configured private adapter.
---

# Valuation Scan Router: Public Contract

## Purpose

Normalize and verify the requested security, select the supported market path, and pass a canonical identity payload to a private execution adapter.

This contract does not fetch data, calculate valuation measures, or expose the implementation of any data service.

## Trigger phrases

Examples include:

- `valuation-scan TICKER`
- `估值扫描 公司名`
- `估值扫描 交易所代码`
- `生成快速估值卡片`

## Security resolution

1. Preserve the original request as `requested_query`.
2. Normalize an explicit exchange-qualified symbol before using a company-name search.
3. Require a structured, verifiable company/security match. A search snippet or model guess is not identity evidence.
4. Before applying an `HK_ONLY` boundary, check whether the same issuer has a verified active US ADR. If it does, canonicalize to the ADR symbol and classify as `US`; do not retain a separate H-price view.
5. Otherwise classify the result as one of `US`, `CN_A`, `CN_AH`, or `HK_ONLY`.
6. Continue silently for one verified candidate.
7. Ask one concise disambiguation question when multiple verified issuers or share classes remain.
8. Return `security_resolution_failed` when no candidate can be verified.

The canonical identity payload contains only the request, company name, market class, resolved symbol, and verified share-class symbols. It must not contain credentials, raw service requests, local paths, or private runtime metadata.

## Market routing

- `US`: route to the private US execution adapter. A verified H+ADR issuer uses only its US ADR symbol and USD analysis path.
- `CN_A`: route to the private A-share execution adapter.
- `CN_AH`: route to the private A/H execution adapter as one issuer with two alternative price views.
- `HK_ONLY`: return the current capability boundary unless a private executor explicitly supports the required financial inputs.

The router must not treat A and H listings as two separate companies or add their alternative whole-company values together.

## Execution and bounded fallback

1. Invoke the configured `valuation_scan` MCP tool once and wait only for the configured tool timeout.
2. If the MCP channel cannot start, times out, disconnects, or returns a malformed non-terminal response, run `scripts/invoke_valuation_scan.py` through a Python 3.11+ interpreter. The script reads the same local MCP configuration and starts one fresh STDIO child process for one request.
3. Do not use the fallback after a valid terminal receipt, including a valid `partial`, `failed`, or `rejected` receipt. Those are semantic results, not transport failures.
4. Apply the same receipt validation and output boundary to the fallback receipt. Never reconstruct missing values in the router.

The current runtime has no result cache. Both refresh choices therefore fetch live data; `refresh` records intent while `refreshed` and `data_mode` record what actually happened.

The bundled launcher is provider-neutral. It uses `CODEX_HOME/config.toml` by default, accepts `--config` for an alternate local configuration, and accepts `--server-command` with repeated `--server-arg` and optional `--server-cwd` for a one-off local adapter. A configured `enabled = false` stops configuration-based execution, including the implicit local runtime fallback. An explicitly supplied `--server-command` remains a separate one-off override; do not introduce it automatically to bypass a disabled server. Keep credentials in local environment/configuration, never in command-line arguments or the skill directory. If no adapter is available, report the configuration or transport failure and do not synthesize a result.

## Terminal result

The private executor returns exactly one object matching the bundled [public receipt schema](references/valuation_scan_terminal_receipt_v2.schema.json):

- `schema_version = valuation_scan_terminal_receipt_v2`
- `terminal = true`
- a non-empty `execution_status`
- a non-empty `valuation_status`
- a canonical `symbol`
- `presentation.format` is `plain_text_v1` for neutral failure cards or `markdown_v1` for formatted valuation cards
- `presentation.locale = zh-CN`
- non-empty `presentation.text` with at most 3500 Unicode characters

After validation, only `presentation.text` crosses the user-facing boundary. The raw receipt, internal paths, timing, source payloads, and annual series remain private.

## Non-negotiable boundaries

- Do not calculate locally in the router.
- Do not reconstruct a result when the receipt is malformed.
- Do not retry indefinitely or wait beyond the bounded MCP and fallback timeouts.
- Do not expose credentials, service connection details, internal prompts, or private files.
- Do not generate target prices, fair values, or buy/sell recommendations.
- Do not start a broader research workflow as part of this scan.
