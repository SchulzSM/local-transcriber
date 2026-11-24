r"""Zeitraster-Textdatei aus einem vorhandenen Transkript erzeugen (ohne neu zu transkribieren).

Aufruf:  Transkribieren.bat --raster <name>.json <raster s> [<raster s> …]   (bzw. Transkribieren.exe --raster …)
  z. B.  … "Zelle I.json" 0.5 1 5   →  Zelle I_raster_500ms.txt, _raster_1s.txt, _raster_5s.txt
Exakt nur, wenn das Transkript mit --woerter (oder --raster) erstellt wurde; sonst Näherung (Wörter gleichmäßig
über die Segmentdauer verteilt) – für Raster ab ca. 5 s meist ausreichend."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transkribieren import raster_datei
from sprache import t


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) < 2:
        sys.exit(t("raster.aufruf"))
    pfad, *raster = argv
    with open(pfad, encoding="utf-8") as f:
        d = json.load(f)
    segs = d["segmente"]
    if not any("woerter" in s for s in segs):
        print(t("raster.genaehert"))
    for r in raster:
        print(raster_datei(segs, float(r.replace(",", ".")), os.path.splitext(pfad)[0]))


if __name__ == "__main__":
    main()
