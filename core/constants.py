"""Konstanta global untuk PDF Multi Slide Pro.

Menggantikan magic number yang sebelumnya tersebar di file monolitik.
"""

# ------------------------------------------------------------------
# Konversi unit
# ------------------------------------------------------------------

# 1 mm = 2.83465 point (1 point = 1/72 inci)
MM_TO_PT = 2.83465


# ------------------------------------------------------------------
# Ukuran kertas
# ------------------------------------------------------------------

# A4 dalam point (595.2756 x 841.8898 pt).
# Portrait: lebar x tinggi. Landscape ditukar oleh kode pemanggil.
A4_WIDTH_PT = 595.2756
A4_HEIGHT_PT = 841.8898

PAPER_SIZE = "A4"


# ------------------------------------------------------------------
# Layout default (tidak ditampilkan di UI)
# ------------------------------------------------------------------

MARGIN_MM = 3  # margin halaman (mm)
GAP_MM = 3     # jarak antar sel (mm)

MARGIN_PT = MARGIN_MM * MM_TO_PT
GAP_PT = GAP_MM * MM_TO_PT


# ------------------------------------------------------------------
# Batasan grid
# ------------------------------------------------------------------

MIN_GRID = 1
MAX_GRID = 100
MAX_SLIDES_PER_PAGE = 100


# ------------------------------------------------------------------
# Orientasi
# ------------------------------------------------------------------

ORIENTATION_PORTRAIT = "Portrait"
ORIENTATION_LANDSCAPE = "Landscape"
