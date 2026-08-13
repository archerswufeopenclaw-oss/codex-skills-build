---
name: markdown-docx
description: Convert a local Markdown article into a styled Microsoft Word DOCX with Pandoc, a bundled Chinese research-article reference document, and Word-native two-stage table auto-fit. Use when Codex is asked to turn a .md or .markdown file into .docx, especially for Chinese investment, tax, legal, or long-form research articles with headings, lists, links, block quotes, footnotes, or pipe tables.
---

# Markdown to DOCX

Convert one explicitly named Markdown file at a time. Preserve the source file and its wording.

## Convert

Run the bundled converter:

```powershell
python -X utf8 -B scripts/convert.py "C:\path\article.md"
```

By default, write `article.docx` beside `article.md`. Use `--output` for another destination. Add `--overwrite` only when replacing an existing DOCX is intended.

The converter:

- uses Pandoc and the sanitized public template `assets/reference-public.docx`;
- runs from the Markdown file's directory so relative resources can resolve;
- opens the generated DOCX with local Microsoft Word and applies `wdAutoFitContent` followed by `wdAutoFitWindow` to every table;
- publishes the final output only after both Pandoc conversion and Word table adjustment succeed;
- refuses silent overwrite and never changes the source Markdown.

## Validate

After conversion:

1. Open or render the DOCX with Microsoft Word.
2. Confirm Chinese text, headings, paragraphs, lists, tables, and links are basically correct.
3. Confirm tables fit the available page width after the content-then-window adjustment.
4. Confirm there is no obvious garbling, missing content, overlap, or page-boundary overflow.

Word's natural pagination, tables crossing pages, a short final page, and formatting errors already present in the Markdown are not converter defects.

## Boundaries

- Do not recursively batch-convert directories.
- Do not repair or rewrite Markdown automatically.
- Do not post-process DOCX XML, optimize pagination beyond the required Word-native table auto-fit, reproduce structure atom by atom, or switch to another converter.
- Do not add a title, table of contents, numbering, or metadata that is absent from the Markdown.
