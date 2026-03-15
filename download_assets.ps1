$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifestPath = Join-Path $root "asset_sources.txt"
$plantsDir = Join-Path $root "assets\\plants"
$zombiesDir = Join-Path $root "assets\\zombies"
$gamePath = Join-Path $root "game.py"

New-Item -ItemType Directory -Force -Path $plantsDir | Out-Null
New-Item -ItemType Directory -Force -Path $zombiesDir | Out-Null

$lines = Get-Content -Encoding UTF8 $gamePath
$plantKeys = New-Object "System.Collections.Generic.HashSet[string]"
$zombieKeys = New-Object "System.Collections.Generic.HashSet[string]"
$mode = ""
foreach ($line in $lines) {
  if ($line -match "^PLANT_NAMES\\s*=\\s*\\{") { $mode = "plant"; continue }
  if ($line -match "^ZOMBIE_NAMES\\s*=\\s*\\{") { $mode = "zombie"; continue }
  if ($mode -ne "" -and $line -match "^\\}\\s*$") { $mode = ""; continue }
  if ($mode -ne "" -and $line -match "^\\s*\"([a-z0-9_]+)\"\\s*:") {
    if ($mode -eq "plant") { [void]$plantKeys.Add($matches[1]) } else { [void]$zombieKeys.Add($matches[1]) }
  }
}

Add-Type -AssemblyName System.Drawing

function Is-DisallowedPlaceholderSource([string]$url) {
  if ([string]::IsNullOrWhiteSpace($url)) { return $true }
  $u = $url.ToLowerInvariant()
  $blocked = @("twemoji", "openmoji", "emoji", "emojipedia", "noto-emoji", "icon", "symbol")
  foreach ($token in $blocked) {
    if ($u.Contains($token)) { return $true }
  }
  return $false
}

function Test-PngHeader([string]$path) {
  try {
    $bytes = [System.IO.File]::ReadAllBytes($path)
    if ($bytes.Length -lt 8) { return $false }
    return ($bytes[0] -eq 137 -and $bytes[1] -eq 80 -and $bytes[2] -eq 78 -and $bytes[3] -eq 71)
  } catch {
    return $false
  }
}

function Test-HasTransparency([string]$path) {
  try {
    $bmp = New-Object System.Drawing.Bitmap($path)
    $w = $bmp.Width
    $h = $bmp.Height
    $stepX = [Math]::Max(1, [Math]::Floor($w / 32))
    $stepY = [Math]::Max(1, [Math]::Floor($h / 32))
    $transparent = $false
    for ($y = 0; $y -lt $h -and -not $transparent; $y += $stepY) {
      for ($x = 0; $x -lt $w; $x += $stepX) {
        if ($bmp.GetPixel($x, $y).A -lt 250) { $transparent = $true; break }
      }
    }
    $bmp.Dispose()
    return $transparent
  } catch {
    return $false
  }
}

