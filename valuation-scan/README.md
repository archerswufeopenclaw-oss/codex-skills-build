# Valuation Scan: Public Contract

This directory contains a public, contract-only description of a fast valuation-pressure screening workflow.

It intentionally excludes executable data acquisition, service connectors, credentials, local runtime paths, internal orchestration, and private research artifacts.

## Included contracts

- `router/SKILL.md`: security-resolution and market-routing contract.
- `us/SKILL.md`: single-ticker US pressure-screen contract.
- `cn-a-ah/SKILL.md`: A-share and A/H pressure-screen contract.
- `schemas/valuation_scan_terminal_receipt_v2.schema.json`: public terminal-receipt shape.
- `SECURITY.md`: publication boundary and review checklist.

## Runtime boundary

The contracts require a private execution adapter to provide verified market and financial inputs. This public package does not prescribe how that adapter obtains data or authenticates to external services.

The workflow is a pressure screen. It is not a target-price model, full DCF, fair-value claim, or buy/sell recommendation.
