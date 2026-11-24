# Änderungen / Changelog

## 1.0.0 – 24.11.2026

Erste öffentliche Version. / First public release.

- **Oberfläche und Kommandozeile** für die Offline-Transkription mit faster-whisper; Audio und Video über ffmpeg,
  auch DVDs (ISO, VIDEO_TS, VOB).
- **Ergebnisse:** reiner Text, Text mit Zeitmarken und Absätzen (Schwelle einstellbar), Untertitel (SRT, höchstens
  2 × 42 Zeichen und etwa 7 s je Einblendung), TSV, JSON, Zeitraster nach Wahl; Protokolldatei je Lauf.
- **Profile je Rechner:** ffmpeg, beliebig viele Modelle, Standardwerte; Platzhalter `{Tools}` und
  Umgebungsvariablen in Pfaden; Einrichtungsprüfung mit Klartextmeldungen; Import und Export.
- **Fachbegriffe** aus Textdateien, in jedem 30-s-Fenster als `hotwords`; Anzeige der Tokens gegen die Grenze von 223.
- **Sprachen der Oberfläche:** Deutsch und Englisch über Sprachdateien in `sprachen\`; weitere Sprachen als Textdatei.
- **Exe ohne Python-Installation** (PyInstaller) mit Anleitungen auf Deutsch und Englisch und
  `THIRD_PARTY_LICENSES.txt`.
- **Datenschutz:** alles läuft lokal; die Telemetrie der Bibliothek pyannote ist fest abgeschaltet.
