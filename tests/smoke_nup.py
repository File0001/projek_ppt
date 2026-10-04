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

    # pipeline gabungan 2 file.
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
    # a: ceil(7/6)=2, b: ceil(3/6)=1 -> total 3
    assert pages_all == 3, f"gabungan harusnya 3 halaman, dapat {pages_all}"
    assert progress and progress[-1] == 100, "progress akhir harus 100"
    assert not [f for f in os.listdir(tmp) if f.startswith("__PDF_MULTI_TEMP_")], \
        "temp tidak boleh tersisa"
    print(f"[OK] pipeline: {pages_all} halaman, progress akhir {progress[-1]}")
    print(f"[OK] status terakhir: {statuses[-1] if statuses else '-'}")
    print("SEMUA UJI LULUS")


if __name__ == "__main__":
    main()
