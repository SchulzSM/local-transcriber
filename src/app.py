"""Gemeinsamer Einstieg für Oberfläche, Kommandozeile und Exe.

  app.py                     Oberfläche
  app.py --cli <audio …>     Transkription auf der Kommandozeile (Optionen: --help)
  app.py --raster <json> 1 5 Zeitraster aus vorhandenem Transkript
  app.py --version
Sprache der Ausgaben: --ui <code> (sonst die in der Oberfläche gewählte bzw. die Windows-Sprache)."""
import os as _os
_os.environ["PYANNOTE_METRICS_ENABLED"] = "false"  # Telemetrie von pyannote aus: es wird nichts übertragen
import os, sys, warnings

# pyannote (vom mobius-faster-whisper geladen) warnt vor torchcodec; Audio kommt hier über ffmpeg
warnings.filterwarnings("ignore", category=UserWarning, module=r"pyannote(..*)?")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "--cli":
        import transkribieren
        transkribieren.main(sys.argv[2:])
    elif arg == "--raster":
        import sprache, transkribieren, transkript_raster
        transkribieren._konsole_utf8()
        rest = sys.argv[2:]
        sprache.waehlen(transkribieren.ui_vorab(rest))
        if "--ui" in rest:  # --ui <code> gehört nicht zu den Rasterwerten
            i = rest.index("--ui"); del rest[i:i + 2]
        transkript_raster.main([x for x in rest if not x.startswith("--ui=")])
    elif arg in ("--version", "-V"):
        import transkribieren
        transkribieren.main(["--version"])
    else:
        import transkribieren_gui
        transkribieren_gui.main()


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main()
