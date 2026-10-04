# Build & Installer — PDF Multi Slide Pro

Folder ini berisi semua **sumber build**. Tidak ada file di sini yang dipakai
saat aplikasi jalan dari source (`python main.py`). Cukup abaikan bila tidak
perlu membuat `.exe`/installer.

## Hasil build

| File | Deskripsi | Ukuran ± |
|------|-----------|---------|
| `dist\PDFMultiSlidePro-Portable.exe` | **Portable**, 1 file, langsung jalan (tanpa install) | 36 MB |
| `dist\PDFMultiSlidePro\PDFMultiSlidePro.exe` | Versi folder (dipakai installer, start lebih cepat) | — |
| `dist\installer\PDFMultiSlidePro-Setup-1.0.0.exe` | **Installer** (Start Menu, shortcut Desktop, uninstaller) | 58 MB |

## Cara build (1 perintah)

Dari root project:

```powershell
powershell -ExecutionPolicy Bypass -File build_assets\build.ps1
```

Opsi:

```powershell
# Hanya .exe, tanpa installer
... -File build_assets\build.ps1 -SkipInstaller

# Bersihkan dulu build/ dan dist/
... -File build_assets\build.ps1 -Clean
```

## Prasyarat build

| Tool | Status | Catatan |
|------|--------|---------|
| Python 3.11+ | wajib | `pip install -r requirements.txt` |
| PyInstaller | wajib | `pip install pyinstaller` |
| Pillow | opsional | hanya untuk membuat ulang `app.ico` |
| Inno Setup 6 | opsional | hanya untuk installer. https://jrsoftware.org/isdl.php |

> Bila Inno Setup tidak ada, script tetap membuat `.exe` dan melewati installer
> dengan pesan peringatan (tidak error).

## Isi folder

| File | Fungsi |
|------|--------|
| `build.ps1` | Orkestrator build end-to-end (cek prasyarat → PyInstaller → Inno Setup → verifikasi). |
| `PDFMultiSlidePro.spec` | Konfigurasi PyInstaller (membangun **onedir + onefile** sekaligus). |
| `installer.iss` | Script Inno Setup untuk installer `.exe`. |
| `make_icon.py` | Membuat `app.ico` dari logo project (reproducible). |
| `app.ico` | Ikon aplikasi (multi-resolusi 16–256 px). Dipakai exe + jendela GUI. |
| `version_info.txt` | Metadata versi exe (ProductName, FileVersion, dll). |

## Catatan teknis penting

- **Modul besar sengaja dikecualikan** (`numpy`, `pandas`, `scipy`, `matplotlib`)
  karena terbukti tidak dipakai — ukuran exe turun dari 84 MB → 36 MB.
- **`tkinterdnd2`** dibundel lengkap termasuk native `tkdnd` (win-x64 + lainnya)
  agar drag & drop tetap jalan di exe. Bila library tkdnd gagal load di runtime,
  aplikasi otomatis fallback ke tombol "Tambah PDF" (sudah di-guard).
- **Ikon jendela**: `utils.fs.app_icon_path()` sadar PyInstaller (`sys._MEIPASS`),
  dipasang di `main.py` via `apply_window_icon()` (aman, di-skip bila tak ada).
- **Menimpa source / file terkunci**: perilaku sama seperti versi source
  (staging temp + `safe_replace()` dengan retry).

## Uji setelah build

```powershell
# Uji cepat: jalankan portable, harus muncul jendela
dist\PDFMultiSlidePro-Portable.exe

# Uji smoke otomatis (dari source)
python tests\smoke_nup.py
python tests\smoke_cli.py
```

## Troubleshooting

- **"Aplikasi hasil build sedang berjalan"** → script menutup otomatis proses
  lama; tutup manual bila masih gagal.
- **Installer tidak dibuat** → pastikan Inno Setup 6 terpasang, atau lewati
  dengan `-SkipInstaller` (portable tetap tersedia).
- **exe besar** → pastikan `EXCLUDES` di `.spec` tidak dihapus.
