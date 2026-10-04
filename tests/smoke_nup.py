"""Uji cepat core N-up (headless). Jalankan: python tests/smoke_nup.py"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymupdf

from core.nup import create_nup_pdf
from core.pipeline import process_all


def make_sample_pdf(path, pages):
    doc = pymupdf.open()
    for i in range(pages):
        page = doc.new_page(width=595, height=842)  # A4 portrait
        page.insert_text((72, 72), f"Slide {i + 1}", fontsize=24)
    doc.save(path)
    doc.close()


def main():
    tmp = tempfile.mkdtemp(prefix="nup_test_")

    src_a = os.path.join(tmp, "a.pdf")
    src_b = os.path.join(tmp, "b.pdf")
    make_sample_pdf(src_a, 7)
    make_sample_pdf(src_b, 3)

    # grid 3x2 = 6 slide/lembar, landscape, dengan nomor.
    out_single = os.path.join(tmp, "out_single.pdf")
    create_nup_pdf(
        src_a, out_single, cols=3, rows=2,
        orientation="Landscape", number_slides=True,
    )
    doc = pymupdf.open(out_single)
    pages_single = len(doc)
    r0 = doc[0].rect
    doc.close()
    assert pages_single == 2, f"harusnya 2 halaman (7 slide / 6), dapat {pages_single}"
    assert abs(r0.width - 841.8898) < 0.5, "landscape width salah"
    print(f"[OK] single: {pages_single} halaman, ukuran {r0.width:.1f}x{r0.height:.1f}")

    # pipeline gabungan 2 file (default pad_even=True: tiap file digenapkan).
    out_all = os.path.join(tmp, "out_all.pdf")
    statuses = []
    progress = []
    process_all(
        input_paths=[src_a, src_b],
        output_path=out_all,
        cols=3, rows=2,
        orientation="Landscape",
        number_slides=False,
        on_status=statuses.append,
        on_progress=progress.append,
    )
    doc = pymupdf.open(out_all)
    pages_all = len(doc)
    doc.close()
    # a: ceil(7/6)=2 (genap), b: ceil(3/6)=1 -> digenapkan jadi 2 -> total 4
    assert pages_all == 4, f"gabungan harusnya 4 halaman, dapat {pages_all}"
    assert progress and progress[-1] == 100, "progress akhir harus 100"
    assert not [f for f in os.listdir(tmp) if f.startswith("__PDF_MULTI_TEMP_")], \
        "temp tidak boleh tersisa"
    print(f"[OK] pipeline: {pages_all} halaman, progress akhir {progress[-1]}")
    print(f"[OK] status terakhir: {statuses[-1] if statuses else '-'}")

    # pad_even eksplisit: file 3 slide (ganjil -> 2 hal).
    out_pad = os.path.join(tmp, "out_pad.pdf")
    create_nup_pdf(
        src_b, out_pad, cols=3, rows=2,
        orientation="Landscape", pad_even=True,
    )
    doc = pymupdf.open(out_pad)
    pages_pad = len(doc)
    doc.close()
    assert pages_pad == 2, f"pad_even harusnya 2 halaman, dapat {pages_pad}"
    print(f"[OK] pad_even: 1 -> {pages_pad} halaman (digenapkan)")

    # pad_even=False: file 3 slide tetap 1 halaman.
    out_nopad = os.path.join(tmp, "out_nopad.pdf")
    create_nup_pdf(
        src_b, out_nopad, cols=3, rows=2,
        orientation="Landscape", pad_even=False,
    )
    doc = pymupdf.open(out_nopad)
    pages_nopad = len(doc)
    doc.close()
    assert pages_nopad == 1, f"tanpa pad harusnya 1 halaman, dapat {pages_nopad}"
    print(f"[OK] pad_even=False: tetap {pages_nopad} halaman")

    print("SEMUA UJI LULUS")


if __name__ == "__main__":
    main()
