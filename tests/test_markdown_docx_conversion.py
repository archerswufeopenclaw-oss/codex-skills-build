from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from xml.etree import ElementTree as ET


CONVERTER_PATH = (
    Path(__file__).parents[1] / "skills" / "markdown-docx" / "scripts" / "convert.py"
)
SPEC = importlib.util.spec_from_file_location("markdown_docx_conversion", CONVERTER_PATH)
assert SPEC and SPEC.loader
CONVERTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONVERTER)


@unittest.skipUnless(os.name == "nt", "The converter requires Windows")
class MarkdownDocxConversionTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory(prefix="markdown-docx-test-")
        self.addCleanup(temporary_directory.cleanup)
        self.directory = Path(temporary_directory.name)
        self.source = self.directory / "article.md"
        self.output = self.directory / "article.docx"
        self.source_bytes = "正文保持原样。\n".encode("utf-8")
        self.source.write_bytes(self.source_bytes)
        self.args = argparse.Namespace(
            input=self.source, output=self.output, overwrite=False
        )
        self.enterContext(patch.object(CONVERTER, "parse_args", return_value=self.args))
        self.enterContext(
            patch.object(
                CONVERTER, "find_windows_powershell", return_value=Path("powershell.exe")
            )
        )
        self.enterContext(redirect_stdout(io.StringIO()))

    def assert_source_and_staging_intact(self) -> None:
        self.assertEqual(self.source.read_bytes(), self.source_bytes)
        self.assertEqual(list(self.directory.glob(".markdown-docx-*")), [])

    def run_with_fake_conversion(self, *, word_failure: bool = False) -> int:
        def run_stage(command: list[str], **_kwargs: object) -> None:
            if "--output" in command:
                staged = Path(command[command.index("--output") + 1])
                staged.write_bytes(b"converted candidate")
            elif word_failure:
                raise SystemExit("Microsoft Word table auto-fit failed with exit code 1")

        with (
            patch.object(CONVERTER, "find_pandoc", return_value=Path("pandoc.exe")),
            patch.object(CONVERTER, "run_checked", side_effect=run_stage),
        ):
            return CONVERTER.main()

    def test_existing_output_without_overwrite_is_untouched(self) -> None:
        self.output.write_bytes(b"existing document")
        with patch.object(CONVERTER, "run_checked") as run_checked:
            with self.assertRaisesRegex(SystemExit, "Output already exists"):
                CONVERTER.main()
            run_checked.assert_not_called()
        self.assertEqual(self.output.read_bytes(), b"existing document")
        self.assert_source_and_staging_intact()

    def test_new_output_publishes_candidate_unchanged(self) -> None:
        self.assertEqual(self.run_with_fake_conversion(), 0)
        self.assertEqual(self.output.read_bytes(), b"converted candidate")
        self.assert_source_and_staging_intact()

    def test_explicit_overwrite_replaces_existing_output(self) -> None:
        self.args.overwrite = True
        self.output.write_bytes(b"existing document")
        self.assertEqual(self.run_with_fake_conversion(), 0)
        self.assertEqual(self.output.read_bytes(), b"converted candidate")
        self.assert_source_and_staging_intact()

    def test_target_appearing_at_publication_is_preserved(self) -> None:
        real_rename = os.rename

        def publish_after_competing_writer(staged: Path, output: Path) -> None:
            # A competing publisher wins immediately before the filesystem operation.
            output.write_bytes(b"competing document")
            real_rename(staged, output)

        with patch.object(CONVERTER.os, "rename", side_effect=publish_after_competing_writer):
            with self.assertRaisesRegex(SystemExit, "refusing to replace"):
                self.run_with_fake_conversion()
        self.assertEqual(self.output.read_bytes(), b"competing document")
        self.assert_source_and_staging_intact()

    def test_word_failure_never_publishes_candidate(self) -> None:
        for existing in (False, True):
            with self.subTest(existing_output=existing):
                self.args.overwrite = existing
                if existing:
                    self.output.write_bytes(b"existing document")
                with self.assertRaisesRegex(SystemExit, "Word table auto-fit failed"):
                    self.run_with_fake_conversion(word_failure=True)
                if existing:
                    self.assertEqual(self.output.read_bytes(), b"existing document")
                else:
                    self.assertFalse(self.output.exists())
                self.assert_source_and_staging_intact()

    def test_real_pandoc_warning_stops_before_word_and_preserves_output(self) -> None:
        try:
            CONVERTER.find_pandoc()
        except SystemExit as error:
            self.skipTest(str(error))
        self.source_bytes = "![必须保留的图表](missing-chart.png)\n".encode("utf-8")
        self.source.write_bytes(self.source_bytes)
        real_run_checked = CONVERTER.run_checked

        def run_pandoc_only(command: list[str], **kwargs: object) -> None:
            if "--output" not in command:
                self.fail("Word must not run after Pandoc warnings")
            real_run_checked(command, **kwargs)

        for existing in (False, True):
            with self.subTest(existing_output=existing):
                self.args.overwrite = existing
                if existing:
                    self.output.write_bytes(b"existing document")
                with patch.object(
                    CONVERTER, "run_checked", side_effect=run_pandoc_only
                ) as run_checked:
                    with self.assertRaisesRegex(SystemExit, "Pandoc conversion failed"):
                        CONVERTER.main()
                    self.assertEqual(run_checked.call_count, 1)
                if existing:
                    self.assertEqual(self.output.read_bytes(), b"existing document")
                else:
                    self.assertFalse(self.output.exists())
                self.assert_source_and_staging_intact()

    def test_real_pandoc_success_preserves_content_and_candidate_bytes(self) -> None:
        try:
            CONVERTER.find_pandoc()
        except SystemExit as error:
            self.skipTest(str(error))
        real_run_checked = CONVERTER.run_checked
        candidate_bytes = None

        def run_stage(command: list[str], **kwargs: object) -> None:
            nonlocal candidate_bytes
            if "--output" in command:
                real_run_checked(command, **kwargs)
            else:
                # Inspect the real Pandoc result without starting Word or COM.
                staged = Path(command[command.index("-InputPath") + 1])
                candidate_bytes = staged.read_bytes()

        with patch.object(CONVERTER, "run_checked", side_effect=run_stage):
            self.assertEqual(CONVERTER.main(), 0)
        self.assertIsNotNone(candidate_bytes)
        self.assertEqual(self.output.read_bytes(), candidate_bytes)
        with zipfile.ZipFile(self.output) as package:
            document = ET.fromstring(package.read("word/document.xml"))
        text = "".join(
            node.text or ""
            for node in document.iter(
                "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"
            )
        )
        self.assertEqual(text, "正文保持原样。")
        self.assert_source_and_staging_intact()


class MarkdownDocxPlatformTests(unittest.TestCase):
    def test_non_windows_platform_is_rejected_before_conversion(self) -> None:
        with (
            patch.object(CONVERTER, "parse_args", return_value=argparse.Namespace()),
            patch.object(CONVERTER.os, "name", "posix"),
            patch.object(CONVERTER, "run_checked") as run_checked,
        ):
            with self.assertRaisesRegex(SystemExit, "requires Windows"):
                CONVERTER.main()
            run_checked.assert_not_called()


if __name__ == "__main__":
    unittest.main()
