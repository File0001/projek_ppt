# ARCHITECTURE.md — PDF Multi Slide Pro

Dokumen arsitektur teknis sistem. Pelengkap `CONTEXT.md`.
Ruang lingkup: aplikasi desktop Python untuk konversi PDF → N-up PDF.
**Status: modular** (`core/` + `ui/` + `utils/` + `main.py`), plus **entry CLI (`cli.py`)**.
Versi monolit lama disimpan sebagai backup. **PyMuPDF diimpor sebagai `pymupdf`.**

---

## 1. Gaya Arsitektur

**Layered monolith → sekarang benar-benar berlapis (separation of concerns).**

Tanggung jawab kini terpisah secara fisik antar folder:

```
┌───────────────────────────────────────────────────────────────┐
│  main.py                 bootstrap (root window + mainloop)    │
├───────────────────────────────────────────────────────────────┤
│  ui/                     VIEW + CONTROLLER (tkinter)           │
│    styles.py  → tema ttk                                       │
│    widgets.py → komponen kustom (badge)                        │
│    app.py     → class PDFMultiSlidePro (event handler + state) │
├───────────────────────────────────────────────────────────────┤
│  core/                   MODEL (headless, TANPA tkinter)       │
│    constants.py → MM_TO_PT, A4, batasan grid, orientasi        │
│    nup.py       → hitung layout + create_nup_pdf()             │
│    pipeline.py  → process_all() via callback status/progress   │
├───────────────────────────────────────────────────────────────┤
│  utils/fs.py             helper lintas layer (path, temp, open)│
└───────────────────────────────────────────────────────────────┘
        ▲                       ▲                      ▲
   tkinter/ttk          UI state (vars)          PyMuPDF / OS
```

**Aturan dependensi (penting):**
- `core/` **tidak boleh** mengimpor `ui/` atau `tkinter` → bisa dipakai CLI/test.
- `ui/` boleh memakai `core/` dan `utils/`.
- `utils/` berdiri sendiri (stdlib saja).
- Komunikasi core→UI **hanya lewat callback** (`on_status`, `on_progress`), bukan referensi widget.

**Prinsip:** KISS, YAGNI, satu fungsi satu tugas, tanpa side-effect tersembunyi di core.


---

## 2. Diagram Komponen

```
                     ┌───────────────┐        ┌───────────────┐
                     │    main.py    │        │    cli.py     │
                     │  (GUI boot)   │        │ (argparse)    │
                     └───────┬───────┘        └───────┬───────┘
                DND_AVAILABLE│                        │
                    ┌────────┴────────┐               │
             TkinterDnD.Tk        tk.Tk               │
                    └────────┬────────┘               │
                             ▼                        │
              ┌──────────────────────────┐            │
              │ ui.app.PDFMultiSlidePro  │            │
              └───┬───────────┬──────────┘            │
                  │           │                       │
     pakai        │           │  pakai                │
                  ▼           ▼                       ▼
   ┌────────────────────┐  ┌──────────────────────────────────┐
   │ ui.styles          │  │ core.pipeline.process_all         │
   │ ui.widgets         │  └───────────┬──────────────────────┘
   └────────────────────┘              │
                                       ▼
                         ┌───────────────────────────┐
                         │ core.nup.create_nup_pdf   │
                         │  (+ compute_grid,         │
                         │   fit_rect_in_cell)       │
                         └───────────┬───────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              ▼                      ▼                      ▼
        core.constants          utils.fs              pymupdf (PyMuPDF)
```

> `main.py` (GUI) dan `cli.py` (CLI) sama-sama memakai `core/`. Ini bukti core benar-benar headless.



---

## 3. Lapisan & Tanggung Jawab

### 3.1 Bootstrap Layer (`if __name__ == "__main__"`)
- Deteksi ketersediaan `tkinterdnd2` (module-level `DND_AVAILABLE`).
- Buat root window sesuai ketersediaan DnD.
- Instansiasi app + `mainloop()`.

