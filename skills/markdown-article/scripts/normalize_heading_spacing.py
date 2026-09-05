#!/usr/bin/env python3
"""Normalize blank lines around ATX headings outside fenced code blocks."""

from __future__ import annotations

import argparse
import codecs
import re
import sys
from pathlib import Path

from _markdown_blocks import protected_line_flags


HEADING_RE = re.compile(r" {0,3}#{1,6}(?:[ \t]+|$)")


def _heading_flags(lines: list[str]) -> list[bool]:
    return [
        not protected and bool(HEADING_RE.match(line))
        for line, protected in zip(lines, protected_line_flags(lines))
    ]


def _split_line_ending(line: str) -> tuple[str, str]:
    for ending in ("\r\n", "\n", "\r"):
        if line.endswith(ending):
            return line[: -len(ending)], ending
    return line, ""


def normalize_heading_spacing(text: str) -> tuple[str, int]:
    """Return normalized text and the number of recognized headings."""
    has_bom = text.startswith(codecs.BOM_UTF8.decode("utf-8"))
    body = text[1:] if has_bom else text
    raw_lines = body.splitlines(keepends=True)
    lines = [_split_line_ending(line)[0] for line in raw_lines]
    headings = _heading_flags(lines)
    preferred_newline = next(
        (ending for line in raw_lines if (ending := _split_line_ending(line)[1])),
        "\n",
    )

    output: list[str] = []
    index = 0
    while index < len(raw_lines):
        if not headings[index]:
            output.append(raw_lines[index])
            index += 1
            continue

        removed_endings: list[str] = []
        while output and not _split_line_ending(output[-1])[0].strip():
            _, ending = _split_line_ending(output.pop())
            if ending:
                removed_endings.append(ending)
        if output:
            _, prior_ending = _split_line_ending(output[-1])
            _, heading_ending = _split_line_ending(raw_lines[index])
            output.append(
                removed_endings[0] if removed_endings else prior_ending or heading_ending or preferred_newline
            )
        output.append(raw_lines[index])

        index += 1
        skipped_endings: list[str] = []
        while index < len(raw_lines) and not lines[index].strip():
            _, ending = _split_line_ending(raw_lines[index])
            if ending:
                skipped_endings.append(ending)
            index += 1
        if index < len(raw_lines):
            _, heading_ending = _split_line_ending(raw_lines[index - len(skipped_endings) - 1])
            output.append(
                skipped_endings[0] if skipped_endings else heading_ending or preferred_newline
            )

    normalized = "".join(output)
    if has_bom:
        normalized = codecs.BOM_UTF8.decode("utf-8") + normalized
    return normalized, sum(headings)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="Update the file in place.")
    mode.add_argument("--check", action="store_true", help="Exit 1 if normalization is needed.")
    parser.add_argument("path", type=Path, help="Markdown file to inspect.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    raw = args.path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        print(f"error: {args.path} is not valid UTF-8: {exc}", file=sys.stderr)
        return 2

    if raw.startswith(codecs.BOM_UTF8):
        text = codecs.BOM_UTF8.decode("utf-8") + text

    normalized, heading_count = normalize_heading_spacing(text)
    normalized_bytes = normalized.encode("utf-8")
    changed = normalized_bytes != raw

    if args.write and changed:
        args.path.write_bytes(normalized_bytes)

    print(f"headings={heading_count} changed={str(changed).lower()}")
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
