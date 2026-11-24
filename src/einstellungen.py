"""Profile (Programmorte, Modelle, Standardwerte), Zustand je Rechner, Fachbegriffe, Einrichtungsprüfung.

Profile liegen als lesbare JSON-Dateien in <Programmordner>\\profile (wandern mit dem Ordner bzw. dem Repo).
Ist der Ordner nicht beschreibbar (z. B. Exe unter C:\\Program Files), wird %APPDATA%\\Transkribieren\\profile genutzt.
Der Zustand (zuletzt aktives Profil, letzte Auftragswerte, Fenstergröße) gilt nur für diesen Rechner und liegt in
%APPDATA%\\Transkribieren\\zustand.json.

Pfade dürfen Platzhalter enthalten: {Tools} = Programmordner, außerdem Umgebungsvariablen wie %USERPROFILE%."""
import json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sprache import t

SCHEMA = 1
TOKEN_GRENZE = 223  # faster-whisper kürzt Hinweise (hotwords) auf max_length // 2 - 1 Tokens


def frozen():
    return bool(getattr(sys, "frozen", False))


def app_dir():
    """Programmordner: neben der Exe bzw. die Repo-Wurzel (Elternordner von src)."""
    if frozen():
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


TOOLS = app_dir()
APPDATA = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "Transkribieren")


def _beschreibbar(d):
    try:
        os.makedirs(d, exist_ok=True)
        t = os.path.join(d, ".schreibtest")
        open(t, "w").close(); os.remove(t)
        return True
    except OSError:
        return False


def profil_dir():
    d = os.path.join(TOOLS, "profile")
    return d if _beschreibbar(d) else os.path.join(APPDATA, "profile")


def zustand_pfad():
    return os.path.join(APPDATA, "zustand.json")


def rechnername():
    return re.sub(r"[^\w\-]", "_", os.environ.get("COMPUTERNAME", "") or "Rechner")


def expand(p):
    """Platzhalter auflösen: {Tools}, %VAR%; leere Werte bleiben leer."""
    if not p:
        return ""
    return os.path.normpath(os.path.expandvars(p.replace("{Tools}", TOOLS)))


def kompakt(p):
    """Pfad portabel schreiben: unter dem Programmordner als {Tools}\\…, unter dem Benutzerordner als %USERPROFILE%\\…"""
    if not p:
        return ""
    p = os.path.normpath(p)
    for basis, ph in ((TOOLS, "{Tools}"), (os.environ.get("USERPROFILE", ""), "%USERPROFILE%")):
        if basis and os.path.normcase(p).startswith(os.path.normcase(os.path.normpath(basis)) + os.sep):
            return ph + p[len(os.path.normpath(basis)):]
    return p


def standard_profil(name=None):
    return {
        "schema": SCHEMA,
        "name": name or rechnername(),
        "beschreibung": "",
        "python": r"C:\Python\venvs\faster-whisper\Scripts\python.exe",
        "ffmpeg": r"C:\Toolbox\ffmpeg\bin\ffmpeg.exe",
        "modelle": [
            # Ordnernamen wie die Modelle auf Hugging Face (Bezugsquellen: Anleitung, Abschnitt 1)
            {"kurz": "de", "name": t("profil.modell_de"), "ordner": r"C:\LLMs\whisper-large-v3-turbo-german-ct2"},
            {"kurz": "multi", "name": t("profil.modell_multi"), "ordner": r"C:\LLMs\faster-whisper-large-v3-turbo-ct2"},
            {"kurz": "large", "name": t("profil.modell_large"), "ordner": r"C:\LLMs\faster-whisper-large-v3"},
        ],
        "standardmodell": "de",
        "sprache": "de",
        "threads": 0,
        "compute": "int8",
        "beam": 5,
        "absatz": 2.0,
        "zielordner": "",
        "begriffsdatei": "",
        "kontext": "",
    }


# ------------------------------------------------------------------ Profile
def _dateiname(name):
    return os.path.join(profil_dir(), re.sub(r'[\\/:*?"<>|]', "_", name.strip()) + ".json")


def profile_liste():
    d = profil_dir()
    if not os.path.isdir(d):
        return []
    return sorted(os.path.splitext(f)[0] for f in os.listdir(d) if f.lower().endswith(".json"))