### 3.2 UI Layer (View)
- **Styling terpusat:** `create_styles()` mengatur tema `clam` + semua style ttk/native.
- **Konstruksi widget:** `create_ui()` menyusun hierarki `.pack`/`.grid`:
  - Header (judul, badge, subtitle)
  - Left panel (Treeview daftar file + tombol file)
  - Center (preview canvas + header/footer)
  - Right panel (pengaturan, fixed 350px)
  - Bottom (status, progressbar, tombol proses)
- **Rendering dinamis:** `update_preview()` (canvas), `refresh_tree()` (treeview).
- Semua widget interactive langsung memanggil handler pada instance.

### 3.3 State / Controller Layer
- State form lewat `tk.*Var` (StringVar/BooleanVar) — single source of truth.
- `self.files` = list path (state non-Var, dikelola manual).
- Handler event: `add_files`, `handle_drop`, `remove_selected`, `clear_files`,
  `start_process`, `update_preview`.
- Validasi terpusat di `validate_settings()`.

### 3.4 Core / PDF Engine (Model) — `core/`
- `create_nup_pdf(input, output, cols, rows, orientation, number_slides, pad_even=True)` — **fungsi inti**.
  - **Headless**: tidak mengimpor tkinter; semua parameter eksplisit.
  - `page.show_pdf_page()` → **vector embed**, bukan rasterisasi → kualitas & ukuran optimal.
  - Auto-center: letterbox menjaga aspect ratio sumber di dalam cell (`fit_rect_in_cell`).
  - `pad_even=True` (default): jumlah halaman hasil **tiap file** digenapkan
    (ditambah 1 halaman kosong bila ganjil) agar tiap file mulai di halaman baru.
  - Helper murni: `compute_page_geometry()`, `compute_grid()`, `compute_cell_rect()`,
    `fit_rect_in_cell()` — bisa di-unit-test tanpa I/O.
- `process_all(input_paths, output_path, cols, rows, orientation, number_slides,
  on_status, on_progress, allow_overwrite_source, pad_even=True)` — orkestrasi
  batch (loop file → temp → merge → cleanup). `pad_even` diteruskan per file.
  - Melaporkan kemajuan via callback, bukan dengan menyentuh widget.

### 3.5 Utils — `utils/fs.py`
- `normalize_key`, `make_temp_path`, `safe_remove`, `is_same_file`, `open_folder`.
- `open_folder` lintas OS (win/mac/linux) — memperbaiki keterbatasan Windows-only.

### 3.6 Entry Points
- `main.py` — bootstrap GUI (pilih TkinterDnD.Tk atau tk.Tk, lalu `PDFMultiSlidePro`).
- `cli.py` — argparse → `expand_inputs` (glob + dedup) → `core.pipeline.process_all`
  dengan reporter status/progress ke `stderr`. Tanpa tkinter. Guard: input valid,
  output ≠ sumber, ekstensi `.pdf` otomatis, batas slide/halaman.



---

## 4. Alur Data (Data Flow)

### 4.1 Konversi (pipeline utama)
```
[User input: files, cols×rows, orientation, options]
                    │
                    ▼
        validate_settings()  ──(invalid)──► dialog error ─► batal
                    │ valid
                    ▼
        asksaveasfilename()  ──(batal)──► batal
                    │ path
                    ▼
   ┌── process_all /*(worker thread)*/ ───────┐
   │  for each file:                          │
   │     create_nup_pdf(file → temp_i, params)│
   │        ├─ compute_grid (margin/gap/cell) │
   │        ├─ loop pages → new A4 page       │
   │        ├─ show_pdf_page(target, src, i)  │
   │        └─ [opsional] insert_textbox nomor│
   │     on_progress(i/total*80) ──┐          │
   │  merge: final.insert_pdf(temp_i...)      │
   │  final.save(output, garbage=4)           │
   │  cleanup temp → on_progress(100) ─┐      │
   └───────────────────────────────────┼──────┘
                    │                   │
                    ▼                   ▼
        (callback) on_status/on_progress → ui.app via root.after(0, ...)
```

