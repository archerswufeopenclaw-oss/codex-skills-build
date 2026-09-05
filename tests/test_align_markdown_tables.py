from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "skills/markdown-article/scripts/align_markdown_tables.py"
SPEC = importlib.util.spec_from_file_location("align_markdown_tables", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.path.insert(0, str(SCRIPT.parent))
try:
    SPEC.loader.exec_module(MODULE)
finally:
    sys.path.pop(0)


class AlignMarkdownTablesTests(unittest.TestCase):
    TABLE = "| a | b |\n| --- | --- |\n| x | y |\n"
    ALIGNED = "| a   | b   |\n| --- | --- |\n| x   | y   |\n"

    def test_formats_plain_table_and_is_idempotent(self) -> None:
        self.assertEqual(MODULE.format_table_block(self.TABLE), self.ALIGNED)
        self.assertEqual(MODULE.format_markdown(self.ALIGNED), (self.ALIGNED, 1))

    def test_preserves_nonclosing_fence_and_resumes_after_valid_close(self) -> None:
        for marker in ["```", "~~~~"]:
            with self.subTest(marker=marker):
                literal = f"{marker}md\n{marker}not-a-close\n" + self.TABLE + marker + "\n"
                source = literal + "\n" + self.TABLE
                expected = literal + "\n" + self.ALIGNED
                self.assertEqual(MODULE.format_markdown(source), (expected, 1))

    def test_preserves_shorter_and_other_character_fences(self) -> None:
        literal = "````md\n```\n~~~\n" + self.TABLE + "````\n"
        self.assertEqual(MODULE.format_markdown(literal), (literal, 0))

    def test_quote_marker_inside_fence_is_literal_content(self) -> None:
        literal = "```md\n> ```\n" + self.TABLE + "```\n"
        self.assertEqual(MODULE.format_markdown(literal), (literal, 0))

    def test_preserves_list_code_and_literal_html(self) -> None:
        indented = "".join("  " + line for line in self.TABLE.splitlines(keepends=True))
        for literal in ["- ```md\n" + indented + "  ```\n", "<pre>\n" + self.TABLE + "</pre>\n"]:
            with self.subTest(literal=literal):
                source = literal + "\n" + self.TABLE
                expected = literal + "\n" + self.ALIGNED
                self.assertEqual(MODULE.format_markdown(source), (expected, 1))

    def test_preserves_continuation_list_fences_and_resumes_after_close(self) -> None:
        for item, indent in [("- item", "  "), ("1. item", "   "), ("- outer\n  - item", "    ")]:
            with self.subTest(item=item):
                table = "".join(indent + line for line in self.TABLE.splitlines(keepends=True))
                literal = f"{item}\n\n{indent}  ```md\n{table}{indent}  ```\n"
                self.assertEqual(MODULE.format_markdown(literal), (literal, 0))
                source = literal + "\n" + self.TABLE
                expected = literal + "\n" + self.ALIGNED
                self.assertEqual(MODULE.format_markdown(source), (expected, 1))
                self.assertEqual(MODULE.format_markdown(expected), (expected, 1))

    def test_indented_fence_without_list_context_does_not_hide_tables(self) -> None:
        for prefix in [
            "",
            "- item\n\noutside\n\n",
            "- item\ncontinued text\n\noutside\n\n",
            "- item\ncontinued text\n# Outside\n\n",
            "- - -\n\n",
        ]:
            with self.subTest(prefix=prefix):
                source = prefix + "    ```md\n\n" + self.TABLE + "\n    ```\n"
                expected = prefix + "    ```md\n\n" + self.ALIGNED + "\n    ```\n"
                self.assertEqual(MODULE.format_markdown(source), (expected, 1))

    def test_preserves_lazy_list_paragraph_before_fence(self) -> None:
        table = "".join("  " + line for line in self.TABLE.splitlines(keepends=True))
        for continuation in ["continued text", "===", "<span>continued</span>"]:
            with self.subTest(continuation=continuation):
                literal = f"- item\n{continuation}\n\n    ```md\n{table}    ```\n"
                self.assertEqual(MODULE.format_markdown(literal), (literal, 0))
                source = literal + "\n" + self.TABLE
                expected = literal + "\n" + self.ALIGNED
                self.assertEqual(MODULE.format_markdown(source), (expected, 1))
                self.assertEqual(MODULE.format_markdown(expected), (expected, 1))

    def test_table_collection_stops_at_literal_block(self) -> None:
        literal = "<pre> | keep\n# literal\n</pre>\n"
        self.assertEqual(MODULE.format_markdown(self.TABLE + literal), (self.ALIGNED + literal, 1))

    def test_preserves_escaped_trailing_pipe(self) -> None:
        for row in [r"x | y\|", r"| x | y\|", r"| x | y\| |"]:
            with self.subTest(row=row):
                source = "| a | b |\n| --- | --- |\n" + row + "\n"
                expected = "| a   | b   |\n| --- | --- |\n| x   | y\\| |\n"
                self.assertEqual(MODULE.format_table_block(source), expected)
                self.assertEqual(MODULE.format_table_block(expected), expected)

    def test_even_backslashes_before_pipe_still_delimit(self) -> None:
        self.assertEqual(MODULE.split_row(r"| x | y\\|"), ("", ["x", "y\\\\"]))

    def test_preserves_bom_crlf_and_missing_final_newline(self) -> None:
        source = "\ufeff" + self.TABLE.replace("\n", "\r\n").rstrip("\r\n")
        expected = "\ufeff" + self.ALIGNED.replace("\n", "\r\n").rstrip("\r\n")
        self.assertEqual(MODULE.format_markdown(source), (expected, 1))

    def test_cli_write_preserves_literal_bytes(self) -> None:
        literal = b"```md\r\n```not-a-close\r\n" + self.TABLE.replace("\n", "\r\n").encode() + b"```\r\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "article.md"
            path.write_bytes(literal)
            for mode in ["--write", "--check"]:
                result = subprocess.run(
                    [sys.executable, "-X", "utf8", "-B", str(SCRIPT), mode, str(path)],
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr.decode())
                self.assertEqual(path.read_bytes(), literal)


if __name__ == "__main__":
    unittest.main()
