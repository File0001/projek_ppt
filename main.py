"""Entry point aplikasi PDF Multi Slide Pro.

Jalankan:  python main.py
"""

import tkinter as tk

from ui.app import DND_AVAILABLE, PDFMultiSlidePro


def main():
    if DND_AVAILABLE:
        # Import di sini agar tidak wajib install tkinterdnd2.
        from tkinterdnd2 import TkinterDnD

        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    PDFMultiSlidePro(root)
    root.mainloop()


if __name__ == "__main__":
    main()