### 4.2 Preview (paralel, main thread)
```
[Event: resize / keyrelease / combobox / check]
                    │
                    ▼
        update_preview()
          ├─ parse cols/rows (fallback 3×2, clamp 1..100, cap ≤100)
          ├─ skala A4 ke canvas
          ├─ gambar kertas + grid + nomor
          └─ update badge & info label
```

---

## 5. Threading Model

- **Main thread:** semua akses widget tkinter + event loop.
- **Worker thread:** satu `threading.Thread(daemon=True)` menjalankan `ui.app._run_pipeline`,
  yang memanggil `core.pipeline.process_all` (dengan callback).
- **Komunikasi:** core **tidak menyentuh widget**; callback `on_status`/`on_progress`
  dari `ui.app` membungkus update UI dengan `self.root.after(0, callable)`.

```
 MAIN THREAD              WORKER THREAD
 ───────────              ─────────────
 start_process
   spawn ─────────────────► _run_pipeline()
   (UI tetap responsif)       process_all(...)
   event loop                   on_status ──┐
   .......                      on_progress ┤ after(0) ──► UI update
   run after() callbacks ◄──────────────────┘
   finished()/failed()
```


**Risiko:** hanya 1 worker; tombol proses di-disable selama berjalan (cegah re-entry).
Tidak ada mekanisme cancel — proses panjang tidak bisa dibatalkan pengguna.

---

## 6. PDF Engine — Detail Teknis

| Aspek | Nilai |
|---|---|
| Unit internal | Point (1 pt = 1/72 inci) |
| Faktor mm→pt | `2.83465` (dihardcode, bukan konstanta bernama) |
| Ukuran A4 | `595.2756 × 841.8898` pt |
| Margin | 3 mm (≈ 8.50395 pt), semua sisi |
| Gap antar sel | 3 mm (≈ 8.50395 pt) |
| Algoritma N-up | Grid `cols × rows`, row-major (kiri→kanan, atas→bawah) |
| Penempatan | `show_pdf_page` (vector) + auto-center letterbox |
| Nomor slide | `insert_textbox`, font `helv`, size 7, rect tinggi 14pt di atas sel |
| Save | `garbage=4, deflate=True` |
| Temp | `__PDF_MULTI_TEMP_{n}.pdf` di folder output |
| Merge | `final.insert_pdf(part)` tiap temp, lalu simpan sekali |

**Rumus layout:**
```
usable_w = width  - 2·margin - gap·(cols-1)
usable_h = height - 2·margin - gap·(rows-1)
cell_w   = usable_w / cols
cell_h   = usable_h / rows
x0 = margin + col·(cell_w + gap)
y0 = margin + row·(cell_h + gap)
```
Auto-center (aspect-fit):
```
if src_ratio > cell_ratio:  new_w = cell_w ; new_h = new_w / src_ratio
else:                       new_h = cell_h ; new_w = new_h * src_ratio
offset ke tengah: (cell - new)/2
```

---

## 7. Batasan & Asumsi

| Batasan | Detail |
|---|---|
| Kolom/baris | 1–100, dan `cols×rows ≤ 100` (validasi + clamp preview) |
| Layout > A4 | `usable_* ≤ 0` → error |
| Output ≠ input | Dicegah (bandingkan absolute path) |
| Platform | Windows-only (`os.startfile`) |
| DnD | Butuh `tkinterdnd2`, jika tidak ada → fallback ke file dialog |
| Temp storage | Semua hasil per-file disimpan di disk sebelum merge (boros disk) |
| Memori | `fitz.open` tiap file di-load penuh saat proses |

---

## 8. Dependency Graph

