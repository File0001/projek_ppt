# CONTEXT.md — PDF Multi Slide Pro

> Checkpoint konteks proyek. Baca file ini terlebih dahulu sebelum mengubah kode.
> Terakhir diperbarui: **Fase 3 — CLI + migrasi PyMuPDF**.

---

## 0. Status Versi

| Versi | Lokasi | Status |
|---|---|---|
| **Baru (modular, GUI)** | `main.py` + `core/` + `ui/` + `utils/` | **AKTIF** |
| **Baru (CLI)** | `cli.py` | **AKTIF** — headless/batch |
| Lama (monolit) | `PDF_Multi_Slide_Layout_Rapi(1).py` | Backup utuh, jangan diubah tanpa izin |
| **Build / Distribusi** | `build_assets/` → `dist/` | **AKTIF** — portable `.exe` + installer `.exe` |

Perilaku konversi **identik** (diverifikasi: `tests/smoke_nup.py` + `tests/smoke_cli.py`).
Fase 2: pemisahan `core/ui/utils` (core headless). Fase 3: CLI mode +
migrasi `import fitz` → `import pymupdf` (peringatan deprecation hilang).

---

## 1. Ringkasan Proyek

**PDF Multi Slide Pro** adalah aplikasi desktop (GUI) Python untuk mengubah satu atau
banyak file PDF menjadi **satu PDF baru** di mana setiap halaman A4 berisi **beberapa
slide/halaman sumber** yang disusun dalam grid (N-up layout). Tujuannya: membuat
dokumen PDF hasil yang "rapi" dan siap dipresentasikan/dicetak (mis. handout).

- **Entry point:** `main.py`
- **Bahasa UI:** Indonesia
- **Platform:** Desktop, lintas OS (buka folder hasil: Win/macOS/Linux)


---

## 2. Fitur Utama

1. **Tambah banyak file PDF** — via dialog file, atau **drag & drop** (opsional).
2. **Manajemen daftar file** — tampil dalam tabel (nama file + jumlah halaman),
   bisa hapus file terpilih / bersihkan semua.
3. **Pengaturan tata letak** — jumlah **Kolom × Baris** (grid) per halaman A4.
4. **Orientasi halaman** — Portrait / Landscape.
5. **Preview visual A4 live** — canvas yang menggambar grid slide + nomor slide,
   ikut berubah saat pengaturan diubah.
6. **Opsi output:**
   - Tampilkan **kotak border** (hanya di preview, bukan di PDF akhir).
   - Tampilkan **nomor slide** ("Slide N") di PDF hasil.
   - **Nama file hasil** yang dapat dikustomisasi.
7. **Progress bar + status** selama proses.
8. **Proses di background thread** agar UI tidak freeze.

---

## 3. Teknologi / Stack

| Komponen | Teknologi | Catatan |
|---|---|---|
| Bahasa | Python 3 | Tanpa `requirements.txt` |
| GUI Toolkit | `tkinter` + `ttk` | Theme `clam` |
| Drag & Drop | `tkinterdnd2` | **Opsional** (soft dependency, di-guard `try/except`) |
| Manipulasi PDF | `PyMuPDF` (`fitz`) | Open, render, N-up, merge, save |
| Threading | `threading.Thread` | Worker `process_all`, daemon |
| Concurrency ke UI | `root.after(0, ...)` | Update UI dari thread worker |
| Packaging (masa depan) | `output/build/dist` di-`.gitignore` | Belum ada spec aktif |

**Dependensi runtime:**
- Wajib: `PyMuPDF`
- Opsional: `tkinterdnd2` (jika tidak ada → drag & drop dinonaktifkan otomatis)

---

## 4. Struktur Kode

