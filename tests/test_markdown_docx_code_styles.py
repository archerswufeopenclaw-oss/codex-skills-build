from __future__ import annotations

import importlib.util
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


REPO = Path(__file__).parents[1]
SKILL = REPO / "skills" / "markdown-docx"
REFERENCE = SKILL / "assets" / "reference-public.docx"
FILTER = SKILL / "scripts" / "inline_code_style.lua"
CONVERTER_PATH = SKILL / "scripts" / "convert.py"
CONVERTER_SPEC = importlib.util.spec_from_file_location(
    "markdown_docx_convert", CONVERTER_PATH
)
assert CONVERTER_SPEC and CONVERTER_SPEC.loader
CONVERTER = importlib.util.module_from_spec(CONVERTER_SPEC)
CONVERTER_SPEC.loader.exec_module(CONVERTER)
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def qn(local: str) -> str:
    return f"{{{W}}}{local}"


def paragraph_text(paragraph: ET.Element) -> str:
    parts: list[str] = []
    for node in paragraph.iter():
        if node.tag == qn("t"):
            parts.append(node.text or "")
        elif node.tag == qn("br"):
            parts.append("\n")
    return "".join(parts)


def paragraph_style(paragraph: ET.Element) -> str | None:
    node = paragraph.find(f"./{qn('pPr')}/{qn('pStyle')}")
    return node.get(qn("val")) if node is not None else None


def run_styles(paragraph: ET.Element) -> set[str]:
    return {
        node.get(qn("val"))
        for node in paragraph.findall(f"./{qn('r')}/{qn('rPr')}/{qn('rStyle')}")
        if node.get(qn("val"))
    }


class MarkdownDocxCodeStyleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pandoc = shutil.which("pandoc")
        if not cls.pandoc:
            raise unittest.SkipTest("Pandoc is not installed")

    def test_inline_text_block_and_program_code_remain_distinct(self) -> None:
        source = """Paragraph with `inline sample`.

```text
借：长期股权投资——国龙医疗
    贷：资本公积——股东资本性投入
```

```python
print("unchanged")
```
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            markdown = temp / "fixture.md"
            output = temp / "fixture.docx"
            markdown.write_text(source, encoding="utf-8")
            subprocess.run(
                [
                    self.pandoc,
                    f"--from={CONVERTER.PANDOC_INPUT_FORMAT}",
                    "--to=docx",
                    "--lua-filter",
                    str(FILTER),
                    "--reference-doc",
                    str(REFERENCE),
                    "--output",
                    str(output),
                    str(markdown),
                ],
                check=True,
            )

            with zipfile.ZipFile(output) as package:
                document = ET.fromstring(package.read("word/document.xml"))
                styles = ET.fromstring(package.read("word/styles.xml"))

        paragraphs = document.findall(f".//{qn('p')}")
        inline = next(p for p in paragraphs if "inline sample" in paragraph_text(p))
        text_block = next(p for p in paragraphs if "长期股权投资" in paragraph_text(p))
        program_block = next(p for p in paragraphs if "print" in paragraph_text(p))

        self.assertIn("InlineCodeEmphasis", run_styles(inline))
        self.assertEqual(paragraph_style(text_block), "SourceCode")
        self.assertEqual(
            paragraph_text(text_block),
            "借：长期股权投资——国龙医疗\n    贷：资本公积——股东资本性投入",
        )
        self.assertIn("TextCodeBlock", run_styles(text_block))
        self.assertNotIn("VerbatimChar", run_styles(text_block))
        self.assertEqual(paragraph_style(program_block), "SourceCode")
        self.assertNotIn("TextCodeBlock", run_styles(program_block))
        self.assertTrue(run_styles(program_block))

        style = styles.find(f".//{qn('style')}[@{qn('styleId')}='TextCodeBlock']")
        self.assertIsNotNone(style)
        properties = style.find(qn("rPr"))
        fonts = properties.find(qn("rFonts"))
        self.assertEqual(
            {name: fonts.get(qn(name)) for name in ("ascii", "eastAsia", "hAnsi", "cs")},
            {name: "楷体" for name in ("ascii", "eastAsia", "hAnsi", "cs")},
        )
        self.assertEqual(properties.find(qn("b")).get(qn("val")), "0")
        self.assertEqual(properties.find(qn("bCs")).get(qn("val")), "0")
        self.assertEqual(properties.find(qn("sz")).get(qn("val")), "20")
        self.assertEqual(properties.find(qn("szCs")).get(qn("val")), "20")

    def test_east_asian_soft_breaks_do_not_create_redundant_spaces(self) -> None:
        source = (
            """中文第一句。
[《慈善法》](https://example.com)继续中文。
OpenAI first
OpenAI second
中文
OpenAI
显式换行。"""
            + "  \n"
            + """下一行。

```text
借：长期股权投资——国龙医疗
    贷：资本公积——股东资本性投入
```
"""
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            markdown = temp / "fixture.md"
            output = temp / "fixture.docx"
            markdown.write_text(source, encoding="utf-8")
            subprocess.run(
                [
                    self.pandoc,
                    f"--from={CONVERTER.PANDOC_INPUT_FORMAT}",
                    "--to=docx",
                    "--lua-filter",
                    str(FILTER),
                    "--reference-doc",
                    str(REFERENCE),
                    "--output",
                    str(output),
                    str(markdown),
                ],
                check=True,
            )

            with zipfile.ZipFile(output) as package:
                document = ET.fromstring(package.read("word/document.xml"))

        paragraphs = document.findall(f".//{qn('p')}")
        prose = next(p for p in paragraphs if "中文第一句" in paragraph_text(p))
        text_block = next(p for p in paragraphs if "长期股权投资" in paragraph_text(p))

        self.assertEqual(CONVERTER.PANDOC_INPUT_FORMAT, "markdown+east_asian_line_breaks")
        self.assertEqual(
            paragraph_text(prose),
            "中文第一句。《慈善法》继续中文。 OpenAI first OpenAI second 中文 OpenAI"
            " 显式换行。\n下一行。",
        )
        self.assertEqual(
            paragraph_text(text_block),
            "借：长期股权投资——国龙医疗\n    贷：资本公积——股东资本性投入",
        )
        self.assertIn("TextCodeBlock", run_styles(text_block))


if __name__ == "__main__":
    unittest.main()
