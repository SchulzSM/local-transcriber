@echo off
rem Transkribieren (lokal) - Starter fuer die Python-Fassung (die Exe braucht diesen Starter nicht).
rem   Doppelklick                         -> Oberflaeche
rem   Transkribieren.bat --cli "Datei.flac" [--profil Name] [--modell de] [--begriffe-datei liste.txt] [--test 120]
rem   Transkribieren.bat --raster "Datei.json" 0.5 1 5
rem   Transkribieren.bat --cli --pruefen   (Einrichtung des Profils pruefen)
rem Python: Umgebungsvariable TRANSKRIBIEREN_PYTHON, sonst die Standard-Umgebung, sonst der Python-Starter "py".
rem Fuer die eigentliche Transkription nutzt die Oberflaeche den Python-Pfad aus dem Profil.
setlocal
set HIER=%~dp0
set PY=%TRANSKRIBIEREN_PYTHON%
if "%PY%"=="" set PY=C:\Python\venvs\faster-whisper\Scripts\python.exe
if not exist "%PY%" set PY=py
if /I "%~1"=="--cli" goto konsole
if /I "%~1"=="--raster" goto konsole
if /I "%PY%"=="py" (start "" pyw "%HIER%src\app.py") else (start "" "%PY:python.exe=pythonw.exe%" "%HIER%src\app.py")
goto :eof
:konsole
"%PY%" "%HIER%src\app.py" %*
