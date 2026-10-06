"""Aplikasi utama: class PDFMultiSlidePro (view + controller).

Logika PDF didelegasikan ke core/ (headless). UI state tetap di tkinter Var.
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import pymupdf

from core.constants import (
    MAX_GRID,
    MAX_SLIDES_PER_PAGE,
    ORIENTATION_LANDSCAPE,
    PAPER_SIZE,
    MIN_GRID,
)
from core.convert import SUPPORTED_EXTS, file_kind
from core.nup import LayoutError, compute_cell_rect, compute_grid, compute_page_geometry
from core.pipeline import process_all
from ui import widgets
from ui.styles import create_styles
from utils.fs import (
    file_size,
    format_size,
    normalize_key,
    open_folder,
    unique_path,
)

# Pola filetype untuk dialog "buka file" (Tk) yang mencakup semua tipe didukung.
_OPEN_FILETYPES = [
    ("Semua file didukung", "*.pdf *.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp *.pptx *.ppt"),
    ("PDF", "*.pdf"),
    ("Gambar", "*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp"),
    ("PowerPoint", "*.pptx *.ppt"),
    ("Semua file", "*.*"),
]


import re as _re


def _strip_trailing_number(stem):
    """Buang akhiran ' (n)' dari nama dasar; 'Hasil (2)' → 'Hasil'.

    Agar penomoran tetap berkelanjutan walau nama dasar yang diusulkan sudah
    mengandung nomor dari sesi sebelumnya.
    """
    return _re.sub(r"\s*\(\d+\)$", "", stem)


# Drag & drop opsional.
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False


class PDFMultiSlidePro:
    """GUI utama: input file → atur grid → hasilkan PDF N-up."""

    # ==========================================================
    # INIT
    # ==========================================================

    def __init__(self, root):
        self.root = root

        self.root.title("PDF ke Slide • Multi Slide Pro")
        self.root.geometry("1400x850")
        self.root.minsize(1180, 720)
        self.root.configure(bg="#F4F6FA")

        self.files = []

        create_styles()
        self.create_ui()

        if DND_AVAILABLE:
            self.enable_drag_drop(self.root)

        self.update_preview()

    # ==========================================================
    # UI
    # ==========================================================

    def create_ui(self):
        root_frame = ttk.Frame(self.root, padding=(22, 18, 22, 14))
        root_frame.pack(fill="both", expand=True)

        self._build_header(root_frame)

        content = ttk.Frame(root_frame)
        content.pack(fill="both", expand=True)

        self._build_left_panel(content)
        self._build_center_panel(content)
        self._build_right_panel(content)
        self._build_bottom(root_frame)

    # ----------------------------------------------------------
    # HEADER
    # ----------------------------------------------------------

    def _build_header(self, parent):
        header = ttk.Frame(parent)
        header.pack(fill="x", pady=(0, 14))

        title_line = ttk.Frame(header)
        title_line.pack(fill="x")

        ttk.Label(
            title_line,
            text="Ubah dokumen jadi presentasi",
            style="Title.TLabel",
        ).pack(side="left")

        widgets.inline_badge(
            title_line, "  Siap dipresentasikan  "
        ).pack(side="left", padx=(12, 0), pady=(5, 0))

        ttk.Label(
            header,
            text=(
                "Susun PDF, gambar, atau PowerPoint menjadi "
                "beberapa slide dalam satu halaman dengan layout rapi."
            ),
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(3, 0))

    # ----------------------------------------------------------
    # LEFT PANEL — daftar file
    # ----------------------------------------------------------

    def _build_left_panel(self, content):
        left = ttk.Frame(content, style="Card.TFrame", padding=14, width=270)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)

        header = ttk.Frame(left, style="Card.TFrame")
        header.pack(fill="x")

        ttk.Label(header, text="Daftar file", style="Section.TLabel").pack(
            side="left"
        )

        self.file_count_var = tk.StringVar(value="0 file • 0 halaman")
        ttk.Label(
            header, textvariable=self.file_count_var, style="Muted.TLabel"
        ).pack(side="right")

        tree_box = ttk.Frame(left, style="Card.TFrame")
        tree_box.pack(fill="both", expand=True, pady=(10, 0))

        self.tree = ttk.Treeview(
            tree_box,
            columns=("no", "name", "pages"),
            show="headings",
            selectmode="extended",
        )
        self.tree.heading("no", text="#")
        self.tree.heading("name", text="Nama file")
        self.tree.heading("pages", text="Hal.")
        self.tree.column("no", width=30, anchor="center", stretch=False)
        self.tree.column("name", width=150, anchor="w")
        self.tree.column("pages", width=42, anchor="center", stretch=False)

        # Dukung pengurutan: klik-drag baris untuk memindah posisi.
        self._drag_item = None
        self.tree.bind("<ButtonPress-1>", self._on_drag_start)
        self.tree.bind("<B1-Motion>", self._on_drag_motion)
        self.tree.bind("<ButtonRelease-1>", self._on_drag_release)

        tree_scroll = ttk.Scrollbar(
            tree_box, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        file_buttons = ttk.Frame(left, style="Card.TFrame")
        file_buttons.pack(fill="x", pady=(8, 0))

        ttk.Button(
            file_buttons,
            text="＋  Tambah file",
            style="Main.TButton",
            command=self.add_files,
        ).pack(fill="x")

        second_row = ttk.Frame(file_buttons, style="Card.TFrame")
        second_row.pack(fill="x", pady=(5, 0))
        second_row.columnconfigure(0, weight=1)
        second_row.columnconfigure(1, weight=1)
        second_row.columnconfigure(2, weight=1)
        second_row.columnconfigure(3, weight=1)

        ttk.Button(
            second_row,
            text="▲",
            style="Main.TButton",
            command=self.move_selected_up,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 3))

        ttk.Button(
            second_row,
            text="▼",
            style="Main.TButton",
            command=self.move_selected_down,
        ).grid(row=0, column=1, sticky="ew", padx=3)

        ttk.Button(
            second_row,
            text="Hapus",
            style="Main.TButton",
            command=self.remove_selected,
        ).grid(row=0, column=2, sticky="ew", padx=3)

        ttk.Button(
            second_row,
            text="Bersihkan",
            style="Main.TButton",
            command=self.clear_files,
        ).grid(row=0, column=3, sticky="ew", padx=(3, 0))

        ttk.Label(
            left,
            text="Seret file (PDF, gambar, PPT) ke sini. "
            "Geser baris atau pakai ▲▼ untuk mengatur urutan.",
            style="Muted.TLabel",
            wraplength=240,
            justify="left",
        ).pack(anchor="w", pady=(7, 0))

    # ----------------------------------------------------------
    # CENTER — preview
    # ----------------------------------------------------------

    def _build_center_panel(self, content):
        center = ttk.Frame(content, style="Card.TFrame")
        center.pack(side="left", fill="both", expand=True, padx=(0, 8))

        preview_header = ttk.Frame(
            center, style="Card.TFrame", padding=(14, 12, 14, 8)
        )
        preview_header.pack(fill="x")

        ttk.Label(
            preview_header,
            text="Preview presentasi",
            style="Section.TLabel",
        ).pack(side="left")

        self.preview_badge = widgets.badge(preview_header, "6 slide / lembar")
        self.preview_badge.pack(side="left", padx=(10, 0))

        ttk.Label(
            preview_header, text="A4 • Otomatis", style="Muted.TLabel"
        ).pack(side="right")

        preview_container = tk.Frame(center, bg="#E8ECF3")
        preview_container.pack(fill="both", expand=True)

        self.preview_canvas = tk.Canvas(
            preview_container, bg="#E8ECF3", highlightthickness=0
        )
        self.preview_canvas.pack(fill="both", expand=True, padx=18, pady=18)
        self.preview_canvas.bind(
            "<Configure>", lambda event: self.update_preview()
        )

        preview_footer = ttk.Frame(
            center, style="Card.TFrame", padding=(14, 8, 14, 10)
        )
        preview_footer.pack(fill="x")

        self.preview_status = tk.Label(
            preview_footer,
            text="● Preview siap",
            bg="#FFFFFF",
            fg="#2D9A70",
            font=("Segoe UI", 8, "bold"),
        )
        self.preview_status.pack(side="left")

        self.preview_info = ttk.Label(
            preview_footer, text="A4 • Auto Center", style="Muted.TLabel"
        )
        self.preview_info.pack(side="right")

    # ----------------------------------------------------------
    # RIGHT PANEL — pengaturan
    # ----------------------------------------------------------

    def _build_right_panel(self, content):
        right = ttk.Frame(content, style="Card.TFrame", padding=14, width=350)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        settings_header = ttk.Frame(right, style="Card.TFrame")
        settings_header.pack(fill="x")

        ttk.Label(
            settings_header, text="Pengaturan slide", style="Section.TLabel"
        ).pack(side="left")
        ttk.Label(
            settings_header, text="Preset: Otomatis", style="Muted.TLabel"
        ).pack(side="right")

        self._build_grid_controls(right)
        self._build_orientation_control(right)

        ttk.Separator(right).pack(fill="x", pady=13)
        self._build_output_options(right)

        ttk.Separator(right).pack(fill="x", pady=13)
        self._build_valid_status(right)
        self._build_process_button(right)

    def _build_grid_controls(self, right):
        ttk.Label(right, text="Tata letak slide", style="Muted.TLabel").pack(
            anchor="w", pady=(18, 7)
        )

        grid_frame = ttk.Frame(right, style="Card.TFrame")
        grid_frame.pack(fill="x")
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=0)
        grid_frame.columnconfigure(2, weight=1)

        ttk.Label(grid_frame, text="Kolom", style="Muted.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(grid_frame, text="Baris", style="Muted.TLabel").grid(
            row=0, column=2, sticky="w"
        )

        self.cols_var = tk.StringVar(value="3")
        self.rows_var = tk.StringVar(value="2")

        cols_entry = ttk.Entry(grid_frame, textvariable=self.cols_var)
        cols_entry.grid(row=1, column=0, sticky="ew", pady=(3, 0))

        tk.Label(
            grid_frame,
            text="×",
            bg="#FFFFFF",
            fg="#7A8496",
            font=("Segoe UI", 10, "bold"),
        ).grid(row=1, column=1, padx=7)

        rows_entry = ttk.Entry(grid_frame, textvariable=self.rows_var)
        rows_entry.grid(row=1, column=2, sticky="ew", pady=(3, 0))

        cols_entry.bind("<KeyRelease>", lambda e: self.update_preview())
        rows_entry.bind("<KeyRelease>", lambda e: self.update_preview())

    def _build_orientation_control(self, right):
        ttk.Label(right, text="Orientasi", style="Muted.TLabel").pack(
            anchor="w", pady=(16, 4)
        )

        self.orientation_var = tk.StringVar(value=ORIENTATION_LANDSCAPE)

        orientation_cb = ttk.Combobox(
            right,
            textvariable=self.orientation_var,
            values=["Portrait", "Landscape"],
            state="readonly",
        )
        orientation_cb.pack(fill="x")
        orientation_cb.bind(
            "<<ComboboxSelected>>", lambda e: self.update_preview()
        )

    def _build_output_options(self, right):
        ttk.Label(right, text="OPSI OUTPUT", style="Muted.TLabel").pack(
            anchor="w"
        )

        self.border_var = tk.BooleanVar(value=True)
        self.number_var = tk.BooleanVar(value=False)
        self.duplex_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(
            right,
            text="Tampilkan kotak pada preview",
            variable=self.border_var,
            command=self.update_preview,
        ).pack(anchor="w", pady=(7, 2))
        ttk.Label(
            right,
            text="Kotak hanya untuk membantu melihat posisi slide.",
            style="Muted.TLabel",
        ).pack(anchor="w", padx=(24, 0))

        ttk.Checkbutton(
            right,
            text="Tampilkan nomor slide pada PDF",
            variable=self.number_var,
        ).pack(anchor="w", pady=(9, 2))
        ttk.Label(
            right,
            text="Nomor ditambahkan pada bagian atas slide.",
            style="Muted.TLabel",
        ).pack(anchor="w", padx=(24, 0))

        ttk.Checkbutton(
            right,
            text="Bolak-balik (duplex)",
            variable=self.duplex_var,
        ).pack(anchor="w", pady=(9, 2))
        ttk.Label(
            right,
            text="Tambahkan halaman kosong bila hasil tiap file ganjil, "
            "agar tiap file mulai di halaman depan.",
            style="Muted.TLabel",
            wraplength=240,
            justify="left",
        ).pack(anchor="w", padx=(24, 0))

    def _build_process_button(self, right):
        # Nama file hasil default (dipakai saat dialog simpan); tidak lagi
        # ditampilkan sebagai input — user memilih nama langsung di dialog simpan.
        self.output_name_var = tk.StringVar(value="Hasil_Gabungan.pdf")

        # Folder hasil terakhir (agar nomor unik bisa dihitung sebelum dialog,
        # dan naik berkelanjutan tiap kali "JADIKAN PDF" diklik).
        self.last_output_dir = None

        self.process_button = ttk.Button(
            right,
            text="📄  JADIKAN PDF",
            style="Process.TButton",
            command=self.start_process,
        )
        self.process_button.pack(fill="x", ipady=6, pady=(4, 0))


    def _build_valid_status(self, right):
        status_valid = tk.Frame(right, bg="#E9F8F1", padx=9, pady=8)
        status_valid.pack(fill="x", pady=(14, 10))

        tk.Label(
            status_valid,
            text="✓",
            bg="#E9F8F1",
            fg="#29966D",
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left")

        tk.Label(
            status_valid,
            text="Semua halaman siap diproses.",
            bg="#E9F8F1",
            fg="#2E8A68",
            font=("Segoe UI", 8, "bold"),
        ).pack(side="left", padx=(6, 0))

    # ----------------------------------------------------------
    # BOTTOM — status + progress + tombol proses
    # ----------------------------------------------------------

    def _build_bottom(self, root_frame):
        bottom = ttk.Frame(root_frame)
        bottom.pack(fill="x", pady=(10, 0))

        status_box = ttk.Frame(bottom)
        status_box.pack(side="left", fill="x", expand=True, padx=(0, 15))

        self.status_var = tk.StringVar(
            value="Siap. Tambahkan file untuk memulai."
        )
        ttk.Label(
            status_box,
            textvariable=self.status_var,
            background="#F4F6FA",
            foreground="#4B5563",
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w")

        self.progress = ttk.Progressbar(
            status_box,
            mode="determinate",
            maximum=100,
            style="Horizontal.TProgressbar",
        )
        self.progress.pack(fill="x", pady=(5, 0))


    # ==========================================================
    # DRAG & DROP
    # ==========================================================

    def enable_drag_drop(self, widget):
        try:
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", self.handle_drop)
        except Exception:
            pass

        try:
            children = widget.winfo_children()
        except Exception:
            children = []

        for child in children:
            self.enable_drag_drop(child)

    def handle_drop(self, event):
        try:
            paths_raw = self.root.tk.splitlist(event.data)
        except Exception:
            paths_raw = [event.data]

        paths = []
        for path in paths_raw:
            path = path.strip()
            if path.startswith("{") and path.endswith("}"):
                path = path[1:-1]

            if os.path.isfile(path) and file_kind(path) != "unknown":
                paths.append(path)

        if paths:
            self.add_dropped_files(paths)

        return "break"

    # ==========================================================
    # FILE MANAGEMENT
    # ==========================================================

    def add_dropped_files(self, paths):
        existing = {normalize_key(p) for p in self.files}
        added = 0

        for path in paths:
            key = normalize_key(path)
            if key in existing:
                continue

            if not self._is_readable(path):
                continue

            self.files.append(path)
            existing.add(key)
            added += 1

        self.refresh_tree()

        if added:
            self.status_var.set(f"{added} file berhasil ditambahkan.")

    @staticmethod
    def _is_readable(path):
        """True bila file valid & bisa dibaca.

        PDF & gambar divalidasi dengan PyMuPDF; file office cukup dicek
        keberadaannya (validasi penuh terjadi saat konversi).
        """
        if not os.path.isfile(path):
            return False

        kind = file_kind(path)
        if kind in ("pdf", "image"):
            try:
                doc = pymupdf.open(path)
                doc.close()
            except Exception:
                return False

        return True

    def add_files(self):
        paths = filedialog.askopenfilenames(
            title="Pilih file (PDF, gambar, atau PowerPoint)",
            filetypes=_OPEN_FILETYPES,
        )
        if paths:
            self.add_dropped_files(paths)

    def refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        total_pages = 0
        for index, path in enumerate(self.files, start=1):
            pages = self._count_pages(path)

            self.tree.insert(
                "",
                "end",
                values=(index, os.path.basename(path), pages),
            )

            if isinstance(pages, int):
                total_pages += pages

        self.file_count_var.set(
            f"{len(self.files)} file • {total_pages} halaman"
        )

    # ----------------------------------------------------------
    # PENGURUTAN (drag baris + tombol ▲▼)
    # ----------------------------------------------------------

    def _selected_indexes(self):
        """Indeks (0-based) baris terpilih, urut menaik."""
        return sorted(self.tree.index(item) for item in self.tree.selection())

    def move_selected_up(self):
        self._move_selected(-1)

    def move_selected_down(self):
        self._move_selected(1)

    def _move_selected(self, direction):
        """Geser semua baris terpilih satu langkah ke atas (-1) / bawah (+1).

        Bila salah satu baris mencapai ujung, tak ada yang digeser agar blok
        tetap kompak.
        """
        indexes = self._selected_indexes()
        if not indexes:
            messagebox.showwarning(
                "Belum Dipilih", "Pilih file yang ingin dipindahkan."
            )
            return

        if direction < 0 and indexes[0] == 0:
            return
        if direction > 0 and indexes[-1] == len(self.files) - 1:
            return

        # Geser mulai dari yang paling ujung sesuai arah agar tidak bertumbukan.
        ordered = indexes if direction < 0 else list(reversed(indexes))
        for i in ordered:
            self.files[i], self.files[i + direction] = (
                self.files[i + direction],
                self.files[i],
            )

        self.refresh_tree()
        self._reselect(indexes, direction)

    def _reselect(self, indexes, direction):
        """Pilih kembali baris yang baru dipindah (posisi sudah bergeser)."""
        children = self.tree.get_children()
        new_indexes = sorted(i + direction for i in indexes)
        items = [children[i] for i in new_indexes if 0 <= i < len(children)]
        if items:
            self.tree.selection_set(items)
            if direction < 0:
                self.tree.see(items[0])
            else:
                self.tree.see(items[-1])

    def _on_drag_start(self, event):
        item = self.tree.identify_row(event.y)
        if item and item not in self.tree.selection():
            self.tree.selection_set(item)
        self._drag_item = item or None

    def _on_drag_motion(self, event):
        if not self._drag_item:
            return
        target = self.tree.identify_row(event.y)
        if not target or target == self._drag_item:
            return

        src_idx = self.tree.index(self._drag_item)
        dst_idx = self.tree.index(target)

        # Pindahkan entri di self.files lalu bangun ulang tampilan.
        path = self.files.pop(src_idx)
        self.files.insert(dst_idx, path)

        self.refresh_tree()
        children = self.tree.get_children()
        if dst_idx < len(children):
            moved = children[dst_idx]
            self.tree.selection_set(moved)
            self.tree.see(moved)
            self._drag_item = moved

    def _on_drag_release(self, event):
        self._drag_item = None

    @staticmethod
    def _count_pages(path):
        """Perkiraan jumlah halaman (int) atau '?' bila tidak bisa dihitung."""
        kind = file_kind(path)

        if kind == "image":
            return 1

        if kind == "pdf":
            try:
                doc = pymupdf.open(path)
                pages = len(doc)
                doc.close()
                return pages
            except Exception:
                return "?"

        if kind == "ppt":
            try:
                from pptx import Presentation

                return len(Presentation(path).slides)
            except Exception:
                return "?"

        return "?"

    def remove_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(
                "Belum Dipilih", "Pilih file yang ingin dihapus."
            )
            return

        indexes = [self.tree.index(item) for item in selected]
        for i in sorted(indexes, reverse=True):
            del self.files[i]

        self.refresh_tree()

    def clear_files(self):
        if not self.files:
            return

        if messagebox.askyesno("Konfirmasi", "Hapus semua file dari daftar?"):
            self.files.clear()
            self.refresh_tree()
            self.status_var.set("Daftar file telah dibersihkan.")

    # ==========================================================
    # PREVIEW
    # ==========================================================

    def update_preview(self):
        if not hasattr(self, "preview_canvas"):
            return

        canvas = self.preview_canvas
        canvas.delete("all")

        cols, rows = self._parse_grid()
        slides_per_page = min(cols * rows, MAX_SLIDES_PER_PAGE)

        # A4 dalam mm (untuk skala preview).
        pw, ph = 210, 297
        if self.orientation_var.get() == ORIENTATION_LANDSCAPE:
            pw, ph = ph, pw

        canvas.update_idletasks()
        cw = max(300, canvas.winfo_width())
        ch = max(300, canvas.winfo_height())

        scale = min((cw - 45) / pw, (ch - 45) / ph)
        w = pw * scale
        h = ph * scale

        x0 = (cw - w) / 2
        y0 = (ch - h) / 2
        x1 = x0 + w
        y1 = y0 + h

        # Shadow + kertas A4.
        canvas.create_rectangle(
            x0 + 5, y0 + 5, x1 + 5, y1 + 5, fill="#CBD1DC", outline=""
        )
        canvas.create_rectangle(
            x0, y0, x1, y1, fill="#FFFFFF", outline="#B7BFCC"
        )

        margin = 3 / pw * w
        gap = 3 / pw * w
        usable_w = w - 2 * margin - gap * (cols - 1)
        usable_h = h - 2 * margin - gap * (rows - 1)
        cell_w = usable_w / cols
        cell_h = usable_h / rows

        for i in range(slides_per_page):
            row = i // cols
            col = i % cols

            sx0 = x0 + margin + col * (cell_w + gap)
            sy0 = y0 + margin + row * (cell_h + gap)
            sx1 = sx0 + cell_w
            sy1 = sy0 + cell_h

            if self.border_var.get():
                canvas.create_rectangle(
                    sx0, sy0, sx1, sy1,
                    fill="#FBFCFE", outline="#AAB3C2", width=1,
                )
            else:
                canvas.create_rectangle(
                    sx0, sy0, sx1, sy1, fill="#FBFCFE", outline=""
                )

            # Garis dekoratif ungu.
            line_y = sy0 + cell_h * 0.18
            canvas.create_line(
                sx0 + cell_w * 0.10, line_y,
                sx0 + cell_w * 0.45, line_y,
                fill="#6868DC", width=2,
            )

            font_size = max(7, min(12, int(min(cell_w, cell_h) / 15)))
            canvas.create_text(
                (sx0 + sx1) / 2,
                (sy0 + sy1) / 2,
                text=str(i + 1),
                fill="#8A94A6",
                font=("Segoe UI", font_size, "bold"),
            )

        self.preview_badge.config(text=f"{slides_per_page} slide / lembar")
        self.preview_info.config(
            text=(
                f"{PAPER_SIZE} • {self.orientation_var.get()} • Auto Center"
            )
        )

    def _parse_grid(self):
        """Baca cols/rows dari entry; fallback & clamp agar selalu valid."""
        try:
            cols = int(self.cols_var.get())
            rows = int(self.rows_var.get())
        except ValueError:
            cols, rows = 3, 2

        cols = max(MIN_GRID, min(MAX_GRID, cols))
        rows = max(MIN_GRID, min(MAX_GRID, rows))
        return cols, rows

    # ==========================================================
    # VALIDASI
    # ==========================================================

    def validate_settings(self):
        try:
            cols = int(self.cols_var.get())
            rows = int(self.rows_var.get())
        except ValueError:
            raise ValueError("Kolom dan baris harus berupa angka.")

        if cols < MIN_GRID or cols > MAX_GRID:
            raise ValueError("Kolom harus antara 1 sampai 100.")

        if rows < MIN_GRID or rows > MAX_GRID:
            raise ValueError("Baris harus antara 1 sampai 100.")

        slides_per_page = cols * rows
        if slides_per_page > MAX_SLIDES_PER_PAGE:
            raise ValueError("Jumlah slide per halaman maksimal 100.")

        return cols, rows, slides_per_page

    # ==========================================================
    # PROSES
    # ==========================================================

    def _default_output_dir(self):
        """Folder default untuk hasil: folder file sumber pertama, atau Documents."""
        if self.files:
            folder = os.path.dirname(os.path.abspath(self.files[0]))
            if os.path.isdir(folder):
                return folder
        return os.path.expanduser("~")

    def start_process(self):
        if not self.files:
            messagebox.showwarning(
                "Belum Ada File", "Tambahkan minimal satu file."
            )
            return

        try:
            self.validate_settings()
        except ValueError as e:
            messagebox.showerror("Pengaturan Tidak Valid", str(e))
            return

        filename = self.output_name_var.get().strip() or "Hasil_Gabungan.pdf"
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"

        # Folder target: pakai folder hasil terakhir, atau folder file sumber,
        # atau Documents. Dipakai untuk menghitung nama ber-nomor SEBELUM dialog
        # dibuka, sehingga dialog sudah menawarkan nama unik (tanpa replace).
        target_dir = self.last_output_dir
        if not target_dir or not os.path.isdir(target_dir):
            target_dir = self._default_output_dir()

        # Nama dasar tanpa nomor lama, mis. "Hasil_Gabungan (2).pdf" → "Hasil_Gabungan".
        base_stem, _ = os.path.splitext(filename)
        base_stem = _strip_trailing_number(base_stem)
        initial_name = os.path.basename(
            unique_path(os.path.join(target_dir, base_stem + ".pdf"))
        )

        output_path = filedialog.asksaveasfilename(
            title="Simpan PDF hasil",
            initialfile=initial_name,
            initialdir=target_dir,
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")],
        )

        if not output_path:
            self.status_var.set("Penyimpanan dibatalkan.")
            return

        if not output_path.lower().endswith(".pdf"):
            output_path += ".pdf"

        # Catat folder yang dipilih untuk klik berikutnya (nomor naik berkelanjutan).
        self.last_output_dir = os.path.dirname(os.path.abspath(output_path))

        # Bila user pindah folder / nama sudah ada (bukan file sumber), pastikan
        # tetap unik agar tidak ada pertanyaan replace & tidak menimpa file lama.
        is_source = normalize_key(output_path) in {
            normalize_key(p) for p in self.files
        }
        if os.path.exists(output_path) and not is_source:
            output_path = unique_path(output_path)

        self.output_name_var.set(os.path.basename(output_path))

        overwrite_source = False
        if is_source:
            if not messagebox.askyesno(
                "Timpa File Sumber?",
                "File hasil bernama SAMA dengan salah satu file sumber:\n\n"
                f"{os.path.basename(output_path)}\n\n"
                "File sumber tersebut akan DITIMPA (diganti) dengan hasil.\n"
                "Lanjutkan?",
                icon="warning",
            ):
                self.status_var.set("Dibatalkan — nama sama dengan file sumber.")
                return
            overwrite_source = True

        self.process_button.config(state="disabled")
        self.progress["value"] = 0
        self.status_var.set("Memulai proses...")

        threading.Thread(
            target=self._run_pipeline,
            args=(output_path, overwrite_source),
            daemon=True,
        ).start()

    def _run_pipeline(self, output_path, overwrite_source=False):
        """Dijalankan di worker thread; semua update UI via root.after."""
        cols, rows, _ = self.validate_settings()

        def on_status(text):
            self.root.after(0, lambda: self.status_var.set(text))

        def on_progress(value):
            self.root.after(0, lambda: self.progress.configure(value=value))

        try:
            process_all(
                input_paths=list(self.files),
                output_path=output_path,
                cols=cols,
                rows=rows,
                orientation=self.orientation_var.get(),
                number_slides=self.number_var.get(),
                on_status=on_status,
                on_progress=on_progress,
                allow_overwrite_source=overwrite_source,
                pad_even=self.duplex_var.get(),
            )
            self.root.after(0, lambda: self.finished(output_path))
        except Exception as e:
            self.root.after(0, lambda err=str(e): self.failed(err))

    # ==========================================================
    # CALLBACK SELESAI / GAGAL
    # ==========================================================

    def finished(self, output_path):
        self.process_button.config(state="normal")
        self.progress["value"] = 100

        size_text = format_size(file_size(output_path))
        self.status_var.set(f"SELESAI — PDF dibuat ({size_text}).")

        if messagebox.askyesno(
            "Berhasil",
            "PDF berhasil dibuat!\n\n"
            f"{output_path}\n"
            f"Ukuran file: {size_text}\n\n"
            "Buka folder hasil?",
        ):
            open_folder(os.path.dirname(output_path))

    def failed(self, error):
        self.process_button.config(state="normal")
        self.status_var.set("Gagal memproses.")
        messagebox.showerror(
            "Gagal Memproses", f"Terjadi kesalahan:\n\n{error}"
        )







