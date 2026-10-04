"""Entry point aplikasi PDF Multi Slide Pro.

Jalankan:  python main.py
"""

import tkinter as tk

from ui.app import DND_AVAILABLE, PDFMultiSlidePro
from utils.fs import app_icon_path


def apply_window_icon(root):
    """Pasang ikon jendela. Aman: diabaikan bila ikon tidak ada / tidak didukung."""
    icon = app_icon_path()
    if not icon:
        return
    try:
        # iconbitmap: dipakai Windows (file .ico). Gagal → lewati tanpa error.
        root.iconbitmap(default=icon)
    except Exception:
        pass


def main():
    if DND_AVAILABLE:
        # Import di sini agar tidak wajib install tkinterdnd2.
        from tkinterdnd2 import TkinterDnD

        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    apply_window_icon(root)

    PDFMultiSlidePro(root)
    root.mainloop()


if __name__ == "__main__":
    main()
