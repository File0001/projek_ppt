"""Uji CLI (headless). Jalankan: python tests/smoke_cli.py"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymupdf

from cli import main


def make_sample_pdf(path, pages):
    doc = pymupdf.open()
    for i in range(pages):
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 72), f"Slide {i + 1}", fontsize=24)
    doc.save(path)
    doc.close()


def page_count(path):
    doc = pymupdf.open(path)
    count = len(doc)
    doc.close()
    return count


def main_test():
    tmp = tempfile.mkdtemp(prefix="cli_test_")
    src_a = os.path.join(tmp, "a.pdf")
    src_b = os.path.join(tmp, "b.pdf")
    make_sample_pdf(src_a, 8)
    make_sample_pdf(src_b, 3)

    out = os.path.join(tmp, "out.pdf")

    # Sukses, quiet. pad_even default: a(8)=2 hal (genap), b(3)=1 -> 2 (digenapkan) = 4.
    code = main(["-o", out, "-q", "-c", "3", "-r", "2", src_a, src_b])
    assert code == 0, f"exit harus 0, dapat {code}"
    assert page_count(out) == 4, "harusnya 4 halaman (tiap file digenapkan)"
    print(f"[OK] CLI sukses: {page_count(out)} halaman, exit {code}")

    # Output sama dengan sumber → error exit 2.
    try:
        main(["-o", src_a, src_a])
    except SystemExit as e:
        assert e.code == 2, f"harusnya exit 2, dapat {e.code}"
        print(f"[OK] guard same-file: exit {e.code}")
    else:
        raise AssertionError("seharusnya SystemExit untuk file output = sumber")

    # Tanpa input valid → error exit 2.
    try:
        main(["-o", out, os.path.join(tmp, "tidak_ada.pdf")])
    except SystemExit as e:
        assert e.code == 2, f"harusnya exit 2, dapat {e.code}"
        print(f"[OK] guard input kosong: exit {e.code}")
    else:
        raise AssertionError("seharusnya SystemExit untuk input tak valid")

    # Output tanpa ekstensi .pdf → ditambah otomatis.
    out_noext = os.path.join(tmp, "hasil")
    code = main(["-o", out_noext, "-q", src_a])
    assert code == 0
    assert os.path.exists(out_noext + ".pdf"), "ekstensi .pdf harus ditambahkan"
    print("[OK] ekstensi .pdf otomatis ditambahkan")

    # Tanpa -f, output = sumber → tetap ditolak (exit 2).
    try:
        main(["-o", src_a, src_a])
    except SystemExit as e:
        assert e.code == 2, f"harusnya exit 2, dapat {e.code}"
        print(f"[OK] same-file tanpa --force ditolak: exit {e.code}")
    else:
        raise AssertionError("seharusnya SystemExit tanpa --force")

    # Dengan -f, output = sumber → diizinkan (menimpa). Sumber 8 hal. → 2 hal.
    src_c = os.path.join(tmp, "c.pdf")
    make_sample_pdf(src_c, 8)
    before = page_count(src_c)
    code = main(["-o", src_c, "-q", "-f", "-c", "3", "-r", "2", src_c])
    assert code == 0, f"exit harus 0, dapat {code}"
    after = page_count(src_c)
    assert before == 8 and after == 2, f"hasil timpa harus 2, dapat {after}"
    print(f"[OK] --force menimpa sumber: {before} -> {after} halaman")

    print("SEMUA UJI CLI LULUS")


if __name__ == "__main__":
    main_test()