def lade_profil(name_oder_pfad):
    p = name_oder_pfad if name_oder_pfad.lower().endswith(".json") and os.path.isfile(name_oder_pfad) \
        else _dateiname(name_oder_pfad)
    with open(p, encoding="utf-8-sig") as f:
        d = json.load(f)
    voll = standard_profil(d.get("name") or os.path.splitext(os.path.basename(p))[0])
    voll.update(d)  # fehlende Schlüssel (ältere Profile) aus dem Standard ergänzen
    return voll


def speichere_profil(d, name=None):
    d = dict(d)
    d["name"] = name or d.get("name") or rechnername()
    d["schema"] = SCHEMA
    p = _dateiname(d["name"])
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    return p


def loesche_profil(name):
    p = _dateiname(name)
    if os.path.isfile(p):
        os.remove(p)


# ------------------------------------------------------------------ Zustand je Rechner
def lade_zustand():
    try:
        with open(zustand_pfad(), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def speichere_zustand(z):
    os.makedirs(APPDATA, exist_ok=True)
    with open(zustand_pfad(), "w", encoding="utf-8") as f:
        json.dump(z, f, ensure_ascii=False, indent=2)


def aktives_profil(gewuenscht=None):
    """Profil laden: gewünschtes, sonst zuletzt aktives, sonst Rechnername, sonst erstes; fehlt alles, wird ein
    Standardprofil mit dem Rechnernamen angelegt. Rückgabe: (profil, neu_angelegt)."""
    vorhanden = profile_liste()
    for kand in (gewuenscht, lade_zustand().get("profil"), rechnername(), *(vorhanden[:1])):
        if kand and (kand in vorhanden or (kand.lower().endswith(".json") and os.path.isfile(kand))):
            return lade_profil(kand), False
    if gewuenscht:
        raise FileNotFoundError(t("profil.nicht_gefunden", name=gewuenscht, ordner=profil_dir()))
    d = standard_profil()
    speichere_profil(d)
    return d, True


# ------------------------------------------------------------------ Modelle
def modell_eintrag(profil, wahl=None):
    """Modell nach Kurzname, Anzeigename oder Ordner; ohne Angabe das Standardmodell. Rückgabe: (eintrag, ordner)."""
    wahl = wahl or profil.get("standardmodell") or ""
    for m in profil.get("modelle", []):
        if wahl in (m.get("kurz"), m.get("name")):
            return m, expand(m.get("ordner", ""))
    if wahl and os.path.isdir(expand(wahl)):
        return {"kurz": "", "name": os.path.basename(expand(wahl)), "ordner": wahl}, expand(wahl)
    ms = profil.get("modelle", [])
    if not wahl and ms:
        return ms[0], expand(ms[0].get("ordner", ""))
    raise KeyError(t("modell.nicht_im_profil", modell=wahl, profil=profil.get("name")))


# ------------------------------------------------------------------ Fachbegriffe
def begriffe_lesen(pfad):
    """Textdatei (UTF-8, auch mit BOM): ein Begriff je Zeile oder durch Komma/Semikolon getrennt; # = Kommentar."""
    if not pfad:
        return []
    with open(expand(pfad), encoding="utf-8-sig", errors="replace") as f:
        text = "\n".join(z.split("#", 1)[0] for z in f)
    return begriffe_teilen(text)


def begriffe_teilen(text):
    return [t.strip() for t in re.split(r"[,;\n\r\t]+", text or "") if t.strip()]


def begriffe_zusammen(*listen):
    """Zusammenführen ohne Dubletten (Groß/Klein egal), Reihenfolge bleibt."""
    out, gesehen = [], set()
    for liste in listen:
        for t in liste:
            if t.lower() not in gesehen:
                gesehen.add(t.lower()); out.append(t)
    return out


def hotwords_text(begriffe):
    return ", ".join(begriffe)


_TOK = {}


def token_zahl(text, modellordner=None):
    """Tokens wie im Modell (tokenizer.json des Modells, falls das Paket „tokenizers“ verfügbar ist);
    sonst Schätzung. Rückgabe: (anzahl, exakt?)."""
    if not text:
        return 0, True
    tj = os.path.join(modellordner or "", "tokenizer.json")
    if modellordner and os.path.isfile(tj):
        try:
            if tj not in _TOK:
                import tokenizers
                _TOK[tj] = tokenizers.Tokenizer.from_file(tj)
            return len(_TOK[tj].encode(" " + text.strip()).ids), True
        except Exception:
            pass
    return int(len(text) / 3.2) + 1, False


# ------------------------------------------------------------------ Einrichtung prüfen
def _lauf(cmd, timeout=60):
    kw = {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, **kw)
    return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()


def ffmpeg_version(pfad):
    code, out, err = _lauf([pfad, "-hide_banner", "-version"], 20)
    return out.splitlines()[0] if code == 0 and out else None


def pruefen(profil):
    """Prüft alle Bestandteile. Rückgabe: Liste (id, bereich, ok: True/False/None=Hinweis, text).
    id ist sprachneutral (programm, python, ffmpeg, modelle, modell:<kurz>, zielordner, begriffsdatei)."""
    erg = []
    if frozen():
        try:
            import faster_whisper, ctranslate2
            erg.append(("programm", t("pruef.programm"), True,
                        t("pruef.exe_ok", fw=faster_whisper.__version__, ct2=ctranslate2.__version__)))
        except Exception as e:  # pragma: no cover
            erg.append(("programm", t("pruef.programm"), False, t("pruef.exe_fw_fehlt", fehler=e)))
    else:
        py = expand(profil.get("python")) or sys.executable
        if not os.path.isfile(py):
            erg.append(("python", "Python", False, t("pruef.nicht_gefunden", pfad=py)))
        else:
            try:
                code, out, err = _lauf([py, "-c", "import sys, faster_whisper, ctranslate2; "
                                        "print(sys.version.split()[0], faster_whisper.__version__, ctranslate2.__version__)"])
                if code == 0:
                    v = out.split()
                    erg.append(("python", "Python", True, t("pruef.python_ok", pfad=py, py=v[0], fw=v[1], ct2=v[2])))
                else:
                    erg.append(("python", "Python", False,
                                t("pruef.python_fw_fehlt", pfad=py, fehler=err.splitlines()[-1] if err else code)))
            except Exception as e:
                erg.append(("python", "Python", False, f"{py}: {e}"))
    ff = expand(profil.get("ffmpeg"))
    try:
        v = ffmpeg_version(ff) if ff else None
    except Exception:
        v = None
    erg.append(("ffmpeg", "ffmpeg", bool(v), v and f"{ff} – {v}" or t("pruef.ffmpeg_fehler", pfad=ff or t("pruef.leer"))))
    if not profil.get("modelle"):
        erg.append(("modelle", t("pruef.modelle"), False, t("pruef.kein_modell")))
    for m in profil.get("modelle", []):
        o = expand(m.get("ordner"))
        kurz = m.get("kurz") or m.get("name")
        mid, lab = f"modell:{kurz}", t("pruef.modell", name=kurz)
        if not os.path.isdir(o):
            lw = os.path.splitdrive(o)[0]
            hinweis = " " + t("pruef.laufwerk", laufwerk=lw) if lw and not os.path.isdir(lw + "\\") else ""
            erg.append((mid, lab, False, t("pruef.ordner_fehlt", pfad=o) + hinweis))
            continue
        fehlt = [f for f in ("model.bin", "config.json") if not os.path.isfile(os.path.join(o, f))]
        if fehlt:
            erg.append((mid, lab, False, t("pruef.es_fehlt", pfad=o, dateien=", ".join(fehlt))))
        elif not os.path.isfile(os.path.join(o, "tokenizer.json")):
            erg.append((mid, lab, None, t("pruef.tokenizer_fehlt", pfad=o)))
        else:
            gb = os.path.getsize(os.path.join(o, "model.bin")) / 1e9
            erg.append((mid, lab, True, f"{o} ({gb:.1f} GB)"))
    for key in ("zielordner", "begriffsdatei"):
        v = expand(profil.get(key))
        if v:
            ok = os.path.isdir(v) if key == "zielordner" else os.path.isfile(v)
            erg.append((key, t(f"pruef.{key}"), ok, v if ok else t("pruef.nicht_gefunden", pfad=v)))
    return erg
