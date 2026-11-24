r"""Lokale Transkription mit Zeitstempeln (faster-whisper, offline; nichts verlässt den Rechner).

Aufruf (Entwicklung): <python der Transkriptions-Umgebung> src\transkribieren.py <audio …> [Optionen]
Bequemer: Transkribieren.bat --cli <audio …> [Optionen]   bzw. Exe: Transkribieren.exe --cli <audio …> [Optionen]

Einstellungen kommen aus einem Profil (profile\<Name>.json; Standard: zuletzt in der Oberfläche aktives Profil):
Programmorte (ffmpeg), Modelle, Standardsprache, Threads, Rechenart, Zielordner, Begriffsdatei, Kontextsatz.
Jede Option auf der Kommandozeile überschreibt den Profilwert.

Optionen
  --profil <Name|Datei.json>          Profil wählen
  --modell <Kurzname|Name|Ordner>     Modell aus dem Profil (z. B. de, large, multi) oder Modellordner
  --sprache de|en|…|auto              Sprache der Aufnahme
  --begriffe "Mitose, Osmose, …"      Fachbegriffe (werden in jedem 30-s-Fenster als Hinweis gegeben, „hotwords“)
  --begriffe-datei <txt>              Fachbegriffe aus Textdatei (je Zeile oder kommagetrennt, # = Kommentar)
  --kontext "Vorlesung Anatomie."     kurzer Satz zum Thema (nur für den Anfang der Aufnahme wirksam)
  --ausgabe <Ordner>                  Zielordner (Standard: Profil, sonst neben der Audiodatei)
  --test <Sekunden>                   nur den Anfang transkribieren (Probelauf)
  --woerter                           Zeitstempel je Wort zusätzlich in der JSON-Datei
  --raster 0.5 1 5                    zusätzlich Text im festen Zeitraster (Sekunden; schaltet --woerter ein)
  --spur <n> / --spuren               Tonspur wählen (0 = erste) / nur Tonspuren auflisten
  --titel <xx> / --nur-datei          DVD: Titelsatz wählen / bei VTS_xx_n.VOB nur diese Datei
  --ffmpeg <exe>  --threads <n>  --compute int8|int8_float32|float32  --beam <n>
  --absatz 1.2                        neuer Absatz in .txt/_nurText.txt ab dieser Sprechpause (s; Standard: Profil, sonst 2)
  --kein-protokoll                    keine Protokolldatei schreiben
  --pruefen                           nur die Einrichtung des Profils prüfen
  --version                           Programmversion
  DVD: Eingabe darf ein .iso, ein DVD-Ordner (mit VIDEO_TS) oder eine VTS_xx_n.VOB sein.

Ausgabe je Audiodatei <name>:
  <name>.tsv / .txt / _nurText.txt / .srt / .json   (wie bisher; _raster_<x>.txt mit --raster)
  <name>_protokoll.txt   Einstellungen, Modell, Versionen, Ein- und Ausgabedateien, Laufzeit
Die TSV wird während des Laufs fortgeschrieben – ein Abbruch verliert nichts Fertiges."""
import os as _os
_os.environ["PYANNOTE_METRICS_ENABLED"] = "false"  # Telemetrie von pyannote aus: es wird nichts übertragen
import argparse, datetime, json, os, platform, shutil, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import einstellungen as E
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module=r"pyannote(..*)?")  # Audio kommt über ffmpeg
from version import __version__, NAME
import sprache as S
from sprache import t

FFMPEG_KANDIDATEN = [os.environ.get("FFMPEG", ""), r"C:\Toolbox\ffmpeg\bin\ffmpeg.exe", "ffmpeg"]
FFMPEG_PFAD = None  # aus --ffmpeg bzw. Profil
SR = 16000


def ffmpeg():
    for k in [FFMPEG_PFAD] + FFMPEG_KANDIDATEN:
        if k and (os.path.isfile(k) or shutil.which(k)):
            return k
    sys.exit(t("cli.ffmpeg_fehlt"))


