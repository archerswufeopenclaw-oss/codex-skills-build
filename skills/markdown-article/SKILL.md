---
name: markdown-article
description: Research and revise local Markdown articles by resolving author directives written as Markdown bold spans. Use when the user invokes markdown-article, @markdown-article, or $markdown-article; asks to start or continue revising an investment, tax, legal, business, or other research article with **...** directives; or requests L0 editing, /review independent review, or /roundtable red-blue verification in a Markdown article.
---

# Markdown Article

Edit the author-selected Markdown article in place. Preserve its voice, argument, structure, and existing citation style unless a directive asks otherwise.

## Author directives

- Treat every `**...**` span outside inline or fenced code as an author directive. It may appear inline or as its own paragraph.
- Never add Markdown bold syntax to the article; it is reserved for the author-agent channel.
- After completing a directive, integrate the result into the prose and remove the whole bold span.
- Let only the main agent modify the article and its companion files.

## Verification levels

- L0 is the default. Research, edit, or format directly without a subagent.
- L1 applies when `/review` occurs anywhere inside a directive. Launch one temporary independent subagent to review the claim, seek relevant evidence, and return findings. Give it the directive and only the article context needed for an independent assessment. Decide in the main agent what to write.
- L2 applies when `/roundtable` occurs anywhere inside a directive. Launch two independent subagents in parallel: red seeks contrary evidence, failure modes, and reasons to reject; blue seeks supporting evidence, valid conditions, and ways to refine the claim. Ask follow-ups only when useful, then adjudicate in the main agent.

Subagents research and advise; they do not edit files.
The main agent may choose each L1 or L2 subagent's model and thinking or reasoning effort based on the task, unless the author specifies them.

## Companion workspace

For `article.md`, create this sibling structure when missing:

```text
article.research/
├── materials/
├── notes.md
└── discussion.md
```

- Put only materials actually used to form the article in `materials/`.
- Keep `notes.md` minimally traceable: record enough source information to relocate important evidence and identify the claim or section it supports. Skip formatting-only edits, agent or task identifiers, execution logs, and failed attempts.
- Append each L2 exercise to `discussion.md` with the proposition, red view, blue view, main-agent decision, and resulting article change. Keep it concise.
- On later passes, reuse existing companion materials and research only what the current directives require.

## Research and writing

- Use the available research tools freely. Prefer filings, company disclosures, regulators, exchanges, and other primary sources for important factual or contested claims.
- Reuse existing materials first. When a directive needs additional sources, locate only the relevant primary materials and search or open the selected files directly. Treat the resulting material set as a convenience, not an exclusive corpus or research boundary.
- Keep sourcing proportionate rather than exhaustive. Distinguish fact, inference, and author opinion when the distinction matters.
- Make the smallest coherent edit that answers the directive, while allowing broader revision when evidence changes the argument.
- Preserve valid Markdown.

### Heading spacing

- Before returning control after editing an article, run `python -X utf8 -B scripts/normalize_heading_spacing.py --write "C:\path\article.md"`, resolving the script relative to this `SKILL.md`.
- The script inserts exactly one blank line before and after each ATX heading outside fenced code, except at the start or end of the file. This is a structural formatting cleanup so downstream Markdown converters can recognize headings reliably.
- Do not record this formatting-only cleanup in `notes.md`. The command is idempotent and must not turn malformed heading-like text into a heading.

### Minimal receipts

- For L1 and L2, ask each subagent to return a compact evidence receipt: judgment; key evidence; source and location; counterevidence or limitation; remaining unknowns. The main agent may use the same format for substantial L0 research. Keep only adopted evidence in `notes.md`.
- For a material calculation used in the article, record in `notes.md`: target; formula; inputs and sources; result with period, unit, and currency; limitations. Use a deterministic calculation tool when practical.
- These are plain Markdown notes, not schemas or gates. Do not create IDs, hashes, statuses, databases, or additional companion files for them.

### Tables

- Use tables for short, comparable cells. Prefer a two-column fact card for long text. In tables with three or more columns, avoid adjacent long-text columns and keep at most one longer explanation column, preferably last.
- Put units, currency, and periods in headers. Keep conclusions, caveats, and interpretation outside the table. Wide numeric tables are acceptable when they remain easy to scan.
- Decide alignment by meaning: dimension and text columns are usually left-aligned; measures are usually right-aligned. Do not infer alignment from characters alone.
- Before inserting a new or changed pipe table, pass only its complete table block through `scripts/align_markdown_tables.py --stdin`, resolved relative to this `SKILL.md`, and insert the returned table. The script handles display width and spaces; do not hand-pad cells or add arbitrary extra width.
- Use `--write` only when the user explicitly requests repair of existing tables, and use `--check` for validation. Do not reformat untouched tables in the normal workflow.

Exact source-pipe alignment is portable only in a monospaced view. Do not use special spaces or pixel-tune for one proportional font.

Before returning control, delete temporary files and directories created during the run; keep only the article, its companion workspace, and user-provided source files. Do not retain rollback copies or run history. Then reread the changed passages and report material research judgments to the author.
