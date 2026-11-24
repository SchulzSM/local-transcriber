r"""Sprachen der Oberfläche: alle sichtbaren Texte stehen in Sprachdateien, nicht im Code.

Ordner: <Programmordner>\sprachen\ (mit dem Programm ausgeliefert) und zusätzlich %APPDATA%\Transkribieren\sprachen\
(eigene Übersetzungen ohne Schreibrecht im Programmordner). Jede gültige Datei <code>.txt dort ist wählbar.

Aufbau einer Sprachdatei (UTF-8):
    # language: English          Kopfzeilen vor dem ersten Eintrag; „language“ erscheint in der Auswahlliste
    # code: en                   Sprachcode (sonst der Dateiname)
    # version: 2.2.0             Programmversion, zu der die Datei passt
    # manual: Manual_en.md       Anleitung neben der Exe in dieser Sprache
    schluessel = Text            ein Eintrag je Zeile; \n = Zeilenumbruch; {name} = Platzhalter
    # …                          sonstige Zeilen mit # sind Kommentare

de.txt ist die Referenz: Fehlt ein Schlüssel in einer anderen Sprache, erscheint der deutsche Text.
Prüfen: Transkribieren --cli --sprachen-pruefen (fehlende, überzählige Schlüssel, abweichende Platzhalter)."""
import json, os, re, sys

REFERENZ = "de"
_PLATZHALTER = re.compile(r"\{(\w+)(:[^{}]*)?\}")


def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


APPDATA = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "Transkribieren")
ORDNER = [os.path.join(_app_dir(), "sprachen"), os.path.join(APPDATA, "sprachen")]

_aktiv = {"code": None, "texte": {}, "ref": {}, "kopf": {}}


def lesen(pfad):
    """Rückgabe: (kopf, texte, probleme) – probleme = Liste (Zeilennummer, Meldung)."""
    kopf, texte, probleme = {}, {}, []
    with open(pfad, encoding="utf-8-sig", errors="replace") as f:
        for nr, zeile in enumerate(f, 1):
            s = zeile.strip()
            if not s:
                continue
            if s.startswith("#"):
                m = re.match(r"#\s*([\w-]+)\s*:\s*(.*)$", s)
                if m and not texte:
                    kopf[m.group(1).lower()] = m.group(2).strip()
                continue
            if "=" not in s:
                probleme.append((nr, "ohne „=“ / no „=“"))
                continue
            k, v = s.split("=", 1)
            k = k.strip()
            if k in texte:
                probleme.append((nr, f"doppelt / duplicate: {k}"))
            texte[k] = v.strip().replace("\\n", "\n")
    return kopf, texte, probleme


def verfuegbar():
    """Liste (code, name, pfad), nach Name sortiert; bei gleichem Code gilt der Programmordner."""
    gefunden = {}
    for d in ORDNER:
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.lower().endswith(".txt"):
                continue
            p = os.path.join(d, f)
            try:
                kopf, texte, _ = lesen(p)
            except OSError:
                continue
            if not texte:
                continue
            code = (kopf.get("code") or os.path.splitext(f)[0]).lower()
            gefunden.setdefault(code, (code, kopf.get("language") or code, p))
    return sorted(gefunden.values(), key=lambda x: x[1].lower())


def systemsprache():
    """Sprache der Windows-Oberfläche als Code (de, en, …) oder ""."""
    try:
        import ctypes, locale
        lcid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        return (locale.windows_locale.get(lcid) or "")[:2].lower()
    except Exception:
        try:
            import locale
            return (locale.getlocale()[0] or "")[:2].lower()
        except Exception:
            return ""


def _gemerkt():
    try:
        with open(os.path.join(APPDATA, "zustand.json"), encoding="utf-8") as f:
            return json.load(f).get("oberflaeche") or ""
    except (OSError, ValueError):
        return ""


def waehlen(code=None):
    """Sprache laden: gewünscht → gemerkt (zustand.json) → Windows-Sprache → Englisch → Deutsch.
    Rückgabe: tatsächlich geladener Code."""
    alle = {c: p for c, _, p in verfuegbar()}
    wahl = next((c for c in ((code or "").lower(), _gemerkt(), systemsprache(), "en", REFERENZ) if c in alle), None)
    ref = {}
    if REFERENZ in alle:
        ref = lesen(alle[REFERENZ])[1]
    kopf, texte = ({}, {}) if wahl is None else lesen(alle[wahl])[:2]
    _aktiv.update(code=wahl or REFERENZ, texte=texte, ref=ref, kopf=kopf)
    return _aktiv["code"]


def code():
    if _aktiv["code"] is None:
        waehlen()
    return _aktiv["code"]


def kopf(feld, standard=""):
    code()
    return _aktiv["kopf"].get(feld, standard)


def _einsetzen(s, kw):
    def ersetzen(m):
        if m.group(1) not in kw:
            return m.group(0)  # z. B. {Tools} bleibt stehen
        return format(kw[m.group(1)], (m.group(2) or ":")[1:])
    return _PLATZHALTER.sub(ersetzen, s)


def t(schluessel, **kw):
    """Text zum Schlüssel in der aktiven Sprache (sonst Deutsch, sonst der Schlüssel selbst)."""
    if _aktiv["code"] is None:
        waehlen()
    for quelle in (_aktiv["texte"], _aktiv["ref"]):
        s = quelle.get(schluessel)
        if s is not None:
            try:
                return _einsetzen(s, kw)
            except (ValueError, TypeError):
                continue  # fehlerhafter Platzhalter in der Übersetzung → Referenz
    return schluessel


def pruefbericht():
    """Alle Sprachdateien gegen de.txt prüfen. Rückgabe: (zeilen, fehlerzahl)."""
    zeilen, fehler = [], 0
    alle = verfuegbar()
    ref_pfad = next((p for c, _, p in alle if c == REFERENZ), None)
    if not ref_pfad:
        return [f"{REFERENZ}.txt fehlt / missing ({', '.join(ORDNER)})"], 1
    _, ref, _ = lesen(ref_pfad)
    for c, name, p in alle:
        kopf_, texte, probleme = lesen(p)
        fehlt = [k for k in ref if k not in texte]
        extra = [k for k in texte if k not in ref]
        platz = [k for k in ref if k in texte and
                 sorted(m.group(1) for m in _PLATZHALTER.finditer(ref[k]))
                 != sorted(m.group(1) for m in _PLATZHALTER.finditer(texte[k]))]
        n = len(fehlt) + len(platz) + len(probleme)
        fehler += n
        zeilen.append(f"{'✓' if not n else '✗'} {name} ({c}) – {p}: {len(texte)}/{len(ref)}, "
                      f"version {kopf_.get('version', '?')}")
        zeilen += [f"    Zeile/line {nr}: {m}" for nr, m in probleme]
        zeilen += [f"    fehlt/missing: {k}" for k in fehlt]
        zeilen += [f"    Platzhalter/placeholders: {k}" for k in platz]
        zeilen += [f"    überzählig/unused: {k}" for k in extra]
    return zeilen, fehler