def lade_audio(pfad, sekunden=None, spur=None):
    """Audio über ffmpeg als 16 kHz mono float32 (flac, mp3, m4a, wav, mp4, mkv, vob, concat:… von DVD)."""
    import numpy as np
    cmd = [ffmpeg(), "-nostdin", "-v", "error", "-probesize", "200M", "-analyzeduration", "200M", "-i", pfad]
    if spur is not None:
        cmd += ["-map", f"0:a:{spur}"]
    if sekunden:
        cmd += ["-t", str(sekunden)]
    cmd += ["-vn", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0 or not r.stdout:
        sys.exit(t("cli.ton_fehler") + (" " + t("cli.ton_fehler_dvd") if "VOB" in pfad.upper() else "") + ":\n"
                 + r.stderr.decode("utf-8", "replace")[-800:])
    return np.frombuffer(r.stdout, np.int16).astype("float32") / 32768.0


# ---------- DVD: ISO einbinden, VIDEO_TS-Titel zusammensetzen ----------
def _ps(cmd):
    r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def iso_einbinden(iso):
    """ISO als Laufwerk einbinden (Windows-Bordmittel). Rückgabe: (Laufwerkswurzel, selbst_eingebunden)."""
    iso = os.path.abspath(iso)
    code, out, err = _ps(f"(Get-DiskImage -ImagePath '{iso}' | Get-Volume).DriveLetter")
    if out:
        return out[-1] + ":\\", False
    code, out, err = _ps(f"(Mount-DiskImage -ImagePath '{iso}' -PassThru | Get-Volume).DriveLetter")
    if not out:
        sys.exit(t("cli.iso_fehler", fehler=err[-300:]))
    return out[-1] + ":\\", True


def iso_freigeben(iso):
    _ps(f"Dismount-DiskImage -ImagePath '{os.path.abspath(iso)}' | Out-Null")


def dvd_titel(ordner, titel=None):
    """VIDEO_TS-Titel: alle VTS_xx_1…n.VOB (ohne Menü _0) eines Titelsatzes; Standard = größter Titelsatz."""
    import re
    vt = ordner if os.path.basename(os.path.normpath(ordner)).upper() == "VIDEO_TS" else os.path.join(ordner, "VIDEO_TS")
    if not os.path.isdir(vt):
        return None
    saetze = {}
    for f in os.listdir(vt):
        m = re.fullmatch(r"VTS_(\d\d)_([1-9])\.VOB", f.upper())
        if m:
            saetze.setdefault(int(m.group(1)), []).append((int(m.group(2)), os.path.join(vt, f)))
    if not saetze:
        return None
    groesse = {k: sum(os.path.getsize(p) for _, p in v) for k, v in saetze.items()}
    print("   " + t("cli.dvd_titelsaetze") + " " + ", ".join(f"{k:02d} ({groesse[k] / 1e9:.1f} GB)" for k in sorted(saetze)), flush=True)
    k = titel if titel is not None else max(groesse, key=groesse.get)
    if k not in saetze:
        sys.exit(t("cli.titelsatz_fehlt", n=k))
    teile = [p for _, p in sorted(saetze[k])]
    print("   → " + t("cli.titelsatz", n=f"{k:02d}", dateien=", ".join(os.path.basename(p) for p in teile)), flush=True)
    return k, "concat:" + "|".join(teile)


def quelle(pfad, a):
    """Eingabe auflösen. Rückgabe: (ffmpeg-Eingabe, Namensstamm, Standard-Zielordner, Aufräumfunktion)."""
    pfad = os.path.abspath(pfad)
    aufr = lambda: None
    stamm = os.path.splitext(os.path.basename(pfad))[0]
    ziel = os.path.dirname(pfad)
    if pfad.lower().endswith(".iso"):
        wurzel, selbst = iso_einbinden(pfad)
        print("   " + t("cli.iso_eingebunden", laufwerk=wurzel), flush=True)
        if selbst:
            aufr = lambda: iso_freigeben(pfad)
        t = dvd_titel(wurzel, a.titel)
        if not t:
            aufr(); sys.exit(t("cli.iso_ohne_dvd"))
        return t[1], f"{stamm}_T{t[0]:02d}", ziel, aufr
    if os.path.isdir(pfad):
        t = dvd_titel(pfad, a.titel)
        if not t:
            sys.exit(t("cli.ordner_ohne_dvd", pfad=pfad))
        basis = os.path.dirname(pfad) if os.path.basename(pfad).upper() == "VIDEO_TS" else pfad
        return t[1], f"{os.path.basename(basis) or 'DVD'}_T{t[0]:02d}", os.path.dirname(basis) or basis, aufr
    import re
    m = re.fullmatch(r"VTS_(\d\d)_[1-9]", stamm.upper())
    if m and not a.nur_datei:  # einzelne VOB eines Titels → ganzen Titel nehmen
        t = dvd_titel(os.path.dirname(pfad), int(m.group(1)))
        if t:
            return t[1], f"{os.path.basename(os.path.dirname(os.path.dirname(pfad))) or 'DVD'}_T{t[0]:02d}", \
                os.path.dirname(os.path.dirname(pfad)), aufr
    return pfad, stamm, ziel, aufr


def spuren_zeigen(eingabe):
    r = subprocess.run([ffmpeg(), "-hide_banner", "-probesize", "200M", "-analyzeduration", "200M", "-i", eingabe],
                       capture_output=True, text=True, errors="replace")
    n = 0
    for line in r.stderr.splitlines():
        if "Audio:" in line:
            print("   " + t("cli.tonspur", n=n, info=line.strip())); n += 1
    if not n:
        print("   " + t("cli.keine_tonspur"))


def ts(sec, srt=False):
    if srt:  # auf Millisekunden runden (8.95 → 00:00:08,950, nicht 08,949)
        ms = int(round(max(sec, 0) * 1000))
        h, r = divmod(ms, 3_600_000); m, r = divmod(r, 60_000); s, ms = divmod(r, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    h, r = divmod(sec, 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{int(s):02d}" if h else f"{int(m):02d}:{int(s):02d}"


# ---------- Text- und Untertiteldateien ----------
SRT_ZEICHEN, SRT_ZEILEN, SRT_DAUER, SRT_MIN = 42, 2, 7.0, 1.0  # Zeichen je Zeile, Zeilen, max./min. Dauer (s)


def text_dateien(alle, basis, absatz=2.0):
    """<basis>.txt (Absätze mit [mm:ss]) und <basis>_nurText.txt; neuer Absatz bei Sprechpause > absatz s."""
    with open(basis + ".txt", "w", encoding="utf-8") as f, open(basis + "_nurText.txt", "w", encoding="utf-8") as g:
        last = None
        for d in alle:
            neu = last is None or d["start"] - last > absatz
            if neu:
                f.write(("\n\n" if last is not None else "") + "[" + ts(d["start"]) + "] " + d["text"])
                g.write(("\n\n" if last is not None else "") + d["text"])
            else:
                f.write(" " + d["text"]); g.write(" " + d["text"])
            last = d["ende"]
        f.write("\n"); g.write("\n")


def _woerter(d):
    """Wörter eines Segments mit Zeiten; ohne Wortzeitstempel anteilig nach Zeichenzahl verteilt."""
    if d.get("woerter"):
        return [(w[0], w[1], w[2]) for w in d["woerter"] if w[2]]
    tok = d["text"].split()
    if not tok:
        return []
    gesamt = sum(len(t) + 1 for t in tok)
    dauer = max(d["ende"] - d["start"], 0.01)
    out, pos = [], 0
    for t in tok:
        a = d["start"] + dauer * pos / gesamt
        pos += len(t) + 1
        out.append((a, d["start"] + dauer * pos / gesamt, t))
    return out


def _umbrechen(text, breite=SRT_ZEICHEN):
    """Höchstens zwei Zeilen; Umbruch an der Lücke, bei der beide Zeilen ≤ breite und möglichst gleich lang sind."""
    if len(text) <= breite:
        return text
    luecken = [i for i, c in enumerate(text) if c == " "]
    if not luecken:
        return text
    passend = [i for i in luecken if i <= breite and len(text) - i - 1 <= breite]
    i = min(passend or luecken, key=lambda k: abs(k - len(text) / 2))
    return text[:i] + "\n" + text[i + 1:]


def _teilen(ws):
    """Wörter eines Segments in n möglichst gleich lange Blöcke; n so, dass Zeichen- und Dauergrenze halten.
    Schnitt bevorzugt hinter Satzzeichen in der Nähe der Sollposition."""
    max_z = SRT_ZEILEN * SRT_ZEICHEN
    text = " ".join(w[2] for w in ws)
    dauer = ws[-1][1] - ws[0][0]
    n = max(1, -(-len(text) // max_z), int(-(-dauer // SRT_DAUER)))
    while True:
        bloecke, akt, laenge = [], [], 0
        soll = len(text) / n
        for j, w in enumerate(ws):
            akt.append(w); laenge += len(w[2]) + 1
            rest = len(ws) - j - 1
            if len(bloecke) < n - 1 and rest:
                satz = w[2][-1:] in ".,;:?!–"
                if laenge >= soll * (0.75 if satz else 1.0):
                    bloecke.append(akt); akt, laenge = [], 0
        if akt:
            bloecke.append(akt)
        zu_lang = any(len(z) > SRT_ZEICHEN for blk in bloecke
                      for z in _umbrechen(" ".join(x[2] for x in blk)).splitlines())
        if not zu_lang or n >= len(ws):
            return bloecke
        n += 1


def srt_bloecke(alle):
    """Segmente in lesbare Untertitel teilen: höchstens SRT_ZEILEN × SRT_ZEICHEN Zeichen und etwa SRT_DAUER s je
    Einblendung, gleichmäßig aufgeteilt (keine einzelnen Restwörter). Blöcke überschreiten Segmentgrenzen nicht."""
    out = []
    for d in alle:
        ws = _woerter(d)
        if not ws:
            continue
        for b in _teilen(ws):
            out.append([b[0][0], max(b[-1][1], b[0][0] + SRT_MIN), _umbrechen(" ".join(x[2] for x in b))])
    for i in range(len(out) - 1):  # keine Überlappung
        out[i][1] = min(out[i][1], out[i + 1][0])
    return out


def srt_datei(alle, basis):
    bl = srt_bloecke(alle)
    with open(basis + ".srt", "w", encoding="utf-8") as f:
        for i, (a, e, t) in enumerate(bl, 1):
            f.write(f"{i}\n{ts(a, True)} --> {ts(e, True)}\n{t}\n\n")
    return len(bl)


def _dateiinfo(pfad):
    try:
        st = os.stat(pfad)
        return t("prot.dateiinfo", mb=f"{st.st_size / 1e6:.1f}",
                 datum=f"{datetime.datetime.fromtimestamp(st.st_mtime):%d.%m.%Y %H:%M}")
    except OSError:
        return "–"


def protokoll(basis, a, lauf, status):
    """Kleine, lesbare Protokolldatei neben den Ergebnissen: Einstellungen, Modell, Versionen, Ein-/Ausgabe.
    Beschriftungen in der Sprache der Oberfläche; die Spaltenbreite richtet sich nach der längsten Beschriftung."""
    if a.kein_protokoll or not basis:
        return
    tok_info = t("prot.begriffe", n=len(a.begriffe_liste), tokens=a.begriffe_tokens) \
        + ("" if a.begriffe_exakt else " " + t("cli.geschaetzt"))
    if a.begriffe_tokens > E.TOKEN_GRENZE:
        tok_info += " – " + t("prot.ueber_grenze", grenze=E.TOKEN_GRENZE)
    param = (f"compute={a.compute}, threads={a.threads}, beam={a.beam}, " + t("prot.vad") + ", "
             + t("prot.wortzeitstempel", wert=t("prot.ja") if a.woerter else t("prot.nein")))
    if a.raster:
        param += ", " + t("prot.raster", werte=" ".join(f"{r:g}" for r in a.raster))
    if a.test:
        param += ", " + t("prot.nur_erste", s=a.test)
    if a.spur is not None:
        param += ", " + t("prot.tonspur", n=a.spur)
    param += (", " + t("prot.absatz", s=f"{a.absatz:g}") + ", "
              + t("prot.untertitel", zeilen=SRT_ZEILEN, zeichen=SRT_ZEICHEN, dauer=f"{SRT_DAUER:g}")
              + ("" if a.woerter else " " + t("prot.genaehert")))
    sprache = a.sprache
    if "sprache" in lauf:
        sprache += " " + t("prot.erkannt", sprache=lauf["sprache"], p=f"{lauf['sprache_p']:.2f}")
    felder = [
        ("status", status),
        ("programmversion", f"{__version__}" + (" (Exe)" if E.frozen() else "")),
        ("start", f"{lauf['start']:%d.%m.%Y %H:%M:%S}"),
    ]
    if "ende" in lauf:
        felder += [("ende", f"{lauf['ende']:%d.%m.%Y %H:%M:%S}"),
                   ("rechenzeit", t("prot.rechenzeit_wert", zeit=ts(lauf["rechenzeit"]), faktor=f"{lauf['faktor']:.2f}"))]
    felder += [
        ("rechner", f"{platform.node()} – {platform.platform()}"),
        ("python", platform.python_version()),
        ("faster_whisper", f"{lauf.get('fw', '?')} / CTranslate2 {lauf.get('ct2', '?')}"),
        ("ffmpeg", lauf.get("ffmpeg", "?")),
        None,
        ("profil", f"{a.profil_name} ({a.profil_datei})"),
        ("modell", f"{a.modell_name} – {a.modell_ordner}"),
        ("sprache", sprache),
        ("parameter", param),
        ("kontextsatz", a.kontext or "–"),
        ("begriffsdatei", E.expand(a.begriffe_datei) if a.begriffe_datei else "–"),
        ("fachbegriffe", tok_info),
        ("", E.hotwords_text(a.begriffe_liste) or "–"),
        None,
        ("eingabe", f"{lauf['eingabe']} ({_dateiinfo(lauf['eingabe'])})"),
    ]
    if lauf.get("ffmpeg_eingabe") and lauf["ffmpeg_eingabe"] != lauf["eingabe"]:
        felder.append(("gelesen_als", lauf["ffmpeg_eingabe"][:300]))
    if "dauer" in lauf:
        felder.append(("aufnahmedauer", f"{ts(lauf['dauer'])} ({lauf['dauer']:.1f} s)"))
    if "segmente" in lauf:
        felder.append(("segmente", str(lauf["segmente"])))
    ausg = lauf.get("ausgaben", []) or ["–"]
    felder += [("ausgabe", ausg[0])] + [("", x) for x in ausg[1:]]
    felder += [None, ("befehlszeile", subprocess.list2cmdline(sys.argv))]
    namen = {k: (t(f"prot.feld.{k}") + ":" if k else "") for k in (f[0] for f in felder if f)}
    breite = max(len(v) for v in namen.values()) + 2
    zeilen = [f"{t('app.name')} – {t('prot.titel')}"]
    zeilen += ["" if f is None else namen[f[0]].ljust(breite) + f[1] for f in felder]
    with open(basis + "_protokoll.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(zeilen) + "\n")


def transkribiere(model, audio_pfad, a):
    print(f"\n== {audio_pfad}", flush=True)
    eingabe, stamm, std_ziel, aufraeumen = quelle(audio_pfad, a)
    try:
        if a.spuren:
            spuren_zeigen(eingabe); return
        print("   " + t("cli.audio_laden"), flush=True)
        audio = lade_audio(eingabe, a.test, a.spur)
    finally:
        aufraeumen()
    ext = os.path.splitext(audio_pfad)[1]
    gleich = [x for x in a.audio if os.path.splitext(os.path.basename(x))[0] == os.path.splitext(os.path.basename(audio_pfad))[0]]
    name = stamm + (f"_{ext.lstrip('.')}" if len(gleich) > 1 and ext else "") + \
        (f"_Spur{a.spur}" if a.spur else "") + ("_test" if a.test else "")
    ziel = a.ausgabe or std_ziel
    os.makedirs(ziel, exist_ok=True)
    basis = os.path.normpath(os.path.join(ziel, name))
    dauer = len(audio) / SR
    lauf = dict(a.lauf_basis, start=datetime.datetime.now(), eingabe=os.path.abspath(audio_pfad),
                ffmpeg_eingabe=eingabe, dauer=dauer, ausgaben=[basis + ".tsv"])
    protokoll(basis, a, lauf, t("prot.status_laeuft"))
    print("   " + t("cli.laeuft", dauer=ts(dauer)), flush=True)
    t0 = time.time()
    segs, info = model.transcribe(
        audio, language=None if a.sprache == "auto" else a.sprache, beam_size=a.beam, vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 700}, word_timestamps=a.woerter,
        initial_prompt=a.kontext or None,  # wirkt nur im ersten 30-s-Fenster
        hotwords=E.hotwords_text(a.begriffe_liste) or None,  # wird in jedem Fenster mitgegeben
        condition_on_previous_text=False)
    alle = []
    with open(basis + ".tsv", "w", encoding="utf-8") as tsv:
        tsv.write("start\tende\ttext\n")
        for s in segs:
            text = s.text.strip()
            if not text:
                continue
            d = {"start": round(s.start, 2), "ende": round(s.end, 2), "text": text}
            if a.woerter and s.words:
                d["woerter"] = [[round(w.start, 2), round(w.end, 2), w.word.strip()] for w in s.words]
            alle.append(d)
            tsv.write(f"{d['start']:.2f}\t{d['ende']:.2f}\t{text}\n"); tsv.flush()
            el = time.time() - t0
            pct = min(100, 100 * s.end / dauer) if dauer else 0
            rest = el / max(s.end, 1) * (dauer - s.end)
            print(f"   [{ts(s.start)}] {pct:5.1f} %  " + t("cli.rest", rest=ts(rest)) + f"  | {text[:70]}", flush=True)
    text_dateien(alle, basis, a.absatz)
    n_srt = srt_datei(alle, basis)
    print("   " + t("cli.untertitel", n=n_srt, zeilen=SRT_ZEILEN, zeichen=SRT_ZEICHEN, dauer=f"{SRT_DAUER:g}")
          + ("" if a.woerter else " – " + t("cli.untertitel_genaehert")), flush=True)
    rechenzeit = time.time() - t0
    with open(basis + ".json", "w", encoding="utf-8") as f:
        json.dump({"audio": os.path.abspath(audio_pfad), "dauer_s": round(dauer, 1), "modell": a.modell_ordner,
                   "modell_name": a.modell_name, "programm": f"{NAME} {__version__}", "profil": a.profil_name,
                   "sprache": info.language, "fachbegriffe": a.begriffe_liste, "kontext": a.kontext,
                   "laufzeit_s": round(rechenzeit), "segmente": alle}, f, ensure_ascii=False, indent=1)
    ausgaben = [basis + x for x in (".tsv", ".txt", "_nurText.txt", ".srt", ".json")]
    for r in a.raster or []:
        rp = raster_datei(alle, r, basis)
        ausgaben.append(rp)
        print("   " + t("cli.raster"), rp, flush=True)
    lauf.update(ende=datetime.datetime.now(), rechenzeit=rechenzeit, faktor=rechenzeit / max(dauer, 1),
                sprache=info.language, sprache_p=info.language_probability, segmente=len(alle),
                ausgaben=ausgaben + [basis + "_protokoll.txt"])
    protokoll(basis, a, lauf, t("prot.status_fertig"))
    print("   " + t("cli.fertig", zeit=ts(rechenzeit)) + f" → {basis}.tsv/.txt/_nurText.txt/.srt/.json (+ _protokoll.txt)",
          flush=True)
    print(f"ERGEBNIS\t{basis}", flush=True)  # Zeile für die Oberfläche („Ergebnis öffnen“)


def ts_ms(sec):
    h, r = divmod(sec, 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"


def raster_datei(segmente, raster, basis):
    """Text in festem Zeitraster (z. B. 0,5 / 1 / 5 s): je Rasterfeld eine Zeile „[hh:mm:ss.mmm] Wörter“.
    Mit Wortzeitstempeln (--woerter) exakt; sonst werden Segmente über ihre Dauer gleichmäßig verteilt (Näherung)."""
    felder = {}
    for d in segmente:
        ws = d.get("woerter")
        if not ws:  # Näherung: Wörter gleichmäßig über das Segment verteilen
            tok = d["text"].split(); n = len(tok) or 1
            ws = [[d["start"] + (d["ende"] - d["start"]) * i / n, 0, w] for i, w in enumerate(tok)]
        for st, _, w in ws:
            felder.setdefault(int(st // raster), []).append(w)
    lab = (f"{raster:g}s" if raster >= 1 else f"{int(round(raster * 1000))}ms")
    pfad = f"{basis}_raster_{lab}.txt"
    with open(pfad, "w", encoding="utf-8") as f:
        for k in sorted(felder):
            f.write(f"[{ts_ms(k * raster)}] {' '.join(felder[k])}\n")
    return pfad


def _konsole_utf8():
    """Ausgabe immer UTF-8 (die Oberfläche liest UTF-8); Exe ohne Konsole: an die aufrufende Konsole anhängen."""
    if sys.stdout is None:
        try:
            import ctypes
            if ctypes.windll.kernel32.AttachConsole(-1):
                sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace")
                sys.stderr = sys.stdout
        except Exception:
            pass
        if sys.stdout is None:
            sys.stdout = sys.stderr = open(os.devnull, "w")
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def argumente(argv=None):
    p = argparse.ArgumentParser(prog="transkribieren",
                                description=f"{t('app.name')} {__version__} – {t('arg.beschreibung')}")
    p.add_argument("audio", nargs="*", help=t("arg.audio"))
    p.add_argument("--profil", help=t("arg.profil"))
    p.add_argument("--modell", help=t("arg.modell"))
    p.add_argument("--sprache", help=t("arg.sprache"))
    p.add_argument("--begriffe", default="", help=t("arg.begriffe"))
    p.add_argument("--begriffe-datei", help=t("arg.begriffe_datei"))
    p.add_argument("--kontext", help=t("arg.kontext"))
    p.add_argument("--ausgabe", help=t("arg.ausgabe"))
    p.add_argument("--test", type=int, help=t("arg.test"))
    p.add_argument("--woerter", action="store_true", help=t("arg.woerter"))
    p.add_argument("--raster", type=float, nargs="+", help=t("arg.raster"))
    p.add_argument("--spur", type=int, help=t("arg.spur"))
    p.add_argument("--spuren", action="store_true", help=t("arg.spuren"))
    p.add_argument("--titel", type=int, help=t("arg.titel"))
    p.add_argument("--nur-datei", action="store_true", help=t("arg.nur_datei"))
    p.add_argument("--ffmpeg", help=t("arg.ffmpeg"))
    p.add_argument("--threads", type=int, help=t("arg.threads"))
    p.add_argument("--compute", help=t("arg.compute"))
    p.add_argument("--beam", type=int, help=t("arg.beam"))
    p.add_argument("--absatz", type=float, help=t("arg.absatz"))
    p.add_argument("--kein-protokoll", action="store_true", help=t("arg.kein_protokoll"))
    p.add_argument("--pruefen", action="store_true", help=t("arg.pruefen"))
    p.add_argument("--ui", help=t("arg.ui"))
    p.add_argument("--sprachen-pruefen", action="store_true", help=t("arg.sprachen_pruefen"))
    p.add_argument("--version", action="version", version=f"{t('app.name')} {__version__}")
    return p.parse_args(argv)


def ui_vorab(argv):
    """--ui <code> vor dem Aufbau der Hilfe auswerten (die Hilfetexte sind bereits übersetzt)."""
    argv = sys.argv[1:] if argv is None else argv
    for i, x in enumerate(argv):
        if x == "--ui" and i + 1 < len(argv):
            return argv[i + 1]
        if x.startswith("--ui="):
            return x[5:]
    return None


def main(argv=None):
    global FFMPEG_PFAD
    _konsole_utf8()
    S.waehlen(ui_vorab(argv))
    a = argumente(argv)
    if a.sprachen_pruefen:
        zeilen, fehler = S.pruefbericht()
        print("\n".join(zeilen))
        sys.exit(1 if fehler else 0)
    try:
        profil, neu = E.aktives_profil(a.profil)
    except FileNotFoundError as e:
        sys.exit(str(e))
    a.profil_name = profil.get("name")
    a.profil_datei = a.profil if a.profil and a.profil.lower().endswith(".json") else E._dateiname(a.profil_name)
    print(f"{t('app.name')} {__version__} – " + t("cli.profil", name=a.profil_name)
          + (" " + t("cli.profil_neu") if neu else ""), flush=True)
    if a.pruefen:
        fehler = 0
        for _id, bereich, ok, text in E.pruefen(profil):
            print(f"  {'✓' if ok else ('!' if ok is None else '✗')} {bereich}: {text}")
            fehler += ok is False
        sys.exit(1 if fehler else 0)
    if not a.audio:
        sys.exit(t("cli.keine_eingabe"))
    FFMPEG_PFAD = E.expand(a.ffmpeg or profil.get("ffmpeg")) or None
    if a.sprache is None:
        a.sprache = profil.get("sprache") or "de"
    if a.threads is None:
        a.threads = int(profil.get("threads") or 0) or max(1, (os.cpu_count() or 4) - 1)
    a.compute = a.compute or profil.get("compute") or "int8"
    if a.absatz is None:
        a.absatz = float(profil.get("absatz") or 2.0)
    a.beam = a.beam or int(profil.get("beam") or 5)
    if a.kontext is None:
        a.kontext = profil.get("kontext") or ""
    if a.begriffe_datei is None:
        a.begriffe_datei = profil.get("begriffsdatei") or ""
    if not a.ausgabe and profil.get("zielordner"):
        a.ausgabe = E.expand(profil["zielordner"])
    if a.raster:
        a.woerter = True
    if a.spuren:
        for f in a.audio:
            transkribiere(None, f, a)
        return
    try:
        eintrag, a.modell_ordner = E.modell_eintrag(profil, a.modell)
    except KeyError as e:
        sys.exit(str(e))
    a.modell_name = eintrag.get("name") or eintrag.get("kurz") or a.modell_ordner
    if not os.path.isfile(os.path.join(a.modell_ordner, "model.bin")):
        lw = os.path.splitdrive(a.modell_ordner)[0]
        sys.exit(t("cli.modell_fehlt", pfad=a.modell_ordner)
                 + (" " + t("pruef.laufwerk", laufwerk=lw) if lw and not os.path.isdir(lw + "\\") else ""))
    try:
        datei_begriffe = E.begriffe_lesen(a.begriffe_datei)
    except OSError as e:
        sys.exit(t("cli.begriffsdatei_fehler", fehler=e))
    a.begriffe_liste = E.begriffe_zusammen(datei_begriffe, E.begriffe_teilen(a.begriffe))
    a.begriffe_tokens, a.begriffe_exakt = E.token_zahl(E.hotwords_text(a.begriffe_liste), a.modell_ordner)
    if a.begriffe_liste:
        print(t("cli.begriffe", n=len(a.begriffe_liste), tokens=a.begriffe_tokens, grenze=E.TOKEN_GRENZE)
              + ("" if a.begriffe_exakt else " " + t("cli.geschaetzt")), flush=True)
        if a.begriffe_tokens > E.TOKEN_GRENZE:
            print("   " + t("cli.begriffe_zu_lang", grenze=E.TOKEN_GRENZE), flush=True)
    import ctranslate2, faster_whisper
    from faster_whisper import WhisperModel
    a.lauf_basis = {"fw": faster_whisper.__version__, "ct2": ctranslate2.__version__,
                    "ffmpeg": f"{ffmpeg()} – {E.ffmpeg_version(ffmpeg()) or '?'}"}
    print(t("cli.modell_laden", name=a.modell_name, pfad=a.modell_ordner, compute=a.compute, threads=a.threads),
          flush=True)
    model = WhisperModel(a.modell_ordner, device="cpu", compute_type=a.compute, cpu_threads=a.threads,
                         local_files_only=True)
    for f in a.audio:
        transkribiere(model, f, a)


if __name__ == "__main__":
    main()
