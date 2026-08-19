from __future__ import annotations

import codecs
import importlib.util
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
SPEC.loader.exec_module(MODULE)


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
