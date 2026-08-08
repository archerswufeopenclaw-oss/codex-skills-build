---
name: valuation-scan-public-router
description: Public contract for routing a valuation-scan or 估值扫描 request to a private, verified execution adapter.
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
4. Classify the result as one of `US`, `CN_A`, `CN_AH`, or `HK_ONLY`.
5. Continue silently for one verified candidate.
6. Ask one concise disambiguation question when multiple verified issuers or share classes remain.
7. Return `security_resolution_failed` when no candidate can be verified.

The canonical identity payload contains only the request, company name, market class, resolved symbol, and verified share-class symbols. It must not contain credentials, raw service requests, local paths, or private runtime metadata.

## Market routing

- `US`: route to the private US execution adapter.
- `CN_A`: route to the private A-share execution adapter.
- `CN_AH`: route to the private A/H execution adapter as one issuer with two alternative price views.
- `HK_ONLY`: return the current capability boundary unless a private executor explicitly supports the required financial inputs.

The router must not treat A and H listings as two separate companies or add their alternative whole-company values together.

## Terminal result

The private executor returns exactly one object matching the public receipt schema:

- `schema_version = valuation_scan_terminal_receipt_v2`
- `terminal = true`
- a non-empty `execution_status`
- a non-empty `valuation_status`
- a canonical `symbol`
- `presentation.format = plain_text_v1`
- `presentation.locale = zh-CN`
- non-empty `presentation.text` with at most 3500 Unicode characters

After validation, only `presentation.text` crosses the user-facing boundary. The raw receipt, internal paths, timing, source payloads, and annual series remain private.

## Non-negotiable boundaries

- Do not calculate locally in the router.
- Do not reconstruct a result when the receipt is malformed.
- Do not expose credentials, service connection details, internal prompts, or private files.
- Do not generate target prices, fair values, or buy/sell recommendations.
- Do not start a broader research workflow as part of this scan.