### 4.1 Struktur baru (modular — AKTIF)
```
projek_ppt/
├── main.py                 # entry point GUI (bootstrap root + mainloop)
├── cli.py                  # entry point CLI (argparse, headless)
├── core/                   # logika PDF murni (headless, tanpa tkinter)
│   ├── constants.py        # MM_TO_PT, A4, margin/gap, batasan grid, orientasi
│   ├── nup.py              # compute_* + fit_rect_in_cell + create_nup_pdf()
│   └── pipeline.py         # process_all(input_paths, params, callbacks)
├── ui/                     # antarmuka
│   ├── app.py              # class PDFMultiSlidePro (view + controller)
│   ├── styles.py           # create_styles() (tema ttk)
│   └── widgets.py          # badge() / inline_badge()
├── utils/
│   └── fs.py               # normalize_key, make_temp_path, safe_remove,
│                           # is_same_file, open_folder (lintas OS)
├── tests/
│   ├── smoke_nup.py        # uji headless core (layout + pipeline)
│   └── smoke_cli.py        # uji CLI (argparse, guard, ekstensi)
├── requirements.txt
├── README.md
├── CONTEXT.md              # dokumen ini
├── ARCHITECTURE.md
└── PDF_Multi_Slide_Layout_Rapi(1).py   # versi lama (backup, jangan diubah)
```

### 4.2 Pemetaan lama → baru
| Monolit lama | Modular baru |
|---|---|
| `PAPER_SIZE/MARGIN_MM/GAP_MM` (class const) | `core/constants.py` (+ `MM_TO_PT`, `A4_*`) |
| `create_styles()` | `ui/styles.py::create_styles()` |
| `create_ui()` + `_build_*` | `ui/app.py` (dipecah per-panel) |
| `create_nup_pdf()` (baca UI var) | `core/nup.py::create_nup_pdf(...)` (parameter) |
| `process_all()` + `make_temp_path()` | `core/pipeline.py` + `utils/fs.py` |
| `finished()/failed()` + `os.startfile` | `ui/app.py` + `utils/fs.py::open_folder()` |
| `update_preview()` | `ui/app.py::update_preview()` (pakai `_parse_grid`) |


---

## 5. Alur Sistem (Flow)

### 5.1 Startup
```
__main__  →  (DND_AVAILABLE ? TkinterDnD.Tk() : tk.Tk())
          →  PDFMultiSlidePro(root)
             ├── create_styles()
             ├── create_ui()
             ├── enable_drag_drop(root)  [jika tkinterdnd2 ada]
             └── update_preview()
          →  root.mainloop()
```

### 5.2 Menambah file
```
add_files()  ─┐
handle_drop()─┴→ add_dropped_files(paths)
                 ├── dedup via set(abs-path lowercase)
                 ├── validasi: fitz.open(path) lalu close()
                 └── refresh_tree() → update Treeview + total halaman
```

### 5.3 Memproses PDF (jalur utama)
```
start_process()
 ├── cek self.files tidak kosong
 ├── validate_settings()          → ValueError → dialog error → stop
 ├── ambil nama file hasil (default "Hasil_Gabungan.pdf")
 ├── filedialog.asksaveasfilename(...)  → batal → stop
 ├── cek output_path != salah satu input (cegah overwrite sumber)
 ├── disable tombol, reset progress
 └── threading.Thread(target=process_all, args=(output_path,), daemon=True).start()

process_all(output_path)   [THREAD]
 ├── for i, source in enumerate(self.files, 1):
 │      create_nup_pdf(source, temp_path_i, pad_even=True)  → tulis PDF temp
 │      └─ hasil TIAP file digenapkan jumlah halamannya SEBELUM digabung
 │      set_progress(i/total * 80)
 ├── set_status("Menggabungkan...")
 ├── final = fitz.open()
 ├── for temp in temp_files: final.insert_pdf(fitz.open(temp))
 ├── final.save(output_path, garbage=4, deflate=True)
 ├── hapus semua temp file
 └── set_progress(100) + root.after(0, finished(output_path))
     (on exception → hapus temp + root.after(0, failed(err)))
```

