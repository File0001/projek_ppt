"""Inti konversi N-up PDF.

Fungsi murni / headless: TIDAK membaca state UI, semua parameter diterima
eksplisit. Ini memisahkan logika PDF dari tkinter sehingga bisa dipakai ulang
(CLI, test) dan mudah diuji.
"""

import pymupdf

from core.constants import (
    A4_HEIGHT_PT,
    A4_WIDTH_PT,
    GAP_PT,
    MARGIN_PT,
    ORIENTATION_LANDSCAPE,
)


class LayoutError(ValueError):
    """Layout tidak muat di halaman (mis. grid terlalu besar)."""


def compute_page_geometry(orientation):
    """Kembalikan (width, height) halaman A4 dalam point sesuai orientasi."""
    width = A4_WIDTH_PT
    height = A4_HEIGHT_PT

    if orientation == ORIENTATION_LANDSCAPE:
        width, height = height, width

    return width, height


def compute_grid(size, cols, rows, margin=MARGIN_PT, gap=GAP_PT):
    """Hitung geometri grid N-up pada satu halaman.

    Args:
        size: (width, height) halaman tujuan dalam point.
        cols: jumlah kolom.
        rows: jumlah baris.
        margin: margin halaman (point).
        gap: jarak antar sel (point).

    Returns:
        dict berisi cell_w, cell_h, margin, gap, cols, rows.

    Raises:
        LayoutError: bila area yang tersedia <= 0.
    """
    width, height = size

    usable_w = width - 2 * margin - gap * (cols - 1)
    usable_h = height - 2 * margin - gap * (rows - 1)

    if usable_w <= 0 or usable_h <= 0:
        raise LayoutError("Layout terlalu besar untuk halaman A4.")

    return {
        "cell_w": usable_w / cols,
        "cell_h": usable_h / rows,
        "margin": margin,
        "gap": gap,
        "cols": cols,
        "rows": rows,
    }


def compute_cell_rect(grid, position):
    """Kotak (x0, y0, x1, y1) untuk sel ke-`position` (row-major)."""
    cols = grid["cols"]
    row = position // cols
    col = position % cols

    x0 = grid["margin"] + col * (grid["cell_w"] + grid["gap"])
    y0 = grid["margin"] + row * (grid["cell_h"] + grid["gap"])

    return x0, y0, x0 + grid["cell_w"], y0 + grid["cell_h"]


def fit_rect_in_cell(cell, source_rect):
    """Hitung rect target di tengah `cell` agar `source_rect` pas (letterbox).

    Menjaga aspect ratio sumber; menghasilkan area yang di-center.
    """
    cell_x0, cell_y0, cell_x1, cell_y1 = cell
    cell_w = cell_x1 - cell_x0
    cell_h = cell_y1 - cell_y0

    source_ratio = source_rect.width / source_rect.height
    cell_ratio = cell_w / cell_h

    if source_ratio > cell_ratio:
        new_w = cell_w
        new_h = new_w / source_ratio
    else:
        new_h = cell_h
        new_w = new_h * source_ratio

    centered_x = cell_x0 + (cell_w - new_w) / 2
    centered_y = cell_y0 + (cell_h - new_h) / 2

    return pymupdf.Rect(
        centered_x,
        centered_y,
        centered_x + new_w,
        centered_y + new_h,
    )


def create_nup_pdf(
    input_path,
    output_path,
    cols,
    rows,
    orientation,
    number_slides=False,
    pad_even=True,
):
    """Buat PDF N-up dari satu file sumber.

    Args:
        input_path: path PDF sumber.
        output_path: path PDF hasil.
        cols: jumlah kolom grid.
        rows: jumlah baris grid.
        orientation: "Portrait" atau "Landscape".
        number_slides: bila True, tulis "Slide N" di area atas tiap sel.
        pad_even: bila True (default), jumlah halaman hasil dibuat GENAP.
            Jika hasil ganjil, ditambahkan satu halaman kosong (A4, orientasi
            sama) di akhir file. Ini memastikan tiap file mulai di halaman
            baru saat digabung (mis. untuk cetak duplex / bolak-balik).
    """
    source = pymupdf.open(input_path)
    result = pymupdf.open()

    try:
        width, height = compute_page_geometry(orientation)
        slides_per_page = cols * rows

        grid = compute_grid((width, height), cols, rows)

        for start in range(0, len(source), slides_per_page):
            page = result.new_page(width=width, height=height)

            end = min(start + slides_per_page, len(source))

            for position, slide_index in enumerate(range(start, end)):
                source_page = source[slide_index]

                cell = compute_cell_rect(grid, position)
                target = fit_rect_in_cell(cell, source_page.rect)

                # Vector embed: kualitas terjaga, tanpa rasterisasi.
                page.show_pdf_page(target, source, slide_index)

                if number_slides:
                    x0, y0, _, _ = cell
                    number_rect = pymupdf.Rect(
                        x0, y0, x0 + grid["cell_w"], y0 + 14
                    )
                    page.insert_textbox(
                        number_rect,
                        f"Slide {slide_index + 1}",
                        fontsize=7,
                        fontname="helv",
                        color=(0.2, 0.2, 0.2),
                        align=1,
                    )

        # Genapkan: bila jumlah halaman hasil ganjil, tambah 1 halaman kosong
        # agar tiap file selalu punya jumlah halaman genap sebelum digabung.
        if pad_even and len(result) % 2 == 1:
            result.new_page(width=width, height=height)

        # Penting: TIDAK ADA border pada PDF hasil.
        result.save(output_path, garbage=4, deflate=True)
    finally:
        source.close()
        result.close()

