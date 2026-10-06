"""Uji cepat: konversi gambar & pptx -> PDF, lalu N-up via pipeline.

Tidak butuh LibreOffice (memakai fallback PyMuPDF / python-pptx).
"""

import os
import tempfile

import pymupdf

from core.pipeline import process_all


def _make_image(path, text="Halo Gambar"):
    doc = pymupdf.open()
    page = doc.new_page(width=300, height=200)
    page.insert_text((40, 100), text, fontsize=24)
    pix = page.get_pixmap()
    pix.save(path)
    doc.close()


def _make_pdf(path, text="Halaman PDF asli"):
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 100), text, fontsize=20)
    doc.save(path)
    doc.close()


def _make_pptx(path):
    try:
        from pptx import Presentation
        from pptx.util import Inches

        prs = Presentation()
        for i in range(3):
            slide = prs.slides.add_slide(prs.slide_layouts[5])
            slide.shapes.title.text = f"Slide {i + 1}"
            box = slide.shapes.add_textbox(
                Inches(1), Inches(2), Inches(6), Inches(1)
            )
            box.text_frame.text = f"Konten slide {i + 1}"
        prs.save(path)
    except ImportError:
        return False
    return True


def main():
    tmp = tempfile.mkdtemp()
    out = os.path.join(tmp, "hasil.pdf")

    # Buat 3 gambar berbeda -> akan digabung jadi SATU PDF oleh pipeline.
    images = []
    for idx in range(3):
        img = os.path.join(tmp, f"gambar{idx}.png")
        _make_image(img, f"Halo Gambar {idx + 1}")
        images.append(img)

    inputs = list(images)

    # PDF asli: harus dipakai langsung tanpa konversi.
    pdf_path = os.path.join(tmp, "sumber.pdf")
    _make_pdf(pdf_path)
    inputs.append(pdf_path)
    print("PDF dibuat -> diuji (passthrough).")

    pptx_path = os.path.join(tmp, "deck.pptx")
    if _make_pptx(pptx_path):
        inputs.append(pptx_path)
        print("PPTX dibuat -> diuji.")
    else:
        print("python-pptx tidak ada -> hanya gambar yang diuji.")

    statuses = []
    process_all(
        input_paths=inputs,
        output_path=out,
        cols=2,
        rows=2,
        orientation="Portrait",
        on_status=lambda t: (print("  [status]", t), statuses.append(t)),
    )

    # Pipeline harus melaporkan penggabungan gambar menjadi satu PDF.
    assert any("Menggabungkan" in s and "gambar" in s for s in statuses), \
        "pipeline tidak menggabungkan gambar jadi satu PDF"

    doc = pymupdf.open(out)
    pages = len(doc)
    # Kumpulkan semua teks hasil untuk memastikan TIDAK kosong.
    all_text = "".join(doc[i].get_text() for i in range(pages))
    doc.close()
    print(f"OK -> {out} ({pages} halaman, {len(all_text)} karakter teks)")

    # Regresi: teks PPT/PDF harus benar-benar tertulis di PDF (tidak kosong).
    assert len(all_text.strip()) > 0, "PDF hasil kosong — teks tidak tertulis!"
    assert "Halaman PDF asli" in all_text, \
        "teks PDF sumber tidak muncul di PDF hasil"
    print("[OK] teks PDF asli terbaca di PDF hasil")
    if os.path.isfile(pptx_path):
        assert "Konten slide" in all_text, \
            "teks pptx tidak muncul di PDF hasil"
        print("[OK] teks PPT terbaca di PDF")
    print("SEMUA UJI CONVERT LULUS")


if __name__ == "__main__":
    main()
