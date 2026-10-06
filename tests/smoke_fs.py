"""Uji helper filesystem: unique_path (anti-duplikat nama output)."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.fs import unique_path  # noqa: E402
from ui.app import _strip_trailing_number  # noqa: E402


def touch(path):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("x")


def main():
    tmp = tempfile.mkdtemp(prefix="fs_test_")
    checks = []

    # 1) File belum ada -> path apa adanya.
    fresh = os.path.join(tmp, "Hasil.pdf")
    checks.append(("belum ada -> tetap", unique_path(fresh) == fresh))

    # 2) File sudah ada -> tambah ' (1)'.
    touch(fresh)
    got = unique_path(fresh)
    want = os.path.join(tmp, "Hasil (1).pdf")
    checks.append(("ada -> (1)", got == want))

    # 3) ' (1)' juga ada -> ' (2)'.
    touch(want)
    got2 = unique_path(fresh)
    want2 = os.path.join(tmp, "Hasil (2).pdf")
    checks.append(("(1) ada -> (2)", got2 == want2))

    # 4) Ekstensi dipertahankan (nama dengan titik ganda).
    dotted = os.path.join(tmp, "laporan.final.pdf")
    touch(dotted)
    got3 = unique_path(dotted)
    want3 = os.path.join(tmp, "laporan.final (1).pdf")
    checks.append(("ekstensi di akhir", got3 == want3))

    # 5) _strip_trailing_number: nomor lama dibuang agar naik berkelanjutan.
    checks.append(("strip '(2)'", _strip_trailing_number("Hasil (2)") == "Hasil"))
    checks.append(("strip tanpa nomor", _strip_trailing_number("Hasil") == "Hasil"))
    checks.append(
        ("strip tidak buang angka biasa",
         _strip_trailing_number("Laporan 2024") == "Laporan 2024")
    )

    # 6) Simulasi penomoran berkelanjutan (klik 1,2,3).
    base = os.path.join(tmp, "Berlanjut.pdf")
    seq = []
    for _ in range(3):
        target = unique_path(base)
        seq.append(os.path.basename(target))
        touch(target)
    checks.append(
        ("berkelanjutan 1,2,3",
         seq == ["Berlanjut.pdf", "Berlanjut (1).pdf", "Berlanjut (2).pdf"])
    )
    print("[i] sekuens:", seq)

    for name, ok in checks:
        print(("[OK]  " if ok else "[FAIL]") + " " + name)

    if all(ok for _, ok in checks):
        print("\nSEMUA UJI FS LULUS")
        return 0
    print("\nADA YANG GAGAL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
