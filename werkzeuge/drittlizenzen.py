r"""THIRD_PARTY_LICENSES.txt für die Exe erzeugen: Python selbst und alle Pakete der Transkriptions-Umgebung
mit Version, Lizenzangabe und vollem Lizenztext (LICENSE, COPYING, NOTICE …).

Aufruf (mit dem Python der Transkriptions-Umgebung, vom Build-Skript):
    <python> werkzeuge\drittlizenzen.py <ausgabedatei>"""
import importlib.metadata as md
import os, re, sys

AUSLASSEN = {"pip", "setuptools", "wheel"}  # Installationswerkzeuge, nicht in der Exe
LIZENZDATEI = re.compile(r"(^|/)(LICEN[CS]E|COPYING|NOTICE|AUTHORS)[^/]*$", re.I)


def lizenzangabe(meta):
    if meta.get("License-Expression"):
        return meta["License-Expression"]
    kl = [c.split("::")[-1].strip() for c in meta.get_all("Classifier") or [] if c.startswith("License ::")]
    lic = (meta.get("License") or "").strip()
    if lic and len(lic) < 120 and "\n" not in lic:
        kl.insert(0, lic)
    return "; ".join(dict.fromkeys(kl)) or "siehe Lizenztext / see license text"


def texte(dist):
    out, gesehen = [], set()
    for f in dist.files or []:
        s = str(f).replace("\\", "/")
        if LIZENZDATEI.search(s) and s not in gesehen:
            gesehen.add(s)
            try:
                out.append((s, open(dist.locate_file(f), encoding="utf-8", errors="replace").read().strip()))
            except OSError:
                pass
    return out


def main(ziel):
    teile = ["Third-party licenses / Lizenzen der Fremdkomponenten",
             "=" * 60,
             "Transkribieren.exe enthält Python und die folgenden Pakete unter ihren eigenen Lizenzen.",
             "Transkribieren.exe bundles Python and the following packages under their own licenses.",
             "ffmpeg und die Whisper-Modelle sind NICHT enthalten. / ffmpeg and the Whisper models are NOT included.",
             ""]
    py_lic = os.path.join(sys.base_prefix, "LICENSE.txt")
    teile += ["-" * 60, f"Python {sys.version.split()[0]}  –  PSF-2.0", "https://www.python.org", "-" * 60]
    if os.path.isfile(py_lic):
        teile.append(open(py_lic, encoding="utf-8", errors="replace").read().strip())
    teile.append("")
    dists = {}
    for d in md.distributions():
        name = d.metadata.get("Name") or "?"
        if name.lower() not in AUSLASSEN:
            dists.setdefault(name.lower(), d)
    ohne = []
    for _, d in sorted(dists.items()):
        m = d.metadata
        url = m.get("Home-page") or next((u.split(",", 1)[1].strip() for u in m.get_all("Project-URL") or []), "")
        teile += ["-" * 60, f"{m['Name']} {d.version}  –  {lizenzangabe(m)}"] + ([url] if url else []) + ["-" * 60]
        tx = texte(d)
        if not tx:
            ohne.append(m["Name"])
            teile.append("(kein Lizenztext im Paket: Lizenz laut Paketangaben, Volltext beim Projekt oben / "
                         "no license file in the package: license as declared, full text at the project above)")
        for pfad, text in tx:
            teile += [f"[{pfad}]", text, ""]
        teile.append("")
    with open(ziel, "w", encoding="utf-8") as f:
        f.write("\n".join(teile) + "\n")
    print(f"{ziel}: {len(dists)} Pakete + Python" + (f"; ohne Lizenztext: {', '.join(ohne)}" if ohne else ""))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "THIRD_PARTY_LICENSES.txt")
