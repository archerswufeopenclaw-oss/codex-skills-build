# Publication Boundary

This package contains public contracts, a terminal schema, and a provider-neutral launcher. It does not contain a data-acquisition implementation or a service connector. Before publication, confirm that the public contract portion contains no:

- credential values, local environment files, or authentication material;
- private filesystem paths, machine names, session identifiers, or internal prompts;
- external-service URLs, provider request templates, or adapter implementation;
- real market-data payloads, reports, logs, cached artifacts, or personal information;
- unpublished provider limits, account details, or operational configuration.

The launcher may read a user's local Codex configuration and inherit local environment variables, but neither the configuration nor its values are shipped with this package or printed by the launcher. Authentication and data acquisition remain the responsibility of a private runtime adapter.

`rebuild/` is an internal early-implementation/OpenClaw archive. Treat its dated fixtures and semantic decisions as historical material, not as current live data or a public execution contract.

## Review checklist

1. Search for credentials and environment files.
2. Search for absolute paths and machine-specific identifiers.
3. Confirm that the launcher only reads local configuration, starts the configured command, and validates the terminal receipt.
4. Validate all JSON files and Markdown links.
5. Keep `rebuild/` and any real research fixtures clearly separated from the public skill roots.
6. Compare the public text with the private source and confirm that only the intended contract semantics remain.
