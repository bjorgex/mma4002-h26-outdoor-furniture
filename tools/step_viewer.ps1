# Browse the repo's STEP files in a 3D viewer (three.js + occt-import-js, runs in the browser).
#   powershell -ExecutionPolicy Bypass -File tools\step_viewer.ps1 [FileName.STEP]
# Then in VS Code: Ctrl+Shift+P > "Simple Browser: Show" > the URL printed below (or any browser).
# Needs Python (for a local web server: browsers won't fetch local files from file:// pages).
param([string]$File = "JigV3.STEP", [int]$Port = 8765)
$repo = Split-Path $PSScriptRoot -Parent
Push-Location $repo
git ls-files "*.step" "*.STEP" "*.stp" "*.STP" | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $PSScriptRoot "step_files.json")
$url = "http://127.0.0.1:$Port/tools/step_viewer.html?f=$File"
Write-Host "STEP viewer: $url   (Ctrl+C stops the server)"
python -m http.server $Port --bind 127.0.0.1
Pop-Location
