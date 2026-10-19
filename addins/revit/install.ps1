# BIM Hub Revit bridge — build (optional) and install for every Revit 2020–2027 found on this PC.
#   powershell -ExecutionPolicy Bypass -File "E:\Ai\BIM Hub\addins\revit\install.ps1"            # install prebuilt
#   powershell -ExecutionPolicy Bypass -File "E:\Ai\BIM Hub\addins\revit\install.ps1" -Build     # rebuild first (needs .NET SDK 10)
#   ... -Versions 2024,2026     only some versions
#   ... -Uninstall              remove from all versions
param(
    [switch]$Build,
    [switch]$Uninstall,
    [int[]]$Versions = @(2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027)
)
$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path

foreach ($v in $Versions) {
    $revitExe  = "C:\Program Files\Autodesk\Revit $v\Revit.exe"
    $addinsDir = Join-Path $env:APPDATA "Autodesk\Revit\Addins\$v"
    $target    = Join-Path $addinsDir "BIMHub.Revit"

    if ($Uninstall) {
        Remove-Item (Join-Path $addinsDir "BIMHub.Revit.addin") -ErrorAction SilentlyContinue
        Remove-Item $target -Recurse -ErrorAction SilentlyContinue
        Write-Host "Revit $v : removed" -ForegroundColor Yellow
        continue
    }
    if (-not (Test-Path $revitExe)) { Write-Host "Revit $v : not installed — skipped" -ForegroundColor DarkGray; continue }

    $dll = Join-Path $Here "dist\$v\BIMHub.Revit.dll"
    if ($Build) {
        & dotnet build (Join-Path $Here "BIMHub.Revit.csproj") -c Release "-p:RevitVersion=$v" -nologo -v q
        if ($LASTEXITCODE -ne 0) { throw "Build failed for Revit $v" }
        $dll = Join-Path $Here "bin\Release\$v\BIMHub.Revit.dll"
    }
    if (-not (Test-Path $dll)) { throw "Missing $dll — run with -Build" }

    if (Get-Process -Name Revit -ErrorAction SilentlyContinue) {
        Write-Host "Revit is running — close it first so the DLL can be replaced." -ForegroundColor Red
        exit 1
    }
    New-Item -ItemType Directory -Force -Path $target | Out-Null
    Copy-Item $dll $target -Force
    Copy-Item (Join-Path $Here "BIMHub.Revit.addin") $addinsDir -Force
    Write-Host "Revit $v : installed → $addinsDir" -ForegroundColor Green
}
Write-Host "`nOpen Revit, accept 'Always Load' for BIM Hub Bridge, open a model, then from the hub run:  .\bimhub.cmd doctor" -ForegroundColor Cyan
