"""Programmangaben (Info-Reiter, Protokolldatei, Kommandozeile --version).
Sichtbare Texte (Programmname, Beschreibung, Lizenzhinweise) stehen in den Sprachdateien (sprachen\\*.txt);
NAME ist der feste Programmname für maschinenlesbare Ausgaben (.json)."""
__version__ = "1.0.0"
NAME = "Transkribieren (lokal)"
AUTOR = "Prof. Dr. Stefan M. Schulz"
KONTAKT = "kommunaut@gmail.com"
REPO_NAME = "local-transcriber"
REPO_URL = "https://github.com/SchulzSM/local-transcriber"
ISSUES_URL = REPO_URL + "/issues"
JAHR = "2026"
# (Name bzw. Sprachschlüssel mit „@“, Lizenz bzw. Sprachschlüssel mit „@“, Link)
KOMPONENTEN = [
    ("faster-whisper", "MIT", "https://github.com/SYSTRAN/faster-whisper"),
    ("CTranslate2", "MIT", "https://github.com/OpenNMT/CTranslate2"),
    ("@info.komp_weitere_name", "@info.komp_weitere", ""),
    ("ffmpeg", "@info.komp_ffmpeg", "https://ffmpeg.org"),
    ("@info.komp_modelle_name", "@info.komp_modelle", ""),
]
