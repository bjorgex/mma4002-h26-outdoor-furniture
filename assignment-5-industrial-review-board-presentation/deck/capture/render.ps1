param([string]$Deck, [string]$OutDir)
New-Item -ItemType Directory -Force $OutDir | Out-Null
Get-ChildItem $OutDir -Filter *.png | Remove-Item -Force
$app = New-Object -ComObject PowerPoint.Application
try {
  $p = $app.Presentations.Open((Resolve-Path $Deck).Path, $true, $false, $false)  # read-only, no title, no window
  $i = 0
  foreach ($s in $p.Slides) { $i++; $s.Export((Join-Path $OutDir ("slide-{0:D2}.png" -f $i)), "PNG", 1600, 900) }
  $p.Close()
  "exported $i slides"
} finally { $app.Quit() | Out-Null }