function Test-CharacterSilhouette([string]$path) {
  try {
    $bmp = New-Object System.Drawing.Bitmap($path)
    $w = $bmp.Width
    $h = $bmp.Height
    if ($w -lt 96 -or $h -lt 96) { $bmp.Dispose(); return $false } # reject tiny icon-sized

    $minX = $w; $minY = $h; $maxX = -1; $maxY = -1
    $opaqueCount = 0
    $sampled = 0
    $colors = New-Object "System.Collections.Generic.HashSet[string]"
    $stepX = [Math]::Max(1, [Math]::Floor($w / 48))
    $stepY = [Math]::Max(1, [Math]::Floor($h / 48))
    $transitions = 0
    $prevOpaque = $null

    for ($y = 0; $y -lt $h; $y += $stepY) {
      for ($x = 0; $x -lt $w; $x += $stepX) {
        $c = $bmp.GetPixel($x, $y)
        $isOpaque = $c.A -gt 180
        $sampled++
        if ($isOpaque) {
          $opaqueCount++
          if ($x -lt $minX) { $minX = $x }
          if ($y -lt $minY) { $minY = $y }
          if ($x -gt $maxX) { $maxX = $x }
          if ($y -gt $maxY) { $maxY = $y }
          [void]$colors.Add(("{0}-{1}-{2}" -f [int]($c.R/16), [int]($c.G/16), [int]($c.B/16)))
        }
        if ($null -ne $prevOpaque -and $prevOpaque -ne $isOpaque) { $transitions++ }
        $prevOpaque = $isOpaque
      }
    }

    if ($sampled -eq 0 -or $opaqueCount -eq 0) { $bmp.Dispose(); return $false }
    $opaqueRatio = $opaqueCount / $sampled
    if ($opaqueRatio -lt 0.08 -or $opaqueRatio -gt 0.82) { $bmp.Dispose(); return $false }

    $bboxW = ($maxX - $minX + 1)
    $bboxH = ($maxY - $minY + 1)
    if ($bboxW -lt 48 -or $bboxH -lt 48) { $bmp.Dispose(); return $false }
    $bboxRatio = ($bboxW * $bboxH) / [double]($w * $h)
    if ($bboxRatio -lt 0.12 -or $bboxRatio -gt 0.90) { $bmp.Dispose(); return $false }

    if ($colors.Count -lt 18) { $bmp.Dispose(); return $false } # reject simple placeholder symbols
    if ($transitions -lt [Math]::Max(14, [Math]::Floor($sampled / 40))) { $bmp.Dispose(); return $false }

    $bmp.Dispose()
    return $true
  } catch {
    return $false
  }
}

$entries = Get-Content -Encoding UTF8 $manifestPath | Where-Object { $_ -match "->" }
$outLines = New-Object "System.Collections.Generic.List[string]"
$downloaded = 0
$missing = 0

foreach ($line in $entries) {
  if ($line -notmatch "^\\s*([^\\s]+)\\s*->\\s*(.+?)\\s*$") { continue }
  $key = $matches[1].Trim()
  $url = $matches[2].Trim()

  $folder = $null
  if ($plantKeys.Contains($key)) { $folder = $plantsDir }
  elseif ($zombieKeys.Contains($key)) { $folder = $zombiesDir }
  else {
    $outLines.Add("$key -> NOT FOUND")
    $missing++
    continue
  }

  $target = Join-Path $folder ($key + ".png")
  $tmp = $target + ".download"
  if (Test-Path $tmp) { Remove-Item -Force $tmp }

  if ($url -eq "NOT FOUND") {
    if (Test-Path $target) { Remove-Item -Force $target }
    $outLines.Add("$key -> NOT FOUND")
    $missing++
    continue
  }
  if (Is-DisallowedPlaceholderSource $url) {
    if (Test-Path $target) { Remove-Item -Force $target }
    $outLines.Add("$key -> NOT FOUND")
    $missing++
    Write-Output "[rejected placeholder source] $key -> $url"
    continue
  }

  $ok = $false
  try {
    Invoke-WebRequest -Uri $url -OutFile $tmp -TimeoutSec 30 | Out-Null
    if ((Test-PngHeader $tmp) -and (Test-HasTransparency $tmp) -and (Test-CharacterSilhouette $tmp)) {
      Move-Item -Force $tmp $target
      $outLines.Add("$key -> $url")
      $downloaded++
      $ok = $true
      Write-Output "[downloaded] $key -> $target"
    }
  } catch {
    $ok = $false
  }

  if (-not $ok) {
    if (Test-Path $tmp) { Remove-Item -Force $tmp }
    if (Test-Path $target) { Remove-Item -Force $target }
    $outLines.Add("$key -> NOT FOUND")
    $missing++
    Write-Output "[missing] $key"
  }
}

Set-Content -Encoding UTF8 -Path $manifestPath -Value $outLines
Write-Output "downloaded=$downloaded"
Write-Output "missing=$missing"
Write-Output "plants_png=$((Get-ChildItem $plantsDir -Filter *.png -File | Measure-Object).Count)"
Write-Output "zombies_png=$((Get-ChildItem $zombiesDir -Filter *.png -File | Measure-Object).Count)"
