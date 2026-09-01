---
name: technical-entry-scan
description: Analyze one A-share's long-horizon technical entry context using exactly MA250, free-float turnover, benchmark-relative strength, and disclosed chip pressure. Use for 四指标技术扫描、长线建仓时点复核或这四项指标的组合解释；do not use for valuation, broad technical-analysis checklists, or buy/sell recommendations.
---

# Technical Entry Scan

## Purpose

Produce one reproducible A-share technical-context card using exactly four indicator families:

1. MA250;
2. free-float turnover;
3. relative strength versus one explicit benchmark;
4. chip pressure with a disclosed data or model method.

This is an entry-context screen, not a valuation claim, bottom call, target price, or buy/sell recommendation. Do not add MACD, RSI, KDJ, Bollinger Bands, candlestick patterns, fundamentals, or a composite score unless the user explicitly asks for a separate expanded analysis.

## What the four indicators can establish

| Indicator | Required measurements | What it can show | What it cannot establish |
|---|---|---|---|
| MA250 | adjusted close, MA250, close gap, 20-session MA250 slope | Whether price is above or below its long-horizon trend/cost anchor and whether that anchor is rising or falling | Fundamental cheapness, intrinsic value, or that a deeply negative gap must mean-revert |
| Free-float turnover | 5-day and 20-day means, 5d/20d ratio, percentile of the current 20-day mean versus its own trailing history | Participation intensity among economically tradable shares, plus contraction or expansion relative to the stock's own recent regime | Accumulation versus distribution, investor identity, or bullish/bearish direction by itself |
| Relative strength | 20-, 60-, and 250-session arithmetic excess returns versus one named benchmark | Whether the stock's opportunity cost is improving or deteriorating relative to the market and whether short-term repair has broader confirmation | Risk-adjusted alpha, causality, or sector-relative strength unless the benchmark is explicitly changed |
| Chip pressure | method, winning/overhead shares, median cost, upper cost quantile, current-price gap | How much estimated or observed supply sits above the current price and where resistance may be concentrated | Account-level holdings, holder intent, exact support/resistance, or future selling pressure |

Use forward-adjusted A-share OHLC for MA250, relative strength, and model chip costs so corporate actions do not create artificial gaps. Keep turnover rates in provider percentage units.

## Identity and inputs

- Accept one verified active A-share symbol in canonical form such as `600519.SH` or `000333.SZ`.
- Resolve a company name before execution. Ask one concise question if multiple issuers remain; never guess.
- Default the benchmark to CSI 300 (`000300.SH`) unless the user explicitly names another broad A-share index.
- Use the latest complete trading day when `as_of` is omitted. Preserve any earlier user-specified date.

## Execution

1. Invoke the configured `technical_entry_scan` MCP tool once with `symbol`, `benchmark_symbol`, and optional `as_of`.
2. Accept only one terminal `technical_entry_scan_receipt_v1` receipt.
3. If the MCP channel cannot start, times out, disconnects, or returns a malformed non-terminal response, run `scripts/invoke_technical_entry_scan.py` once through Python 3.11+ using the same inputs.
4. Do not run the fallback after a valid `ready`, `partial`, `not_assessed`, `failed`, or `rejected` terminal receipt. These are semantic results, not transport failures.
5. If no configured executor exists, report that the public skill contract is installed but the private adapter is unavailable. Do not calculate an ad hoc replacement inside the router.

The public launcher is provider-neutral. Credentials and provider adapters stay in local configuration or a private runtime, never in this skill.

## Chip-method boundary

`chip_method` must be explicit:

- `provider_distribution`: a provider supplied a point-in-time distribution;
- `free_float_turnover_decay_v1`: a deterministic estimate that decays an active free-float price distribution by daily free-float turnover and allocates each day's new chips across its adjusted trading range;
- `unavailable`: chip pressure is not assessed.

Never silently replace one method with another. When `free_float_turnover_decay_v1` is used, call the result a model estimate and disclose that it cannot observe real accounts, block transfers, holder intent, or all effects of price limits.

## Synthesis

Explain the four dimensions separately, then combine them without a score:

- MA250 supplies the long-trend regime.
- Free-float turnover says whether participation is cooling, stable, or expanding within that regime.
- Relative strength says whether the stock is still losing ground to the benchmark or beginning to repair.
- Chip pressure says how much overhead supply may obstruct a repair.

State both supporting and contradicting evidence. A low-turnover stock far below a falling MA250 is only a weak-trend/low-participation configuration; it does not become an attractive entry until relative strength and price behavior provide confirmation. High overhead chip share can mean substantial prior losses, but it is resistance evidence rather than proof of undervaluation.

## Output boundary

- Present the executor's Chinese `markdown_v1` card and keep it concise.
- Include symbol, data date, benchmark, all four methods/measurements, one combined interpretation, and explicit non-inferences.
- Preserve `partial` or `not_assessed` when required data are missing. Do not treat null as zero or invent a peer/market comparison.
- Never expose credentials, local paths, private adapter details, raw provider payloads, or internal timing.
