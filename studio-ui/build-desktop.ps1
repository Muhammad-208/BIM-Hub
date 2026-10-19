# Build "BIM Hub Studio" for Windows → installer .exe (NSIS) + .msi
#   powershell -ExecutionPolicy Bypass -File "E:\Ai\BIM Hub\studio-ui\build-desktop.ps1"
# Needs once: Node.js 20+, Rust (https://rustup.rs, MSVC toolchain), and the hub installed (install.ps1 → mcp-layer\.venv).
$ErrorActionPreference = "Stop"
$Ui    = Split-Path -Parent $MyInvocation.MyCommand.Path
$Hub   = Split-Path -Parent $Ui
$Layer = Join-Path $Hub "mcp-layer"
$VPy   = Join-Path $Layer ".venv\Scripts\python.exe"
if (-not (Test-Path $VPy)) { throw "Run install.ps1 first (mcp-layer\.venv missing)" }

Push-Location $Ui
Write-Host "1/4 UI (React + three.js)" -ForegroundColor Cyan
npm install --no-fund --no-audit
npm run build
$UiTarget = Join-Path $Layer "src\bimhub\studio\ui"
if (Test-Path $UiTarget) { Remove-Item $UiTarget -Recurse -Force }
Copy-Item dist $UiTarget -Recurse

Write-Host "2/4 Backend sidecar (PyInstaller)" -ForegroundColor Cyan
& $VPy -m pip install --quiet -e "$Layer[studio,ingest]" pyinstaller
& $VPy -m PyInstaller --noconfirm --clean --onefile --name bimhub-studio `
    --collect-submodules bimhub --collect-data bimhub `
    --hidden-import uvicorn.logging --hidden-import uvicorn.loops.auto --hidden-import uvicorn.protocols.http.auto `
    --hidden-import uvicorn.protocols.websockets.auto --hidden-import uvicorn.lifespan.on `
    --distpath desktop\dist --workpath desktop\build --specpath desktop `
    desktop\studio_entry.py
New-Item -ItemType Directory -Force -Path src-tauri\binaries | Out-Null
Copy-Item desktop\dist\bimhub-studio.exe src-tauri\binaries\bimhub-studio-x86_64-pc-windows-msvc.exe -Force

Write-Host "3/4 Icons" -ForegroundColor Cyan
npx tauri icon desktop\app-icon.png -o src-tauri\icons

Write-Host "4/4 Desktop app (Tauri)" -ForegroundColor Cyan
npx tauri build
Pop-Location

$out = Join-Path $Ui "src-tauri\target\release\bundle"
Write-Host "`nDone. Installers:" -ForegroundColor Green
Get-ChildItem $out -Recurse -Include *.exe, *.msi | ForEach-Object { Write-Host "  $($_.FullName)" }
