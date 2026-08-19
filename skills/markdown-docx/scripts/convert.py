#!/usr/bin/env python3
"""Convert one Markdown file to DOCX with Pandoc and Word table auto-fit."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REFERENCE = SKILL_ROOT / "assets" / "reference-public.docx"
AUTOFIT_SCRIPT = SKILL_ROOT / "scripts" / "autofit_tables.ps1"
INLINE_CODE_FILTER = SKILL_ROOT / "scripts" / "inline_code_style.lua"


def find_pandoc() -> Path:
    if found := shutil.which("pandoc"):
        return Path(found)
    if local_app_data := os.environ.get("LOCALAPPDATA"):
        installed = Path(local_app_data) / "Pandoc" / "pandoc.exe"
        if installed.is_file():
            return installed
    raise SystemExit("Pandoc was not found in PATH or the standard per-user location.")


def find_windows_powershell() -> Path:
    if found := shutil.which("powershell.exe"):
        return Path(found)
    raise SystemExit(
        "Windows PowerShell was not found; Microsoft Word table auto-fit cannot run."
    )


def run_checked(command: list[str], *, cwd: Path, failure_message: str) -> None:
    completed = subprocess.run(command, cwd=cwd, check=False)
    if completed.returncode != 0:
        raise SystemExit(f"{failure_message} with exit code {completed.returncode}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert one Markdown article to a styled DOCX."
    )
    parser.add_argument("input", type=Path, help="Input .md or .markdown file")
    parser.add_argument("-o", "--output", type=Path, help="Output .docx path")
    parser.add_argument(
        "--overwrite", action="store_true", help="Allow replacing an existing DOCX"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.input.expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"Input file does not exist: {source}")
    if source.suffix.lower() not in {".md", ".markdown"}:
        raise SystemExit(f"Input must be Markdown (.md or .markdown): {source}")

    output = (
        args.output.expanduser().resolve()
        if args.output
        else source.with_suffix(".docx")
    )
    if output.suffix.lower() != ".docx":
        raise SystemExit(f"Output must end in .docx: {output}")
    if output.exists() and not args.overwrite:
        raise SystemExit(f"Output already exists; pass --overwrite to replace it: {output}")

    if not DEFAULT_REFERENCE.is_file():
        raise SystemExit(f"Reference DOCX does not exist: {DEFAULT_REFERENCE}")
    if not AUTOFIT_SCRIPT.is_file():
        raise SystemExit(f"Word table auto-fit script does not exist: {AUTOFIT_SCRIPT}")
    if not INLINE_CODE_FILTER.is_file():
        raise SystemExit(f"Inline-code filter does not exist: {INLINE_CODE_FILTER}")

    pandoc = find_pandoc()
    powershell = find_windows_powershell()
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        dir=output.parent, prefix=".markdown-docx-"
    ) as temporary_directory:
        staged_output = Path(temporary_directory) / output.name
        pandoc_command = [
            str(pandoc),
            "--from=markdown",
            "--to=docx",
            "--lua-filter",
            str(INLINE_CODE_FILTER),
            "--reference-doc",
            str(DEFAULT_REFERENCE),
            "--output",
            str(staged_output),
            str(source),
        ]
        run_checked(
            pandoc_command,
            cwd=source.parent,
            failure_message="Pandoc conversion failed",
        )

        autofit_command = [
            str(powershell),
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(AUTOFIT_SCRIPT),
            "-InputPath",
            str(staged_output),
        ]
        run_checked(
            autofit_command,
            cwd=source.parent,
            failure_message="Microsoft Word table auto-fit failed",
        )

        if output.exists() and not args.overwrite:
            raise SystemExit(
                f"Output appeared during conversion; refusing to replace it: {output}"
            )
        os.replace(staged_output, output)

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
