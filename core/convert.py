"""Konversi sumber non-PDF (gambar, PowerPoint) menjadi PDF.

Headless: tidak mengimpor tkinter. Dipakai oleh pipeline sebelum tahap
N-up. Strategi (untuk PPT, berurutan dari yang paling akurat):

1. Microsoft PowerPoint (COM, Windows) -> **format 100% utuh**.
2. LibreOffice/`soffice`               -> sangat akurat (lintas OS).
3. Fallback python-pptx                -> HANYA teks (format hilang).

- PDF    -> dilewati (sudah PDF, tidak dikonversi).
- Gambar -> dirender ke halaman PDF seukuran gambar (PyMuPDF).
"""

import os
import shutil
import subprocess
import tempfile

import pymupdf

# Ekstensi yang dikenali (lowercase, termasuk titik).
IMAGE_EXTS = {
    ".png", ".jpg", ".jpeg", ".bmp", ".gif",
    ".tif", ".tiff", ".webp",
}
PPT_EXTS = {".pptx", ".ppt"}
SUPPORTED_EXTS = {".pdf"} | IMAGE_EXTS | PPT_EXTS


def file_kind(path):
    """Kembalikan jenis file: 'pdf', 'image', 'ppt', atau 'unknown'."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return "pdf"
    if ext in IMAGE_EXTS:
        return "image"
    if ext in PPT_EXTS:
        return "ppt"
    return "unknown"


def is_supported(path):
    """True bila ekstensi file termasuk yang didukung."""
    return file_kind(path) != "unknown"


def find_soffice():
    """Path ke LibreOffice `soffice`, atau None bila tidak ditemukan.

    Urutan pencarian: PATH, lalu lokasi umum instalasi di Windows/macOS/Linux.
    """
    found = shutil.which("soffice") or shutil.which("libreoffice")
    if found:
        return found

    candidates = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/usr/bin/soffice",
        "/usr/local/bin/soffice",
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None


def _convert_image_to_pdf(input_path, output_path):
    """Render satu gambar ke satu halaman PDF seukuran gambar."""
    doc = pymupdf.open()
    try:
        img = pymupdf.open(input_path)
        try:
            rect = img[0].rect
            width, height = rect.width, rect.height
        finally:
            img.close()

        page = doc.new_page(width=width, height=height)
        page.insert_image(
            pymupdf.Rect(0, 0, width, height), filename=input_path
        )
        doc.save(output_path, garbage=4, deflate=True)
    finally:
        doc.close()


def images_to_pdf(image_paths, output_path):
    """Gabungkan BANYAK gambar menjadi SATU PDF (1 gambar = 1 halaman).

    Tiap halaman dibuat seukuran gambarnya sendiri, sehingga rasio asli
    terjaga. Bila `image_paths` kosong, menghasilkan PDF 1 halaman kosong
    agar pipeline tetap punya sesuatu untuk diproses.
    """
    doc = pymupdf.open()
    try:
        for image_path in image_paths:
            try:
                img = pymupdf.open(image_path)
                try:
                    rect = img[0].rect
                    width, height = rect.width, rect.height
                finally:
                    img.close()

                page = doc.new_page(width=width, height=height)
                page.insert_image(
                    pymupdf.Rect(0, 0, width, height), filename=image_path
                )
            except Exception:
                # Lewati gambar yang rusak/tidak terbaca, lanjut ke berikutnya.
                continue

        if len(doc) == 0:
            doc.new_page()

        doc.save(output_path, garbage=4, deflate=True)
    finally:
        doc.close()


def _convert_with_ppt_com(input_path, output_path):
    """Konversi PPT via Microsoft PowerPoint (COM). True bila sukses.

    Hanya di Windows dan bila Microsoft PowerPoint terpasang. Hasilnya
    **100% mengikuti format asli** (tema, gambar, warna, layout) karena
    memakai mesin Office yang sama.
    """
    if os.name != "nt":
        return False

    try:
        import pythoncom  # pywin32
        import win32com.client  # pywin32
    except ImportError:
        return False

    if file_kind(input_path) != "ppt":
        return False

    input_abs = os.path.abspath(input_path)
    output_abs = os.path.abspath(output_path)

    app = None
    doc = None
    # WAJIB: inisialisasi COM untuk thread ini. Tanpa ini, panggilan COM dari
    # worker thread (bukan main thread) bisa MENGGANTUNG tanpa error.
    com_initialized = False
    try:
        pythoncom.CoInitialize()
        com_initialized = True
    except Exception:
        return False

    try:
        app = win32com.client.DispatchEx("PowerPoint.Application")
        doc = app.Presentations.Open(
            input_abs, WithWindow=False, ReadOnly=True
        )
        # 32 = ppSaveAsPDF
        doc.SaveAs(output_abs, 32)

        return os.path.isfile(output_abs) and os.path.getsize(output_abs) > 0

    except Exception:
        return False

    finally:
        # Tutup dokumen & aplikasi dengan aman (abaikan error apa pun).
        try:
            if doc is not None:
                doc.Close()
        except Exception:
            pass
        try:
            if app is not None:
                app.Quit()
        except Exception:
            pass
        if com_initialized:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass


def find_office_com():
    """Kembalikan True bila Microsoft PowerPoint COM tersedia.

    Dipakai UI/CLI/diagnostik untuk memberi tahu pengguna mesin mana yang
    dipakai. Tidak membuka aplikasi apa pun.
    """
    if os.name != "nt":
        return False
    try:
        import win32com.client  # noqa: F401
    except ImportError:
        return False
    return True


def _convert_office_with_soffice(input_path, output_path):
    """Konversi office via LibreOffice. True bila sukses menghasilkan PDF."""
    soffice = find_soffice()
    if not soffice:
        return False

    # LibreOffice menulis sendiri nama output (mengikuti nama sumber),
    # jadi kita konversi ke folder sementara lalu pindahkan ke tujuan.
    with tempfile.TemporaryDirectory() as tmp_dir:
        cmd = [
            soffice,
            "--headless",
            "--norestore",
            "--convert-to",
            "pdf",
            "--outdir",
            tmp_dir,
            input_path,
        ]
        try:
            subprocess.run(
                cmd, check=True, capture_output=True, timeout=180
            )
        except (subprocess.SubprocessError, OSError):
            return False

        expected = os.path.join(
            tmp_dir,
            os.path.splitext(os.path.basename(input_path))[0] + ".pdf",
        )
        if not os.path.isfile(expected):
            return False

        try:
            os.replace(expected, output_path)
            return True
        except OSError:
            shutil.copyfile(expected, output_path)
            return True


def _wrap_text(text, fontname, fontsize, max_width):
    """Pecah teks menjadi baris-baris agar muat dalam `max_width` (point).

    Memakai pengukuran lebar teks PyMuPDF. Berguna karena `insert_text`
    tidak otomatis membungkus paragraf panjang.
    """
    text = text.rstrip()
    if not text:
        return [""]

    words = text.split(" ")
    lines = []
    current = ""

    for word in words:
        candidate = word if not current else current + " " + word
        width = pymupdf.get_text_length(candidate, fontname=fontname, fontsize=fontsize)
        if width <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word

    if current:
        lines.append(current)
    return lines


def _convert_pptx_fallback(input_path, output_path):
    """Fallback PPT tanpa LibreOffice: satu slide → satu halaman PDF (teks)."""
    from pptx import Presentation  # python-pptx

    prs = Presentation(input_path)

    # Ukuran halaman mengikuti ukuran slide (EMU → point: 1 pt = 12700 EMU).
    slide_w = prs.slide_width or 9144000
    slide_h = prs.slide_height or 6858000
    width = slide_w / 12700
    height = slide_h / 12700

    margin = 36
    fontname = "helv"
    fontsize = 12
    line_height = fontsize * 1.4
    max_width = width - 2 * margin

    doc = pymupdf.open()
    try:
        for slide in prs.slides:
            texts = []
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        line = "".join(run.text for run in para.runs)
                        if line.strip():
                            texts.append(line)

            page = doc.new_page(width=width, height=height)
            y = margin + fontsize
            for text in texts:
                for line in _wrap_text(text, fontname, fontsize, max_width):
                    if y > height - margin:
                        break
                    page.insert_text(
                        (margin, y),
                        line,
                        fontsize=fontsize,
                        fontname=fontname,
                    )
                    y += line_height

        if len(doc) == 0:
            doc.new_page(width=width, height=height)

        doc.save(output_path, garbage=4, deflate=True)
    finally:
        doc.close()


def convert_to_pdf(input_path, output_path):
    """Konversi file apa pun yang didukung menjadi PDF di `output_path`.

    Raises:
        ValueError: jenis file tidak dikenali/didukung.
        Exception: error konversi diteruskan ke pemanggil.

    Returns:
        Path `output_path` bila berhasil.
    """
    kind = file_kind(input_path)

    if kind == "unknown":
        raise ValueError(
            f"Jenis file tidak didukung: {os.path.basename(input_path)}"
        )

    if kind == "image":
        _convert_image_to_pdf(input_path, output_path)
        return output_path

    if kind == "ppt":
        # 1) Microsoft PowerPoint (COM) — format 100% utuh (Windows + Office).
        if _convert_with_ppt_com(input_path, output_path):
            return output_path

        # 2) LibreOffice (soffice) — sangat akurat, lintas platform.
        if _convert_office_with_soffice(input_path, output_path):
            return output_path

        # 3) Fallback murni Python (butuh python-pptx).
        _convert_pptx_fallback(input_path, output_path)
        return output_path

    raise ValueError(
        f"File sudah berupa PDF, tidak perlu konversi: "
        f"{os.path.basename(input_path)}"
    )


