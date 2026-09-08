from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


SKILL = Path(__file__).parents[1] / "skills" / "markdown-docx"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def text(element: ET.Element) -> str:
    return "".join(node.text or "" for node in element.iter(W + "t"))


class AuthorNoteConversionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pandoc = shutil.which("pandoc")
        if not cls.pandoc:
            raise unittest.SkipTest("Pandoc is not installed")

    def convert(self, source: str) -> tuple[ET.Element, dict[str, ET.Element], ET.Element]:
        with tempfile.TemporaryDirectory() as folder:
            markdown = Path(folder) / "input.md"
            output = Path(folder) / "output.docx"
            markdown.write_text(source, encoding="utf-8")
            subprocess.run(
                [
                    self.pandoc, "--from=markdown+east_asian_line_breaks", "--to=docx",
                    "--fail-if-warnings", "--lua-filter", str(SKILL / "scripts/inline_code_style.lua"),
                    "--reference-doc", str(SKILL / "assets/reference-public.docx"),
                    "--output", str(output), str(markdown),
                ],
                check=True, capture_output=True,
            )
            with zipfile.ZipFile(output) as package:
                document = ET.fromstring(package.read("word/document.xml"))
                styles = ET.fromstring(package.read("word/styles.xml"))
                relationships = ET.fromstring(package.read("word/_rels/document.xml.rels"))
        return document, {s.get(W + "styleId"): s for s in styles.findall(W + "style")}, relationships

    def assert_left_style(self, style: ET.Element) -> None:
        self.assertEqual(style.find(W + "pPr/" + W + "jc").get(W + "val"), "left")
        indent = style.find(W + "pPr/" + W + "ind")
        self.assertEqual(indent.get(W + "firstLine"), "0")
        self.assertEqual(indent.get(W + "firstLineChars"), "0")

    def test_note_paragraphs_links_and_inline_code_share_red_text_style(self) -> None:
        document, styles, relationships = self.convert(
            '> <span class="author-note">🔴 作者说明（供作者阅读，可整段删除）</span>\n>\n'
            '> 解释[原始资料](https://example.com/evidence)与 `指标`。\n>\n'
            '> 后一段说明。\n\n普通正文。\n'
        )
        paragraphs = list(document.iter(W + "p"))
        self.assertEqual([text(p) for p in paragraphs], [
            "🔴 作者说明（供作者阅读，可整段删除）", "解释原始资料与 指标。", "后一段说明。", "普通正文。",
        ])
        for paragraph in paragraphs[:3]:
            self.assertEqual(paragraph.find(W + "pPr/" + W + "pStyle").get(W + "val"), "AuthorNote")
            for run in paragraph.iter(W + "r"):
                if text(run):
                    self.assertEqual(run.find(W + "rPr/" + W + "rStyle").get(W + "val"), "AuthorNoteText")
        self.assert_left_style(styles["AuthorNote"])
        for name in ("AuthorNote", "AuthorNoteText"):
            properties = styles[name].find(W + "rPr")
            self.assertEqual(properties.find(W + "color").get(W + "val"), "C00000")
            self.assertEqual(properties.find(W + "sz").get(W + "val"), "22")
            self.assertEqual(properties.find(W + "b").get(W + "val"), "0")
            self.assertEqual(properties.find(W + "rFonts").get(W + "eastAsia"), "宋体")
        self.assertTrue(any(r.get("Target") == "https://example.com/evidence" for r in relationships.findall(REL + "Relationship")))

    def test_document_metadata_has_left_alignment_and_preserves_hard_break(self) -> None:
        document, styles, _ = self.convert(
            '# 示例\n\n<span class="doc-meta">内部决策讨论稿\\\n政策核查截至某日</span>\n\n'
            '正文仍需两端对齐。\n'
        )
        paragraphs = list(document.iter(W + "p"))
        metadata = paragraphs[1]
        self.assertEqual(text(metadata), "内部决策讨论稿政策核查截至某日")
        self.assertEqual(len(list(metadata.iter(W + "br"))), 1)
        self.assertEqual(metadata.find(W + "pPr/" + W + "pStyle").get(W + "val"), "DocMeta")
        self.assert_left_style(styles["DocMeta"])
        self.assertEqual(styles["DocMetaText"].find(W + "rPr/" + W + "sz").get(W + "val"), "24")
        normal = next(s for s in styles.values() if s.find(W + "name").get(W + "val") == "Normal")
        self.assertEqual(normal.find(W + "pPr/" + W + "jc").get(W + "val"), "both")
        self.assertNotEqual(paragraphs[2].find(W + "pPr/" + W + "pStyle").get(W + "val"), "DocMeta")

    def test_plain_marker_supported_but_ordinary_quotes_and_code_are_unchanged(self) -> None:
        document, _, _ = self.convert(
            '> 🔴 作者说明（供作者阅读，可整段删除）\n>\n> 说明。\n\n'
            '> 普通引用也可以提到作者说明。\n\n'
            '> 🔴 作者说明（供作者阅读，可整段删除）：这不是约定的独立首行。\n\n'
            '普通 `行内代码`。\n\n```text\n> 🔴 作者说明（供作者阅读，可整段删除）\n```\n'
        )
        paragraphs = list(document.iter(W + "p"))
        styles = [p.find(W + "pPr/" + W + "pStyle").get(W + "val") for p in paragraphs]
        self.assertEqual(styles[:2], ["AuthorNote", "AuthorNote"])
        self.assertNotIn("AuthorNote", styles[2:])
        inline_styles = [r.get(W + "val") for r in paragraphs[4].iter(W + "rStyle")]
        self.assertIn("InlineCodeEmphasis", inline_styles)
        self.assertIn("TextCodeBlock", [r.get(W + "val") for r in paragraphs[5].iter(W + "rStyle")])


if __name__ == "__main__":
    unittest.main()
