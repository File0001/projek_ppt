"""Helper filesystem: path temp, path normalisasi, buka folder. Tanpa UI."""

import os
import subprocess
import sys
import time


def normalize_key(path):
    """Kunci dedup/komparasi path (absolute + lowercase)."""
    return os.path.abspath(path).lower()


def resource_path(relative):
    """Path absolut ke resource, sadar PyInstaller (onefile/onedir).

    - Dibundel: sys._MEIPASS berisi folder ekstraksi sementara.
    - Saat dikembangkan: relatif terhadap root project (dua level di atas file ini).
    """
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


def app_icon_path():
    """Kandidat path ikon aplikasi (None bila tidak ada)."""
    for name in ("build_assets/app.ico", "app.ico"):
        candidate = resource_path(name)
        if os.path.isfile(candidate):
            return candidate
    return None


def make_temp_path(output_path, number):
    """Path temp unik di folder output: __PDF_MULTI_TEMP_{number}.pdf.

    Pembuatan nama bersifat atomik (O_CREAT|O_EXCL) agar dua pemakaian
    berurutan / bersamaan tidak pernah bertabrakan nama. File penanda
    kosong langsung dihapus — hanya namanya yang dipakai.
    """
    folder = os.path.dirname(os.path.abspath(output_path)) or "."

    counter = 0
    while True:
        suffix = "" if counter == 0 else f"_{counter}"
        candidate = os.path.join(folder, f"__PDF_MULTI_TEMP_{number}{suffix}.pdf")
        try:
            # Klaim nama secara atomik.
            fd = os.open(candidate, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            os.remove(candidate)
            return candidate
        except FileExistsError:
            counter += 1
        except OSError:
            # Folder tidak bisa ditulisi → kembalikan kandidat apa adanya.
            return candidate



def safe_remove(path, retries=5, delay=0.15):
    """Hapus file dengan retry.

    Di Windows, file PDF yang baru ditutup (mis. oleh PyMuPDF) kadang masih
    terkunci sesaat → error "Permission denied". Kita coba beberapa kali
    dengan jeda kecil sebelum menyerah (best-effort, tidak melempar error).
    """
    for attempt in range(retries):
        try:
            os.remove(path)
            return True
        except FileNotFoundError:
            return True  # sudah tidak ada → anggap sukses
        except PermissionError:
            if attempt < retries - 1:
                time.sleep(delay)
                continue
        except OSError:
            if attempt < retries - 1:
                time.sleep(delay)
                continue

    return False


def is_same_file(path_a, path_b):
    """True bila dua path menunjuk file yang sama (case-insensitive)."""
    return normalize_key(path_a) == normalize_key(path_b)


def unique_path(path):
    """Kembalikan path yang belum terpakai; bila sudah ada, tambah ' (n)'.

    Contoh: "Hasil.pdf" → "Hasil (1).pdf" → "Hasil (2).pdf".
    Ekstensi dipertahankan di akhir.
    """
    if not os.path.exists(path):
        return path

    folder = os.path.dirname(path)
    name = os.path.basename(path)
    stem, ext = os.path.splitext(name)

    counter = 1
    while True:
        candidate = os.path.join(folder, f"{stem} ({counter}){ext}")
        if not os.path.exists(candidate):
            return candidate
        counter += 1


def format_size(num_bytes):
    """Format ukuran byte jadi string ringkas (mis. '8.2 KB', '1.4 MB')."""
    if num_bytes is None:
        return "?"
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024


def file_size(path):
    """Ukuran file dalam byte, atau None bila tidak bisa dibaca."""
    try:
        return os.path.getsize(path)
    except OSError:
        return None


def safe_replace(src, dst, retries=5, delay=0.15):
    """Pindahkan src → dst menggantikan dst, dengan retry (Windows lock).

    Dipakai untuk menyelesaikan output ke file tujuan yang mungkin masih
    terkunci sesaat. Bila gagal total, src TIDAK dihapus (dipulihkan ke
    pemanggil lewat return False) sehingga tidak ada data yang hilang.
    """
    for attempt in range(retries):
        try:
            os.replace(src, dst)
            return True
        except PermissionError:
            if attempt < retries - 1:
                time.sleep(delay)
                continue
        except OSError:
            if attempt < retries - 1:
                time.sleep(delay)
                continue

    return False


def open_folder(folder):
    """Buka folder di file manager OS. Best-effort, tidak melempar error."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(folder)  # noqa: S606 (Windows-only, disengaja)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])
    except Exception:
        pass


