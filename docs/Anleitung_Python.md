# Transkribieren (lokal) – Anleitung für die Python-Fassung

Version 1.1.0 · für Betrieb aus dem Quellcode, Entwicklung und Exe-Build ·
[github.com/SchulzSM/local-transcriber](https://github.com/SchulzSM/local-transcriber) ·
Fragen und Fehler: [GitHub Issues](https://github.com/SchulzSM/local-transcriber/issues)

Die **Bedienung** (Oberfläche, Profile, Begriffsdateien, Ergebnisdateien, Zeitraster, DVDs, Optionen) ist in beiden
Fassungen gleich und steht in [Anleitung_Exe.md](Anleitung_Exe.md) bzw. [Manual_en.md](Manual_en.md). Diese
Anleitung beschreibt nur, was die Python-Fassung anders macht: Installation, Start, Python-Pfad im Profil, Exe-Build
und Versionierung.

## Inhalt

1. [Unterschiede zur Exe](#1-unterschiede-zur-exe)
2. [Einrichten](#2-einrichten)
3. [Starten](#3-starten)
4. [Profile in der Python-Fassung](#4-profile-in-der-python-fassung)
5. [Exe bauen und weitergeben](#5-exe-bauen-und-weitergeben)
6. [Aufbau des Quellcodes](#6-aufbau-des-quellcodes)
7. [Versionierung mit Git](#7-versionierung-mit-git)

## 1. Unterschiede zur Exe

| | Python-Fassung | Exe |
|---|---|---|
| Start | `Transkribieren.bat` | `Transkribieren.exe` |
| Kommandozeile | `Transkribieren.bat --cli …` | `Transkribieren.exe --cli …` |
| Transkription läuft mit | Python-Umgebung aus dem Profil (Feld „Python der Transkriptions-Umgebung“) | eingebautem Python |
| Profile | `<Repo>\profile\` | `<Exe-Ordner>\profile\` (eigene, getrennte Profile) |
| `{Tools}` bedeutet | Repo-Ordner | Exe-Ordner |
| Anleitung im Info-Reiter | Deutsch: diese Datei; andere Sprachen: `docs\Manual_<code>.md` | `Anleitung.md` bzw. `Manual_<code>.md` neben der Exe |
| Sprachdateien | `<Repo>\sprachen\` | de/en eingebaut (`_internal\sprachen_eingebaut`), weitere in `<Exe-Ordner>\sprachen\` (optional) |

Profile der beiden Fassungen sind getrennte Dateien. Zum Übertragen im jeweils anderen Programm
**Einstellungen → Importieren …** verwenden.

## 2. Einrichten

Benötigt werden Python 3.14 (64 Bit), ffmpeg und mindestens ein Modellordner (Bezugsquellen: Anleitung_Exe,
Abschnitt 1).

```bat
py -3.14 -m venv C:\Python\venvs\faster-whisper
C:\Python\venvs\faster-whisper\Scripts\python.exe -m pip install -r requirements.txt
```

- **Ohne Internet** auf dem Zielrechner: auf einem Rechner mit Internet die Pakete in einen Ordner laden
  (`… -m pip download -r requirements.txt -d <Paketordner>`), den Ordner mitnehmen und dort
  `… -m pip install --no-index --find-links <Paketordner> -r requirements.txt` ausführen.
- `requirements.txt` nennt die getesteten Versionen.
- Die Umgebung nutzt die Abspaltung `mobius-faster-whisper`. Sie lädt zusätzlich PyTorch und pyannote, das macht die
  Exe groß (Abschnitt 5). Die Telemetrie von pyannote schaltet das Programm beim Start ab
  (`PYANNOTE_METRICS_ENABLED=false`).
- Fehlt in einem Modellordner `tokenizer.json`, kann sie aus einem anderen large-v3-Modell kopiert werden (gleicher
  Tokenizer); sonst wird die Tokenzahl der Fachbegriffe nur geschätzt.

## 3. Starten

```bat
Transkribieren.bat
Transkribieren.bat --cli "D:\Audio\Vorlesung.flac" --begriffe-datei "{Tools}\begriffe\Beispiel_Histologie.txt"
Transkribieren.bat --cli --pruefen
Transkribieren.bat --raster "D:\Audio\Vorlesung.json" 0.5 1 5
```

- **Welches Python startet die Oberfläche:** die Umgebungsvariable `TRANSKRIBIEREN_PYTHON`, sonst
  `C:\Python\venvs\faster-whisper\Scripts\python.exe`, sonst der Python-Starter `py`.
- Die Oberfläche selbst braucht nur Python mit tkinter. Die Transkription läuft mit dem **Python aus dem Profil**.
- Direkt ohne Starter: `<python> src\app.py` (Oberfläche) bzw. `<python> src\app.py --cli …`.

## 4. Profile in der Python-Fassung

Zusätzlich zu den Einstellungen der Exe gibt es das Feld **Python der Transkriptions-Umgebung**: die `python.exe` einer
Umgebung, in der faster-whisper installiert ist. **Einrichtung prüfen** startet diese Umgebung und meldet die Versionen
von Python, faster-whisper und CTranslate2.

Profile (`profile\*.json`) sind rechnerbezogen und werden **nicht** versioniert (`.gitignore`). Als Vorlage liegt
`profile\Beispiel.json.example` bei; beim ersten Start legt das Programm ohnehin ein „Standard-Profil“ an (Name aus der Sprachdatei, `profil.standardname`).

## 5. Exe bauen und weitergeben

```powershell
powershell -ExecutionPolicy Bypass -File build_exe.ps1
```

- **Ergebnis:**
  - `dist\Transkribieren\Transkribieren.exe` mit `Anleitung.md` (= `docs\Anleitung_Exe.md`), `Manual_en.md`,
    `LICENSE`, `THIRD_PARTY_LICENSES.txt`, `CHANGELOG.md`, `sprachen\`, `begriffe\` und `profile\` nur mit der
    Vorlage `Beispiel.json.example`. So bekommen Empfänger kein Profil vom Build-Rechner.
  - dazu `dist\Transkribieren_<Version>.zip`.
- **Sprachen:** `de.txt` und `en.txt` gehen per `--add-data` fest in die Exe (`_internal\sprachen_eingebaut`); alle
  Sprachdateien liegen zusätzlich in `dist\Transkribieren\sprachen\`. Gleiche Codes im Ordner überschreiben die
  eingebauten.
- **Lizenzen:** `werkzeuge\drittlizenzen.py` schreibt Version, Lizenzangabe und Lizenztext von Python und allen Paketen
  der Transkriptions-Umgebung in `THIRD_PARTY_LICENSES.txt` (Pflicht bei Weitergabe der Exe).
- **Build-Umgebung:** `C:\Python\venvs\transkribieren-build` enthält nur PyInstaller. Die Pakete der
  Transkriptions-Umgebung werden per `.pth`-Datei eingebunden; das spart den erneuten Download. Beide Umgebungen
  brauchen dieselbe Python-Version.
- **Größe:** etwa 1,2 GB entpackt, ZIP etwa 420 MB. Der größte Teil ist PyTorch, das `mobius-faster-whisper` lädt.
  Ausschließen führt zu Importfehlern.
- **Nicht enthalten** sind Modelle und ffmpeg (Größe und Lizenzen).
- **Testen nach dem Build:**
  - `dist\Transkribieren\Transkribieren.exe --cli --pruefen`
  - ein Probelauf mit `--test 120`
  - Tests legen ein Profil in `dist\…\profile\` an. Vor der Weitergabe neu bauen oder die `.json` dort löschen.
- **Weitergabe:** das ZIP als GitHub-Release anhängen (Tag `v<Version>`), nicht den Ordner `build\`.
- **Ordner gesperrt:** Ist eine Konsole noch in `dist\` geöffnet, scheitert PyInstaller mit „WinError 32“. Konsole
  schließen bzw. das Verzeichnis wechseln.

## 6. Aufbau des Quellcodes

| Pfad | Inhalt |
|---|---|
| `src\app.py` | Einstieg für Oberfläche, `--cli`, `--raster` und die Exe |
| `src\transkribieren.py` | Transkription, Text-/SRT-/Raster-Dateien, Protokoll, Kommandozeile |
| `src\transkribieren_gui.py` | Oberfläche (tkinter) |
| `src\einstellungen.py` | Profile, Zustand je Rechner, Fachbegriffe, Tokenzählung, Einrichtungsprüfung |
| `src\transkript_raster.py` | Zeitraster aus vorhandenem Transkript |
| `src\sprache.py` | Sprachdateien lesen, `t("schlüssel", …)`, Sprachwahl, Prüfbericht |
| `src\version.py` | Version, Kontakt, Repo-Link (sichtbare Texte stehen in den Sprachdateien) |
| `sprachen\` | Sprachdateien der Oberfläche (`de.txt` = Referenz, `en.txt`) |
| `docs\` | Anleitungen (Exe deutsch und englisch, Python) |
| `begriffe\`, `profile\` | Begriffsdateien; Profile (nur die Vorlage ist versioniert) |
| `werkzeuge\drittlizenzen.py` | Lizenzliste der Fremdpakete für die Exe |
| `build_exe.ps1` | Exe-Build (UTF-8 mit BOM speichern, wegen Windows PowerShell 5.1) |

**Technische Hinweise:**
- **Sprachen:**
  - Kein sichtbarer Text im Code: Oberfläche, Meldungen, `--help` und Protokoll holen ihn mit
    `t("schlüssel", platzhalter=…)` aus `sprachen\<code>.txt`. Neuer Text: Schlüssel in `de.txt` **und** `en.txt`
    eintragen, dann `Transkribieren.bat --cli --sprachen-pruefen`.
  - Fehlt ein Schlüssel, gilt `de.txt`; fehlt er auch dort, erscheint der Schlüssel selbst.
  - Sprachwahl: `--ui` → `zustand.json` (`oberflaeche`) → Windows-Sprache → Englisch → Deutsch. Die Oberfläche gibt
    `--ui` an den Transkriptionsprozess weiter; nach einem Wechsel baut `main()` das Fenster neu auf.
  - Fest und sprachunabhängig bleiben Profil- und JSON-Schlüssel, Dateinamen der Ergebnisse, Optionsnamen und die
    Zeile `ERGEBNIS<Tab>…`, die die Oberfläche auswertet.
  - `einstellungen.pruefen()` liefert `(id, bereich, ok, text)`; die Oberfläche wertet nur die sprachneutrale `id` aus.
- **Fachbegriffe:** gehen als `hotwords` an faster-whisper und gelten so in jedem 30-s-Fenster. Der Kontextsatz geht
  als `initial_prompt`; der wirkt wegen `condition_on_previous_text=False` nur im ersten Fenster. Grenze für die
  Begriffe: 223 Tokens.
- **Untertitel:**
  - Whisper-Abschnitte werden gleichmäßig geteilt (`SRT_ZEICHEN = 42`, `SRT_ZEILEN = 2`, `SRT_DAUER = 7`), Schnitt
    bevorzugt an Satzzeichen.
  - Ohne Wortzeitstempel werden die Zeiten anteilig nach Zeichenzahl verteilt.
- **Oberfläche:**
  - Ergebnisse aus Hilfsthreads laufen über die Warteschlange, nie direkt über `after()`.
  - Fenster: gespeicherte Position nur, wenn die Titelleiste auf einem Bildschirm liegt (`MonitorFromPoint`), sonst
    `standard_fenster()` (mittig auf dem Hauptbildschirm); minimiert wird nichts gespeichert, maximiert als
    `maximiert` im Zustand.
  - Die Einrichtungsprüfung der Exe importiert faster-whisper nicht (Versionen per `importlib.metadata`), damit der
    Start nicht PyTorch lädt.
  - Die Darstellung ist DPI-bewusst.

## 7. Versionierung mit Git

- Branch `main`, GitHub: [SchulzSM/local-transcriber](https://github.com/SchulzSM/local-transcriber).
- **Je Änderung:** Version in `src\version.py`, `CHANGELOG.md`, den Kopfzeilen `# version:` der Sprachdateien und den
  Versionszeilen der Anleitungen gemeinsam erhöhen (1.0.0 → 1.0.1 Korrektur, → 1.1.0 neue Funktion), committen, Exe
  neu bauen, ZIP als Release `v<Version>` anhängen.
- Fehler und Wünsche: [GitHub Issues](https://github.com/SchulzSM/local-transcriber/issues).
