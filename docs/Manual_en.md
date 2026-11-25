# Local Transcriber – Manual for the exe

Version 1.1.0 · © 2026 Prof. Dr. Stefan M. Schulz · License: MIT ·
[github.com/SchulzSM/local-transcriber](https://github.com/SchulzSM/local-transcriber) ·
Questions and bugs: [GitHub Issues](https://github.com/SchulzSM/local-transcriber/issues) · Contact: kommunaut@gmail.com

The program transcribes audio, video and DVDs. It runs entirely on your own computer: no internet connection is
needed, and no file leaves the computer. Python does **not** need to be installed.

German version: `Anleitung.md` next to the exe.

## Contents

1. [What you need](#1-what-you-need)
2. [First start and setup](#2-first-start-and-setup)
3. [Profiles](#3-profiles)
4. [Transcribing](#4-transcribing)
5. [Terms and term files](#5-terms-and-term-files)
6. [Output files and log](#6-output-files-and-log)
7. [Timestamps at any resolution](#7-timestamps-at-any-resolution)
8. [DVDs: ISO, VIDEO_TS, VOB](#8-dvds-iso-video_ts-vob)
9. [Command line](#9-command-line)
10. [Duration and performance](#10-duration-and-performance)
11. [Common problems](#11-common-problems)
12. [Interface language](#12-interface-language)
13. [Privacy](#13-privacy)

## 1. What you need

| Part | Note |
|---|---|
| Program folder `Transkribieren` | extract it **completely** from the ZIP to a **writable** location (e.g. `C:\Tools\Transkribieren` or your user folder). The exe needs the `_internal` folder next to it; for the desktop, create a shortcut (right-click the exe → *Send to → Desktop*) instead of copying the exe alone. Under `C:\Program Files`, profiles are stored in `%APPDATA%\Transkribieren\profile` instead |
| ffmpeg | reads every audio and video format; not included for licensing reasons. Windows build from [ffmpeg.org](https://ffmpeg.org/download.html); only `ffmpeg.exe` is needed |
| Whisper model | folder with `model.bin`, `config.json`, `tokenizer.json`, `vocabulary.json`, `preprocessor_config.json` (CTranslate2 format for faster-whisper); sources in the table below |
| Computer | Windows 10/11, 64 bit; 8 GB RAM or more; processing time depends on the number of CPU cores |

**Downloading models:** on Hugging Face, open the model, go to *Files and versions* and download the five files
listed above into a folder of their own. New profiles expect the folders under `C:\LLMs\`, named like the model;
other locations can be chosen in the settings.

| Purpose | Model | Folder (default) | Size |
|---|---|---|---|
| English and other languages, fast (recommended) | [deepdml/faster-whisper-large-v3-turbo-ct2](https://huggingface.co/deepdml/faster-whisper-large-v3-turbo-ct2) | `C:\LLMs\faster-whisper-large-v3-turbo-ct2` | 1.6 GB |
| Multilingual, large (slower) | [Systran/faster-whisper-large-v3](https://huggingface.co/Systran/faster-whisper-large-v3) | `C:\LLMs\faster-whisper-large-v3` | 3.1 GB |
| German | [TheTobyB/whisper-large-v3-turbo-german-ct2](https://huggingface.co/TheTobyB/whisper-large-v3-turbo-german-ct2) | `C:\LLMs\whisper-large-v3-turbo-german-ct2` | 1.6 GB |

One model is enough; remove entries you do not have from the profile.

## 2. First start and setup

1. Double-click `Transkribieren.exe`. On the first start the program creates a “Default profile”. The very first
   start may take a while because the virus scanner checks the program files.
   The interface appears in the Windows language (German or English, otherwise English); change it at the top right
   under **Interface language** (section 12).
2. **Settings** tab:
   - **ffmpeg**: “…” → choose `ffmpeg.exe`.
   - **Models**: point the existing entries to your own model folders with **Edit …** or add new ones with
     **Add …**. Each model has a short name (for the command line) and a display name. **Set as default** marks the
     model that is preselected at start (★).
   - The field “Python of the transcription environment” is greyed out in the exe; it is not needed.
3. **Save**, then **Check setup**. Green ticks ✓ for program, ffmpeg and models mean: everything is ready. The top of
   the window then shows “Setup ✓”.

Note: the default profile lists the three models from section 1 with the standard folders. For English, set
**Multilingual (large-v3-turbo)** as default (select it, **Set as default**) and the recording language to `en`.

## 3. Profiles

A profile contains everything that depends on the computer: ffmpeg, models and default values. It is a readable file
`profile\<name>.json` in the program folder.

| Setting | Meaning |
|---|---|
| ffmpeg | path to `ffmpeg.exe` |
| Models | any number; ★ = default |
| Recording language | default language of new runs (`de`, `en`, …, `auto` = detect) |
| CPU cores | 0 = all but one; fewer keeps the computer usable meanwhile |
| Compute type | `int8` is fastest and usually sufficient |
| New paragraph after pause (s) | speech pause after which the text files start a new paragraph (default 2.0; e.g. 1.2 for more paragraphs) |
| Output folder | empty = next to the source file |
| Term file, context sentence | defaults for new runs (section 5) |

- **Buttons:** New …, Save, Save as …, Delete, Import … (take over a profile file from another computer), Open
  profile folder. Unsaved changes are shown by a `*` after the profile name.
- **Placeholders in paths:** `{Tools}` = program folder, plus environment variables such as `%USERPROFILE%`. The
  dialog writes paths below these folders that way automatically. A profile then still works after the folder has
  been moved.
- **At the next start** the last active profile, the last job values and the window size are restored (stored in
  `%APPDATA%\Transkribieren\zustand.json`, only for this computer).
- The **About** tab shows the active profile and all storage locations under “Locations”; they follow the profile
  that is currently loaded.

## 4. Transcribing

1. **Choose files …**: one or more files (`.mp4`, `.mkv`, `.mov`, `.webm`, `.mp3`, `.flac`, `.m4a`, `.wav`, `.ogg`,
   `.opus`, `.vob`, `.iso`); for DVD folders **DVD folder …**; **Clear list** resets.
2. Check **Model** and **Recording language** (English lecture: a multilingual model, `en`).
3. Optional:
   - **Term file** and **Additional terms** (section 5)
   - **Context sentence**, e.g. “Anatomy lecture, topic respiration.”; only affects the beginning of the recording
   - **Output folder**: “change …”; “Default” = profile or next to the file
   - **sample only (first 2 min)**: quick test whether model and terms fit
   - **word timestamps**: more precise subtitles and time grids (somewhat slower)
   - **Time grid in s**, e.g. `0.5 1 5` (section 7)
   - **Audio track**: number; “Show audio tracks” lists them
4. **Start**:
   - Progress is shown with percentage and estimated remaining time.
   - **Cancel** stops the run; what has been recognised so far is already in the `.tsv`.
5. Afterwards **Open output folder**, **Open text** and **Open log** lead directly to the files.
   **Copy command** puts the matching command line on the clipboard (section 9).

Note: a run uses the **saved** profile. If there are unsaved changes, the program asks.

## 5. Terms and term files

Terms improve spelling, e.g. “chylomicrons” instead of “kilo microns”.

- **Term file:**
  - text file (UTF-8), one term per line or several separated by commas; everything after `#` is a comment.
  - An example (German histology terms) is in `begriffe\Beispiel_Histologie.txt`.
  - In the Transcription tab: “…” chooses the file, “open” edits it or creates a new one, “×” removes it from the run.
- **Additional terms:** merged with the file; duplicates are dropped.
- **Limited length:**
  - The model uses at most **223 tokens**, that is roughly **35–40 technical terms**; the rest is cut off.
  - The display below the field shows terms and tokens and turns red if the list is too long.
  - Therefore prefer **one short file per topic** over one complete list.
- **Effect:** the terms are passed with every 30-second section of the recording.
- **Misrecognised words:** add words that the model repeatedly misspells to the term file, spelled correctly.
- **Sample run:** occasionally the model writes a term that was not said; then shorten the list.

## 6. Output files and log

All files are named like the source file (with `_test` for a sample run). If two files processed together have the
same name, the extension is appended (`Talk_mp4.txt`). The file names are the same in every interface language.

| File | Content |
|---|---|
| `<name>_nurText.txt` | plain text, new paragraph at speech pauses (profile value “New paragraph after pause”) |
| `<name>.txt` | the same text, each paragraph starts with `[mm:ss]` |
| `<name>.srt` | subtitles: at most 2 lines of 42 characters and about 7 s per cue |
| `<name>.tsv` | segments with start and end (s); written during the run, opens in Excel |
| `<name>.json` | everything machine-readable, with model, profile, program version, terms; with word timestamps per word |
| `<name>_raster_1s.txt` etc. | one line per grid cell (only with a time grid) |
| `<name>_protokoll.txt` | log of the run, in the interface language |

- **Subtitles:** long segments are spread evenly over several cues, preferably at punctuation. With **word
  timestamps** the times are exact to the word; without, they are approximated within a segment.
- **Log** – contains:
  - status (“finished”; “running” remains if the run was cancelled), start, end, processing time
  - computer and versions (program, faster-whisper, CTranslate2, ffmpeg)
  - profile, model, language (set and detected), all parameters, context sentence, terms with token count
  - input file (size, date, duration), all output files and the command line

  This makes every transcript traceable and repeatable with the same settings.

## 7. Timestamps at any resolution

- **Without timestamps:** `<name>_nurText.txt`.
- **Natural resolution** (segments, mostly 2–15 s): `.txt`, `.tsv`; subtitles in `.srt`.
- **Fixed grid** (0.5 s, 1 s, 5 s …): field “Time grid in s”. Each line contains the words that begin in that time
  window; pauses are skipped.
- **A different grid afterwards** (without transcribing again), in a command prompt in the program folder:
  `Transkribieren.exe --raster "D:\Audio\Lecture.json" 0.5 2 10`. Exact only if the transcript was made with a time
  grid or word timestamps; otherwise approximated (usable from about 5 s).
- **Accuracy:** word timestamps are about 0.1–0.3 s off the start of the word; finer than 0.5 s is not useful.

## 8. DVDs: ISO, VIDEO_TS, VOB

| Input | What happens |
|---|---|
| `Film.iso` | is mounted temporarily and released afterwards |
| DVD or `VIDEO_TS` folder (inserted DVD: `E:\VIDEO_TS`) | the parts of a title (`VTS_01_1.VOB`, `_2`, …) are joined seamlessly, the menu is skipped |
| a single `VTS_01_1.VOB` | the whole title 01 |

- Without further input, the largest title set is used (usually the main film); the list appears in the progress
  window.
- Result name `<ISO or folder name>_T01…`; for an inserted DVD choose an output folder.
- **Unprotected DVDs only.** With copy-protected DVDs the program stops; it does not circumvent copy protection.

## 9. Command line

In a command prompt in the program folder (or with the full path to the exe):

```bat
Transkribieren.exe --cli "D:\Videos\Talk.mp4" --ui en
Transkribieren.exe --cli "D:\Audio\Interview.mp3" --modell large --sprache en
Transkribieren.exe --cli "D:\Audio\Lecture.flac" --begriffe-datei "{Tools}\begriffe\Beispiel_Histologie.txt" --raster 1 5
Transkribieren.exe --cli "D:\a.flac" "D:\b.mp3" --ausgabe "D:\Transcripts" --absatz 1.2
Transkribieren.exe --cli --pruefen
Transkribieren.exe --raster "D:\Audio\Lecture.json" 0.5 2 10
```

Values not given come from the profile (default: the profile last active in the interface). Messages and the log
use the interface language; `--ui en` sets it explicitly. The option names themselves are German and the same in
every language. All options: `Transkribieren.exe --cli --help --ui en`.

| Option | Meaning |
|---|---|
| `--profil <name\|file.json>` | choose profile |
| `--modell <short name\|name\|folder>` | model from the profile or a model folder |
| `--sprache de\|en\|…\|auto` | language of the recording |
| `--begriffe "A, B"` / `--begriffe-datei <txt>` | terms |
| `--kontext "…"` | sentence about the topic |
| `--ausgabe <folder>` | output folder |
| `--absatz 1.2` | new paragraph after this speech pause (s) |
| `--woerter` / `--raster 0.5 1 5` | word timestamps / additional time grid |
| `--test 120` | only the first 120 s |
| `--spur <n>` / `--spuren` | choose / list audio tracks |
| `--titel <n>` / `--nur-datei` | DVD title set / only this VOB file |
| `--threads`, `--compute`, `--beam`, `--ffmpeg` | performance or ffmpeg path |
| `--kein-protokoll` | no log file |
| `--pruefen` | check setup (exit code 1 on errors) |
| `--ui de\|en` | language of messages and log (default: as in the interface) |
| `--sprachen-pruefen` | check language files for missing entries |
| `--version` | program version |

## 10. Duration and performance

- German model, `int8`, 11 cores: about **0.65–0.85 × recording length** (1 h of audio ≈ 40–50 min).
- Do **not start two runs at the same time**; put several files into one run instead.
- The first start of the exe takes a few seconds longer (libraries are loaded).

## 11. Common problems

| Message / problem | Remedy |
|---|---|
| “Setup ✗” | Settings → Check setup; correct the paths with “…”, save |
| “Failed to load Python DLL …\_internal\python314.dll” | The exe was copied without the `_internal` folder. Use the whole program folder; only a shortcut on the desktop |
| Window does not appear | Right-click the taskbar icon → “Maximize”. Otherwise the program opens the window centred on the main screen when the saved position is not visible |
| “Model not found … drive not connected?” | connect the drive or change the model folder in the profile |
| “ffmpeg not found” | set the path in the profile |
| Windows shows “Windows protected your PC” (SmartScreen) | “More info” → “Run anyway”; the exe is not signed |
| Technical terms misspelled | extend the term file (mind the length); if necessary compare model `large` in a sample run |
| German text with “heisst” instead of “heißt” | quirk of the German model (Swiss spelling); replace in the text if needed |
| English passages in a German lecture | mostly English: language `en`; mixed: model `large`, language `auto` |
| Computer sluggish during the run | reduce CPU cores in the profile |
| “ffmpeg could not read the audio” for a DVD | encrypted DVD (not possible) or wrong audio track |
| “ISO could not be mounted” | in Explorer right-click → “Mount”, then use `E:\VIDEO_TS` as input |
| Any other problem | report it as a [GitHub issue](https://github.com/SchulzSM/local-transcriber/issues), with program version and log file (without confidential paths) |

## 12. Interface language

- **Change:** choose **Interface language** at the top right; the window then restarts in the new language (you are
  asked about unsaved profile changes first). The choice applies to this computer.
- **What changes:** all labels, messages, the command line and the log file. **Unchanged**: the recording language
  (a separate setting), the names of the output files (`_nurText`, `_protokoll` …), the `.json` and the profiles;
  profiles can therefore be shared between languages.
- **Manual:** “Open manual” in the About tab opens the manual in the chosen language.
- **Included:** German and English are built in. French, Spanish and Chinese (simplified) come as language files in
  the `sprachen\` folder; for these languages the manual is available in English.
- **Language files:** in the `sprachen\` folder next to the exe, one text file per language (`fr.txt`, `es.txt`,
  `zh.txt` …). Every file there appears in the selection; a `de.txt` or `en.txt` there replaces the built-in version.
  Own translations without write access to the program folder: `%APPDATA%\Transkribieren\sprachen\`. The folder is
  optional: if it is missing, the program keeps running with German and English and does not create it.
- **Adding a language:**
  1. Copy `en.txt`, e.g. as `fr.txt`.
  2. Adjust the header lines: `# language: Français` (name in the selection), `# code: fr`, `# manual:` (manual, if
     available).
  3. Translate the text to the right of `=` on each line. Do not change the key on the left or placeholders such as
     `{name}`; `\n` is a line break.
  4. Check: `Transkribieren.exe --cli --sprachen-pruefen` lists missing entries and wrong placeholders. Missing
     entries appear in German.

## 13. Privacy

- The telemetry of the bundled pyannote library is permanently switched off in the program.

- Everything stays local; models are loaded without internet access.
- Transcripts of teaching sessions may contain names or contributions of students. Check and shorten them before
  passing them on.
- The log contains the computer name and file paths; do not pass it on together with transcripts.
