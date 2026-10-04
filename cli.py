"""Antarmuka baris perintah (CLI) untuk PDF Multi Slide Pro.

Memakai core/ tanpa membuka GUI — cocok untuk otomasi / batch.

Contoh:
    python cli.py -o hasil.pdf slide1.pdf slide2.pdf
    python cli.py -o hasil.pdf -c 2 -r 3 -O Portrait -n *.pdf
    python cli.py -o hasil.pdf --json progres.txt slide*.pdf
"""

import argparse
import glob
import os
import sys

from core.constants import (
    MAX_GRID,
    MAX_SLIDES_PER_PAGE,
    MIN_GRID,
    ORIENTATION_LANDSCAPE,
    ORIENTATION_PORTRAIT,
)
from core.pipeline import process_all
from utils.fs import file_size, format_size


def expand_inputs(patterns):
    """Kembangkan glob pattern jadi daftar file PDF yang ada (urutan terjaga).

    Normalisasi separator agar path bergaya Unix ('folder/file.pdf') tetap
    dikenali di Windows.
    """
    paths = []
    for pattern in patterns:
        # Samakan separator agar 'a/b.pdf' dan 'a\\b.pdf' sama-sama jalan.
        pattern = os.path.normpath(pattern)

        matches = glob.glob(pattern)
        if not matches:
            matches = [pattern]

        for match in matches:
            if os.path.isfile(match) and match.lower().endswith(".pdf"):
                paths.append(match)

    # Dedup case-insensitive, jaga urutan.
    seen = set()
    unique = []
    for path in paths:
        key = os.path.abspath(path).lower()
        if key not in seen:
            seen.add(key)
            unique.append(path)

    return unique



def positive_int_in_range(value, minimum, maximum, label):
    """parse_int + validasi rentang; dipakai sebagai type= argparse."""
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{label} harus berupa angka.")

    if number < minimum or number > maximum:
        raise argparse.ArgumentTypeError(
            f"{label} harus antara {minimum} sampai {maximum}."
        )
    return number


def build_parser():
    parser = argparse.ArgumentParser(
        prog="pdf-multi-slide",
        description=(
            "Gabungkan PDF menjadi satu PDF N-up (beberapa slide per "
            "halaman A4). Tanpa GUI."
        ),
    )

    parser.add_argument(
        "inputs",
        nargs="+",
        help="File PDF sumber (boleh beberapa; mendukung pattern seperti *.pdf).",
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Path PDF hasil.",
    )
    parser.add_argument(
        "-c", "--cols",
        type=lambda v: positive_int_in_range(v, MIN_GRID, MAX_GRID, "Kolom"),
        default=3,
        help="Jumlah kolom per halaman (default: 3).",
    )
    parser.add_argument(
        "-r", "--rows",
        type=lambda v: positive_int_in_range(v, MIN_GRID, MAX_GRID, "Baris"),
        default=2,
        help="Jumlah baris per halaman (default: 2).",
    )
    parser.add_argument(
        "-O", "--orientation",
        choices=[ORIENTATION_PORTRAIT, ORIENTATION_LANDSCAPE],
        default=ORIENTATION_LANDSCAPE,
        help="Orientasi halaman (default: Landscape).",
    )
    parser.add_argument(
        "-n", "--number",
        action="store_true",
        help="Tulis nomor slide pada PDF hasil.",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Jangan tampilkan progres.",
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Izinkan menimpa output yang sama dengan file sumber.",
    )

    return parser


def make_reporter(quiet):
    """Kembalikan callback status/progress untuk CLI."""
    if quiet:
        return (lambda text: None), (lambda value: None)

    def on_status(text):
        sys.stderr.write(f"\r{text[:70]:<70}")
        sys.stderr.flush()

    def on_progress(value):
        sys.stderr.write(f"\r  progres: {value:5.1f}%  ")
        sys.stderr.flush()

    return on_status, on_progress


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    inputs = expand_inputs(args.inputs)
    if not inputs:
        parser.error("Tidak ada file PDF valid yang ditemukan.")

    slides_per_page = args.cols * args.rows
    if slides_per_page > MAX_SLIDES_PER_PAGE:
        parser.error(
            f"Jumlah slide per halaman ({slides_per_page}) melebihi "
            f"batas {MAX_SLIDES_PER_PAGE}."
        )

    if not args.output.lower().endswith(".pdf"):
        args.output += ".pdf"

    output_dir = os.path.dirname(os.path.abspath(args.output))
    if not os.path.isdir(output_dir):
        parser.error(f"Folder output tidak ada: {output_dir}")

    source_keys = {os.path.abspath(p).lower() for p in inputs}
    overwrite_source = os.path.abspath(args.output).lower() in source_keys
    if overwrite_source and not args.force:
        parser.error(
            "Path output sama dengan file sumber. "
            "Tambahkan -f/--force untuk menimpa file sumber."
        )

    on_status, on_progress = make_reporter(args.quiet)

    if not args.quiet:
        print(
            f"Memproses {len(inputs)} PDF → {args.cols}x{args.rows} "
            f"({slides_per_page} slide/lembar), {args.orientation}",
            file=sys.stderr,
        )

    try:
        process_all(
            input_paths=inputs,
            output_path=args.output,
            cols=args.cols,
            rows=args.rows,
            orientation=args.orientation,
            number_slides=args.number,
            on_status=on_status,
            on_progress=on_progress,
            allow_overwrite_source=overwrite_source,
        )
    except Exception as error:
        sys.stderr.write("\n")
        print(f"GAGAL: {error}", file=sys.stderr)
        return 1

    if not args.quiet:
        sys.stderr.write("\n")

    print(f"Selesai: {args.output} ({format_size(file_size(args.output))})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
