# Änderungen / Changelog

## 1.1.0 – 25.11.2026

- **Neue Sprachen der Oberfläche:** Französisch, Spanisch und Chinesisch (vereinfacht) als Sprachdateien im Ordner
  `sprachen\`. / New interface languages: French, Spanish, Chinese (simplified).
- **Deutsch und Englisch fest eingebaut:** Die Exe läuft auch ohne Ordner `sprachen\`; dieser ist nur noch für weitere
  Sprachen da, wird gelesen, aber nie angelegt. Vorher erschienen ohne ihn Schlüssel wie `lauf.aendern`.
- **Fensterposition:** Eine gespeicherte Position gilt nur, wenn das Fenster auf einem angeschlossenen Bildschirm liegt;
  sonst öffnet es mittig auf dem Hauptbildschirm. Bei minimiertem Fenster wird keine Position gespeichert; ein
  maximiertes Fenster öffnet wieder maximiert. Vorher konnte das Fenster unsichtbar außerhalb des Bildschirms öffnen.
- **Neutraler Profilname:** Ein neues Profil heißt „Standard-Profil“ (je nach Sprache) statt nach dem Rechnernamen.
- **Schnellerer Start der Exe:** Die Einrichtungsprüfung liest die Versionen nur aus, statt faster-whisper und PyTorch
  zu laden.
- Protokolldatei: Spalten bleiben auch mit chinesischen Beschriftungen bündig.
- Anleitungen: ganzen Programmordner entpacken (die Exe braucht `_internal`), auf dem Desktop nur eine Verknüpfung;
  erster Start kann wegen des Virenscanners länger dauern.

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
