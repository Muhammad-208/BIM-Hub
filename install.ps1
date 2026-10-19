# BIM Hub installer — run from anywhere:
#   powershell -ExecutionPolicy Bypass -File "E:\Ai\BIM Hub\install.ps1"
$ErrorActionPreference = "Stop"
$Hub   = Split-Path -Parent $MyInvocation.MyCommand.Path
$Layer = Join-Path $Hub "mcp-layer"
$Venv  = Join-Path $Layer ".venv"

# 1) find a Python >= 3.10 (py launcher first, then python on PATH)
$py = $null; $pyArgs = @()
foreach ($c in @("py -3.12", "py -3.11", "py -3.10", "py -3", "python")) {
    $parts = $c.Split(" ")
    $exe = $parts[0]
    $a = @(); if ($parts.Length -gt 1) { $a = @($parts[1]) }
    try {
        $v = & $exe @a -c "import sys;print('%d.%d'%sys.version_info[:2])" 2>$null
        if ($LASTEXITCODE -eq 0 -and $v -and [version]$v -ge [version]"3.10") { $py = $exe; $pyArgs = $a; break }
    } catch {}
}
if (-not $py) { throw "Python 3.10+ not found. Install from python.org (tick 'Add to PATH') and re-run." }
Write-Host "Using Python $v  ($py $pyArgs)" -ForegroundColor Cyan

# 2) venv + install
if (-not (Test-Path (Join-Path $Venv "Scripts\python.exe"))) {
    & $py @pyArgs -m venv $Venv
}
$VPy = Join-Path $Venv "Scripts\python.exe"
& $VPy -m pip install --upgrade pip --quiet
& $VPy -m pip install -e "$Layer[ingest,dev,studio]" --quiet
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }

# 3) tests + doctor
Push-Location $Layer
& $VPy -m pytest -q -p no:cacheprovider
Pop-Location
& $VPy -m bimhub.cli.main doctor

# 4) re-sync existing projects so .mcp.json points at this venv's python
& $VPy -m bimhub.cli.main sync

Write-Host "`nDone. Use:  `"$Hub\bimhub.cmd`" <command>   (or add $Hub to PATH and just type: bimhub ...)" -ForegroundColor Green
