# local-transcriber – Transkribieren (lokal)

Offline-Transkription von Audio, Video und DVD mit [faster-whisper](https://github.com/SYSTRAN/faster-whisper).
Alles läuft auf dem eigenen Rechner – keine Internetverbindung, keine Datei verlässt den Rechner.

Version 1.0.0 · © 2026 Prof. Dr. Stefan M. Schulz · Lizenz: MIT (`LICENSE`) ·
Fragen und Fehler: [GitHub Issues](https://github.com/SchulzSM/local-transcriber/issues) · Kontakt: kommunaut@gmail.com

*English summary below.*

## Funktionen

- Oberfläche und Kommandozeile; Audio- und Videoformate über ffmpeg, auch DVDs (ISO, VIDEO_TS, VOB)
- Ergebnisse als reiner Text, Text mit Zeitmarken, Untertitel (SRT), Tabelle (TSV), JSON und Zeitraster nach Wahl
- Profile je Rechner (ffmpeg, Modelle, Standardwerte), Einrichtungsprüfung mit Klartextmeldungen
- Fachbegriffe aus Textdateien mit Tokenanzeige
- Protokolldatei je Lauf (Einstellungen, Versionen, Ein- und Ausgabedateien)
- Oberfläche auf Deutsch und Englisch; weitere Sprachen als Textdatei in `sprachen\`

## Anleitungen

| Für wen | Datei |
|---|---|
| Nutzung der **Exe** (ohne Python) – vollständige Bedienungsanleitung | [docs/Anleitung_Exe.md](docs/Anleitung_Exe.md) |
| **Manual (English)** for the exe | [docs/Manual_en.md](docs/Manual_en.md) |
| Betrieb aus dem **Quellcode**, Entwicklung, Exe-Build, Git | [docs/Anleitung_Python.md](docs/Anleitung_Python.md) |
| Änderungen | [CHANGELOG.md](CHANGELOG.md) |

## Schnellstart

1. **Exe:** ZIP aus den [Releases](https://github.com/SchulzSM/local-transcriber/releases) an einen beschreibbaren
   Ort entpacken (z. B. `C:\Tools\Transkribieren`).
2. **ffmpeg** besorgen ([ffmpeg.org](https://ffmpeg.org/download.html); gebraucht wird nur `ffmpeg.exe`).
3. **Modell** herunterladen (Tabelle unten), je Modell einen Ordner, z. B. unter `C:\LLMs\`.
4. `Transkribieren.exe` starten → **Einstellungen**: ffmpeg und Modellordner wählen → **Speichern** →
   **Einrichtung prüfen** → Reiter **Transkription**: Dateien wählen → **Start**.

**Python:** Umgebung nach `docs/Anleitung_Python.md` einrichten → `Transkribieren.bat`.

## Modelle / Models

Modelle und ffmpeg sind nicht enthalten (Größe und Lizenzen). Benötigt wird das CTranslate2-Format für
faster-whisper. Je Modell auf Hugging Face unter *Files and versions* die Dateien `model.bin`, `config.json`,
`tokenizer.json`, `vocabulary.json` und `preprocessor_config.json` in einen eigenen Ordner laden.

| Zweck / Purpose | Modell / Model | Größe | Lizenz |
|---|---|---|---|
| Deutsch (empfohlen) / German | [TheTobyB/whisper-large-v3-turbo-german-ct2](https://huggingface.co/TheTobyB/whisper-large-v3-turbo-german-ct2) (Basis: [primeline/whisper-large-v3-turbo-german](https://huggingface.co/primeline/whisper-large-v3-turbo-german)) | 1,6 GB | Basismodell Apache-2.0 |
| Mehrsprachig, schnell / multilingual, fast | [deepdml/faster-whisper-large-v3-turbo-ct2](https://huggingface.co/deepdml/faster-whisper-large-v3-turbo-ct2) | 1,6 GB | MIT |
| Mehrsprachig, groß / multilingual, large | [Systran/faster-whisper-large-v3](https://huggingface.co/Systran/faster-whisper-large-v3) | 3,1 GB | MIT |

Die Standardpfade neuer Profile entsprechen diesen Namen unter `C:\LLMs\` (z. B.
`C:\LLMs\whisper-large-v3-turbo-german-ct2`).

## English summary

**local-transcriber** transcribes audio, video and DVDs completely offline with faster-whisper on Windows. No
internet connection is needed and no file leaves your computer.

- Graphical interface and command line; any audio/video format via ffmpeg; DVDs (ISO, VIDEO_TS, VOB).
- Output: plain text, text with timestamps, subtitles (SRT), TSV, JSON, custom time grids, and a log file per run.
- Profiles per computer, setup check, term lists to improve the spelling of technical vocabulary.
- Interface in English and German; further languages can be added as text files in `sprachen\`.

**Getting started:** download the ZIP from the [releases](https://github.com/SchulzSM/local-transcriber/releases),
extract it, get [ffmpeg](https://ffmpeg.org/download.html) and a model from the table above, start
`Transkribieren.exe`, set ffmpeg and the model folder under *Settings*, save, *Check setup*, then choose files and
*Start*. Full instructions: [docs/Manual_en.md](docs/Manual_en.md).

Questions and bug reports: [GitHub Issues](https://github.com/SchulzSM/local-transcriber/issues) · Contact:
kommunaut@gmail.com · License: MIT.
