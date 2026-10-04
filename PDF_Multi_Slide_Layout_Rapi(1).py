import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import fitz
import os
import threading


# ============================================================
# DRAG & DROP
# ============================================================

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False


# ============================================================
# PDF MULTI SLIDE PRO
# ============================================================

class PDFMultiSlidePro:

    # ========================================================
    # PENGATURAN OTOMATIS
    # Tidak ditampilkan di UI
    # ========================================================

    PAPER_SIZE = "A4"
    MARGIN_MM = 3
    GAP_MM = 3


    # ========================================================
    # INIT
    # ========================================================

    def __init__(self, root):

        self.root = root

        self.root.title(
            "PDF ke Slide • Multi Slide Pro"
        )

        self.root.geometry(
            "1400x850"
        )

        self.root.minsize(
            1180,
            720
        )

        self.root.configure(
            bg="#F4F6FA"
        )

        self.files = []

        self.create_styles()
        self.create_ui()

        if DND_AVAILABLE:
            self.enable_drag_drop(
                self.root
            )

        self.update_preview()


    # ========================================================
    # STYLE
    # ========================================================

    def create_styles(self):

        style = ttk.Style()

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass


        style.configure(
            "TFrame",
            background="#F4F6FA"
        )


        style.configure(
            "Card.TFrame",
            background="#FFFFFF"
        )


        style.configure(
            "TLabel",
            background="#FFFFFF",
            foreground="#172033",
            font=("Segoe UI", 9)
        )


        style.configure(
            "Title.TLabel",
            background="#F4F6FA",
            foreground="#172033",
            font=("Segoe UI", 23, "bold")
        )


        style.configure(
            "Subtitle.TLabel",
            background="#F4F6FA",
            foreground="#6B7280",
            font=("Segoe UI", 10)
        )


        style.configure(
            "Section.TLabel",
            background="#FFFFFF",
            foreground="#172033",
            font=("Segoe UI", 11, "bold")
        )


        style.configure(
            "Muted.TLabel",
            background="#FFFFFF",
            foreground="#7A8496",
            font=("Segoe UI", 8)
        )


        style.configure(
            "Main.TButton",
            font=("Segoe UI", 8, "bold"),
            padding=(7, 6)
        )


        style.configure(
            "Process.TButton",
            font=("Segoe UI", 11, "bold"),
            padding=(20, 11),
            foreground="white",
            background="#5656D9",
            borderwidth=0
        )


        style.map(
            "Process.TButton",
            background=[
                ("active", "#4545C7"),
                ("pressed", "#3E3EB8")
            ]
        )


        style.configure(
            "TEntry",
            padding=6
        )


        style.configure(
            "TCombobox",
            padding=5
        )


        style.configure(
            "TCheckbutton",
            background="#FFFFFF",
            foreground="#172033",
            font=("Segoe UI", 9)
        )


        style.configure(
            "Treeview",
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
            foreground="#172033",
            rowheight=29,
            borderwidth=0,
            font=("Segoe UI", 8)
        )


        style.configure(
            "Treeview.Heading",
            background="#F3F5F9",
            foreground="#5C6678",
            font=("Segoe UI", 8, "bold"),
            relief="flat"
        )


        style.map(
            "Treeview",
            background=[
                ("selected", "#E8E8FF")
            ],
            foreground=[
                ("selected", "#3535A0")
            ]
        )


        style.configure(
            "Horizontal.TProgressbar",
            troughcolor="#E7EAF1",
            background="#5656D9",
            borderwidth=0,
            thickness=8
        )


    # ========================================================
    # UI
    # ========================================================

    def create_ui(self):

        root_frame = ttk.Frame(
            self.root,
            padding=(22, 18, 22, 14)
        )

        root_frame.pack(
            fill="both",
            expand=True
        )


        # ====================================================
        # HEADER
        # ====================================================

        header = ttk.Frame(
            root_frame
        )

        header.pack(
            fill="x",
            pady=(0, 14)
        )


        title_line = ttk.Frame(
            header
        )

        title_line.pack(
            fill="x"
        )


        ttk.Label(
            title_line,
            text="Ubah PDF jadi presentasi",
            style="Title.TLabel"
        ).pack(
            side="left"
        )


        badge = tk.Label(
            title_line,
            text="  Siap dipresentasikan  ",
            bg="#E5F6EF",
            fg="#2E8A68",
            font=("Segoe UI", 8, "bold"),
            padx=4,
            pady=3
        )

        badge.pack(
            side="left",
            padx=(12, 0),
            pady=(5, 0)
        )


        ttk.Label(
            header,
            text=(
                "Susun PDF menjadi beberapa slide "
                "dalam satu halaman dengan layout yang rapi."
            ),
            style="Subtitle.TLabel"
        ).pack(
            anchor="w",
            pady=(3, 0)
        )


        # ====================================================
        # CONTENT
        # ====================================================

        content = ttk.Frame(
            root_frame
        )

        content.pack(
            fill="both",
            expand=True
        )


        # ====================================================
        # LEFT PANEL
        # ====================================================

        left = ttk.Frame(
            content,
            style="Card.TFrame",
            padding=12,
            width=285
        )

        left.pack(
            side="left",
            fill="y",
            padx=(0, 8)
        )

        left.pack_propagate(False)


        ttk.Label(
            left,
            text="Dokumen sumber",
            style="Section.TLabel"
        ).pack(
            anchor="w"
        )


        self.file_count_var = tk.StringVar(
            value="0 file"
        )


        ttk.Label(
            left,
            textvariable=self.file_count_var,
            style="Muted.TLabel"
        ).pack(
            anchor="w",
            pady=(2, 8)
        )


        # ====================================================
        # UPLOAD AREA
        # ====================================================

        upload_box = tk.Frame(
            left,
            bg="#FAFBFE",
            highlightbackground="#A5A5E8",
            highlightcolor="#A5A5E8",
            highlightthickness=1,
            height=110
        )

        upload_box.pack(
            fill="x",
            pady=(0, 10)
        )

        upload_box.pack_propagate(False)


        tk.Label(
            upload_box,
            text="↑",
            bg="#E9E9FF",
            fg="#5656D9",
            font=("Segoe UI", 18, "bold"),
            width=3
        ).pack(
            pady=(9, 3)
        )


        tk.Label(
            upload_box,
            text="Tarik PDF ke area ini",
            bg="#FAFBFE",
            fg="#172033",
            font=("Segoe UI", 9, "bold")
        ).pack()


        tk.Label(
            upload_box,
            text="atau pilih file dari perangkat",
            bg="#FAFBFE",
            fg="#7A8496",
            font=("Segoe UI", 7)
        ).pack(
            pady=(1, 4)
        )


        tk.Button(
            upload_box,
            text="＋  Unggah PDF",
            command=self.add_files,
            bg="#FFFFFF",
            fg="#252B3A",
            activebackground="#F0F0FF",
            relief="solid",
            bd=1,
            font=("Segoe UI", 8, "bold"),
            padx=8,
            pady=3
        ).pack()


        # ====================================================
        # DAFTAR SUMBER
        # ====================================================

        ttk.Label(
            left,
            text="DAFTAR SUMBER",
            style="Muted.TLabel"
        ).pack(
            anchor="w",
            pady=(1, 5)
        )


        tree_box = ttk.Frame(
            left,
            style="Card.TFrame"
        )

        tree_box.pack(
            fill="both",
            expand=True
        )


        self.tree = ttk.Treeview(
            tree_box,
            columns=("name", "pages"),
            show="headings",
            selectmode="extended"
        )


        self.tree.heading(
            "name",
            text="Nama file"
        )


        self.tree.heading(
            "pages",
            text="Hal."
        )


        self.tree.column(
            "name",
            width=175,
            anchor="w"
        )


        self.tree.column(
            "pages",
            width=45,
            anchor="center",
            stretch=False
        )


        tree_scroll = ttk.Scrollbar(
            tree_box,
            orient="vertical",
            command=self.tree.yview
        )


        self.tree.configure(
            yscrollcommand=tree_scroll.set
        )


        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )


        tree_scroll.pack(
            side="right",
            fill="y"
        )


        # ====================================================
        # TOMBOL FILE
        # ====================================================

        file_buttons = ttk.Frame(
            left,
            style="Card.TFrame"
        )

        file_buttons.pack(
            fill="x",
            pady=(8, 0)
        )


        ttk.Button(
            file_buttons,
            text="＋  Tambah PDF",
            style="Main.TButton",
            command=self.add_files
        ).pack(
            fill="x"
        )


        second_row = ttk.Frame(
            file_buttons,
            style="Card.TFrame"
        )

        second_row.pack(
            fill="x",
            pady=(5, 0)
        )


        second_row.columnconfigure(
            0,
            weight=1
        )


        second_row.columnconfigure(
            1,
            weight=1
        )


        ttk.Button(
            second_row,
            text="Hapus",
            style="Main.TButton",
            command=self.remove_selected
        ).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 3)
        )


        ttk.Button(
            second_row,
            text="Bersihkan",
            style="Main.TButton",
            command=self.clear_files
        ).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(3, 0)
        )


        ttk.Label(
            left,
            text="Seret PDF ke area mana pun untuk menambahkannya.",
            style="Muted.TLabel"
        ).pack(
            anchor="w",
            pady=(7, 0)
        )


        # ====================================================
        # CENTER PREVIEW
        # ====================================================

        center = ttk.Frame(
            content,
            style="Card.TFrame"
        )

        center.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 8)
        )


        preview_header = ttk.Frame(
            center,
            style="Card.TFrame",
            padding=(14, 12, 14, 8)
        )

        preview_header.pack(
            fill="x"
        )


        ttk.Label(
            preview_header,
            text="Preview presentasi",
            style="Section.TLabel"
        ).pack(
            side="left"
        )


        self.preview_badge = tk.Label(
            preview_header,
            text="6 slide / lembar",
            bg="#EBEBFF",
            fg="#4E4EBC",
            font=("Segoe UI", 8, "bold"),
            padx=9,
            pady=4
        )

        self.preview_badge.pack(
            side="left",
            padx=(10, 0)
        )


        ttk.Label(
            preview_header,
            text="A4 • Otomatis",
            style="Muted.TLabel"
        ).pack(
            side="right"
        )


        preview_container = tk.Frame(
            center,
            bg="#E8ECF3"
        )

        preview_container.pack(
            fill="both",
            expand=True
        )


        self.preview_canvas = tk.Canvas(
            preview_container,
            bg="#E8ECF3",
            highlightthickness=0
        )


        self.preview_canvas.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=18
        )


        self.preview_canvas.bind(
            "<Configure>",
            lambda event: self.update_preview()
        )


        preview_footer = ttk.Frame(
            center,
            style="Card.TFrame",
            padding=(14, 8, 14, 10)
        )

        preview_footer.pack(
            fill="x"
        )


        self.preview_status = tk.Label(
            preview_footer,
            text="● Preview siap",
            bg="#FFFFFF",
            fg="#2D9A70",
            font=("Segoe UI", 8, "bold")
        )

        self.preview_status.pack(
            side="left"
        )


        self.preview_info = ttk.Label(
            preview_footer,
            text="A4 • Auto Center",
            style="Muted.TLabel"
        )

        self.preview_info.pack(
            side="right"
        )


        # ====================================================
        # RIGHT PANEL
        # ====================================================

        right = ttk.Frame(
            content,
            style="Card.TFrame",
            padding=14,
            width=350
        )

        right.pack(
            side="right",
            fill="y"
        )

        right.pack_propagate(False)


        settings_header = ttk.Frame(
            right,
            style="Card.TFrame"
        )

        settings_header.pack(
            fill="x"
        )


        ttk.Label(
            settings_header,
            text="Pengaturan slide",
            style="Section.TLabel"
        ).pack(
            side="left"
        )


        ttk.Label(
            settings_header,
            text="Preset: Otomatis",
            style="Muted.TLabel"
        ).pack(
            side="right"
        )


        # ====================================================
        # GRID
        # ====================================================

        ttk.Label(
            right,
            text="Tata letak slide",
            style="Muted.TLabel"
        ).pack(
            anchor="w",
            pady=(18, 7)
        )


        grid_frame = ttk.Frame(
            right,
            style="Card.TFrame"
        )

        grid_frame.pack(
            fill="x"
        )


        grid_frame.columnconfigure(
            0,
            weight=1
        )


        grid_frame.columnconfigure(
            1,
            weight=0
        )


        grid_frame.columnconfigure(
            2,
            weight=1
        )


        ttk.Label(
            grid_frame,
            text="Kolom",
            style="Muted.TLabel"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )


        ttk.Label(
            grid_frame,
            text="Baris",
            style="Muted.TLabel"
        ).grid(
            row=0,
            column=2,
            sticky="w"
        )


        self.cols_var = tk.StringVar(
            value="3"
        )


        self.rows_var = tk.StringVar(
            value="2"
        )


        cols_entry = ttk.Entry(
            grid_frame,
            textvariable=self.cols_var
        )


        cols_entry.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(3, 0)
        )


        tk.Label(
            grid_frame,
            text="×",
            bg="#FFFFFF",
            fg="#7A8496",
            font=("Segoe UI", 10, "bold")
        ).grid(
            row=1,
            column=1,
            padx=7
        )


        rows_entry = ttk.Entry(
            grid_frame,
            textvariable=self.rows_var
        )


        rows_entry.grid(
            row=1,
            column=2,
            sticky="ew",
            pady=(3, 0)
        )


        cols_entry.bind(
            "<KeyRelease>",
            lambda e: self.update_preview()
        )


        rows_entry.bind(
            "<KeyRelease>",
            lambda e: self.update_preview()
        )


        # ====================================================
        # ORIENTASI
        # ====================================================

        ttk.Label(
            right,
            text="Orientasi",
            style="Muted.TLabel"
        ).pack(
            anchor="w",
            pady=(16, 4)
        )


        self.orientation_var = tk.StringVar(
            value="Landscape"
        )


        orientation_cb = ttk.Combobox(
            right,
            textvariable=self.orientation_var,
            values=[
                "Portrait",
                "Landscape"
            ],
            state="readonly"
        )


        orientation_cb.pack(
            fill="x"
        )


        orientation_cb.bind(
            "<<ComboboxSelected>>",
            lambda e: self.update_preview()
        )


        ttk.Separator(
            right
        ).pack(
            fill="x",
            pady=13
        )


        # ====================================================
        # OUTPUT
        # ====================================================

        ttk.Label(
            right,
            text="OPSI OUTPUT",
            style="Muted.TLabel"
        ).pack(
            anchor="w"
        )


        self.border_var = tk.BooleanVar(
            value=True
        )


        self.number_var = tk.BooleanVar(
            value=False
        )


        ttk.Checkbutton(
            right,
            text="Tampilkan kotak pada preview",
            variable=self.border_var,
            command=self.update_preview
        ).pack(
            anchor="w",
            pady=(7, 2)
        )


        ttk.Label(
            right,
            text="Kotak hanya untuk membantu melihat posisi slide.",
            style="Muted.TLabel"
        ).pack(
            anchor="w",
            padx=(24, 0)
        )


        ttk.Checkbutton(
            right,
            text="Tampilkan nomor slide pada PDF",
            variable=self.number_var
        ).pack(
            anchor="w",
            pady=(9, 2)
        )


        ttk.Label(
            right,
            text="Nomor ditambahkan pada bagian atas slide.",
            style="Muted.TLabel"
        ).pack(
            anchor="w",
            padx=(24, 0)
        )


        ttk.Separator(
            right
        ).pack(
            fill="x",
            pady=13
        )


        # ====================================================
        # NAMA FILE
        # ====================================================

        ttk.Label(
            right,
            text="NAMA FILE HASIL",
            style="Muted.TLabel"
        ).pack(
            anchor="w"
        )


        self.output_name_var = tk.StringVar(
            value="Hasil_Gabungan.pdf"
        )


        ttk.Entry(
            right,
            textvariable=self.output_name_var
        ).pack(
            fill="x",
            pady=(6, 0)
        )


        ttk.Label(
            right,
            text="Nama ini digunakan sebagai nama awal saat menyimpan.",
            style="Muted.TLabel"
        ).pack(
            anchor="w",
            pady=(4, 0)
        )


        # ====================================================
        # STATUS VALID
        # ====================================================

        status_valid = tk.Frame(
            right,
            bg="#E9F8F1",
            padx=9,
            pady=8
        )


        status_valid.pack(
            fill="x",
            pady=(14, 10)
        )


        tk.Label(
            status_valid,
            text="✓",
            bg="#E9F8F1",
            fg="#29966D",
            font=("Segoe UI", 11, "bold")
        ).pack(
            side="left"
        )


        tk.Label(
            status_valid,
            text="Semua halaman siap diproses.",
            bg="#E9F8F1",
            fg="#2E8A68",
            font=("Segoe UI", 8, "bold")
        ).pack(
            side="left",
            padx=(6, 0)
        )


        # ====================================================
        # BOTTOM
        # ====================================================

        bottom = ttk.Frame(
            root_frame
        )


        bottom.pack(
            fill="x",
            pady=(10, 0)
        )


        status_box = ttk.Frame(
            bottom
        )


        status_box.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 15)
        )


        self.status_var = tk.StringVar(
            value="Siap. Tambahkan file PDF untuk memulai."
        )


        ttk.Label(
            status_box,
            textvariable=self.status_var,
            background="#F4F6FA",
            foreground="#4B5563",
            font=("Segoe UI", 8, "bold")
        ).pack(
            anchor="w"
        )


        self.progress = ttk.Progressbar(
            status_box,
            mode="determinate",
            maximum=100,
            style="Horizontal.TProgressbar"
        )


        self.progress.pack(
            fill="x",
            pady=(5, 0)
        )


        self.process_button = ttk.Button(
            bottom,
            text="📄  JADIKAN PDF",
            style="Process.TButton",
            command=self.start_process
        )


        self.process_button.pack(
            side="right",
            ipadx=10
        )


    # ========================================================
    # DRAG & DROP
    # ========================================================

    def enable_drag_drop(
        self,
        widget
    ):

        try:

            widget.drop_target_register(
                DND_FILES
            )


            widget.dnd_bind(
                "<<Drop>>",
                self.handle_drop
            )

        except Exception:
            pass


        try:

            children = widget.winfo_children()

        except Exception:

            children = []


        for child in children:

            self.enable_drag_drop(
                child
            )


    def handle_drop(
        self,
        event
    ):

        try:

            paths = self.root.tk.splitlist(
                event.data
            )

        except Exception:

            paths = [
                event.data
            ]


        pdf_paths = []


        for path in paths:

            path = path.strip()


            if (
                path.startswith("{")
                and
                path.endswith("}")
            ):

                path = path[1:-1]


            if (
                os.path.isfile(path)
                and
                path.lower().endswith(".pdf")
            ):

                pdf_paths.append(
                    path
                )


        if pdf_paths:

            self.add_dropped_files(
                pdf_paths
            )


        return "break"


    def add_dropped_files(
        self,
        paths
    ):

        existing = {
            os.path.abspath(
                p
            ).lower()
            for p in self.files
        }


        added = 0


        for path in paths:

            key = os.path.abspath(
                path
            ).lower()


            if key in existing:
                continue


            try:

                doc = fitz.open(
                    path
                )


                doc.close()


                self.files.append(
                    path
                )


                existing.add(
                    key
                )


                added += 1


            except Exception:

                pass


        self.refresh_tree()


        if added:

            self.status_var.set(
                f"{added} PDF berhasil ditambahkan."
            )


    # ========================================================
    # ADD FILES
    # ========================================================

    def add_files(self):

        paths = filedialog.askopenfilenames(

            title="Pilih File PDF",

            filetypes=[
                (
                    "PDF Files",
                    "*.pdf"
                ),
                (
                    "All Files",
                    "*.*"
                )
            ]
        )


        if paths:

            self.add_dropped_files(
                paths
            )


    # ========================================================
    # REFRESH TREE
    # ========================================================

    def refresh_tree(self):

        for item in self.tree.get_children():

            self.tree.delete(
                item
            )


        total_pages = 0


        for path in self.files:

            try:

                doc = fitz.open(
                    path
                )


                pages = len(
                    doc
                )


                doc.close()

            except Exception:

                pages = "?"


            self.tree.insert(
                "",
                "end",
                values=(
                    os.path.basename(path),
                    pages
                )
            )


            if isinstance(
                pages,
                int
            ):

                total_pages += pages


        self.file_count_var.set(
            f"{len(self.files)} file • {total_pages} halaman"
        )


    # ========================================================
    # REMOVE
    # ========================================================

    def remove_selected(self):

        selected = self.tree.selection()


        if not selected:

            messagebox.showwarning(
                "Belum Dipilih",
                "Pilih file yang ingin dihapus."
            )

            return


        indexes = [
            self.tree.index(item)
            for item in selected
        ]


        for i in sorted(
            indexes,
            reverse=True
        ):

            del self.files[i]


        self.refresh_tree()


    # ========================================================
    # CLEAR
    # ========================================================

    def clear_files(self):

        if not self.files:

            return


        if messagebox.askyesno(
            "Konfirmasi",
            "Hapus semua PDF dari daftar?"
        ):

            self.files.clear()


            self.refresh_tree()


            self.status_var.set(
                "Daftar PDF telah dibersihkan."
            )


    # ========================================================
    # PREVIEW
    # ========================================================

    def update_preview(self):

        if not hasattr(
            self,
            "preview_canvas"
        ):

            return


        canvas = self.preview_canvas


        canvas.delete(
            "all"
        )


        try:

            cols = int(
                self.cols_var.get()
            )

            rows = int(
                self.rows_var.get()
            )

        except ValueError:

            cols = 3
            rows = 2


        cols = max(
            1,
            min(
                100,
                cols
            )
        )


        rows = max(
            1,
            min(
                100,
                rows
            )
        )


        slides_per_page = (
            cols *
            rows
        )


        if slides_per_page > 100:

            slides_per_page = 100


        # ====================================================
        # A4
        # ====================================================

        pw = 210
        ph = 297


        if (
            self.orientation_var.get()
            ==
            "Landscape"
        ):

            pw, ph = ph, pw


        canvas.update_idletasks()


        cw = max(
            300,
            canvas.winfo_width()
        )


        ch = max(
            300,
            canvas.winfo_height()
        )


        available_w = cw - 45
        available_h = ch - 45


        scale = min(
            available_w / pw,
            available_h / ph
        )


        w = pw * scale
        h = ph * scale


        x0 = (
            cw - w
        ) / 2


        y0 = (
            ch - h
        ) / 2


        x1 = x0 + w
        y1 = y0 + h


        # ====================================================
        # SHADOW
        # ====================================================

        canvas.create_rectangle(
            x0 + 5,
            y0 + 5,
            x1 + 5,
            y1 + 5,
            fill="#CBD1DC",
            outline=""
        )


        # ====================================================
        # A4 PAPER
        # ====================================================

        canvas.create_rectangle(
            x0,
            y0,
            x1,
            y1,
            fill="#FFFFFF",
            outline="#B7BFCC"
        )


        # ====================================================
        # AUTO 3 MM
        # ====================================================

        margin = (
            3 /
            pw *
            w
        )


        gap = (
            3 /
            pw *
            w
        )


        usable_w = (
            w -
            2 * margin -
            gap * (
                cols - 1
            )
        )


        usable_h = (
            h -
            2 * margin -
            gap * (
                rows - 1
            )
        )


        cell_w = (
            usable_w /
            cols
        )


        cell_h = (
            usable_h /
            rows
        )


        # ====================================================
        # GRID
        # ====================================================

        for i in range(
            slides_per_page
        ):

            row = (
                i //
                cols
            )


            col = (
                i %
                cols
            )


            sx0 = (
                x0 +
                margin +
                col *
                (
                    cell_w +
                    gap
                )
            )


            sy0 = (
                y0 +
                margin +
                row *
                (
                    cell_h +
                    gap
                )
            )


            sx1 = (
                sx0 +
                cell_w
            )


            sy1 = (
                sy0 +
                cell_h
            )


            if self.border_var.get():

                canvas.create_rectangle(
                    sx0,
                    sy0,
                    sx1,
                    sy1,
                    fill="#FBFCFE",
                    outline="#AAB3C2",
                    width=1
                )

            else:

                canvas.create_rectangle(
                    sx0,
                    sy0,
                    sx1,
                    sy1,
                    fill="#FBFCFE",
                    outline=""
                )


            # Garis preview

            line_y = (
                sy0 +
                cell_h *
                0.18
            )


            canvas.create_line(
                sx0 +
                cell_w *
                0.10,

                line_y,

                sx0 +
                cell_w *
                0.45,

                line_y,

                fill="#6868DC",
                width=2
            )


            # Nomor preview

            font_size = max(
                7,
                min(
                    12,
                    int(
                        min(
                            cell_w,
                            cell_h
                        ) / 15
                    )
                )
            )


            canvas.create_text(
                (
                    sx0 +
                    sx1
                ) / 2,

                (
                    sy0 +
                    sy1
                ) / 2,

                text=str(
                    i + 1
                ),

                fill="#8A94A6",

                font=(
                    "Segoe UI",
                    font_size,
                    "bold"
                )
            )


        self.preview_badge.config(
            text=(
                f"{slides_per_page} "
                "slide / lembar"
            )
        )


        self.preview_info.config(
            text=(
                "A4 • "
                f"{self.orientation_var.get()} • "
                "Auto Center"
            )
        )


    # ========================================================
    # VALIDASI
    # ========================================================

    def validate_settings(self):

        try:

            cols = int(
                self.cols_var.get()
            )


            rows = int(
                self.rows_var.get()
            )

        except ValueError:

            raise ValueError(
                "Kolom dan baris harus berupa angka."
            )


        if cols < 1 or cols > 100:

            raise ValueError(
                "Kolom harus antara 1 sampai 100."
            )


        if rows < 1 or rows > 100:

            raise ValueError(
                "Baris harus antara 1 sampai 100."
            )


        slides_per_page = (
            cols *
            rows
        )


        if slides_per_page > 100:

            raise ValueError(
                "Jumlah slide per halaman maksimal 100."
            )


        return (
            cols,
            rows,
            slides_per_page
        )


    # ========================================================
    # START PROCESS
    # ========================================================

    def start_process(self):

        if not self.files:

            messagebox.showwarning(
                "Belum Ada PDF",
                "Tambahkan minimal satu file PDF."
            )

            return


        try:

            self.validate_settings()

        except ValueError as e:

            messagebox.showerror(
                "Pengaturan Tidak Valid",
                str(e)
            )

            return


        filename = (
            self.output_name_var
            .get()
            .strip()
        )


        if not filename:

            filename = (
                "Hasil_Gabungan.pdf"
            )


        if not filename.lower().endswith(
            ".pdf"
        ):

            filename += ".pdf"


        # ====================================================
        # SAVE AS
        # ====================================================

        output_path = filedialog.asksaveasfilename(

            title="Simpan PDF hasil",

            initialfile=filename,

            defaultextension=".pdf",

            filetypes=[
                (
                    "PDF Files",
                    "*.pdf"
                ),
                (
                    "All Files",
                    "*.*"
                )
            ]
        )


        if not output_path:

            self.status_var.set(
                "Penyimpanan dibatalkan."
            )

            return


        if not output_path.lower().endswith(
            ".pdf"
        ):

            output_path += ".pdf"


        self.output_name_var.set(
            os.path.basename(
                output_path
            )
        )


        input_paths = {
            os.path.abspath(
                p
            ).lower()
            for p in self.files
        }


        if (
            os.path.abspath(
                output_path
            ).lower()
            in input_paths
        ):

            messagebox.showerror(
                "Nama File Tidak Valid",
                "File hasil tidak boleh sama dengan file sumber."
            )

            return


        self.process_button.config(
            state="disabled"
        )


        self.progress["value"] = 0


        self.status_var.set(
            "Memulai proses..."
        )


        threading.Thread(
            target=self.process_all,
            args=(
                output_path,
            ),
            daemon=True
        ).start()


    # ========================================================
    # PROCESS ALL
    # ========================================================

    def process_all(
        self,
        output_path
    ):

        temp_files = []


        try:

            total = len(
                self.files
            )


            # =================================================
            # PROSES MASING-MASING PDF SECARA TERPISAH
            # =================================================

            for i, source_path in enumerate(
                self.files,
                1
            ):

                self.set_status(
                    f"Memproses PDF {i} dari {total}: "
                    f"{os.path.basename(source_path)}"
                )


                temp_path = self.make_temp_path(
                    output_path,
                    i
                )


                temp_files.append(
                    temp_path
                )


                self.create_nup_pdf(
                    source_path,
                    temp_path
                )


                self.set_progress(
                    (
                        i /
                        total
                    ) * 80
                )


            # =================================================
            # GABUNGKAN HASIL
            # =================================================

            self.set_status(
                "Menggabungkan semua PDF hasil..."
            )


            final = fitz.open()


            for temp in temp_files:

                part = fitz.open(
                    temp
                )


                final.insert_pdf(
                    part
                )


                part.close()


            final.save(
                output_path,
                garbage=4,
                deflate=True
            )


            final.close()


            # =================================================
            # HAPUS TEMP
            # =================================================

            for temp in temp_files:

                try:

                    os.remove(
                        temp
                    )

                except OSError:

                    pass


            self.set_progress(
                100
            )


            self.root.after(
                0,
                lambda:
                self.finished(
                    output_path
                )
            )


        except Exception as e:

            for temp in temp_files:

                try:

                    os.remove(
                        temp
                    )

                except OSError:

                    pass


            self.root.after(
                0,
                lambda err=str(e):
                self.failed(
                    err
                )
            )


    # ========================================================
    # CREATE NUP PDF
    # ========================================================

    def create_nup_pdf(
        self,
        input_path,
        output_path
    ):

        source = fitz.open(
            input_path
        )


        result = fitz.open()


        # ====================================================
        # A4
        # ====================================================

        width = 595.2756
        height = 841.8898


        if (
            self.orientation_var.get()
            ==
            "Landscape"
        ):

            width, height = (
                height,
                width
            )


        # ====================================================
        # MARGIN 3 MM
        # ====================================================

        margin = (
            3 *
            2.83465
        )


        # ====================================================
        # GAP 3 MM
        # ====================================================

        gap = (
            3 *
            2.83465
        )


        cols = int(
            self.cols_var.get()
        )


        rows = int(
            self.rows_var.get()
        )


        slides_per_page = (
            cols *
            rows
        )


        usable_width = (
            width -
            2 * margin -
            gap * (
                cols - 1
            )
        )


        usable_height = (
            height -
            2 * margin -
            gap * (
                rows - 1
            )
        )


        if (
            usable_width <= 0
            or
            usable_height <= 0
        ):

            source.close()
            result.close()


            raise ValueError(
                "Layout terlalu besar untuk halaman A4."
            )


        cell_width = (
            usable_width /
            cols
        )


        cell_height = (
            usable_height /
            rows
        )


        # ====================================================
        # SETIAP HALAMAN OUTPUT
        # ====================================================

        for start in range(
            0,
            len(source),
            slides_per_page
        ):

            page = result.new_page(
                width=width,
                height=height
            )


            end = min(
                start +
                slides_per_page,
                len(source)
            )


            for position, slide_index in enumerate(
                range(
                    start,
                    end
                )
            ):

                source_page = source[
                    slide_index
                ]


                row = (
                    position //
                    cols
                )


                col = (
                    position %
                    cols
                )


                x0 = (
                    margin +
                    col *
                    (
                        cell_width +
                        gap
                    )
                )


                y0 = (
                    margin +
                    row *
                    (
                        cell_height +
                        gap
                    )
                )


                cell = fitz.Rect(
                    x0,
                    y0,
                    x0 +
                    cell_width,
                    y0 +
                    cell_height
                )


                # =================================================
                # AUTO CENTER
                # =================================================

                source_rect = (
                    source_page.rect
                )


                source_ratio = (
                    source_rect.width /
                    source_rect.height
                )


                cell_ratio = (
                    cell.width /
                    cell.height
                )


                if source_ratio > cell_ratio:

                    new_width = (
                        cell.width
                    )


                    new_height = (
                        new_width /
                        source_ratio
                    )

                else:

                    new_height = (
                        cell.height
                    )


                    new_width = (
                        new_height *
                        source_ratio
                    )


                # Posisi tengah

                centered_x = (
                    x0 +
                    (
                        cell.width -
                        new_width
                    ) / 2
                )


                centered_y = (
                    y0 +
                    (
                        cell.height -
                        new_height
                    ) / 2
                )


                target = fitz.Rect(
                    centered_x,
                    centered_y,
                    centered_x +
                    new_width,
                    centered_y +
                    new_height
                )


                # =================================================
                # MASUKKAN SLIDE
                # =================================================

                page.show_pdf_page(
                    target,
                    source,
                    slide_index,
                    keep_proportion=True
                )


                # =================================================
                # NOMOR SLIDE
                # =================================================

                if self.number_var.get():

                    number_rect = fitz.Rect(
                        x0,
                        y0,
                        x0 +
                        cell_width,
                        y0 +
                        14
                    )


                    page.insert_textbox(
                        number_rect,
                        f"Slide {slide_index + 1}",
                        fontsize=7,
                        fontname="helv",
                        color=(
                            0.2,
                            0.2,
                            0.2
                        ),
                        align=1
                    )


                # =================================================
                # PENTING:
                # TIDAK ADA BORDER PADA PDF HASIL
                # =================================================


        source.close()


        result.save(
            output_path,
            garbage=4,
            deflate=True
        )


        result.close()


    # ========================================================
    # TEMP FILE
    # ========================================================

    def make_temp_path(
        self,
        output_path,
        number
    ):

        folder = os.path.dirname(
            output_path
        )


        base = (
            f"__PDF_MULTI_TEMP_{number}"
        )


        path = os.path.join(
            folder,
            base +
            ".pdf"
        )


        counter = 1


        while os.path.exists(
            path
        ):

            path = os.path.join(
                folder,
                f"{base}_{counter}.pdf"
            )


            counter += 1


        return path


    # ========================================================
    # STATUS
    # ========================================================

    def set_status(
        self,
        text
    ):

        self.root.after(
            0,
            lambda:
            self.status_var.set(
                text
            )
        )


    def set_progress(
        self,
        value
    ):

        self.root.after(
            0,
            lambda:
            self.progress.configure(
                value=value
            )
        )


    # ========================================================
    # SELESAI
    # ========================================================

    def finished(
        self,
        output_path
    ):

        self.process_button.config(
            state="normal"
        )


        self.progress["value"] = 100


        self.status_var.set(
            "SELESAI — PDF berhasil dibuat."
        )


        result = messagebox.askyesno(
            "Berhasil",
            "PDF berhasil dibuat!\n\n"
            f"{output_path}\n\n"
            "Buka folder hasil?"
        )


        if result:

            try:

                os.startfile(
                    os.path.dirname(
                        output_path
                    )
                )

            except Exception:

                pass


    # ========================================================
    # GAGAL
    # ========================================================

    def failed(
        self,
        error
    ):

        self.process_button.config(
            state="normal"
        )


        self.status_var.set(
            "Gagal memproses PDF."
        )


        messagebox.showerror(
            "Gagal Memproses",
            "Terjadi kesalahan:\n\n"
            f"{error}"
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    if DND_AVAILABLE:

        root = TkinterDnD.Tk()

    else:

        root = tk.Tk()


    app = PDFMultiSlidePro(
        root
    )


    root.mainloop()
