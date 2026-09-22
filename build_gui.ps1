$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$releaseDir = Join-Path $projectRoot "dist\GoExport-GUI"
$temporaryDist = Join-Path $projectRoot "gui-build-output"
$temporaryWork = Join-Path $projectRoot "build\GoExport-GUI"

& "$projectRoot\.venv\Scripts\python.exe" -m PyInstaller `
    "$projectRoot\GoExport-GUI.spec" `
    --noconfirm `
    --clean `
    --distpath $temporaryDist `
    --workpath $temporaryWork

New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null
$builtGui = "$temporaryDist\GoExport-GUI.exe"
$publishedGui = "$releaseDir\GoExport-GUI.exe"
try {
    Copy-Item $builtGui $publishedGui -Force -ErrorAction Stop
} catch [System.IO.IOException] {
    $pendingGui = "$releaseDir\GoExport-GUI.updated.exe"
    Copy-Item $builtGui $pendingGui -Force
    Write-Warning "GoExport-GUI.exe is currently open. The update was saved as GoExport-GUI.updated.exe."
}
Copy-Item "$projectRoot\presets.toml" "$releaseDir\presets.toml" -Force
Copy-Item "$projectRoot\version.txt" "$releaseDir\version.txt" -Force

if ($temporaryDist.StartsWith($projectRoot + "\")) {
    Remove-Item -LiteralPath $temporaryDist -Recurse -Force
}
if ($temporaryWork.StartsWith($projectRoot + "\")) {
    Remove-Item -LiteralPath $temporaryWork -Recurse -Force
}

Write-Host "Updated dist\GoExport-GUI\GoExport-GUI.exe"
Write-Host "The existing GoExport.exe, bin, resources, and _internal files were preserved."
