# PDF Multi Slide Pro

Aplikasi desktop (Python + tkinter) untuk mengubah satu atau banyak dokumen —
**PDF, gambar, atau PowerPoint** — menjadi satu PDF baru bergaya **N-up**:
setiap halaman A4 memuat beberapa slide/halaman sumber yang disusun dalam grid
rapi — siap dicetak sebagai handout atau dipresentasikan.

---

## Fitur

- Tambah banyak file (PDF, gambar, `.pptx`/`.ppt`) via dialog
  atau **drag & drop**.
- **Konversi otomatis** sumber non-PDF ke PDF sebelum disusun:
  - **Gambar** (png/jpg/jpeg/bmp/gif/tif/tiff/webp) → 1 gambar = 1 slide.
  - **PowerPoint** → konversi **format 100% utuh**. Mesin dicoba berurutan:
    1. **Microsoft PowerPoint** (bila Office terpasang) — paling akurat.
    2. **LibreOffice/soffice** — sangat akurat, lintas platform.
    3. **python-pptx** — fallback cepat, tapi **hanya teks**
       (tema, layout, gambar hilang). `.ppt` lama butuh Office/LibreOffice.
- Atur **grid** (Kolom × Baris) per halaman A4.
- **Orientasi** Portrait / Landscape.
- **Preview A4 live** yang ikut berubah saat pengaturan diubah.
- Opsi **nomor slide** pada PDF hasil.
- **Setiap file digenapkan** jumlah halamannya sebelum digabung (bila hasil
  ganjil, ditambah 1 halaman kosong) — tiap file mulai di halaman baru.
- Proses di **background thread** (UI tidak freeze) + progress bar.


---

## Instalasi

```bash
pip install -r requirements.txt
```

> `tkinterdnd2` opsional. Bila tidak dipasang, drag & drop dinonaktifkan otomatis;
> tombol "Tambah file" tetap berfungsi.
>
> `python-pptx` juga opsional — hanya dipakai sebagai **fallback
> terakhir** konversi PPT. Untuk hasil **format 100% utuh**, cukup punya
> **Microsoft PowerPoint** (otomatis terdeteksi via COM) **atau** **LibreOffice**.
> Di Windows dengan Office terpasang, tidak perlu memasang apa pun lagi.

**Prasyarat:** Python 3.8+ dan tkinter (biasanya terpasang bersama Python).

---

## Menjalankan

### GUI
```bash
python main.py
```

### CLI (tanpa GUI, untuk otomasi/batch)
```bash
python cli.py -o hasil.pdf slide1.pdf slide2.pdf
python cli.py -o handout.pdf -c 2 -r 3 -O Portrait -n *.pdf
python cli.py -o out.pdf --quiet laporan/*.pdf
```

Opsi CLI: `-o/--output`, `-c/--cols`, `-r/--rows`, `-O/--orientation`,
`-n/--number`, `-q/--quiet`. Tekan `python cli.py -h` untuk bantuan.

Aplikasi versi monolit lama tetap tersedia sebagai backup:
`PDF_Multi_Slide_Layout_Rapi(1).py`.

---

## Cara Pakai

1. Klik **Tambah file** (atau seret file ke jendela) — PDF, gambar, atau PPT.
2. Atur **Kolom** dan **Baris** (mis. 3 × 2 = 6 slide per lembar).
3. Pilih **Orientasi**.
4. (Opsional) aktifkan **Tampilkan nomor slide pada PDF**.
5. Isi **nama file hasil**, lalu klik **JADIKAN PDF** dan pilih lokasi simpan.

---

## Struktur Proyek

```
projek_ppt/
├── main.py                 # entry point GUI
├── cli.py                  # entry point CLI (headless, argparse)
├── requirements.txt
├── README.md
├── core/                   # logika PDF murni (headless, tanpa tkinter)
│   ├── constants.py        # MM_TO_PT, ukuran A4, batasan grid
│   ├── convert.py          # gambar/PPT → PDF (soffice + fallback)
│   ├── nup.py              # hitung layout + create_nup_pdf()
│   └── pipeline.py         # process_all(): konversi → temp → merge → save
├── ui/                     # antarmuka
│   ├── app.py              # class PDFMultiSlidePro (view + controller)
│   ├── styles.py           # tema ttk
│   └── widgets.py          # komponen kecil (badge)
├── utils/
│   └── fs.py               # helper path/temp/buka folder
└── tests/
    ├── smoke_nup.py        # uji core N-up
    └── smoke_cli.py        # uji CLI
```

Dokumentasi lebih dalam: [CONTEXT.md](CONTEXT.md) dan [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Catatan Platform

- Buka folder hasil otomatis mendukung Windows / macOS / Linux (`utils/fs.py`).
- Font UI memakai **Segoe UI** (default Windows); di OS lain tetap tampil dengan font fallback.
