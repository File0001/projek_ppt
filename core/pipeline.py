"""Orkestrasi batch: proses banyak PDF → satu PDF hasil.

UI-agnostic: kemajuan dilaporkan lewat callback, sehingga pipeline yang sama
dapat dipakai oleh GUI, CLI, maupun test.
"""

import os

import pymupdf

from core.convert import (
    convert_to_pdf,
    file_kind,
    images_to_pdf,
)
from core.nup import create_nup_pdf
from utils.fs import make_temp_path, safe_remove, safe_replace



def process_all(
    input_paths,
    output_path,
    cols,
    rows,
    orientation,
    number_slides=False,
    on_status=None,
    on_progress=None,
    allow_overwrite_source=False,
    pad_even=False,
):
    """Proses semua file sumber lalu gabungkan jadi satu file output.

    File sumber boleh beragam jenis: PDF, gambar (png/jpg/dll), atau
    PowerPoint (.pptx/.ppt). Sumber non-PDF dikonversi otomatis ke PDF
    terlebih dahulu (lihat `core.convert`).

    Args:
        input_paths: daftar path sumber (urutan = urutan output).

        output_path: path PDF hasil akhir.
        cols, rows: grid N-up.
        orientation: "Portrait" / "Landscape".
        number_slides: tulis nomor slide di PDF hasil.
        on_status: callback(text) opsional untuk pesan status.
        on_progress: callback(percent) opsional untuk progress 0..100.
        allow_overwrite_source: bila False (default), menolak output yang
            sama dengan file sumber. Bila True, mengizinkan menimpa file
            sumber (caller sudah mengonfirmasi; aman karena sumber hanya
            dibaca sebelum output final ditulis).
        pad_even: bila True, jumlah halaman hasil TIAP file dibuat genap
            (ditambah 1 halaman kosong bila ganjil) SEBELUM digabung. Ini
            memastikan tiap file mulai di halaman baru — dipakai untuk cetak
            bolak-balik (duplex). Default False (tidak menambah halaman).

    Raises:
        ValueError: output sama dengan sumber padahal tidak diizinkan.
        Exception: error apa pun diteruskan ke pemanggil; temp selalu dibersihkan.
    """

    def status(text):
        if on_status:
            on_status(text)

    def progress(value):
        if on_progress:
            on_progress(value)

    # Pengaman: output = salah satu sumber.
    if not allow_overwrite_source:
        source_keys = {os.path.abspath(p).lower() for p in input_paths}
        if os.path.abspath(output_path).lower() in source_keys:
            raise ValueError(
                "Output tidak boleh sama dengan file sumber "
                "(tanpa izin menimpa)."
            )

    # temp_files   : file hasil N-up yang akan DIGABUNG (urutan penting).
    # cleanup_files: SEMUA file sementara (termasuk PDF hasil konversi).
    temp_files = []
    cleanup_files = []
    staging_path = None

    try:
        # ==============================================================
        # FASE 1 — Konversi SEMUA sumber ke PDF terlebih dahulu.
        #   - Gambar  : digabung jadi SATU PDF (1 gambar = 1 halaman).
        #   - PPT     : tiap file -> 1 PDF sendiri.
        #   - PDF asli: dipakai langsung.
        # Hasilnya: daftar `pdf_inputs` (semuanya sudah berwujud PDF).
        # ==============================================================
        pdf_inputs = []  # daftar (path_pdf, label_sumber)
        image_buffer = []  # kumpulkan gambar dulu untuk digabung

        def _flush_images():
            """Gabungkan gambar yang terkumpul jadi 1 PDF, masukkan ke daftar."""
            if not image_buffer:
                return
            converted = make_temp_path(output_path, f"IMGS{len(pdf_inputs)}")
            cleanup_files.append(converted)
            status(
                f"Menggabungkan {len(image_buffer)} gambar menjadi 1 PDF..."
            )
            images_to_pdf(list(image_buffer), converted)
            pdf_inputs.append((converted, f"{len(image_buffer)} gambar"))
            image_buffer.clear()

        for source_path in input_paths:
            kind = file_kind(source_path)
            name = os.path.basename(source_path)

            if kind == "pdf":
                # PDF asli: tidak perlu dikonversi.
                pdf_inputs.append((source_path, name))
                continue

            if kind == "image":
                # Tunda: gabungkan semua gambar di akhir jadi 1 PDF.
                image_buffer.append(source_path)
                continue

            if kind == "ppt":
                # PowerPoint: tiap file -> 1 PDF sendiri.
                converted = make_temp_path(
                    output_path, f"PPT{len(pdf_inputs)}"
                )
                cleanup_files.append(converted)
                status(f"Mengonversi PowerPoint: {name}")
                convert_to_pdf(source_path, converted)
                pdf_inputs.append((converted, name))

        # Gambar yang terkumpul digabung jadi SATU PDF di akhir fase ini.
        _flush_images()

        # ==============================================================
        # FASE 2 — Semua sudah PDF: proses N-up per file lalu gabungkan.
        # ==============================================================
        count = len(pdf_inputs)
        for i, (pdf_source, label) in enumerate(pdf_inputs, 1):
            status(f"Memproses halaman {i} dari {count}: {label}")

            temp_path = make_temp_path(output_path, i)
            cleanup_files.append(temp_path)
            temp_files.append(temp_path)

            create_nup_pdf(
                pdf_source,
                temp_path,
                cols=cols,
                rows=rows,
                orientation=orientation,
                number_slides=number_slides,
                pad_even=pad_even,
            )

            progress((i / count) * 80)

        # ----------------------------------------------------------
        # Gabungkan hasil
        # ----------------------------------------------------------
        status("Menggabungkan semua PDF hasil...")

        # Simpan dulu ke file sementara di folder output, BARU pindahkan ke
        # tujuan. Ini menghindari error "cannot remove file: Permission denied"
        # saat file tujuan sudah ada & masih terkunci (mis. sedang dibuka).
        staging_path = make_temp_path(output_path, "FINAL")

        final = pymupdf.open()
        try:
            for temp in temp_files:
                part = pymupdf.open(temp)
                try:
                    final.insert_pdf(part)
                finally:
                    part.close()

            final.save(staging_path, garbage=4, deflate=True)
        finally:
            final.close()

        # Pindahkan staging -> output (menggantikan bila sudah ada).
        if not safe_replace(staging_path, output_path):
            safe_remove(staging_path)
            staging_path = None
            raise PermissionError(
                f"Tidak bisa menulis hasil ke '{output_path}'. "
                "File mungkin sedang dibuka di aplikasi lain (PDF viewer) — "
                "tutup file itu lalu coba lagi."
            )
        staging_path = None

        # ----------------------------------------------------------
        # Hapus temp
        # ----------------------------------------------------------
        for temp in cleanup_files:
            safe_remove(temp)

        progress(100)
        return output_path

    except Exception:
        for temp in cleanup_files:
            safe_remove(temp)
        if staging_path:
            safe_remove(staging_path)
        raise
