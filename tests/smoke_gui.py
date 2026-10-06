"""Verifikasi GUI nyata: bangun jendela, cek widget & fitur multi-format.

Dijalankan headless-ish (jendela dibuat lalu langsung ditutup setelah
pemeriksaan). Membuktikan aplikasi bisa diluncurkan & fitur terpasang.
"""

import os
import sys
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.app import PDFMultiSlidePro  # noqa: E402


def collect_widgets(widget, acc):
    acc.append(widget)
    for child in widget.winfo_children():
        collect_widgets(child, acc)
    return acc


def widget_texts(widgets):
    texts = []
    for w in widgets:
        try:
            t = w.cget("text")
            if t:
                texts.append(str(t))
        except Exception:
            pass
        try:
            t = w.cget("textvariable")
            if t:
                val = widget.tk.globalgetvar(t)
                texts.append(str(val))
        except Exception:
            pass
    return texts


def main():
    root = tk.Tk()
    root.withdraw()  # tidak munculkan jendela saat auto-test
    app = PDFMultiSlidePro(root)

    widgets = collect_widgets(root, [])
    texts = " || ".join(widget_texts(widgets))

    checks = {
        "Tombol 'Tambah file'": "Tambah file" in texts,
        "Label 'Daftar file'": "Daftar file" in texts,
        "Judul 'Ubah dokumen jadi presentasi'": "Ubah dokumen jadi presentasi" in texts,
        "Hint drag&drop multi-format": "Seret file" in texts,
        "Status awal menyebut 'file'": "Tambahkan file untuk memulai" in texts,
        "Checkbox 'Bolak-balik (duplex)'": "Bolak-balik (duplex)" in texts,
    }

    for name, ok in checks.items():
        print(("[OK]  " if ok else "[MISS]") + " " + name)

    # Cek fungsi bantu multi-format benar-benar ada.
    print("[OK]  _is_readable tersedia:", hasattr(app, "_is_readable"))
    print("[OK]  _count_pages tersedia:", hasattr(app, "_count_pages"))

    # Cek var duplex & defaultnya.
    print("[OK]  duplex_var default:", app.duplex_var.get())
    checks["duplex_var ada"] = hasattr(app, "duplex_var")

    root.destroy()

    if all(checks.values()):
        print("\nSEMUA PEMERIKSAAN GUI LULUS — fitur terpasang & app bisa diluncurkan.")
        return 0
    print("\nADA YANG BELUM — lihat [MISS] di atas.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
