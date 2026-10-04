"""Buat build_assets/app.ico dari logo project (sekali jalan, reproducible).

Sumber: file PNG logo di root project. Bila tidak ada, script berhenti tanpa
error (ikon opsional; exe tetap bisa dibuild tanpa ikon).

Jalankan:  python build_assets/make_icon.py
"""

import os
import sys

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ASSETS_DIR)
ICO_OUT = os.path.join(ASSETS_DIR, "app.ico")

# Kandidat sumber logo (urutan prioritas).
SOURCES = [
    "ChatGPT Image 4 Okt 2026, 21.44.02.png",
]


def main():
    try:
        from PIL import Image
    except ImportError:
        print("[!] Pillow tidak terpasang (pip install pillow). Ikon dilewati.")
        return 0

    src = None
    for name in SOURCES:
        candidate = os.path.join(PROJECT_ROOT, name)
        if os.path.isfile(candidate):
            src = candidate
            break

    if src is None:
        print("[!] Sumber logo tidak ditemukan. Ikon dilewati.")
        return 0

    im = Image.open(src).convert("RGBA")
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    im.save(ICO_OUT, sizes=sizes)
    print(f"[OK] Ikon dibuat: {ICO_OUT} ({os.path.getsize(ICO_OUT)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
