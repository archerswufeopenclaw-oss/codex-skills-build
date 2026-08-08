---
name: valuation-scan-us
description: Public contract for a single-ticker US valuation-pressure screen.
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

## Ready presentation

For a ready result, the human card may show:

- company identity and relative historical pressure;
- Owner FCFF with basis and period;
- Operating EV with its market-data date;
- Owner FCFF Yield;
- implied five-year Owner FCFF CAGR;
- Revenue, NOPAT, and Owner FCFF three-year/five-year comparisons;
- the selected historical reference, gap, and valuation ruler.

The frozen ruler is five explicit years, a 10% discount rate, and 0% terminal growth.

Amounts and dates must retain the canonical artifact's units and as-of basis.

## Non-ready presentation

`partial`, `not_assessed`, rejected, and failed states must remain explicit and include a concise human-readable reason. Missing or unsolved inputs must not be converted into a valuation conclusion.

## Output boundary

The executor returns one `valuation_scan_terminal_receipt_v2` object. Internal paths, raw source payloads, annual series, credentials, and runtime metadata are not part of the public presentation.

## Prohibitions

- No target price, fair value, or buy/sell conclusion.
- No second calculator.
- No direct service calls from this public contract.
- No SEC, transcript, or broader research expansion.
