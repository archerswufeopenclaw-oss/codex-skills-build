from __future__ import annotations

import codecs
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).parents[1]
    / "skills"
    / "markdown-article"
    / "scripts"
    / "normalize_heading_spacing.py"
)
SPEC = importlib.util.spec_from_file_location("normalize_heading_spacing", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.path.insert(0, str(SCRIPT.parent))
try:
    SPEC.loader.exec_module(MODULE)
finally:
    sys.path.pop(0)


class NormalizeHeadingSpacingTests(unittest.TestCase):
    def test_adds_one_blank_line_around_headings(self) -> None:
        source = "intro\n\n\n# Heading\ntext\n## Next\n\nbody\n"
        expected = "intro\n\n# Heading\n\ntext\n\n## Next\n\nbody\n"
        actual, count = MODULE.normalize_heading_spacing(source)
        self.assertEqual(actual, expected)
        self.assertEqual(count, 2)

    def test_preserves_boundaries_and_is_idempotent(self) -> None:
        source = "# First\n\ntext\n\n# Last\n"
        once, count = MODULE.normalize_heading_spacing(source)
        twice, _ = MODULE.normalize_heading_spacing(once)
        self.assertEqual(once, source)
        self.assertEqual(twice, source)
        self.assertEqual(count, 2)

    def test_ignores_fenced_and_malformed_heading_like_text(self) -> None:
        source = (
            "before\n```md\n# code heading\n```not-a-close\n"
            "## still code\n```\n#not-a-heading\nafter\n"
        )
        actual, count = MODULE.normalize_heading_spacing(source)
        self.assertEqual(actual, source)
        self.assertEqual(count, 0)

    def test_preserves_utf8_bom_crlf_and_missing_final_newline(self) -> None:
        source = "前文\r\n# 标题\r\n后文"
        text = codecs.BOM_UTF8.decode("utf-8") + source
        expected = codecs.BOM_UTF8.decode("utf-8") + "前文\r\n\r\n# 标题\r\n\r\n后文"
        actual, count = MODULE.normalize_heading_spacing(text)
        self.assertEqual(actual, expected)
        self.assertEqual(count, 1)

    def test_preserves_list_fences_and_resumes_after_closing(self) -> None:
        for opener, indent in [("- ```", "  "), ("1. ~~~", "   ")]:
            with self.subTest(opener=opener):
                marker = opener.split()[-1]
                literal = f"{opener}\n{indent}# keep\n{indent}literal\n{indent}{marker}\n"
                source = literal + "# Real\nbody\n"
                expected = literal + "\n# Real\n\nbody\n"
                self.assertEqual(MODULE.normalize_heading_spacing(source), (expected, 1))
                self.assertEqual(MODULE.normalize_heading_spacing(expected), (expected, 1))

    def test_unclosed_list_fence_ends_at_container_boundary(self) -> None:
        literal = "- ```\n  # keep\n  literal\n"
        source = literal + "\n# Real\nbody\n"
        expected = literal + "\n# Real\n\nbody\n"
        self.assertEqual(MODULE.normalize_heading_spacing(source), (expected, 1))

    def test_preserves_continuation_list_fences_and_resumes_after_close(self) -> None:
        for item, indent in [("- item", "  "), ("1. item", "   ")]:
            with self.subTest(item=item):
                literal = f"{item}\n\n{indent}  ```md\n{indent}# keep\n{indent}literal\n{indent}  ```\n"
                source = literal + "# Real\nbody\n"
                expected = literal + "\n# Real\n\nbody\n"
                self.assertEqual(MODULE.normalize_heading_spacing(source), (expected, 1))
                self.assertEqual(MODULE.normalize_heading_spacing(expected), (expected, 1))

    def test_indented_fence_without_list_context_does_not_hide_heading(self) -> None:
        source = "    ```md\n\n# Real\nbody\n\n    ```\n"
        expected = "    ```md\n\n# Real\n\nbody\n\n    ```\n"
        self.assertEqual(MODULE.normalize_heading_spacing(source), (expected, 1))

    def test_preserves_lazy_list_paragraph_before_fence(self) -> None:
        literal = "- item\ncontinued text\n\n    ```md\n  # keep\n  literal\n    ```\n"
        source = literal + "# Real\nbody\n"
        expected = literal + "\n# Real\n\nbody\n"
        self.assertEqual(MODULE.normalize_heading_spacing(source), (expected, 1))
        self.assertEqual(MODULE.normalize_heading_spacing(expected), (expected, 1))

    def test_heading_and_separate_paragraph_end_lazy_list_context(self) -> None:
        for boundary, expected_boundary, boundary_count in [
            ("# Outside\nbody\n", "\n# Outside\n\nbody\n", 1),
            ("\noutside\n", "\noutside\n", 0),
        ]:
            with self.subTest(boundary=boundary):
                prefix = "- item\ncontinued text\n"
                source = prefix + boundary + "\n    ```md\n\n# Real\nbody\n\n    ```\n"
                expected = prefix + expected_boundary + "\n    ```md\n\n# Real\n\nbody\n\n    ```\n"
                self.assertEqual(
                    MODULE.normalize_heading_spacing(source), (expected, 1 + boundary_count)
                )

    def test_preserves_literal_html_blocks(self) -> None:
        for tag in ["pre", "code", "script", "style", "textarea", "PRE"]:
            with self.subTest(tag=tag):
                literal = f'<{tag} class="sample">\n# keep\n\nliteral\n</{tag}>\n'
                source = literal + "# Real\nbody\n"
                expected = literal + "\n# Real\n\nbody\n"
                self.assertEqual(MODULE.normalize_heading_spacing(source), (expected, 1))

    def test_preserves_unclosed_html_and_html_comments(self) -> None:
        for source in ["<pre>\n# keep\nliteral\n", "<!--\n# keep\nliteral\n-->\n"]:
            with self.subTest(source=source):
                self.assertEqual(MODULE.normalize_heading_spacing(source), (source, 0))

    def test_does_not_treat_invalid_backtick_info_as_a_fence(self) -> None:
        source = "```invalid`info\n# Real\nbody\n"
        expected = "```invalid`info\n\n# Real\n\nbody\n"
        self.assertEqual(MODULE.normalize_heading_spacing(source), (expected, 1))

    def test_preserves_existing_mixed_line_endings(self) -> None:
        source = "first\r\n# Heading\nlast\r\n"
        expected = "first\r\n\r\n# Heading\n\nlast\r\n"
        actual, count = MODULE.normalize_heading_spacing(source)
        self.assertEqual(actual, expected)
        self.assertEqual(count, 1)

    def test_cli_write_then_check(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "article.md"
            path.write_text("text\n# Title\nbody\n", encoding="utf-8")
            self.assertEqual(MODULE.main(["--write", str(path)]), 0)
            self.assertEqual(MODULE.main(["--check", str(path)]), 0)


if __name__ == "__main__":
    unittest.main()
