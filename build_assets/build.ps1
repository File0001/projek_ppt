# ======================================================================
# Build script: PDF Multi Slide Pro
# Menghasilkan:
#   1. dist\PDFMultiSlidePro\PDFMultiSlidePro.exe        (onedir, untuk installer)
#   2. dist\PDFMultiSlidePro-Portable.exe                (onefile, portable)
#   3. dist\installer\PDFMultiSlidePro-Setup-1.0.0.exe   (installer Inno Setup)
#
# Cara pakai (dari root project):
#   powershell -ExecutionPolicy Bypass -File build_assets\build.ps1
# Opsi:
#   -SkipInstaller   -> hanya build .exe (tanpa installer)
#   -Clean           -> hapus build/ dist/ dulu
# ======================================================================

[CmdletBinding()]
param(
    [switch]$SkipInstaller,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

# --- Lokasi -----------------------------------------------------------
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

$SpecFile  = Join-Path $ScriptDir "PDFMultiSlidePro.spec"
$Version   = "1.0.0"
$DistDir   = Join-Path $ProjectRoot "dist"
$InstSetup = Join-Path $DistDir "installer"

function Write-Section($text) {
    Write-Host ""
    Write-Host "===================================================" -ForegroundColor Cyan
    Write-Host " $text" -ForegroundColor Cyan
    Write-Host "===================================================" -ForegroundColor Cyan
}

# --- 0. Cek prasyarat -------------------------------------------------
Write-Section "0/5  Cek prasyarat"

try {
    python -c "import PyInstaller" 2>$null
    $pyiVer = python -c "import PyInstaller; print(PyInstaller.__version__)"
    Write-Host "[OK] PyInstaller $pyiVer" -ForegroundColor Green
} catch {
    throw "PyInstaller belum terpasang. Jalankan: pip install pyinstaller"
}

try {
    python -c "import pymupdf" 2>$null
    Write-Host "[OK] PyMuPDF" -ForegroundColor Green
} catch {
    throw "PyMuPDF belum terpasang. Jalankan: pip install -r requirements.txt"
}

if (-not (Test-Path (Join-Path $ScriptDir "app.ico"))) {
    Write-Host "[!] app.ico tidak ada - menjalankan pembuat ikon..." -ForegroundColor Yellow
    python (Join-Path $ScriptDir "make_icon.py")
}

# --- Proses GUI yang mungkin mengunci file ----------------------------
$running = Get-Process -Name "PDFMultiSlidePro", "PDFMultiSlidePro-Portable" -ErrorAction SilentlyContinue
if ($running) {
    Write-Host "[!] Aplikasi hasil build sedang berjalan. Menutup paksa..." -ForegroundColor Yellow
    $running | Stop-Process -Force
    Start-Sleep -Seconds 1
}

# --- 1. Bersihkan (opsional) -----------------------------------------
if ($Clean) {
    Write-Section "1/5  Bersihkan build lama"
    Remove-Item -Recurse -Force (Join-Path $ProjectRoot "build") -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force $DistDir -ErrorAction SilentlyContinue
    Write-Host "[OK] build\ dan dist\ dihapus" -ForegroundColor Green
}

# --- 2. Build .exe ----------------------------------------------------
Write-Section "2/5  Build .exe (PyInstaller)"
python -m PyInstaller --noconfirm --clean $SpecFile
if ($LASTEXITCODE -ne 0) { throw "PyInstaller gagal (exit $LASTEXITCODE)." }

$ExeOnedir   = Join-Path $DistDir "PDFMultiSlidePro\PDFMultiSlidePro.exe"
$ExePortable = Join-Path $DistDir "PDFMultiSlidePro-Portable.exe"

# --- 3. Verifikasi hasil ---------------------------------------------
Write-Section "3/5  Verifikasi hasil build"
foreach ($f in @($ExeOnedir, $ExePortable)) {
    if (Test-Path $f) {
        $mb = [math]::Round((Get-Item $f).Length / 1MB, 1)
        Write-Host "[OK] $f  ($mb MB)" -ForegroundColor Green
    } else {
        throw "File hasil tidak ditemukan: $f"
    }
}

# --- 4. Buat installer (Inno Setup) ----------------------------------
if ($SkipInstaller) {
    Write-Host "[i] -SkipInstaller aktif: installer dilewati." -ForegroundColor Yellow
} else {
    Write-Section "4/5  Buat installer (Inno Setup)"

    $Iscc = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1

    if (-not $Iscc) {
        Write-Host "[!] Inno Setup tidak ditemukan - installer dilewati." -ForegroundColor Yellow
        Write-Host "    Unduh: https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    } else {
        New-Item -ItemType Directory -Force -Path $InstSetup | Out-Null
        & $Iscc "/DMyAppVersion=$Version" (Join-Path $ScriptDir "installer.iss")
        if ($LASTEXITCODE -ne 0) { throw "Inno Setup gagal (exit $LASTEXITCODE)." }

        $Installer = Get-ChildItem $InstSetup -Filter "*.exe" | Select-Object -First 1
        if ($Installer) {
            $mb = [math]::Round($Installer.Length / 1MB, 1)
            Write-Host "[OK] $($Installer.FullName)  ($mb MB)" -ForegroundColor Green
        }
    }
}

# --- 5. Ringkasan -----------------------------------------------------
Write-Section "5/5  Selesai"
Write-Host "Portable : dist\PDFMultiSlidePro-Portable.exe" -ForegroundColor White
Write-Host "Installer: dist\installer\PDFMultiSlidePro-Setup-$Version.exe" -ForegroundColor White
Write-Host ""
