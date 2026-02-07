#!/usr/bin/env python3
"""Compress a PDF into a smaller single PDF (no splitting)."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

import pikepdf


def compress_with_pikepdf(input_path: Path, output_path: Path, quality: str) -> None:
    # pikepdf mainly re-compresses streams; it does not aggressively downsample images.
    # Use Ghostscript method for stronger compression.
    if quality == "strong":
        compress_streams = True
        object_streams = pikepdf.ObjectStreamMode.generate
        linearize = False
    elif quality == "light":
        compress_streams = True
        object_streams = pikepdf.ObjectStreamMode.disable
        linearize = True
    else:  # medium
        compress_streams = True
        object_streams = pikepdf.ObjectStreamMode.generate
        linearize = True

    with pikepdf.open(str(input_path)) as pdf:
        pdf.save(
            str(output_path),
            compress_streams=compress_streams,
            object_stream_mode=object_streams,
            linearize=linearize,
        )


def find_ghostscript(explicit_path: Path | None) -> str | None:
    if explicit_path:
        return str(explicit_path) if explicit_path.exists() else None

    gs = shutil.which("gs") or shutil.which("gswin64c") or shutil.which("gswin32c")
    if gs:
        return gs

    # Common Windows install locations.
    candidates = []
    candidates.extend(Path("C:/Program Files/gs").glob("**/bin/gswin64c.exe"))
    candidates.extend(Path("C:/Program Files (x86)/gs").glob("**/bin/gswin32c.exe"))
    if candidates:
        return str(sorted(candidates)[-1])
    return None


def compress_with_ghostscript(
    input_path: Path, output_path: Path, quality: str, gs_path: Path | None
) -> None:
    gs = find_ghostscript(gs_path)
    if not gs:
        raise RuntimeError(
            "Ghostscript not found. Install it or use --method pikepdf, or pass --gs-path."
        )

    # Map quality to Ghostscript settings.
    if quality == "strong":
        pdf_setting = "/screen"
    elif quality == "light":
        pdf_setting = "/prepress"
    else:  # medium
        pdf_setting = "/ebook"

    cmd = [
        gs,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={pdf_setting}",
        "-dNOPAUSE",
        "-dBATCH",
        "-dQUIET",
        f"-sOutputFile={output_path}",
        str(input_path),
    ]

    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compress a PDF into a smaller single PDF (no splitting)."
    )
    parser.add_argument("input_pdf", type=Path, help="Path to the input PDF")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output PDF path (default: input name + _compressed.pdf)",
    )
    parser.add_argument(
        "-m",
        "--method",
        choices=["pikepdf", "ghostscript"],
        default="pikepdf",
        help="Compression method (default: pikepdf)",
    )
    parser.add_argument(
        "-q",
        "--quality",
        choices=["light", "medium", "strong"],
        default="medium",
        help="Compression level (default: medium)",
    )
    parser.add_argument(
        "--gs-path",
        type=Path,
        default=None,
        help="Path to Ghostscript executable (gswin64c.exe)",
    )

    args = parser.parse_args()
    output_path = args.output or args.input_pdf.with_name(
        f"{args.input_pdf.stem}_compressed.pdf"
    )

    if args.method == "ghostscript":
        compress_with_ghostscript(
            args.input_pdf, output_path, args.quality, args.gs_path
        )
    else:
        compress_with_pikepdf(args.input_pdf, output_path, args.quality)


if __name__ == "__main__":
    main()
