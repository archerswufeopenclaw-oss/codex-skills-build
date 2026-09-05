---
name: markdown-docx
description: Convert a local .md or .markdown article to a styled Word .docx on Windows using Pandoc, the bundled Chinese article template, and Microsoft Word table auto-fit. Preserve the source wording.
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
- suppresses spaces that Pandoc would otherwise insert at soft line breaks between East Asian characters, while preserving English and mixed-script word boundaries, explicit hard line breaks, and code-block whitespace;
- runs from the Markdown file's directory so relative resources can resolve;
- opens the generated DOCX with local Microsoft Word and applies `wdAutoFitContent` followed by `wdAutoFitWindow` to every table;
- maps Markdown inline code (single-backtick text) through a small Pandoc filter to the template's `Inline Code Emphasis` style: 楷体, bold, 12 pt (小四);
- maps fenced code blocks labeled `text` to the template's `Text Code Block` style: 楷体, regular weight, 10 pt, while preserving literal line breaks and leading spaces;
- publishes the final output only after both Pandoc conversion and Word table adjustment succeed;
- stops on Pandoc warnings, including missing images, without publishing a new output;
- refuses silent overwrite and never changes the source Markdown.

## Validate

After conversion:

1. Open or render the DOCX with Microsoft Word.
2. Confirm Chinese text, headings, paragraphs, lists, tables, and links are basically correct.
3. Confirm tables fit the available page width after the content-then-window adjustment.
4. Confirm there is no obvious garbling, missing content, overlap, or page-boundary overflow.
5. When inline code is present, confirm it uses 楷体, bold, 12 pt (小四) while fenced blocks not labeled `text` retain their existing code formatting.
6. When a fenced code block is labeled `text`, confirm it uses 楷体, regular weight, 10 pt and preserves its literal indentation; fenced blocks with other language labels must retain the original code formatting.
7. Confirm East Asian prose does not gain spaces at source soft line breaks, while intentional spaces, English or mixed-script boundaries, explicit hard line breaks, and code indentation remain intact.

Word's natural pagination, tables crossing pages, a short final page, and formatting errors already present in the Markdown are not converter defects.

## Boundaries

- Do not recursively batch-convert directories.
- Do not repair or rewrite Markdown automatically.
- Do not globally strip whitespace; only Pandoc's East Asian soft-line-break handling is enabled.
- Do not post-process DOCX XML, optimize pagination beyond the required Word-native table auto-fit, reproduce structure atom by atom, or switch to another converter.
- Do not add a title, table of contents, numbering, or metadata that is absent from the Markdown.
