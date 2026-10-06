# -*- mode: python ; coding: utf-8 -*-
"""Spec PyInstaller untuk PDF Multi Slide Pro (mode onedir + onefile).

Dipakai oleh build_installer.ps1. Menghasilkan:
  dist/PDFMultiSlidePro/PDFMultiSlidePro.exe          (onedir, untuk installer)
  dist/PDFMultiSlidePro-Portable.exe                  (onefile, portable)

Catatan:
- tkinterdnd2 butuh file data (tkdnd native lib) -> dikumpulkan otomatis.
- PyMuPDF (pymupdf) punya native lib -> jangan di-exclude; biarkan collect.
- GUI mode: console=False (tanpa jendela hitam). CLI tetap tersedia via
  PDFMultiSlidePro.exe dengan argumen? Tidak -- GUI & CLI dipisah (lihat catatan di README_BUILD).
"""

import os

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

SPEC_DIR = os.path.abspath(os.path.dirname(SPEC))
PROJECT_DIR = os.path.dirname(SPEC_DIR)
ENTRY_SCRIPT = os.path.join(PROJECT_DIR, "main.py")
BUILD_ASSETS = SPEC_DIR
ICON_PATH = os.path.join(BUILD_ASSETS, "app.ico")
VERSION_FILE = os.path.join(BUILD_ASSETS, "version_info.txt")

# --- Data files --------------------------------------------------------
# tkinterdnd2 membawa library tkdnd (folder tkdnd2/). Wajib ikut dibundel.
datas = []
try:
    datas += collect_data_files("tkinterdnd2")
except Exception:
    # tkinterdnd2 opsional: aplikasi tetap jalan tanpa drag & drop.
    pass

# Ikon jendela aplikasi (dipakai utils.fs.app_icon_path saat runtime).
datas += [(os.path.join(BUILD_ASSETS, "app.ico"), "build_assets")]

# --- Hidden imports ----------------------------------------------------
hiddenimports = []
try:
    hiddenimports += collect_submodules("tkinterdnd2")
except Exception:
    pass

# PyMuPDF kadang butuh submodul ini agar tidak "no module named".
hiddenimports += ["pymupdf", "pymupdf.utils", "pymupdf._extra"]

# Konversi PowerPoint (opsional): modul diimpor dinamis di dalam fungsi, jadi
# PyInstaller bisa melewatkannya. Tambahkan bila terpasang.
for _mod in ("pptx", "win32com", "win32com.client", "pythoncom", "pywintypes"):
    try:
        __import__(_mod)
        hiddenimports.append(_mod)
    except Exception:
        pass

# Modul yang TIDAK dipakai aplikasi -> dikecualikan agar exe kecil & cepat.
# (Terverifikasi: pymupdf tidak mengimpor numpy/pandas/scipy.)
EXCLUDES = [
    "fitz",          # binding lama; kita pakai pymupdf
    "numpy",
    "pandas",
    "scipy",
    "matplotlib",
    "PIL.ImageQt",
    "IPython",
    "pytest",
    "setuptools",
    "pip",
    "tkinter.test",
    "unittest",
    "pydoc_data",
]

block_cipher = None


# ======================================================================
# ONEDIR  -> dipakai installer (start cepat, isi folder).
# ======================================================================
a_onedir = Analysis(
    [ENTRY_SCRIPT],
    pathex=[PROJECT_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz_onedir = PYZ(a_onedir.pure, a_onedir.zipped_data, cipher=block_cipher)

exe_onedir = EXE(
    pyz_onedir,
    a_onedir.scripts,
    a_onedir.binaries,
    a_onedir.zipfiles,
    a_onedir.datas,
    [],
    name="PDFMultiSlidePro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_PATH,
    version=VERSION_FILE,
)

coll_onedir = COLLECT(
    exe_onedir,
    a_onedir.binaries,
    a_onedir.zipfiles,
    a_onedir.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="PDFMultiSlidePro",
)


# ======================================================================
# ONEFILE -> portable, satu file .exe.
# ======================================================================
a_onefile = Analysis(
    [ENTRY_SCRIPT],
    pathex=[PROJECT_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz_onefile = PYZ(a_onefile.pure, a_onefile.zipped_data, cipher=block_cipher)

exe_onefile = EXE(
    pyz_onefile,
    a_onefile.scripts,
    a_onefile.binaries,
    a_onefile.zipfiles,
    a_onefile.datas,
    [],
    name="PDFMultiSlidePro-Portable",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_PATH,
    version=VERSION_FILE,
)
