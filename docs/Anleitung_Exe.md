# Transkribieren (lokal) – Anleitung für die Exe

Version 1.0.0 · © 2026 Prof. Dr. Stefan M. Schulz · Lizenz: MIT ·
[github.com/SchulzSM/local-transcriber](https://github.com/SchulzSM/local-transcriber) ·
Fragen und Fehler: [GitHub Issues](https://github.com/SchulzSM/local-transcriber/issues) · Kontakt: kommunaut@gmail.com

Das Programm schreibt Audio, Video und DVDs ab (Transkription). Es läuft vollständig auf dem eigenen Rechner: Es wird
keine Internetverbindung gebraucht, und keine Datei verlässt den Rechner. Python muss **nicht** installiert sein.

## Inhalt

1. [Was Sie brauchen](#1-was-sie-brauchen)
2. [Erster Start und Einrichtung](#2-erster-start-und-einrichtung)
3. [Profile](#3-profile)
4. [Transkribieren](#4-transkribieren)
5. [Fachbegriffe und Begriffsdateien](#5-fachbegriffe-und-begriffsdateien)
6. [Ergebnisdateien und Protokoll](#6-ergebnisdateien-und-protokoll)
7. [Zeitstempel mit frei wählbarer Auflösung](#7-zeitstempel-mit-frei-wählbarer-auflösung)
8. [DVDs: ISO, VIDEO_TS, VOB](#8-dvds-iso-video_ts-vob)
9. [Kommandozeile](#9-kommandozeile)
10. [Dauer und Leistung](#10-dauer-und-leistung)
11. [Häufige Probleme](#11-häufige-probleme)
12. [Sprache der Oberfläche](#12-sprache-der-oberfläche)
13. [Datenschutz](#13-datenschutz)

English: see `Manual_en.md` next to the exe.

## 1. Was Sie brauchen

| Teil | Hinweis |
|---|---|
| Programmordner `Transkribieren` | aus dem ZIP; an einen **beschreibbaren** Ort entpacken (z. B. `C:\Tools\Transkribieren` oder in den Benutzerordner). Unter `C:\Program Files` liegen Profile stattdessen in `%APPDATA%\Transkribieren\profile` |
| ffmpeg | liest jedes Audio- und Videoformat; aus Lizenzgründen nicht enthalten. Windows-Fassung von [ffmpeg.org](https://ffmpeg.org/download.html), gebraucht wird nur `ffmpeg.exe` |
| Whisper-Modell | Ordner mit `model.bin`, `config.json`, `tokenizer.json`, `vocabulary.json`, `preprocessor_config.json` (CTranslate2-Format für faster-whisper); Bezugsquellen in der Tabelle unten |
| Rechner | Windows 10/11, 64 Bit; 8 GB Arbeitsspeicher oder mehr; die Rechenzeit hängt an der Zahl der Prozessorkerne |

**Modelle herunterladen:** Auf Hugging Face beim Modell unter *Files and versions* die fünf genannten Dateien in einen
eigenen Ordner laden. Neue Profile erwarten die Ordner unter `C:\LLMs\` mit dem Namen des Modells; andere Orte
lassen sich in den Einstellungen wählen.

| Zweck | Modell | Ordner (Standard) | Größe |
|---|---|---|---|
| Deutsch (empfohlen) | [TheTobyB/whisper-large-v3-turbo-german-ct2](https://huggingface.co/TheTobyB/whisper-large-v3-turbo-german-ct2) | `C:\LLMs\whisper-large-v3-turbo-german-ct2` | 1,6 GB |
| Mehrsprachig, schnell | [deepdml/faster-whisper-large-v3-turbo-ct2](https://huggingface.co/deepdml/faster-whisper-large-v3-turbo-ct2) | `C:\LLMs\faster-whisper-large-v3-turbo-ct2` | 1,6 GB |
| Mehrsprachig, groß (langsamer) | [Systran/faster-whisper-large-v3](https://huggingface.co/Systran/faster-whisper-large-v3) | `C:\LLMs\faster-whisper-large-v3` | 3,1 GB |

Es genügt ein Modell; nicht vorhandene Einträge lassen sich im Profil entfernen.

## 2. Erster Start und Einrichtung

1. `Transkribieren.exe` doppelklicken. Beim ersten Start legt das Programm ein Profil mit dem Rechnernamen an.
   Die Oberfläche erscheint in der Sprache von Windows (Deutsch oder Englisch, sonst Englisch); umstellen oben rechts
   unter **Sprache der Oberfläche** (Abschnitt 12).
2. Reiter **Einstellungen**:
   - **ffmpeg**: „…“ → `ffmpeg.exe` wählen.
   - **Modelle**: vorhandene Einträge mit **Bearbeiten …** auf den eigenen Modellordner setzen oder mit
     **Hinzufügen …** neue eintragen. Je Modell gibt es einen Kurznamen (für die Kommandozeile) und einen
     Anzeigenamen. **Als Standard** markiert das Modell, das beim Start vorgewählt ist (★).
   - Das Feld „Python der Transkriptions-Umgebung“ ist in der Exe ausgegraut; es wird nicht gebraucht.
3. **Speichern** und dann **Einrichtung prüfen**. Grüne Haken ✓ bei Programm, ffmpeg und Modellen bedeuten: alles
   bereit. Oben im Fenster steht dann „Einrichtung ✓“.

## 3. Profile

Ein Profil enthält alle rechnerabhängigen Angaben: ffmpeg, Modelle und Standardwerte. Es ist eine lesbare Datei
`profile\<Name>.json` im Programmordner.

| Einstellung | Bedeutung |
|---|---|
| ffmpeg | Pfad zu `ffmpeg.exe` |
| Modelle | beliebig viele; ★ = Standard |
| Sprache der Aufnahme | Standardsprache neuer Läufe (`de`, `en`, …, `auto` = erkennen) |
| Rechenkerne | 0 = alle bis auf einen; weniger lässt den Rechner nebenher bedienbar |
| Rechenart | `int8` ist am schnellsten und reicht in der Regel |
| Neuer Absatz ab Pause (s) | Sprechpause, ab der die Textdateien einen neuen Absatz beginnen (Standard 2,0; z. B. 1,2 für mehr Absätze) |
| Zielordner | leer = neben der Quelldatei |
| Begriffsdatei, Kontextsatz | Standardwerte für neue Läufe (Abschnitt 5) |

- **Knöpfe:** Neu …, Speichern, Speichern unter …, Löschen, Importieren … (Profildatei eines anderen Rechners
  übernehmen), Profilordner öffnen. Ungespeicherte Änderungen zeigt ein `*` hinter dem Profilnamen.
- **Platzhalter in Pfaden:** `{Tools}` = Programmordner, außerdem Umgebungsvariablen wie `%USERPROFILE%`. Pfade unter
  diesen Ordnern schreibt der Dialog automatisch so. Dann funktioniert ein Profil auch nach dem Verschieben des Ordners.
- **Beim nächsten Start** werden das zuletzt aktive Profil, die letzten Auftragswerte und die Fenstergröße
  wiederhergestellt (gespeichert in `%APPDATA%\Transkribieren\zustand.json`, nur für diesen Rechner).
- Der Reiter **Info** zeigt unter „Orte“ das aktive Profil und alle Speicherorte; die Angaben folgen dem gerade
  geladenen Profil.

## 4. Transkribieren

1. **Dateien wählen …**: eine oder mehrere Dateien (`.mp4`, `.mkv`, `.mov`, `.webm`, `.mp3`, `.flac`, `.m4a`,
   `.wav`, `.ogg`, `.opus`, `.vob`, `.iso`); für DVD-Ordner **DVD-Ordner …**; **Liste leeren** setzt zurück.
2. **Modell** und **Sprache der Aufnahme** prüfen (deutsche Vorlesung: Deutsch, `de`).
3. Optional:
   - **Begriffsdatei** und **Fachbegriffe** (Abschnitt 5)
   - **Kontextsatz**, z. B. „Vorlesung Anatomie, Thema Atmung.“; wirkt nur am Anfang der Aufnahme
   - **Zielordner**: „ändern …“; „Standard“ = Profil bzw. neben der Datei
   - **nur Probe (erste 2 min)**: schneller Test, ob Modell und Begriffe passen
   - **Zeitstempel je Wort**: genauere Untertitel und Zeitraster (etwas langsamer)
   - **Zeitraster in s**, z. B. `0.5 1 5` (Abschnitt 7)
   - **Tonspur**: Nummer; „Tonspuren anzeigen“ listet sie auf
4. **Start**:
   - Der Fortschritt erscheint mit Prozent und geschätzter Restzeit.
   - **Abbrechen** stoppt den Lauf; das bis dahin Erkannte steht bereits in der `.tsv`.
5. Danach führen **Ergebnisordner öffnen**, **Text öffnen** und **Protokoll öffnen** direkt zu den Dateien.
   **Befehl kopieren** legt den passenden Kommandozeilenbefehl in die Zwischenablage (Abschnitt 9).

Hinweis: Ein Lauf nutzt das **gespeicherte** Profil. Bei ungespeicherten Änderungen fragt das Programm nach.

## 5. Fachbegriffe und Begriffsdateien

Fachbegriffe verbessern die Schreibweise, z. B. „Chylomikronen“ statt „Kilo-Mikronen“.

- **Begriffsdatei:**
  - Textdatei (UTF-8), ein Begriff je Zeile oder mehrere durch Komma getrennt; alles nach `#` ist Kommentar.
  - Ein Beispiel liegt in `begriffe\Beispiel_Histologie.txt`.
  - Im Reiter Transkription: „…“ wählt die Datei, „öffnen“ bearbeitet sie oder legt eine neue an, „×“ nimmt sie aus
    dem Lauf.
- **Fachbegriffe (zusätzlich):** werden mit der Datei zusammengeführt; doppelte Einträge fallen weg.
- **Länge begrenzt:**
  - Das Modell nutzt höchstens **223 Tokens**, das sind etwa **35–40 deutsche Fachbegriffe**; der Rest wird
    abgeschnitten.
  - Die Anzeige unter dem Feld zeigt Begriffe und Tokens und wird rot, wenn die Liste zu lang ist.
  - Deshalb besser **eine kurze Datei je Thema** als eine Gesamtliste.
- **Wirkung:** Die Begriffe werden in jedem 30-Sekunden-Abschnitt der Aufnahme mitgegeben.
- **Falsch erkannte Wörter:** Wörter, die das Modell wiederholt falsch schreibt (z. B. „Atemungsregulation“), richtig
  geschrieben in die Begriffsdatei aufnehmen.
- **Probelauf:** Selten schreibt das Modell einen Begriff, der nicht gesagt wurde; dann die Liste kürzen.

## 6. Ergebnisdateien und Protokoll

Alle Dateien heißen wie die Quelldatei (beim Probelauf mit `_test`). Haben zwei gleichzeitig verarbeitete Dateien
denselben Namen, wird die Endung angehängt (`Vortrag_mp4.txt`).

| Datei | Inhalt |
|---|---|
| `<name>_nurText.txt` | reiner Text, neuer Absatz bei Sprechpausen (Profilwert „Neuer Absatz ab Pause“) |
| `<name>.txt` | derselbe Text, jeder Absatz beginnt mit `[mm:ss]` |
| `<name>.srt` | Untertitel: höchstens 2 Zeilen à 42 Zeichen und etwa 7 s je Einblendung |
| `<name>.tsv` | Satzabschnitte mit Start und Ende (s); wird während des Laufs geschrieben, öffnet in Excel |
| `<name>.json` | alles maschinenlesbar, mit Modell, Profil, Programmversion, Fachbegriffen; mit Wortzeitstempeln je Wort |
| `<name>_raster_1s.txt` usw. | eine Zeile je Rasterfeld (nur mit Zeitraster) |
| `<name>_protokoll.txt` | Protokoll des Laufs |

- **Untertitel:** Lange Abschnitte werden gleichmäßig auf mehrere Einblendungen verteilt, bevorzugt an Satzzeichen.
  Mit **Zeitstempel je Wort** stimmen die Zeiten wortgenau; ohne werden sie innerhalb eines Abschnitts angenähert.
- **Protokoll** – enthält:
  - Status („fertig“; „läuft“ bleibt stehen, wenn der Lauf abgebrochen wurde), Start, Ende, Rechenzeit
  - Rechner und Versionen (Programm, faster-whisper, CTranslate2, ffmpeg)
  - Profil, Modell, Sprache (eingestellt und erkannt), alle Parameter, Kontextsatz, Fachbegriffe mit Tokenzahl
  - Eingabedatei (Größe, Datum, Dauer), alle Ausgabedateien und die Befehlszeile

  So lässt sich jedes Transkript nachvollziehen und mit denselben Einstellungen wiederholen.

## 7. Zeitstempel mit frei wählbarer Auflösung

- **Ohne Zeitstempel:** `<name>_nurText.txt`.
- **Natürliche Auflösung** (Satzabschnitte, meist 2–15 s): `.txt`, `.tsv`; Untertitel in `.srt`.
- **Festes Raster** (0,5 s, 1 s, 5 s …): Feld „Zeitraster in s“. Jede Zeile enthält die Wörter, die in diesem
  Zeitfenster beginnen; Pausen werden ausgelassen.
- **Nachträglich ein anderes Raster** (ohne neu zu transkribieren), in der Eingabeaufforderung im Programmordner:
  `Transkribieren.exe --raster "D:\Audio\Vorlesung.json" 0.5 2 10`. Exakt nur, wenn mit Zeitraster oder
  Wortzeitstempeln transkribiert wurde; sonst angenähert (ab etwa 5 s brauchbar).
- **Genauigkeit:** Wortzeitstempel liegen etwa 0,1–0,3 s neben dem Wortbeginn; feiner als 0,5 s ist nicht sinnvoll.

## 8. DVDs: ISO, VIDEO_TS, VOB

| Eingabe | Was passiert |
|---|---|
| `Film.iso` | wird vorübergehend eingebunden und danach freigegeben |
| DVD- oder `VIDEO_TS`-Ordner (eingelegte DVD: `E:\VIDEO_TS`) | die Teile eines Titels (`VTS_01_1.VOB`, `_2`, …) werden lückenlos verbunden, das Menü übersprungen |
| eine `VTS_01_1.VOB` | der ganze Titel 01 |

- Ohne Angabe wird der größte Titelsatz genommen (meist der Hauptfilm); die Liste erscheint im Fortschrittsfenster.
- Ergebnisname `<ISO- bzw. Ordnername>_T01…`; bei einer eingelegten DVD einen Zielordner wählen.
- **Nur ungeschützte DVDs.** Bei kopiergeschützten DVDs bricht das Programm ab; es umgeht keinen Kopierschutz
  (§ 95a UrhG).

## 9. Kommandozeile

In der Eingabeaufforderung im Programmordner (oder mit vollem Pfad zur Exe):

```bat
Transkribieren.exe --cli "D:\Videos\Vortrag.mp4"
Transkribieren.exe --cli "D:\Audio\Interview.mp3" --modell large --sprache en
Transkribieren.exe --cli "D:\Audio\Vorlesung.flac" --begriffe-datei "{Tools}\begriffe\Beispiel_Histologie.txt" --raster 1 5
Transkribieren.exe --cli "D:\a.flac" "D:\b.mp3" --ausgabe "D:\Transkripte" --absatz 1.2
Transkribieren.exe --cli --pruefen
Transkribieren.exe --raster "D:\Audio\Vorlesung.json" 0.5 2 10
```

Werte ohne Angabe kommen aus dem Profil (Standard: zuletzt in der Oberfläche aktives Profil). Alle Optionen:
`Transkribieren.exe --cli --help`.

| Option | Bedeutung |
|---|---|
| `--profil <Name\|Datei.json>` | Profil wählen |
| `--modell <Kurzname\|Name\|Ordner>` | Modell aus dem Profil oder ein Modellordner |
| `--sprache de\|en\|…\|auto` | Sprache der Aufnahme |
| `--begriffe "A, B"` / `--begriffe-datei <txt>` | Fachbegriffe |
| `--kontext "…"` | Satz zum Thema |
| `--ausgabe <Ordner>` | Zielordner |
| `--absatz 1.2` | neuer Absatz ab dieser Sprechpause (s) |
| `--woerter` / `--raster 0.5 1 5` | Wortzeitstempel / zusätzliches Zeitraster |
| `--test 120` | nur die ersten 120 s |
| `--spur <n>` / `--spuren` | Tonspur wählen / auflisten |
| `--titel <n>` / `--nur-datei` | DVD-Titelsatz / nur diese VOB-Datei |
| `--threads`, `--compute`, `--beam`, `--ffmpeg` | Leistung bzw. ffmpeg-Pfad |
| `--kein-protokoll` | keine Protokolldatei |
| `--pruefen` | Einrichtung prüfen (Rückgabewert 1 bei Fehlern) |
| `--ui de\|en` | Sprache der Meldungen und des Protokolls (Standard: wie in der Oberfläche) |
| `--sprachen-pruefen` | Sprachdateien auf fehlende Einträge prüfen |
| `--version` | Programmversion |

## 10. Dauer und Leistung

- Deutsches Modell, `int8`, 11 Kerne: etwa **0,65–0,85 × Aufnahmedauer** (1 h Ton ≈ 40–50 min).
- **Nicht zwei Läufe gleichzeitig** starten, sondern mehrere Dateien in einem Lauf.
- Der erste Start der Exe dauert einige Sekunden länger (Bibliotheken werden geladen).

## 11. Häufige Probleme

| Meldung / Problem | Abhilfe |
|---|---|
| „Einrichtung ✗“ | Einstellungen → Einrichtung prüfen; Pfade per „…“ korrigieren, speichern |
| „Modell nicht gefunden … Laufwerk nicht verbunden?“ | Laufwerk anschließen oder Modellordner im Profil ändern |
| „ffmpeg nicht gefunden“ | Pfad im Profil setzen |
| Windows meldet „Der Computer wurde geschützt“ (SmartScreen) | „Weitere Informationen“ → „Trotzdem ausführen“; die Exe ist nicht signiert |
| Fachwörter falsch geschrieben | Begriffsdatei ergänzen (Länge beachten), ggf. Modell `large` im Probelauf vergleichen |
| „heisst“ statt „heißt“ | Eigenheit des deutschen Modells (Schweizer Schreibung); bei Bedarf im Text ersetzen |
| Englische Passagen in deutscher Vorlesung | überwiegend Englisch: Sprache `en`; gemischt: Modell `large`, Sprache `auto` |
| Rechner während des Laufs träge | Rechenkerne im Profil verringern |
| „ffmpeg konnte den Ton nicht lesen“ bei DVD | verschlüsselte DVD (nicht möglich) oder falsche Tonspur |
| „ISO konnte nicht eingebunden werden“ | im Explorer Rechtsklick → „Bereitstellen“, dann `E:\VIDEO_TS` als Eingabe |
| Anderes Problem | als [GitHub Issue](https://github.com/SchulzSM/local-transcriber/issues) melden, mit Programmversion und Protokolldatei (ohne vertrauliche Pfade) |

## 12. Sprache der Oberfläche

- **Umstellen:** oben rechts **Sprache der Oberfläche** wählen; das Fenster startet danach in der neuen Sprache neu
  (vorher wird nach ungespeicherten Profiländerungen gefragt). Die Wahl gilt für diesen Rechner.
- **Was sich ändert:** alle Beschriftungen, Meldungen, die Kommandozeile und die Protokolldatei. **Gleich bleiben**:
  die Sprache der Aufnahme (eigene Einstellung), die Dateinamen der Ergebnisse (`_nurText`, `_protokoll` …), die
  `.json` und die Profile; Profile lassen sich daher zwischen Sprachen austauschen.
- **Anleitung:** „Anleitung öffnen“ im Reiter Info öffnet die Anleitung in der gewählten Sprache.
- **Sprachdateien:** im Ordner `sprachen\` neben der Exe, je Sprache eine Textdatei (`de.txt`, `en.txt`). Jede Datei
  dort erscheint in der Auswahl. Eigene Übersetzungen ohne Schreibrecht im Programmordner:
  `%APPDATA%\Transkribieren\sprachen\`.
- **Neue Sprache anlegen:**
  1. `en.txt` kopieren, z. B. als `fr.txt`.
  2. Kopfzeilen anpassen: `# language: Français` (Name in der Auswahl), `# code: fr`, `# manual:` (Anleitung, falls
     vorhanden).
  3. Je Zeile den Text rechts von `=` übersetzen. Den Schlüssel links und Platzhalter wie `{name}` nicht ändern;
     `\n` ist ein Zeilenumbruch.
  4. Prüfen: `Transkribieren.exe --cli --sprachen-pruefen` nennt fehlende Einträge und falsche Platzhalter.
     Fehlende Einträge erscheinen auf Deutsch.

## 13. Datenschutz

- Die Telemetrie der mitgelieferten Bibliothek pyannote ist im Programm fest abgeschaltet.

- Alles bleibt lokal; Modelle werden ohne Internet geladen.
- Transkripte von Lehrveranstaltungen können Namen oder Wortbeiträge von Studierenden enthalten. Vor einer Weitergabe
  prüfen und ggf. kürzen.
- Das Protokoll nennt Rechnername und Dateipfade; bei Weitergabe von Transkripten nicht mitgeben.
