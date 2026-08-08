---
name: valuation-scan-cn-a-ah
description: Public contract for a fast A-share or A/H-listed non-financial valuation-pressure screen.
---

# A-share and A/H Valuation Scan: Public Contract

## Purpose

Produce a fast CNY pressure-screen card for one verified A-share or A/H-listed non-financial issuer.

This is a screening contract, not a filing-reconciliation workflow, target-price model, full DCF, or buy/sell recommendation.

## Identity boundary

The execution adapter accepts an explicit six-digit A-share symbol or a verified company-name resolution. A pure Hong Kong listing is a capability boundary unless a private executor supplies the required consolidated financial inputs.

Banks, insurers, and securities firms are outside this industrial-company cash-flow bridge unless a separate contract is provided.

## Calculation contract

For an annual row:

```text
Owner FCFF proxy = operating cash flow - long-term construction spending
```

For a cumulative interim row, use a period bridge:

```text
TTM component = latest YTD + prior FY - prior same YTD
TTM FCFF = TTM operating cash flow - TTM long-term construction spending
```

Do not annualize a single quarterly or half-year cumulative value. If the bridge is unavailable, use the latest complete fiscal year and label the fallback.

The lightweight Operating EV combines total equity market value with debt-like liabilities, leases, minority interests, preferred/perpetual instruments, and cash-like deductions. Missing required inputs remain `partial`; optional zero defaults must remain visible in provenance.

Historical pressure compares the bounded implied five-year Owner FCFF CAGR with the lowest valid Revenue, NOPAT, and Owner FCFF three-year/five-year CAGR reference. Invalid or non-positive endpoints are excluded rather than changed to zero.

The frozen ruler is five explicit years, a 10% discount rate, and 0% terminal growth. A gap of at most 2% is `light`; above 2% through 8% is `explainable`; above 8% through 15% is `stretched`; above 15% is `high_pressure`.

## A/H price views

For an A/H issuer:

- use separately verified issued A- and H-share counts;
- use one shared consolidated Owner FCFF and historical reference;
- render A-price and H-price Operating EV, Yield, implied five-year CAGR, gap, and pressure separately;
- treat the two values as alternative whole-company price views, never as additive market values;
- do not use book-value share-capital fields as a share count.

The card may retain a combined market-value calculation for internal audit compatibility, but it must not be the human-facing headline.

## Output boundary

Return one `valuation_scan_terminal_receipt_v2` object with a deterministic Chinese `presentation`. Keep source names, raw rows, credentials, local paths, and adapter details outside the public presentation.

## Prohibitions

- No target price, fair value, or investment recommendation.
- No invented share count, FX rate, or historical CAGR.
- No silent fallback that hides a missing or partial input.
- No filing, transcript, or broader research workflow.
