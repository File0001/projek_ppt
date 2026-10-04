"""Orkestrasi batch: proses banyak PDF → satu PDF hasil.

UI-agnostic: kemajuan dilaporkan lewat callback, sehingga pipeline yang sama
dapat dipakai oleh GUI, CLI, maupun test.
"""

import os

import pymupdf

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
    pad_even=True,
):
    """Proses semua PDF lalu gabungkan jadi satu file output.

    Args:
        input_paths: daftar path PDF sumber (urutan = urutan output).
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
        pad_even: bila True (default), jumlah halaman hasil TIAP file
            dibuat genap (ditambah 1 halaman kosong bila ganjil) SEBELUM
            digabung. Ini memastikan tiap file mulai di halaman baru.

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

    temp_files = []
    staging_path = None
    total = len(input_paths)

    try:
        # ----------------------------------------------------------
        # Proses tiap PDF secara terpisah -> file temp
        # ----------------------------------------------------------
        for i, source_path in enumerate(input_paths, 1):
            status(f"Memproses PDF {i} dari {total}: {source_path}")

            temp_path = make_temp_path(output_path, i)
            temp_files.append(temp_path)

            create_nup_pdf(
                source_path,
                temp_path,
                cols=cols,
                rows=rows,
                orientation=orientation,
                number_slides=number_slides,
                pad_even=pad_even,
            )

            progress((i / total) * 80)

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
        for temp in temp_files:
            safe_remove(temp)

        progress(100)
        return output_path

    except Exception:
        for temp in temp_files:
            safe_remove(temp)
        if staging_path:
            safe_remove(staging_path)
        raise
