---
name: valuation-scan-us
description: Render a US valuation-pressure card from a verified security and canonical indicator artifact supplied by the valuation-scan router or private adapter. Use for the US output path; do not acquire data or resolve identity here.
---

# US Valuation Scan: Public Contract

## Purpose

Render a fast pressure-screen card from a canonical indicator artifact supplied by a private execution adapter.

This skill is not a data-acquisition implementation, SEC first-read workflow, full DCF, target-price model, fair-value claim, or investment recommendation.

## Input contract

The private adapter supplies:

- a verified US-listed `symbol`;
- an optional verified display name;
- a refresh or reuse decision;
- a canonical indicator artifact with calculation provenance.

The skill must not rediscover the company or silently replace the supplied identity.

## Calculation boundary

One canonical calculator owns Owner FCFF, Operating EV, tax treatment, historical growth comparisons, and bounded reverse-DCF pressure diagnostics.

The renderer may read the canonical artifact and render its values. It must not recompute measures from raw statement rows or introduce a second formula.

All monetary inputs used in one calculation must be in the canonical USD analysis currency. For a foreign issuer or ADR whose FMP statements retain a non-USD `reportedCurrency`, the private adapter must verify one statement currency and apply an FMP-sourced conversion consistently to every statement and balance-sheet monetary value. The USD quote and market capitalization remain unconverted. Missing or inconsistent currency evidence fails closed; profile `isAdr` alone is not routing or currency evidence.

The current adapter has no reusable result cache. A call therefore fetches live data whether `refresh` is true or false, and records `refresh_requested`, `refreshed`, and `data_mode` separately.

## Ready presentation

For a ready result, return `markdown_v1` and render every line in this order:

```text
{company_name}（{symbol}）
相对历史增长压力：{中文标签}

Owner FCFF：{一位小数} 亿美元
（最近完整年度，截至 {period_end}）
Operating EV：{一位小数} 亿美元
（市值截至 {market_data_date}）
Owner FCFF Yield：{一位小数百分比}

**隐含 5Y Owner FCFF CAGR：**
**{一位小数百分比}**

历史增长对照
- 营收 CAGR：3Y {百分比}｜5Y {百分比}
- NOPAT CAGR：3Y {百分比}｜5Y {百分比}
- Owner FCFF CAGR：3Y {百分比}｜5Y {百分比}

标签参考：{中文历史指标名称}（{百分比}）
隐含增速较标签参考：{高或低} {百分点绝对值} 个百分点
估值尺子：5 年显性期｜10% 折现率｜0% 永续增长
结果状态：ready。
```

Translate pressure labels as `light=较轻`, `explainable=可解释`, `stretched=偏高`, and `high_pressure=高压力`. Never expose internal keys such as `light`, `fcff_5y`, or raw decimal ratios in the card.

The frozen ruler is five explicit years, a 10% discount rate, and 0% terminal growth.

Amounts and dates must retain the canonical artifact's units and as-of basis. Format USD amounts in hundred-million USD units and all ratios as percentages with one decimal place.

## Non-ready presentation

`partial` and `not_assessed` use the same ordered card with `未形成` placeholders and the actual result status. Rejected and failed states use a concise neutral card. Detailed reason codes stay in the private receipt for diagnosis; the public card states only that no valuation conclusion was formed. Missing or unsolved inputs must not be converted into a valuation conclusion.

## Output boundary

The executor returns one `valuation_scan_terminal_receipt_v2` object. Internal paths, raw source payloads, annual series, credentials, and runtime metadata are not part of the public presentation.

## Prohibitions

- No target price, fair value, or buy/sell conclusion.
- No second calculator.
- No direct service calls from this public contract.
- No SEC, transcript, or broader research expansion.