```
ui/app.py
 ├── tkinter / tkinter.ttk (stdlib)
 ├── threading (stdlib)
 ├── pymupdf (PyMuPDF)           → cek jumlah halaman & validasi file
 ├── ui.styles, ui.widgets
 ├── core.constants
 ├── core.nup                    → create_nup_pdf (tidak dipakai langsung; via pipeline)
 ├── core.pipeline               → process_all
 ├── utils.fs                    → normalize_key, open_folder
 └── tkinterdnd2 [OPSIONAL]      → drag & drop (guarded try/except)

cli.py
 ├── argparse, glob, os, sys (stdlib)
 ├── core.constants
 └── core.pipeline               → process_all (callback → stderr)

core/pipeline.py
 ├── pymupdf (PyMuPDF)           → merge & save
 ├── core.nup
 └── utils.fs                    → make_temp_path, safe_remove

core/nup.py
 ├── pymupdf (PyMuPDF)           → show_pdf_page, insert_textbox
 └── core.constants

utils/fs.py  → hanya stdlib (os, subprocess, sys)

main.py  → ui.app (DND_AVAILABLE), tkinter, tkinterdnd2 [opsional]
```

**Jaminan batas lapisan:** `core/`, `utils/`, dan `cli.py` **tidak** mengimpor `tkinter` maupun `ui/`.


---

## 9. Status Debt Teknis (Setelah Fase 2)

| # | Debt | Status |
|---|---|---|
| 1 | Monolit 1 file / 1 class | ✅ **Selesai** — dipecah ke `core/`, `ui/`, `utils/` |
| 2 | Gaya penulisan ultra-vertical | ✅ Membaik (kode baru ditulis wajar); file lama tetap sebagai backup |
| 3 | Magic number `2.83465` | ✅ **Selesai** — `core/constants.MM_TO_PT` |
| 4 | UI var bocor ke core | ✅ **Selesai** — core menerima parameter eksplisit |
| 5 | Tanpa `requirements.txt`/README | ✅ **Selesai** |
| 6 | Tanpa cancel / progress per-file | ⏳ Belum — progress global OK, cancel belum ada |
| 7 | `os.startfile` Windows-only | ✅ **Selesai** — `utils/fs.open_folder` win/mac/linux |
| 8 | Nomor slide bisa menutupi konten | ⏳ Belum — perilaku dipertahankan (kompatibel) |
| 9 | `import fitz` deprecated | ✅ **Selesai** — semua kode pakai `import pymupdf` |
| 10 | Hanya GUI, tak bisa otomasi | ✅ **Selesai** — `cli.py` (argparse, headless) |



---

## 10. Roadmap Fase 4 (belum diimplementasi)

- **Cancel token** di GUI (hentikan proses besar dengan aman).
- **Unit test (pytest)** menyeluruh untuk helper layout (edge case aspect ratio).
- **Reservasi area nomor slide** agar tidak menutupi konten.

Fase 1 (housekeeping), Fase 2 (modularisasi), dan Fase 3 (CLI + migrasi `pymupdf`)
sudah **selesai** — lihat `CONTEXT.md §11`.


---

## 11. Ringkasan Satu Paragraf

Aplikasi ini adalah **tool PDF N-up berlapis** (tkinter + PyMuPDF) untuk menggabungkan
kumpulan PDF menjadi satu PDF A4 (grid `cols×rows`, margin & gap 3mm, auto-center, opsi
nomor slide). Logika PDF terisolasi di `core/` yang **headless**, dipakai bersama oleh
**dua entry point**: GUI (`main.py`/`ui/`) dan **CLI (`cli.py`)**. Alur utama: pilih file →
atur grid → proses → worker thread (GUI) / langsung (CLI) menghasilkan PDF temp per file →
merge → simpan → cleanup. Diuji via `tests/smoke_nup.py` + `tests/smoke_cli.py`.
Batasan tersisa: 100 slide/halaman dan belum ada cancel.





