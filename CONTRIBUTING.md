# Mitwirken / Contributing

Danke für Ihr Interesse an **local-transcriber**! / Thank you for your interest in **local-transcriber**!

*English version below.*

## Deutsch

### Fehler melden und Wünsche äußern

- Bitte ein [Issue](https://github.com/SchulzSM/local-transcriber/issues/new/choose) mit der passenden Vorlage
  anlegen („Fehler melden“ oder „Wunsch“). Vorher kurz in der Anleitung unter „Häufige Probleme“ nachsehen.
- **Datenschutz:** Issues sind öffentlich. Bitte keine Transkripte, Audiodateien, Namen oder vertraulichen Pfade
  einfügen; Auszüge aus der Protokolldatei vorher kürzen.
- Anliegen, die nicht öffentlich sein sollen: kommunaut@gmail.com.

### Übersetzungen

Neue Sprachen der Oberfläche sind besonders willkommen und brauchen keine Programmierkenntnisse:

1. `sprachen/en.txt` kopieren, z. B. als `sprachen/fr.txt`.
2. Kopfzeilen anpassen (`# language: Français`, `# code: fr`).
3. Den Text rechts von `=` übersetzen; Schlüssel links und Platzhalter wie `{name}` unverändert lassen.
4. Prüfen: `Transkribieren.exe --cli --sprachen-pruefen` (bzw. `Transkribieren.bat --cli --sprachen-pruefen`).
5. Als Pull Request einreichen oder die Datei an ein Issue anhängen.

### Code beitragen (Pull Requests)

- Bei größeren Änderungen bitte zuerst ein Issue eröffnen, damit wir den Weg abstimmen können.
- Ein Pull Request je Thema, möglichst klein und mit kurzer Beschreibung, was und warum.
- Einrichtung der Entwicklungsumgebung, Aufbau des Codes und Exe-Build: [docs/Anleitung_Python.md](docs/Anleitung_Python.md).
- **Konventionen:**
  - Kein sichtbarer Text im Code: neue Texte als Schlüssel in `sprachen/de.txt` **und** `sprachen/en.txt`, Aufruf
    über `t("schlüssel")`; danach `--sprachen-pruefen`.
  - Profile (`profile/*.json`) enthalten rechnerbezogene Pfade und werden nicht eingecheckt.
  - PowerShell-Skripte als UTF-8 **mit BOM** speichern (Windows PowerShell 5.1).
  - Nichts darf Daten übertragen: keine Telemetrie, keine Online-Abrufe während der Transkription.
- Version, CHANGELOG und Releases pflegt der Maintainer.

### Lizenz und Umgang

- Beiträge stehen wie das Projekt unter der [MIT-Lizenz](LICENSE).
- Es gilt der [Verhaltenskodex](CODE_OF_CONDUCT.md) (Contributor Covenant 2.1).

## English

### Reporting bugs and requesting features

- Please open an [issue](https://github.com/SchulzSM/local-transcriber/issues/new/choose) using the matching template
  (“Bug report” or “Feature request”). Check “Common problems” in the [manual](docs/Manual_en.md) first.
- **Privacy:** issues are public. Do not paste transcripts, audio files, names or confidential paths; shorten excerpts
  from the log file.
- For matters that should not be public: kommunaut@gmail.com.

### Translations

New interface languages are especially welcome and need no programming:

1. Copy `sprachen/en.txt`, e.g. as `sprachen/fr.txt`.
2. Adjust the header lines (`# language: Français`, `# code: fr`).
3. Translate the text to the right of `=`; keep the keys on the left and placeholders such as `{name}` unchanged.
4. Check: `Transkribieren.exe --cli --sprachen-pruefen`.
5. Submit a pull request or attach the file to an issue.

### Contributing code (pull requests)

- For larger changes, please open an issue first so we can agree on the approach.
- One pull request per topic, as small as possible, with a short description of what and why.
- Development setup, code structure and exe build: [docs/Anleitung_Python.md](docs/Anleitung_Python.md) (German).
- **Conventions:**
  - No visible text in the code: add new texts as keys to `sprachen/de.txt` **and** `sprachen/en.txt` and use
    `t("key")`; then run `--sprachen-pruefen`.
  - Profiles (`profile/*.json`) contain machine-specific paths and are not committed.
  - Save PowerShell scripts as UTF-8 **with BOM** (Windows PowerShell 5.1).
  - Nothing may transmit data: no telemetry, no online requests during transcription.
- Versions, changelog and releases are maintained by the maintainer.

### License and conduct

- Contributions are licensed under the project's [MIT License](LICENSE).
- The [Code of Conduct](CODE_OF_CONDUCT.md) (Contributor Covenant 2.1) applies.
