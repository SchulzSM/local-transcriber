# Baut Transkribieren.exe (PyInstaller, Ordnerfassung) nach dist\Transkribieren und packt ein ZIP.
# Aufruf: powershell -ExecutionPolicy Bypass -File build_exe.ps1 [-Transkription <venv>] [-Build <venv>]
# Die Build-Umgebung enthaelt nur PyInstaller; faster-whisper & Co. kommen per .pth-Datei aus der
# Transkriptions-Umgebung (gleiche Python-Version noetig), ohne erneuten Download.
param(
    [string]$Transkription = "C:\Python\venvs\faster-whisper",
    [string]$Build = "C:\Python\venvs\transkribieren-build"
)
$ErrorActionPreference = "Stop"
$hier = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $hier

$basisPy = (Get-Content "$Transkription\pyvenv.cfg" | Where-Object { $_ -match '^executable\s*=' }) -replace '^executable\s*=\s*', ''
if (-not (Test-Path "$Build\Scripts\python.exe")) {
    Write-Host "Build-Umgebung anlegen: $Build (Basis $basisPy)"
    & $basisPy -m venv $Build
}
$py = "$Build\Scripts\python.exe"
$site = (& $py -c "import site; print(site.getsitepackages()[-1])").Trim()
$quelle = (& "$Transkription\Scripts\python.exe" -c "import site; print(site.getsitepackages()[-1])").Trim()
Set-Content -Path (Join-Path $site "transkription_umgebung.pth") -Value $quelle -Encoding ASCII
$hat = (& $py -c "import importlib.util; print(importlib.util.find_spec('PyInstaller') is not None)").Trim()
if ($hat -ne "True") {
    Write-Host "PyInstaller installieren (Download) ..."
    & $py -m pip install --disable-pip-version-check pyinstaller
}
$version = (& $py -c "import sys; sys.path.insert(0, 'src'); import version; print(version.__version__)").Trim()
Write-Host "Baue Transkribieren $version ..."

& $py -m PyInstaller --noconfirm --clean --windowed --name Transkribieren `
    --paths src `
    --collect-data faster_whisper --collect-binaries ctranslate2 --collect-binaries onnxruntime `
    --hidden-import ctranslate2 --hidden-import tokenizers --hidden-import onnxruntime `
    --collect-data pyannote.audio --collect-data pyannote.core --collect-data pyannote.pipeline `
    --copy-metadata pyannote.audio --copy-metadata torch `
    --copy-metadata mobius-faster-whisper --copy-metadata ctranslate2 `
    --add-data "sprachen\de.txt;sprachen_eingebaut" --add-data "sprachen\en.txt;sprachen_eingebaut" `
    --exclude-module tensorflow --exclude-module IPython `
    src\app.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller-Fehler" }

$ziel = "dist\Transkribieren"
foreach ($f in "LICENSE", "CHANGELOG.md") { Copy-Item $f $ziel -Force }
# Lizenztexte aller eingebauten Pakete (Pflicht bei Weitergabe der Exe)
& "$Transkription\Scripts\python.exe" "werkzeuge\drittlizenzen.py" "$ziel\THIRD_PARTY_LICENSES.txt"
if ($LASTEXITCODE -ne 0) { throw "Lizenzliste nicht erzeugt" }
Copy-Item "docs\Anleitung_Exe.md" "$ziel\Anleitung.md" -Force
Get-ChildItem "docs\Manual_*.md" | Copy-Item -Destination $ziel -Force  # Anleitungen weiterer Sprachen
New-Item -ItemType Directory -Force "$ziel\begriffe", "$ziel\profile", "$ziel\sprachen" | Out-Null
Get-ChildItem "$ziel\profile" -File | Remove-Item -Force  # kein Profil des Build-Rechners weitergeben
Copy-Item "profile\Beispiel.json.example" "$ziel\profile" -Force
Copy-Item "begriffe\*.txt" "$ziel\begriffe" -Force
Get-ChildItem "$ziel\sprachen" -File | Remove-Item -Force
Copy-Item "sprachen\*.txt" "$ziel\sprachen" -Force
$zip = "dist\Transkribieren_$version.zip"
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path $ziel -DestinationPath $zip
$mb = [math]::Round((Get-ChildItem $ziel -Recurse | Measure-Object Length -Sum).Sum / 1MB)
Write-Host "Fertig: $ziel\Transkribieren.exe ($mb MB) und $zip"
