#!/usr/bin/env python3
"""Align standard Markdown pipe tables without changing cell content."""

from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path

from _markdown_blocks import protected_line_flags


def display_width(text: str) -> int:
    width = 0
    for char in text:
        if char == "\t":
            width += 4
        elif unicodedata.combining(char):
            continue
        elif unicodedata.east_asian_width(char) in {"W", "F"}:
            width += 2
        else:
            width += 1
    return width


def split_row(line: str) -> tuple[str, list[str]] | None:
    indent = line[: len(line) - len(line.lstrip(" "))]
    if len(indent) > 3:
        return None
    text = line[len(indent) :].strip()
    if "|" not in text:
        return None

    cells: list[str] = []
    current: list[str] = []
    code_ticks = 0
    trailing_separator = False
    index = 0
    while index < len(text):
        char = text[index]
        if char == "`":
            run = 1
            while index + run < len(text) and text[index + run] == "`":
                run += 1
            current.extend("`" * run)
            code_ticks = 0 if code_ticks == run else run if code_ticks == 0 else code_ticks
            index += run
            continue
        if char == "|" and code_ticks == 0:
            backslashes = 0
            cursor = len(current) - 1
            while cursor >= 0 and current[cursor] == "\\":
                backslashes += 1
                cursor -= 1
            if backslashes % 2 == 0:
                cells.append("".join(current).strip())
                current = []
                trailing_separator = index == len(text) - 1
                index += 1
                continue
        current.append(char)
        index += 1
    cells.append("".join(current).strip())

    if text.startswith("|"):
        cells = cells[1:]
    if trailing_separator:
        cells = cells[:-1]
    return (indent, cells) if len(cells) >= 2 else None


def separator_alignment(cell: str) -> str | None:
    compact = cell.replace(" ", "")
    left = compact.startswith(":")
    right = compact.endswith(":")
    core = compact[left : len(compact) - right if right else None]
    if len(core) < 3 or set(core) != {"-"}:
        return None
    if left and right:
        return "center"
    if right:
        return "right"
    return "left"


def pad(text: str, width: int, alignment: str) -> str:
    remaining = width - display_width(text)
    if alignment == "right":
        return " " * remaining + text
    if alignment == "center":
        left = remaining // 2
        return " " * left + text + " " * (remaining - left)
    return text + " " * remaining


def separator(width: int, alignment: str) -> str:
    if alignment == "center":
        width = max(width, 5)
        return ":" + "-" * (width - 2) + ":"
    if alignment == "right":
        width = max(width, 4)
        return "-" * (width - 1) + ":"
    width = max(width, 3)
    return "-" * width


def split_line_ending(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith(("\n", "\r")):
        return line[:-1], line[-1]
    return line, ""


def format_table(rows: list[tuple[str, list[str]]]) -> list[str] | None:
    column_count = len(rows[0][1])
    if any(len(cells) != column_count for _, cells in rows):
        return None
    alignments = [separator_alignment(cell) for cell in rows[1][1]]
    if any(value is None for value in alignments):
        return None

    widths = []
    for column in range(column_count):
        content_width = max(
            display_width(cells[column])
            for row_index, (_, cells) in enumerate(rows)
            if row_index != 1
        )
        minimum = 5 if alignments[column] == "center" else 4 if alignments[column] == "right" else 3
        widths.append(max(content_width, minimum))

    output = []
    indent = rows[0][0]
    for row_index, (_, cells) in enumerate(rows):
        if row_index == 1:
            rendered = [separator(widths[i], alignments[i]) for i in range(column_count)]
        else:
            rendered = [pad(cells[i], widths[i], alignments[i]) for i in range(column_count)]
        output.append(indent + "| " + " | ".join(rendered) + " |")
    return output


def format_markdown(text: str) -> tuple[str, int]:
    bom = "\ufeff" if text.startswith("\ufeff") else ""
    if bom:
        text = text[1:]
    records = [split_line_ending(line) for line in text.splitlines(keepends=True)]
    lines = [line for line, _ in records]
    protected = protected_line_flags(lines)
    output: list[str] = []
    table_count = 0
    index = 0

    while index < len(lines):
        if protected[index]:
            output.append(lines[index] + records[index][1])
            index += 1
            continue

        header = split_row(lines[index])
        next_row = (
            split_row(lines[index + 1])
            if index + 1 < len(lines) and not protected[index + 1]
            else None
        )
        if header and next_row and len(header[1]) == len(next_row[1]):
            if all(separator_alignment(cell) for cell in next_row[1]):
                rows = [header, next_row]
                cursor = index + 2
                while cursor < len(lines) and not protected[cursor]:
                    parsed = split_row(lines[cursor])
                    if not parsed or len(parsed[1]) != len(header[1]):
                        break
                    rows.append(parsed)
                    cursor += 1
                rendered = format_table(rows)
                if rendered:
                    output.extend(
                        line + records[index + offset][1]
                        for offset, line in enumerate(rendered)
                    )
                    table_count += 1
                    index = cursor
                    continue
        output.append(lines[index] + records[index][1])
        index += 1

    return bom + "".join(output), table_count


def format_table_block(text: str) -> str:
    """Format one complete table block or reject invalid input."""
    bom = "\ufeff" if text.startswith("\ufeff") else ""
    if bom:
        text = text[1:]
    records = [split_line_ending(line) for line in text.splitlines(keepends=True)]
    while records and not records[0][0].strip():
        records.pop(0)
    while records and not records[-1][0].strip():
        records.pop()
    lines = [line for line, _ in records]
    if len(lines) < 2 or any(not line.strip() for line in lines):
        raise ValueError("stdin must contain exactly one complete table block")

    rows: list[tuple[str, list[str]]] = []
    for line_number, line in enumerate(lines, start=1):
        parsed = split_row(line)
        if parsed is None:
            raise ValueError(f"invalid table row at stdin line {line_number}")
        rows.append(parsed)

    column_count = len(rows[0][1])
    if any(len(cells) != column_count for _, cells in rows):
        raise ValueError("table rows have different column counts")
    if any(separator_alignment(cell) is None for cell in rows[1][1]):
        raise ValueError("stdin line 2 is not a valid Markdown table delimiter")
    if any(indent != rows[0][0] for indent, _ in rows):
        raise ValueError("table rows use inconsistent indentation")

    rendered = format_table(rows)
    if rendered is None:
        raise ValueError("invalid Markdown table")
    result = "".join(
        line + records[index][1] for index, line in enumerate(rendered)
    )
    return bom + result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, help="Markdown file to inspect")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="Rewrite the file in place")
    mode.add_argument("--check", action="store_true", help="Exit 1 when alignment would change")
    mode.add_argument(
        "--stdin",
        action="store_true",
        help="Read and format exactly one table block from standard input",
    )
    args = parser.parse_args()

    if args.stdin:
        if args.path is not None:
            parser.error("path is not allowed with --stdin")
        try:
            formatted = format_table_block(sys.stdin.buffer.read().decode("utf-8"))
        except ValueError as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
        sys.stdout.buffer.write(formatted.encode("utf-8"))
        return 0

    if args.path is None:
        parser.error("path is required with --write or --check")
    with args.path.open("r", encoding="utf-8", newline="") as source:
        original = source.read()
    formatted, table_count = format_markdown(original)
    changed = formatted != original
    if args.write and changed:
        with args.path.open("w", encoding="utf-8", newline="") as destination:
            destination.write(formatted)
    print(f"tables={table_count} changed={str(changed).lower()}")
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
