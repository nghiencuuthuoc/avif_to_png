#!/usr/bin/env python3
"""
Convert all AVIF images in an input folder to PNG.

Requirements:
    pip install pillow pillow-avif-plugin

Usage:
    python avif_to_png.py --input-folder "E:/input_avif"
    python avif_to_png.py --input-folder "E:/input_avif" --output-folder "E:/output_png"
    python avif_to_png.py --input-folder "E:/input_avif" --recursive
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from PIL import Image
import pillow_avif  # noqa: F401  # Registers AVIF support in Pillow


SUPPORTED_EXTENSIONS = {".avif"}


def find_avif_files(input_folder: Path, recursive: bool) -> Iterable[Path]:
    if recursive:
        for ext in SUPPORTED_EXTENSIONS:
            yield from input_folder.rglob(f"*{ext}")
    else:
        for ext in SUPPORTED_EXTENSIONS:
            yield from input_folder.glob(f"*{ext}")


def convert_avif_to_png(
    src_path: Path,
    input_root: Path,
    output_root: Path,
) -> tuple[bool, str]:
    try:
        relative_path = src_path.relative_to(input_root)
        dst_path = (output_root / relative_path).with_suffix(".png")
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        with Image.open(src_path) as img:
            # Convert unsupported modes safely to RGBA or RGB
            if img.mode in ("RGBA", "LA") or ("transparency" in img.info):
                converted = img.convert("RGBA")
            else:
                converted = img.convert("RGB")

            converted.save(dst_path, format="PNG")

        return True, f"OK   | {src_path} -> {dst_path}"
    except Exception as exc:
        return False, f"FAIL | {src_path} | {exc}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert AVIF images in a folder to PNG.")
    parser.add_argument(
        "--input-folder",
        required=True,
        help="Folder containing AVIF files.",
    )
    parser.add_argument(
        "--output-folder",
        default=None,
        help="Folder to save PNG files. Default: create 'png_output' inside input folder.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search AVIF files recursively in subfolders.",
    )
    args = parser.parse_args()

    input_folder = Path(args.input_folder).expanduser().resolve()
    if not input_folder.exists() or not input_folder.is_dir():
        raise SystemExit(f"Input folder does not exist or is not a folder: {input_folder}")

    if args.output_folder:
        output_folder = Path(args.output_folder).expanduser().resolve()
    else:
        output_folder = input_folder / "png_output"

    output_folder.mkdir(parents=True, exist_ok=True)

    avif_files = list(find_avif_files(input_folder, args.recursive))
    if not avif_files:
        print("No AVIF files found.")
        return

    print(f"Input folder : {input_folder}")
    print(f"Output folder: {output_folder}")
    print(f"Files found  : {len(avif_files)}")
    print("-" * 80)

    success_count = 0
    fail_count = 0

    for src_path in avif_files:
        ok, message = convert_avif_to_png(
            src_path=src_path,
            input_root=input_folder,
            output_root=output_folder,
        )
        print(message)
        if ok:
            success_count += 1
        else:
            fail_count += 1

    print("-" * 80)
    print(f"Done. Success: {success_count} | Failed: {fail_count}")


if __name__ == "__main__":
    main()