### 5.4 Inti N-up — `create_nup_pdf(input, output, ..., pad_even=True)`
```
source = fitz.open(input);  result = fitz.open()
width, height = A4 (595.2756 × 841.8898 pt)
  └─ jika Landscape → tukar width/height
margin = 3mm = 3 * 2.83465 pt
gap    = 3mm = 3 * 2.83465 pt
cols, rows = dari UI; slides_per_page = cols*rows
usable_w = width  - 2*margin - gap*(cols-1)
usable_h = height - 2*margin - gap*(rows-1)
  └─ <= 0 → ValueError "Layout terlalu besar untuk halaman A4"
cell_w = usable_w/cols ;  cell_h = usable_h/rows

for start in range(0, len(source), slides_per_page):
    page = result.new_page(width, height)
    for position, slide_index in enumerate(range(start, end)):
        row, col = position//cols, position%cols
        cell = Rect(x0, y0, x0+cell_w, y0+cell_h)
        # AUTO CENTER (jaga aspect ratio sumber, letterbox):
        #   source lebih lebar dari cell → fit ke cell.width, tinggi proporsional
        #   else → fit ke cell.height, lebar proporsional
        target = Rect di tengah cell dengan ukuran hasil fit
        page.show_pdf_page(target, source, slide_index)   # tempatkan slide
        if number_var: page.insert_textbox("Slide N", fontsize=7)
# GENAPKAN: bila jumlah halaman hasil ganjil → tambah 1 halaman kosong
# (A4, orientasi sama) agar tiap file selalu genap sebelum digabung.
if pad_even and len(result) % 2 == 1: result.new_page(width, height)
source.close();  result.save(output, garbage=4, deflate=True);  result.close()
```

> **Catatan:** border/kotak hanya digambar di **preview** (`update_preview`), **tidak**
> ditulis ke PDF hasil (lihat komentar eksplisit "TIDAK ADA BORDER PADA PDF HASIL").

### 5.5 Preview — `update_preview()`
- Baca `cols`/`rows` dari entry (fallback 3×2 kalau tidak valid), clamp 1–100, cap total ≤ 100.
- Hitung skala A4 agar pas di canvas (dengan padding 45px), gambar:
  shadow → kertas A4 → grid sel (opsional border) → garis dekoratif ungu → nomor sel.
- Update badge ("N slide / lembar") dan info ("A4 • Orientasi • Auto Center").
- Dipanggil saat: init, resize canvas (`<Configure>`), key release pada entry, ganti orientasi, toggle border.

---

## 6. Model Data / State

| State | Tipe | Default | Keterangan |
|---|---|---|---|
| `self.files` | `list[str]` | `[]` | Daftar path PDF (urutan = urutan output) |
| `self.cols_var` | `StringVar` | `"3"` | Kolom grid |
| `self.rows_var` | `StringVar` | `"2"` | Baris grid (default 3×2 = 6 slide/lembar) |
| `self.orientation_var` | `StringVar` | `"Landscape"` | Portrait / Landscape |
| `self.border_var` | `BooleanVar` | `True` | Border di preview saja |
| `self.number_var` | `BooleanVar` | `False` | Nomor slide di PDF hasil |
| `self.output_name_var` | `StringVar` | `"Hasil_Gabungan.pdf"` | Nama awal saat Save As |
| `self.status_var` | `StringVar` | pesan siap | Teks status bawah |
| `self.tree` | `Treeview` | — | Tabel daftar file |
| `self.preview_canvas` | `Canvas` | — | Area preview |
| `self.progress` | `Progressbar` | — | 0–100 |

**Thread safety:** state UI hanya diubah dari main thread. Worker memakai
`root.after(0, ...)` (via `set_status`/`set_progress`/`finished`/`failed`).

---

## 7. UI Sistem

### Palette warna (brand)
| Peran | Hex |
|---|---|
| Background app | `#F4F6FA` |
| Card / panel | `#FFFFFF` |
| Teks utama | `#172033` |
| Teks muted | `#7A8496` / `#6B7280` |
| Aksen ungu (primary) | `#5656D9` / `#4E4EBC` |
| Badge sukses | bg `#E5F6EF`, fg `#2E8A68` |
| Preview area | `#E8ECF3` |

