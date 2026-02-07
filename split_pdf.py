#!/usr/bin/env python3
"""Split a PDF into parts of a maximum size (in MB)."""

from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path

from PyPDF2 import PdfReader, PdfWriter


def bytes_for_writer(writer: PdfWriter) -> bytes:
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def remove_last_page(writer: PdfWriter) -> PdfWriter:
    if hasattr(writer, "remove_page"):
        writer.remove_page(-1)
        return writer
    # Fallback for older PyPDF2 versions without remove_page().
    if len(writer.pages) == 0:
        return writer
    new_writer = PdfWriter()
    for page in writer.pages[:-1]:
        new_writer.add_page(page)
    return new_writer


def split_pdf(input_path: Path, output_dir: Path, base_name: str, max_mb: float) -> None:
    max_bytes = int(max_mb * 1024 * 1024)
    reader = PdfReader(str(input_path))

    output_dir.mkdir(parents=True, exist_ok=True)

    part_index = 1
    writer = PdfWriter()

    for page_index, page in enumerate(reader.pages, start=1):
        writer.add_page(page)
        current_bytes = bytes_for_writer(writer)

        if len(current_bytes) > max_bytes and len(writer.pages) > 1:
            # Remove last page, write the previous part, then start a new one.
            writer = remove_last_page(writer)
            part_bytes = bytes_for_writer(writer)
            output_path = output_dir / f"{base_name}_part{part_index}.pdf"
            output_path.write_bytes(part_bytes)

            part_index += 1
            writer = PdfWriter()
            writer.add_page(page)

            # If a single page is already above the limit, still write it alone.
            single_bytes = bytes_for_writer(writer)
            if len(single_bytes) > max_bytes:
                output_path = output_dir / f"{base_name}_part{part_index}.pdf"
                output_path.write_bytes(single_bytes)
                part_index += 1
                writer = PdfWriter()

    if len(writer.pages) > 0:
        output_path = output_dir / f"{base_name}_part{part_index}.pdf"
        output_path.write_bytes(bytes_for_writer(writer))


def main() -> None:
    parser = argparse.ArgumentParser(description="Split a PDF into parts with a max size.")
    parser.add_argument("input_pdf", type=Path, help="Path to the input PDF")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Output directory (default: current directory)",
    )
    parser.add_argument(
        "-b",
        "--base-name",
        default=None,
        help="Base name for output files (default: input file name)",
    )
    parser.add_argument(
        "-m",
        "--max-mb",
        type=float,
        default=10.0,
        help="Maximum size per part in MB (default: 10)",
    )

    args = parser.parse_args()
    base_name = args.base_name or args.input_pdf.stem

    split_pdf(args.input_pdf, args.output_dir, base_name, args.max_mb)


if __name__ == "__main__":
    main()

