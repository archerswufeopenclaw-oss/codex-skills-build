# Publication Boundary

This package is documentation and schema only. Before publication, confirm that it contains no:

- credential values, local environment files, or authentication material;
- private filesystem paths, machine names, session identifiers, or internal prompts;
- external-service URLs, request templates, transport details, or adapter code;
- real market-data payloads, reports, logs, cached artifacts, or personal information;
- unpublished provider limits, account details, or operational configuration.

The public contract describes inputs, outputs, calculation ownership, and user-facing boundaries. Authentication and data acquisition belong to a private runtime adapter.

## Review checklist

1. Search for credentials and environment files.
2. Search for absolute paths and machine-specific identifiers.
3. Search for external-service names, URLs, request parameters, and transport details.
4. Validate all JSON files and Markdown links.
5. Compare the public text with the private source and confirm that only the intended contract semantics remain.