### Font
- Utama: `Segoe UI` (judul 23 bold, section 11 bold, body 8–10).
- Treeview font 8, rowheight 29.

### Layout window (grid besar)
```
┌─────────────────────────── HEADER ──────────────────────────────┐
│ "Ubah PDF jadi presentasi"  [Badge: Siap dipresentasikan]        │
│ Subtitle: "Susun PDF menjadi beberapa slide ..."                 │
├───────────────┬──────────────────────────────┬──────────────────┤
│ LEFT PANEL    │ CENTER (PREVIEW)             │ RIGHT PANEL      │
│ Daftar file   │ Header: "Preview presentasi" │ "Pengaturan      │
│ (Treeview:    │   + badge "N slide/lembar"   │  slide"          │
│  Nama|Hal.)   │ Canvas A4 live               │ - Kolom × Baris  │
│ [＋Tambah PDF] │ Footer: status + info        │ - Orientasi      │
│ [Hapus][Brsih]│                              │ - Opsi output    │
│ hint DnD      │                              │   (border, nomor)│
│               │                              │ - Nama file      │
│               │                              │ - Status valid   │
├───────────────┴──────────────────────────────┴──────────────────┤
│ BOTTOM: status text + progress bar ............ [📄 JADIKAN PDF] │
└─────────────────────────────────────────────────────────────────┘
```
- Window default `1400x850`, minimum `1180x720`.
- Panel kanan fixed width 350 (`pack_propagate(False)`).
- Tombol aksi utama: `Process.TButton` "JADIKAN PDF".

---

## 8. Edge Cases & Error Handling

Sudah ditangani:
- `tkinterdnd2` tidak terpasang → `DND_AVAILABLE = False`, drop dinonaktifkan, file dialog tetap jalan.
- Kolom/baris bukan angka / di luar 1–100 / total > 100 → `ValueError` + dialog.
- Layout lebih besar dari A4 (usable ≤ 0) → `ValueError`.
- Output sama dengan file sumber → dialog error, proses dibatalkan.
- File PDF korup/tidak bisa dibuka → di-skip saat add (`try/except`).
- Temp file dibersihkan baik saat sukses maupun saat gagal.
- PDF di-save dengan `garbage=4, deflate=True` (kompresi + bersihkan objek).
- Update UI dari thread lewat `root.after` (aman).

Belum ditangani / potensi risiko:
- Belum ada `requirements.txt` / `README`.
- File monolitik 2.7k baris → sulit dipelihara.
- Belum ada penanganan jika folder output read-only / kehabisan disk.
- Nomor slide di-overlay di area atas sel (bisa menutupi konten slide).
- `os.startfile` hanya Windows (tidak cross-platform).
- Tidak ada batas jumlah file / memori (semua temp disimpan di disk sampai merge).

---

## 9. Cara Menjalankan

```powershell
pip install -r requirements.txt

# GUI
python main.py

# CLI (tanpa GUI)
python cli.py -o hasil.pdf -c 3 -r 2 -O Landscape -n input/*.pdf
```

Uji headless:

```powershell
python tests/smoke_nup.py
python tests/smoke_cli.py
```

Versi lama (backup):

```powershell
python "PDF_Multi_Slide_Layout_Rapi(1).py"
```

### Build `.exe` & installer

```powershell
# 1 perintah: cek prasyarat → PyInstaller → Inno Setup → verifikasi
powershell -ExecutionPolicy Bypass -File build_assets\build.ps1

# Hanya .exe (tanpa installer) / bersihkan dulu
... -File build_assets\build.ps1 -SkipInstaller
... -File build_assets\build.ps1 -Clean
```

Hasil: `dist\PDFMultiSlidePro-Portable.exe` (36 MB, 1 file) dan
`dist\installer\PDFMultiSlidePro-Setup-1.0.0.exe` (58 MB). Detail: `build_assets/README.md`.

---

## 10. Aturan Kerja (dari .clinerules)

