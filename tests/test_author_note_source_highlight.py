from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path

import test_markdown_docx_author_notes as docx_tests


SETTINGS = (
    Path(__file__).parents[1]
    / "skills/markdown-article/assets/vscode-author-notes.settings.json"
)
HEADER = '<span class="author-note">🔴 作者说明（供作者阅读，可整段删除）</span>'
NOTES = [
    f"> {HEADER}\n>\n"
    "> 第一块解释[原始资料](https://example.com/evidence)与 `指标`。\n>\n"
    "> 第一块的第二段。",
    f"> {HEADER}\n>\n> 第二块解释，保留可编辑的源码。",
    f"> {HEADER}\n>\n> 第三块解释位于文件末尾。",
]
SOURCE = (
    "正文开头。\n\n> 普通引用。\n\n"
    + NOTES[0]
    + "\n\n第一块之后的正文。\n\n"
    + f"> {HEADER}：这是普通引用的较长首行。\n> 不属于作者说明。\n\n"
    + NOTES[1]
    + "\n\n第二块之后的正文与 `普通代码`。\n\n"
    + "> 普通引用也可以提到作者说明。\n\n"
    + NOTES[2]
)


class AuthorNoteSourceHighlightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.node = shutil.which("node")
        if not cls.node:
            raise unittest.SkipTest("Node.js is required to test ECMAScript highlight regexes")

    def test_source_rules_match_only_the_three_complete_note_blocks(self) -> None:
        settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
        rules = settings["highlight.regexes"]
        self.assertEqual(len(rules), 1)
        pattern, options = next(iter(rules.items()))
        self.assertEqual(len(options["decorations"]), 1)
        self.assertTrue(options["decorations"][0]["isWholeLine"])

        # Execute the extension's actual regex dialect; Python re is not equivalent.
        script = r"""
const fs = require('node:fs');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const regex = new RegExp(input.pattern, input.options.regexFlags);
const filter = new RegExp(input.options.filterLanguageRegex);
const matches = Array.from(input.source.matchAll(regex), match => ({
    text: match[0], captures: match.slice(1)
}));
const languages = ['markdown', 'plaintext', 'html', 'python', 'markdown-extra']
    .filter(language => filter.test(language));
process.stdout.write(JSON.stringify({matches, languages}));
"""
        for newline in ("\n", "\r\n"):
            with self.subTest(newline=repr(newline)):
                result = subprocess.run(
                    [self.node, "-e", script],
                    input=json.dumps({
                        "pattern": pattern,
                        "options": options,
                        "source": SOURCE.replace("\n", newline),
                    }),
                    text=True, encoding="utf-8", capture_output=True, check=True,
                )
                actual = json.loads(result.stdout)
                expected = [note.replace("\n", newline) for note in NOTES]
                self.assertEqual(actual["languages"], ["markdown"])
                self.assertEqual([match["text"] for match in actual["matches"]], expected)
                self.assertEqual(
                    [match["captures"] for match in actual["matches"]],
                    [[note] for note in expected],
                )


class SourceHighlightDocxCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pandoc = shutil.which("pandoc")
        if not cls.pandoc:
            raise unittest.SkipTest("Pandoc is not installed")

    def test_same_source_preserves_red_docx_notes_and_ordinary_quotes(self) -> None:
        document, styles, relationships = docx_tests.AuthorNoteConversionTests.convert(self, SOURCE)
        word = docx_tests.W
        paragraphs = list(document.iter(word + "p"))
        expected_notes = [
            "🔴 作者说明（供作者阅读，可整段删除）",
            "第一块解释原始资料与 指标。",
            "第一块的第二段。",
            "🔴 作者说明（供作者阅读，可整段删除）",
            "第二块解释，保留可编辑的源码。",
            "🔴 作者说明（供作者阅读，可整段删除）",
            "第三块解释位于文件末尾。",
        ]
        notes = [
            paragraph for paragraph in paragraphs
            if paragraph.find(word + "pPr/" + word + "pStyle").get(word + "val") == "AuthorNote"
        ]
        self.assertEqual([docx_tests.text(paragraph) for paragraph in notes], expected_notes)
        for paragraph in notes:
            for run in paragraph.iter(word + "r"):
                if docx_tests.text(run):
                    self.assertEqual(
                        run.find(word + "rPr/" + word + "rStyle").get(word + "val"),
                        "AuthorNoteText",
                    )
        for name in ("AuthorNote", "AuthorNoteText"):
            properties = styles[name].find(word + "rPr")
            self.assertEqual(properties.find(word + "color").get(word + "val"), "C00000")
            self.assertEqual(properties.find(word + "sz").get(word + "val"), "22")
            self.assertIsNone(properties.find(word + "shd"))
            self.assertIsNone(properties.find(word + "highlight"))
        self.assertFalse(list(document.iter(word + "shd")))
        self.assertFalse(list(document.iter(word + "highlight")))
        self.assertEqual([docx_tests.text(p) for p in paragraphs if p not in notes], [
            "正文开头。", "普通引用。", "第一块之后的正文。",
            "🔴 作者说明（供作者阅读，可整段删除）：这是普通引用的较长首行。不属于作者说明。",
            "第二块之后的正文与 普通代码。", "普通引用也可以提到作者说明。",
        ])
        for paragraph in paragraphs:
            if paragraph not in notes:
                self.assertNotIn("AuthorNoteText", [
                    style.get(word + "val") for style in paragraph.iter(word + "rStyle")
                ])
        document_text = docx_tests.text(document)
        for editor_setting in ("highlight.regexes", "backgroundColor", "overviewRulerColor"):
            self.assertNotIn(editor_setting, document_text)
        self.assertTrue(any(
            relation.get("Target") == "https://example.com/evidence"
            for relation in relationships.findall(docx_tests.REL + "Relationship")
        ))


if __name__ == "__main__":
    unittest.main()
