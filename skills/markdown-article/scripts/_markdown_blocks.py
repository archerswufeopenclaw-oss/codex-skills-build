"""Protect fenced code and literal HTML regions during line-based formatting.

This is deliberately a small protection scanner, not a full Markdown parser.
It recognizes quote/list containers and leaves their literal contents untouched.
"""

from __future__ import annotations

import re


FENCE_RE = re.compile(r" {0,3}(`{3,}|~{3,})(.*)$")
QUOTE_RE = re.compile(r" {0,3}>[ \t]?")
LIST_RE = re.compile(r" {0,3}(?:[-+*]|[0-9]{1,9}[.)])[ \t]{1,4}")
THEMATIC_BREAK_RE = re.compile(r" {0,3}(?:(?:\* *){3,}|(?:- *){3,}|(?:_ *){3,})$")
HTML_RE = re.compile(r" {0,3}<(pre|code|script|style|textarea)(?=[\s>])", re.I)
HEADING_RE = re.compile(r" {0,3}#{1,6}(?:[ \t]+|$)")


def _is_paragraph_text(view: str) -> bool:
    """Reject clear block boundaries; leave unfamiliar text conservative."""
    fence = FENCE_RE.fullmatch(view)
    return bool(view.strip()) and not (
        HEADING_RE.match(view)
        or THEMATIC_BREAK_RE.fullmatch(view)
        or QUOTE_RE.match(view)
        or LIST_RE.match(view)
        or HTML_RE.match(view)
        or re.match(r" {0,3}<!--", view)
        or (fence and not (fence.group(1)[0] == "`" and "`" in fence.group(2)))
    )


def protected_line_flags(lines: list[str]) -> list[bool]:
    """Identify literal lines, including their opening and closing markers."""
    flags: list[bool] = []
    fence: tuple[str, int] | None = None
    html_end: re.Pattern[str] | None = None
    quote_depth = 0
    list_indent = 0
    list_context: list[tuple[int, int]] = []
    paragraph_open = False

    for line in lines:
        view = line.expandtabs(4)
        depth = 0
        active = bool(fence or html_end)
        while (not active or depth < quote_depth) and (match := QUOTE_RE.match(view)):
            depth += 1
            view = view[match.end():]

        if fence or html_end:
            paragraph_open = False
            indent = len(view) - len(view.lstrip(" "))
            # Leaving a container also ends its otherwise unclosed literal block.
            if depth < quote_depth or (view.strip() and indent < list_indent):
                fence = None
                html_end = None
            else:
                flags.append(True)
                content = view[list_indent:]
                if fence:
                    match = FENCE_RE.fullmatch(content)
                    if (
                        match
                        and match.group(1)[0] == fence[0]
                        and len(match.group(1)) >= fence[1]
                        and not match.group(2).strip()
                    ):
                        fence = None
                elif html_end and html_end.search(content):
                    html_end = None
                continue

        # A fence may start on a later line of an existing list item. Keep its
        # content indent across blank lines and lazy paragraph continuations.
        indent = len(view) - len(view.lstrip(" "))
        if (
            list_context
            and depth == list_context[-1][0]
            and indent < list_context[-1][1]
            and paragraph_open
            and _is_paragraph_text(view)
        ):
            # An unindented continuation belongs to the open list paragraph;
            # do not remove a content indent that this line does not have.
            flags.append(False)
            continue
        while list_context and (
            depth != list_context[-1][0]
            or (view.strip() and indent < list_context[-1][1])
        ):
            list_context.pop()
        list_indent = list_context[-1][1] if list_context else 0
        view = view[list_indent:]
        while not THEMATIC_BREAK_RE.fullmatch(view) and (match := LIST_RE.match(view)):
            list_indent += match.end()
            list_context.append((depth, list_indent))
            view = view[match.end():]
        quote_depth = depth
        paragraph_open = _is_paragraph_text(view)

        match = FENCE_RE.fullmatch(view)
        if match and not (match.group(1)[0] == "`" and "`" in match.group(2)):
            fence = (match.group(1)[0], len(match.group(1)))
            flags.append(True)
            continue

        match = HTML_RE.match(view)
        if match:
            html_end = re.compile(r"</" + match.group(1) + r"\s*>", re.I)
        elif re.match(r" {0,3}<!--", view):
            html_end = re.compile(r"-->")
        if html_end:
            flags.append(True)
            if html_end.search(view):
                html_end = None
            continue

        flags.append(False)

    return flags