- Selalu baca `CONTEXT.md` sebelum mengubah kode.
- Jangan langsung memberi solusi kode / membuat file pada prompt pertama; tanya dulu jika ambigu (Socratic).
- Prioritaskan solusi sederhana (KISS/YAGNI), pertimbangkan edge case + security.
- Jangan hapus/ubah file inti tanpa izin.
- Selesaikan satu tugas → berhenti → laporkan.
- Error >3 kali berturut-turut → berhenti & minta arahan.
- **Update `CONTEXT.md`** setiap selesai perubahan (checkpoint).
- Bahasa profesional, ringkas, terstruktur (bullet + bold).

---

## 11. Rekomendasi Lanjutan (Fase 4 — belum diimplementasi)

Sudah selesai:
- ✅ Fase 1: `requirements.txt`, `README.md`, konstanta `MM_TO_PT`/`A4_*`.
- ✅ Fase 2: struktur `core/` `ui/` `utils/` + `main.py`; core headless.
- ✅ Fase 3: **CLI mode** (`cli.py`) + **migrasi `import fitz` → `import pymupdf`**.
- ✅ **Build & Installer**: `build_assets/` (spec PyInstaller + Inno Setup + `build.ps1`).
  Menghasilkan portable `.exe` (36 MB) + installer `.exe` (58 MB). Modul
  `numpy/pandas/scipy` di-exclude (exe turun dari 84 MB). Ikon aplikasi multi-resolusi.
- ✅ **Penggenapan per file**: tiap file digenapkan jumlah halamannya sebelum
  digabung (`pad_even=True` default di `create_nup_pdf`/`process_all`).

Belum:
1. **Unit test lebih lengkap** (pytest) untuk `compute_grid`/`fit_rect_in_cell` (edge case ratio).
2. **Cancel token** di GUI (hentikan proses besar di tengah jalan).
3. Pertimbangkan reservasi area nomor slide agar tidak menutupi konten.
4. (Opsional) dukung `--number` CLI menulis nomor pada margin, bukan overlay.
5. (Opsional) **Code signing** installer agar tidak muncul peringatan SmartScreen.


---

## 12. Uji Coba Manual (verifikasi)

1. Jalankan app → window tampil, preview A4+grid 3×2 muncul.
2. Ubah Kolom/Baris → preview ikut berubah, badge update.
3. Tambah 1 PDF 10+ halaman (dialog) → muncul di tabel + jumlah halaman benar.
4. Drag & drop PDF (jika tkinterdnd2 ada) → masuk daftar; drop duplicate → di-skip.
5. Ganti orientasi Landscape↔Portrait → preview berubah.
6. Klik JADIKAN PDF → Save As → proses jalan, progress sampai 100, folder terbuka.
7. Buka PDF hasil → 6 slide/lembar, rasio terjaga, tidak ada border (jika border off).
7b. Pastikan **setiap file** menghasilkan jumlah halaman **genap** (bila sumber
    menghasilkan ganjil, ada 1 halaman kosong di akhir file itu) — cek dengan
    membuka hasil dan menghitung halaman per bagian file.
8. Aktifkan "nomor slide" → PDF hasil menampilkan "Slide N".
9. Coba input kolom = 0 / `abc` → muncul dialog error.
10. Coba simpan dengan nama sama seperti file sumber → dialog error, proses batal.
11. Pastikan tidak ada file `__PDF_MULTI_TEMP_*` tersisa setelah proses.

### Verifikasi versi build (installer/portable)

12. Jalankan `dist\PDFMultiSlidePro-Portable.exe` → jendela muncul (judul
    "PDF ke Slide • Multi Slide Pro"), ikon tampil, dragging file PDF jalan.
13. Install `dist\installer\PDFMultiSlidePro-Setup-1.0.0.exe` → cek shortcut
    Start Menu + Desktop, lalu buka dari shortcut.
14. Uninstall lewat "Apps & features" (atau `uninst000.exe`) → folder install
    terhapus (sisa file terkunci baru hilang setelah reboot bila app masih jalan).
15. Konversi PDF nyata dari versi build → hasil identik dengan versi source.




