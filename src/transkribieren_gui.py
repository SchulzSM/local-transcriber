"""Oberfläche für transkribieren.py: Reiter Transkription, Einstellungen (Profile), Info.
Start: Transkribieren.bat (Entwicklung) bzw. Transkribieren.exe.
Alle sichtbaren Texte kommen aus den Sprachdateien (sprachen\\<code>.txt) über t("schlüssel")."""
import os, queue, re, subprocess, sys, threading, webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import einstellungen as E
import sprache as S
from sprache import t
from version import __version__, AUTOR, KONTAKT, JAHR, KOMPONENTEN, REPO_URL, ISSUES_URL

HIER = os.path.dirname(os.path.abspath(__file__))
SPRACHEN = ["de", "en", "fr", "es", "it", "nl", "tr", "auto"]  # Sprache der Aufnahme (nicht der Oberfläche)
COMPUTE = ["int8", "int8_float32", "float32"]
GRUEN, ROT, ORANGE, GRAU, LINK = "#1a7f37", "#c62828", "#b26a00", "#666", "#0b62c4"


def titel():
    return t("app.name")


def typen_audio():
    return [(t("dlg.typ_audio"), "*.flac *.mp3 *.m4a *.wav *.ogg *.opus *.mp4 *.mkv *.mov *.webm *.vob *.iso"),
            (t("dlg.typ_alle"), "*.*")]


def typen_text():
    return [(t("dlg.typ_text"), "*.txt"), (t("dlg.typ_alle"), "*.*")]


def text_oder_schluessel(x):
    """Einträge aus version.KOMPONENTEN: „@schlüssel“ wird übersetzt, sonst unverändert."""
    return t(x[1:]) if x.startswith("@") else x


def oeffnen(pfad):
    try:
        os.startfile(pfad)
    except OSError as e:
        messagebox.showerror(titel(), t("dlg.oeffnen_fehler", pfad=pfad, fehler=e))


class Pfadzeile:
    """Beschriftung + Eingabefeld + „…“-Knopf (Datei- oder Ordnerdialog) + Ampel."""

    def __init__(self, eltern, zeile, text, art="datei", typen=None, aenderung=None, hinweis=""):
        self.var = tk.StringVar()
        self.art, self.typen = art, typen or [(t("dlg.typ_alle"), "*.*")]
        ttk.Label(eltern, text=text).grid(row=zeile, column=0, sticky="w", pady=2)
        self.entry = ttk.Entry(eltern, textvariable=self.var, width=70)
        self.entry.grid(row=zeile, column=1, sticky="we", padx=4)
        self.knopf = ttk.Button(eltern, text="…", width=3, command=self.waehlen)
        self.knopf.grid(row=zeile, column=2)
        self.ampel = ttk.Label(eltern, text="", width=3)
        self.ampel.grid(row=zeile, column=3)
        if hinweis:
            ttk.Label(eltern, text=hinweis, foreground=GRAU).grid(row=zeile + 1, column=1, sticky="w", padx=4)
        if aenderung:
            self.var.trace_add("write", lambda *_: aenderung())

    def waehlen(self):
        start = E.expand(self.var.get())
        ini = start if os.path.isdir(start) else os.path.dirname(start) if start else None
        if self.art == "ordner":
            p = filedialog.askdirectory(initialdir=ini or None)
        else:
            p = filedialog.askopenfilename(initialdir=ini or None, filetypes=self.typen)
        if p:
            self.var.set(E.kompakt(p))

    def ampel_setzen(self, ok):
        self.ampel.config(text={True: "✓", False: "✗", None: "!"}.get(ok, ""),
                          foreground={True: GRUEN, False: ROT, None: ORANGE}.get(ok, "black"))

    def zustand(self, an=True):
        s = "normal" if an else "disabled"
        self.entry.config(state=s); self.knopf.config(state=s)


class App(tk.Tk):
    def __init__(self):
        try:  # scharfe Darstellung bei Bildschirmskalierung (125 %, 150 % …)
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
        super().__init__()
        self.skala = max(1.0, self.winfo_fpixels("1i") / 96)
        ttk.Style(self).configure("Treeview", rowheight=int(22 * self.skala))
        self.title(f"{titel()} {__version__}")
        self.q = queue.Queue(); self.proc = None; self.neustart = False
        self.dateien, self.zielpfad, self.letztes_ergebnis = [], None, None
        self.zustand = E.lade_zustand()
        self.fenster_setzen(self.zustand.get("fenster"))
        if self.zustand.get("maximiert"):
            self.state("zoomed")
        self.profil, neu = E.aktives_profil()
        self.geaendert = False

        kopf = ttk.Frame(self, padding=(10, 8, 10, 0)); kopf.pack(fill="x")
        ttk.Label(kopf, text=t("kopf.profil")).pack(side="left")
        self.profilwahl = ttk.Combobox(kopf, state="readonly", width=28)
        self.profilwahl.pack(side="left", padx=4)
        self.profilwahl.bind("<<ComboboxSelected>>", lambda e: self.profil_wechseln(self.profilwahl.get()))
        self.einrichtung = ttk.Label(kopf, text="")
        self.einrichtung.pack(side="left", padx=10)
        self.sprachen = S.verfuegbar()
        self.oberflaeche = ttk.Combobox(kopf, state="readonly", width=12, values=[n for _, n, _ in self.sprachen])
        self.oberflaeche.pack(side="right")
        self.oberflaeche.set(next((n for c, n, _ in self.sprachen if c == S.code()), S.code()))
        self.oberflaeche.bind("<<ComboboxSelected>>", lambda e: self.oberflaeche_wechseln(self.oberflaeche.get()))
        ttk.Label(kopf, text=t("kopf.oberflaeche")).pack(side="right", padx=4)

        nb = ttk.Notebook(self); nb.pack(fill="both", expand=True, padx=10, pady=8)
        self.nb = nb
        self.tab_lauf = ttk.Frame(nb, padding=10); nb.add(self.tab_lauf, text=t("reiter.transkription"))
        self.tab_einst = ttk.Frame(nb, padding=10); nb.add(self.tab_einst, text=t("reiter.einstellungen"))
        self.tab_info = ttk.Frame(nb, padding=10); nb.add(self.tab_info, text=t("reiter.info"))
        self.bau_lauf(); self.bau_einstellungen(); self.bau_info()

        self.profil_anzeigen()
        self.letzte_werte_setzen()
        if neu:
            self.log(t("log.profil_neu_start", name=self.profil["name"], ordner=E.profil_dir()) + "\n")
        if not self.sprachen:
            self.log(t("log.keine_sprachdateien", ordner=S.ORDNER[0]) + "\n")
        self.protocol("WM_DELETE_WINDOW", self.schliessen)
        self._poll_id = self.after(200, self.poll)
        self.after(300, self.pruefen_im_hintergrund)

    # ================================================================ Reiter Transkription
    def bau_lauf(self):
        f = self.tab_lauf
        f.columnconfigure(1, weight=1)
        z = 0
        kn = ttk.Frame(f); kn.grid(row=z, column=0, columnspan=4, sticky="w")
        ttk.Button(kn, text=t("lauf.dateien"), command=self.waehlen).pack(side="left")
        ttk.Button(kn, text=t("lauf.dvd"), command=self.dvdordner).pack(side="left", padx=4)
        ttk.Button(kn, text=t("lauf.leeren"), command=lambda: self.dateien_setzen([])).pack(side="left")
        z += 1
        self.liste = tk.Listbox(f, height=4)
        self.liste.grid(row=z, column=0, columnspan=4, sticky="we", pady=4)
        z += 1
        ttk.Label(f, text=t("lauf.modell")).grid(row=z, column=0, sticky="w", pady=3)
        zm = ttk.Frame(f); zm.grid(row=z, column=1, columnspan=3, sticky="w")
        self.modell = ttk.Combobox(zm, state="readonly", width=40)
        self.modell.pack(side="left")
        self.modell.bind("<<ComboboxSelected>>", lambda e: self.tokens_anzeigen())
        ttk.Label(zm, text="   " + t("lauf.sprache")).pack(side="left")
        self.sprache = ttk.Combobox(zm, values=SPRACHEN, width=6); self.sprache.pack(side="left", padx=4)
        z += 1
        ttk.Label(f, text=t("lauf.begriffsdatei")).grid(row=z, column=0, sticky="w", pady=3)
        self.begriffsdatei = tk.StringVar()
        ttk.Entry(f, textvariable=self.begriffsdatei).grid(row=z, column=1, sticky="we", padx=4)
        bf = ttk.Frame(f); bf.grid(row=z, column=2, columnspan=2, sticky="w")
        ttk.Button(bf, text="…", width=3, command=self.begriffsdatei_waehlen).pack(side="left")
        ttk.Button(bf, text=t("lauf.oeffnen"), command=self.begriffsdatei_oeffnen).pack(side="left", padx=2)
        ttk.Button(bf, text="×", width=2, command=lambda: self.begriffsdatei.set("")).pack(side="left")
        z += 1
        ttk.Label(f, text=t("lauf.begriffe")).grid(row=z, column=0, sticky="w", pady=3)
        self.begriffe = tk.StringVar()
        ttk.Entry(f, textvariable=self.begriffe).grid(row=z, column=1, columnspan=3, sticky="we", padx=4)
        z += 1
        self.tokeninfo = ttk.Label(f, text="", foreground=GRAU)
        self.tokeninfo.grid(row=z, column=1, columnspan=3, sticky="w", padx=4)
        for v in (self.begriffsdatei, self.begriffe):
            v.trace_add("write", lambda *_: self.after_idle(self.tokens_anzeigen))
        z += 1
        ttk.Label(f, text=t("lauf.kontext")).grid(row=z, column=0, sticky="w", pady=3)
        self.kontext = tk.StringVar()
        ttk.Entry(f, textvariable=self.kontext).grid(row=z, column=1, columnspan=3, sticky="we", padx=4)
        z += 1
        ttk.Label(f, text=t("lauf.zielordner")).grid(row=z, column=0, sticky="w", pady=3)
        self.ziel = tk.StringVar()
        ttk.Label(f, textvariable=self.ziel).grid(row=z, column=1, sticky="w", padx=4)
        zf = ttk.Frame(f); zf.grid(row=z, column=2, columnspan=2, sticky="w")
        ttk.Button(zf, text=t("lauf.aendern"), command=self.zielwahl).pack(side="left")
        ttk.Button(zf, text=t("lauf.standard"), command=lambda: self.ziel_setzen(None)).pack(side="left", padx=2)
        z += 1
        op = ttk.Frame(f); op.grid(row=z, column=0, columnspan=4, sticky="w", pady=4)
        self.test = tk.BooleanVar(); self.woerter = tk.BooleanVar()
        ttk.Checkbutton(op, text=t("lauf.probe"), variable=self.test).pack(side="left")
        ttk.Checkbutton(op, text=t("lauf.woerter"), variable=self.woerter).pack(side="left", padx=10)
        ttk.Label(op, text=t("lauf.raster")).pack(side="left")
        self.raster = ttk.Entry(op, width=12); self.raster.pack(side="left", padx=4)
        ttk.Label(op, text="   " + t("lauf.tonspur")).pack(side="left")
        self.spur = ttk.Entry(op, width=4); self.spur.pack(side="left", padx=4)
        ttk.Button(op, text=t("lauf.tonspuren"), command=lambda: self.los(nur_spuren=True)).pack(side="left")
        z += 1
        st = ttk.Frame(f); st.grid(row=z, column=0, columnspan=4, sticky="w", pady=4)
        self.startknopf = ttk.Button(st, text=t("lauf.start"), command=self.los); self.startknopf.pack(side="left")
        ttk.Button(st, text=t("lauf.abbrechen"), command=self.stop).pack(side="left", padx=4)
        ttk.Button(st, text=t("lauf.befehl"), command=self.befehl_kopieren).pack(side="left", padx=4)
        self.k_ordner = ttk.Button(st, text=t("lauf.ergebnisordner"), state="disabled",
                                   command=lambda: oeffnen(os.path.dirname(self.letztes_ergebnis)))
        self.k_ordner.pack(side="left", padx=4)
        self.k_txt = ttk.Button(st, text=t("lauf.text_oeffnen"), state="disabled",
                                command=lambda: oeffnen(self.letztes_ergebnis + ".txt"))
        self.k_txt.pack(side="left")
        self.k_prot = ttk.Button(st, text=t("lauf.protokoll_oeffnen"), state="disabled",
                                 command=lambda: oeffnen(self.letztes_ergebnis + "_protokoll.txt"))
        self.k_prot.pack(side="left", padx=4)
        z += 1
        lf = ttk.Frame(f); lf.grid(row=z, column=0, columnspan=4, sticky="nsew")
        f.rowconfigure(z, weight=1)
        self.logtext = tk.Text(lf, height=14, wrap="word")
        sb = ttk.Scrollbar(lf, command=self.logtext.yview); self.logtext.config(yscrollcommand=sb.set)
        self.logtext.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")

    def log(self, text):
        self.logtext.insert("end", text); self.logtext.see("end")

    def dateien_setzen(self, liste):
        self.dateien = liste
        self.liste.delete(0, "end")
        for x in liste:
            self.liste.insert("end", x)

    def waehlen(self):
        neu = list(filedialog.askopenfilenames(title=t("dlg.dateien_titel"), filetypes=typen_audio(),
                                               initialdir=self.zustand.get("letzter_ordner") or None))
        if neu:
            self.zustand["letzter_ordner"] = os.path.dirname(neu[0])
            self.dateien_setzen(self.dateien + [os.path.normpath(x) for x in neu if os.path.normpath(x) not in self.dateien])

    def dvdordner(self):
        d = filedialog.askdirectory(title=t("dlg.dvd_titel"))
        if d:
            self.dateien_setzen(self.dateien + [os.path.normpath(d)])

    def ziel_setzen(self, d):
        self.zielpfad = d or None
        std = E.expand(self.profil.get("zielordner"))
        self.ziel.set(d or (t("lauf.ziel_profil", pfad=std) if std else t("lauf.ziel_neben")))

    def zielwahl(self):
        d = filedialog.askdirectory(initialdir=self.zielpfad or None)
        if d:
            self.ziel_setzen(os.path.normpath(d))

    def begriffsdatei_waehlen(self):
        start = E.expand(self.begriffsdatei.get()) or os.path.join(E.TOOLS, "begriffe")
        p = filedialog.askopenfilename(initialdir=os.path.dirname(start) if os.path.isfile(start) else start,
                                       filetypes=typen_text())
        if p:
            self.begriffsdatei.set(E.kompakt(p))

    def begriffsdatei_oeffnen(self):
        p = E.expand(self.begriffsdatei.get())
        if p and os.path.isfile(p):
            oeffnen(p)
        elif messagebox.askyesno(titel(), t("dlg.begriffsdatei_neu")):
            p = filedialog.asksaveasfilename(initialdir=os.path.join(E.TOOLS, "begriffe"), defaultextension=".txt",
                                             filetypes=typen_text()[:1])
            if p:
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write("# " + t("dlg.begriffsdatei_kopf") + "\n")
                self.begriffsdatei.set(E.kompakt(p)); oeffnen(p)

    def modellordner(self):
        try:
            return E.modell_eintrag(self.profil, self.modell_kurz())[1]
        except KeyError:
            return ""

    def modell_kurz(self):
        name = self.modell.get()
        for m in self.profil.get("modelle", []):
            if m.get("name") == name:
                return m.get("kurz") or m.get("name")
        return name

    def begriffsliste(self):
        try:
            datei = E.begriffe_lesen(self.begriffsdatei.get())
        except OSError:
            datei = None
        return datei, E.begriffe_zusammen(datei or [], E.begriffe_teilen(self.begriffe.get()))

    def tokens_anzeigen(self):
        datei, alle = self.begriffsliste()
        if datei is None:
            self.tokeninfo.config(text=t("lauf.begriffsdatei_fehlt"), foreground=ROT); return
        if not alle:
            self.tokeninfo.config(text=t("lauf.keine_begriffe"), foreground=GRAU); return
        n, exakt = E.token_zahl(E.hotwords_text(alle), self.modellordner())
        zu_lang = n > E.TOKEN_GRENZE
        self.tokeninfo.config(
            text=t("lauf.tokens" if exakt else "lauf.tokens_ca", n=len(alle), tokens=n, grenze=E.TOKEN_GRENZE)
                 + (" – " + t("lauf.zu_lang") if zu_lang else ""),
            foreground=ROT if zu_lang else GRUEN)

    def befehl(self, nur_spuren=False):
        if E.frozen():
            cmd = [sys.executable, "--cli"]
        else:
            py = E.expand(self.profil.get("python")) or sys.executable.replace("pythonw.exe", "python.exe")
            cmd = [py, "-u", os.path.join(HIER, "transkribieren.py")]
        cmd += [*self.dateien, "--profil", self.profil["name"], "--modell", self.modell_kurz(),
                "--sprache", self.sprache.get() or "de", "--ui", S.code()]
        if self.begriffsdatei.get().strip():
            cmd += ["--begriffe-datei", self.begriffsdatei.get().strip()]
        else:
            cmd += ["--begriffe-datei", ""]
        if self.begriffe.get().strip():
            cmd += ["--begriffe", self.begriffe.get().strip()]
        cmd += ["--kontext", self.kontext.get().strip()]
        if self.zielpfad:
            cmd += ["--ausgabe", self.zielpfad]
        if self.test.get():
            cmd += ["--test", "120"]
        if self.woerter.get():
            cmd += ["--woerter"]
        r = self.raster.get().replace(",", ".").replace(";", " ").split()
        if r:
            cmd += ["--raster", *r]
        if self.spur.get().strip():
            cmd += ["--spur", self.spur.get().strip()]
        if nur_spuren:
            cmd += ["--spuren"]
        return cmd

    def befehl_kopieren(self):
        platzhalter = "<" + t("lauf.platzhalter_datei") + ">"
        if not self.dateien:
            self.dateien_setzen([platzhalter])
        text = subprocess.list2cmdline(self.befehl())
        if self.dateien == [platzhalter]:
            self.dateien_setzen([])
        self.clipboard_clear(); self.clipboard_append(text)
        self.log(t("log.befehl_kopiert") + "\n" + text + "\n")

    def los(self, nur_spuren=False):
        if self.proc:
            return
        if not self.dateien:
            messagebox.showinfo(titel(), t("dlg.erst_dateien")); return
        if self.geaendert and not messagebox.askyesno(titel(), t("dlg.ungespeichert_start")):
            return
        self.letzte_werte_merken()
        cmd = self.befehl(nur_spuren)
        self.log("\n" + t("log.start") + " " + subprocess.list2cmdline(cmd) + "\n")
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
        try:
            self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                         encoding="utf-8", errors="replace", env=env,
                                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except OSError as e:
            self.log(t("log.start_fehler", fehler=e) + "\n"); return
        self.startknopf.config(state="disabled")
        threading.Thread(target=self.lesen, daemon=True).start()

    def lesen(self):
        p = self.proc
        for line in p.stdout:
            self.q.put(line)
        p.wait(); self.q.put(("ENDE", p.returncode))

    def stop(self):
        if self.proc:
            self.proc.terminate(); self.log("\n" + t("log.abbruch") + "\n")

    def poll(self):
        while not self.q.empty():
            x = self.q.get()
            if isinstance(x, tuple) and x[0] == "PRUEFUNG":
                self.pruefung_fertig(x[1], x[2])
            elif isinstance(x, tuple):
                self.log("\n== " + t("log.beendet", code=x[1]) + "\n"); self.proc = None
                self.startknopf.config(state="normal")
            elif x.startswith("ERGEBNIS\t"):
                self.letztes_ergebnis = x.split("\t", 1)[1].strip()
                for k in (self.k_ordner, self.k_txt, self.k_prot):
                    k.config(state="normal")
            else:
                self.log(x)
        self._poll_id = self.after(200, self.poll)

    # ================================================================ Reiter Einstellungen
    def bau_einstellungen(self):
        f = self.tab_einst
        f.columnconfigure(0, weight=1)
        pr = ttk.LabelFrame(f, text=t("einst.profil"), padding=8); pr.grid(row=0, column=0, sticky="we")
        self.profilname = ttk.Label(pr, text="", font=("Segoe UI", 10, "bold")); self.profilname.pack(side="left")
        for k, c in (("einst.neu", self.profil_neu), ("einst.speichern", self.profil_speichern),
                     ("einst.speichern_unter", self.profil_speichern_unter), ("einst.loeschen", self.profil_loeschen),
                     ("einst.importieren", self.profil_import),
                     ("einst.profilordner", lambda: oeffnen(E.profil_dir()))):
            ttk.Button(pr, text=t(k), command=c).pack(side="left", padx=3)
        self.beschreibung = tk.StringVar()
        bz = ttk.Frame(f); bz.grid(row=1, column=0, sticky="we", pady=(4, 0))
        ttk.Label(bz, text=t("einst.beschreibung")).pack(side="left")
        ttk.Entry(bz, textvariable=self.beschreibung, width=80).pack(side="left", padx=6, fill="x", expand=True)
        self.beschreibung.trace_add("write", lambda *_: self.markiere())

        pg = ttk.LabelFrame(f, text=t("einst.programme"), padding=8); pg.grid(row=2, column=0, sticky="we", pady=6)
        pg.columnconfigure(1, weight=1)
        self.p_python = Pfadzeile(pg, 0, t("einst.python"), typen=[("python.exe", "python.exe")],
                                  aenderung=self.markiere,
                                  hinweis=t("einst.python_exe") if E.frozen() else t("einst.python_hinweis"))
        self.p_ffmpeg = Pfadzeile(pg, 2, "ffmpeg", typen=[("ffmpeg.exe", "ffmpeg.exe"), (t("dlg.typ_alle"), "*.*")],
                                  aenderung=self.markiere)
        if E.frozen():
            self.p_python.zustand(False)

        mo = ttk.LabelFrame(f, text=t("einst.modelle"), padding=8); mo.grid(row=3, column=0, sticky="nsew")
        f.rowconfigure(3, weight=1)
        self.baum = ttk.Treeview(mo, columns=("std", "kurz", "name", "ordner", "ok"), show="headings", height=5)
        for c, k, w in (("std", "einst.spalte_std", 40), ("kurz", "einst.spalte_kurz", 105),
                        ("name", "einst.spalte_name", 220), ("ordner", "einst.spalte_ordner", 360), ("ok", "", 30)):
            self.baum.heading(c, text=t(k) if k else ""); self.baum.column(c, width=int(w * self.skala), stretch=(c == "ordner"))
        self.baum.pack(side="left", fill="both", expand=True)
        mk = ttk.Frame(mo); mk.pack(side="left", fill="y", padx=6)
        for k, c in (("einst.modell_neu", self.modell_neu), ("einst.modell_bearbeiten", self.modell_bearbeiten),
                     ("einst.modell_entfernen", self.modell_entfernen), ("einst.modell_standard", self.modell_standard)):
            ttk.Button(mk, text=t(k), command=c).pack(fill="x", pady=2)

        sw = ttk.LabelFrame(f, text=t("einst.standardwerte"), padding=8); sw.grid(row=4, column=0, sticky="we", pady=6)
        sw.columnconfigure(1, weight=1)
        zl = ttk.Frame(sw); zl.grid(row=0, column=0, columnspan=4, sticky="w", pady=2)
        ttk.Label(zl, text=t("einst.sprache")).pack(side="left")
        self.s_sprache = ttk.Combobox(zl, values=SPRACHEN, width=6); self.s_sprache.pack(side="left", padx=(4, 16))
        ttk.Label(zl, text=t("einst.threads")).pack(side="left")
        self.s_threads = ttk.Spinbox(zl, from_=0, to=64, width=4); self.s_threads.pack(side="left", padx=(4, 16))
        ttk.Label(zl, text=t("einst.compute")).pack(side="left")
        self.s_compute = ttk.Combobox(zl, values=COMPUTE, width=13, state="readonly"); self.s_compute.pack(side="left", padx=(4, 16))
        ttk.Label(zl, text=t("einst.absatz")).pack(side="left")
        self.s_absatz = ttk.Spinbox(zl, from_=0.5, to=10, increment=0.1, width=5, format="%.1f")
        self.s_absatz.pack(side="left", padx=4)
        for w in (self.s_sprache, self.s_compute):
            w.bind("<<ComboboxSelected>>", lambda e: self.markiere())
        for w in (self.s_sprache, self.s_threads, self.s_absatz):
            w.bind("<KeyRelease>", lambda e: self.markiere())
        self.s_threads.config(command=self.markiere)
        self.s_absatz.config(command=self.markiere)
        self.p_ziel = Pfadzeile(sw, 1, t("einst.zielordner"), art="ordner", aenderung=self.markiere)
        self.p_begriffe = Pfadzeile(sw, 2, t("einst.begriffsdatei"), typen=typen_text()[:1], aenderung=self.markiere)
        ttk.Label(sw, text=t("einst.kontext")).grid(row=3, column=0, sticky="w", pady=2)
        self.s_kontext = tk.StringVar(); self.s_kontext.trace_add("write", lambda *_: self.markiere())
        ttk.Entry(sw, textvariable=self.s_kontext).grid(row=3, column=1, sticky="we", padx=4)
        ttk.Label(sw, text=t("einst.platzhalter"), foreground=GRAU).grid(row=4, column=1, sticky="w", padx=4)

        pk = ttk.Frame(f); pk.grid(row=5, column=0, sticky="we")
        ttk.Button(pk, text=t("einst.pruefen"), command=self.pruefen_anzeigen).pack(side="left")
        self.pruef_text = tk.Text(f, height=7, wrap="word", font=("Segoe UI", 9))
        self.pruef_text.grid(row=6, column=0, sticky="we", pady=4)
        for tag, farbe in (("ok", GRUEN), ("fehler", ROT), ("hinweis", ORANGE)):
            self.pruef_text.tag_config(tag, foreground=farbe)

    def markiere(self, *_):
        if getattr(self, "_laden", False):
            return
        self.geaendert = True
        self.profilname.config(text=f"{self.profil['name']} *")

    def profil_anzeigen(self):
        self._laden = True
        p = self.profil
        self.profilwahl.config(values=E.profile_liste()); self.profilwahl.set(p["name"])
        self.profilname.config(text=p["name"])
        self.beschreibung.set(p.get("beschreibung", ""))
        self.p_python.var.set(p.get("python", "")); self.p_ffmpeg.var.set(p.get("ffmpeg", ""))
        self.s_sprache.set(p.get("sprache", "de")); self.s_compute.set(p.get("compute", "int8"))
        self.s_threads.set(str(p.get("threads", 0)))
        self.s_absatz.set(f"{float(p.get('absatz', 2.0)):.1f}")
        self.p_ziel.var.set(p.get("zielordner", "")); self.p_begriffe.var.set(p.get("begriffsdatei", ""))
        self.s_kontext.set(p.get("kontext", ""))
        self.modelle = [dict(m) for m in p.get("modelle", [])]
        self.std_modell = p.get("standardmodell", "")
        self.baum_fuellen()
        self.modell.config(values=[m.get("name") or m.get("kurz") for m in self.modelle])
        std = None
        for m in self.modelle:
            if self.std_modell in (m.get("kurz"), m.get("name")):
                std = m.get("name") or m.get("kurz")
        self.modell.set(std or (self.modelle[0].get("name") if self.modelle else ""))
        self.sprache.set(p.get("sprache", "de"))
        self.begriffsdatei.set(p.get("begriffsdatei", "")); self.kontext.set(p.get("kontext", ""))
        self.ziel_setzen(None)
        self.geaendert = False
        self._laden = False
        self.tokens_anzeigen()
        self.info_orte_aktualisieren()

    def baum_fuellen(self, status=None):
        self.baum.delete(*self.baum.get_children())
        for i, m in enumerate(self.modelle):
            std = "★" if self.std_modell in (m.get("kurz"), m.get("name")) else ""
            ok = "✓" if os.path.isfile(os.path.join(E.expand(m.get("ordner")), "model.bin")) else "✗"
            self.baum.insert("", "end", iid=str(i), values=(std, m.get("kurz", ""), m.get("name", ""), m.get("ordner", ""), ok))

    def aus_formular(self):
        p = dict(self.profil)
        try:
            threads = int(self.s_threads.get() or 0)
        except ValueError:
            threads = 0
        try:
            absatz = max(0.5, float(self.s_absatz.get().replace(",", ".")))
        except ValueError:
            absatz = 2.0
        p["absatz"] = absatz
        p.update(beschreibung=self.beschreibung.get(), python=self.p_python.var.get().strip(),
                 ffmpeg=self.p_ffmpeg.var.get().strip(), modelle=self.modelle, standardmodell=self.std_modell,
                 sprache=self.s_sprache.get() or "de", threads=threads, compute=self.s_compute.get() or "int8",
                 zielordner=self.p_ziel.var.get().strip(), begriffsdatei=self.p_begriffe.var.get().strip(),
                 kontext=self.s_kontext.get().strip())
        return p

    def ungesichert_fragen(self):
        if not self.geaendert:
            return True
        a = messagebox.askyesnocancel(titel(), t("dlg.aenderungen_speichern", name=self.profil["name"]))
        if a is None:
            return False
        if a:
            self.profil_speichern()
        return True

    def profil_wechseln(self, name):
        if name == self.profil["name"]:
            return
        if not self.ungesichert_fragen():
            self.profilwahl.set(self.profil["name"]); return
        self.profil = E.lade_profil(name)
        self.zustand["profil"] = name
        self.profil_anzeigen(); self.pruefen_im_hintergrund()
        self.log(t("log.profil_geladen", name=name) + "\n")

    def profil_speichern(self):
        self.profil = self.aus_formular()
        pfad = E.speichere_profil(self.profil)
        self.zustand["profil"] = self.profil["name"]
        self.profil_anzeigen(); self.pruefen_im_hintergrund()
        self.log(t("log.profil_gespeichert", pfad=pfad) + "\n")

    def profil_speichern_unter(self):
        name = simpledialog.askstring(titel(), t("dlg.profilname"), parent=self, initialvalue=E.rechnername())
        if not name:
            return
        if name in E.profile_liste() and not messagebox.askyesno(titel(), t("dlg.profil_ueberschreiben", name=name)):
            return
        self.profil = self.aus_formular(); self.profil["name"] = name
        self.profil_speichern()

    def profil_neu(self):
        if not self.ungesichert_fragen():
            return
        name = simpledialog.askstring(titel(), t("dlg.profilname_neu"), parent=self, initialvalue=E.rechnername())
        if not name:
            return
        if name in E.profile_liste():
            messagebox.showerror(titel(), t("dlg.profil_gibt_es", name=name)); return
        self.profil = E.standard_profil(name)
        E.speichere_profil(self.profil); self.zustand["profil"] = name
        self.profil_anzeigen(); self.pruefen_im_hintergrund()
        self.log(t("log.profil_neu", name=name) + "\n")

    def profil_loeschen(self):
        name = self.profil["name"]
        if len(E.profile_liste()) <= 1:
            messagebox.showinfo(titel(), t("dlg.letztes_profil")); return
        if not messagebox.askyesno(titel(), t("dlg.profil_loeschen", name=name)):
            return
        E.loesche_profil(name)
        self.profil = E.lade_profil(E.profile_liste()[0]); self.zustand["profil"] = self.profil["name"]
        self.geaendert = False
        self.profil_anzeigen(); self.pruefen_im_hintergrund()
        self.log(t("log.profil_geloescht", name=name) + "\n")

    def profil_import(self):
        if not self.ungesichert_fragen():
            return
        p = filedialog.askopenfilename(filetypes=[(t("dlg.typ_profil"), "*.json")])
        if not p:
            return
        try:
            d = E.lade_profil(p)
        except (OSError, ValueError) as e:
            messagebox.showerror(titel(), t("dlg.profil_unlesbar", fehler=e)); return
        name = simpledialog.askstring(titel(), t("dlg.import_name"), parent=self, initialvalue=d["name"])
        if not name:
            return
        d["name"] = name
        E.speichere_profil(d); self.profil = d; self.zustand["profil"] = name
        self.profil_anzeigen(); self.pruefen_im_hintergrund()
        self.log(t("log.profil_importiert", name=name, pfad=p) + "\n")

    # --- Modelle
    def _modell_dialog(self, m=None):
        m = dict(m or {})
        o = filedialog.askdirectory(title=t("dlg.modellordner"), initialdir=E.expand(m.get("ordner")) or None)
        if not o and not m:
            return None
        if o:
            m["ordner"] = E.kompakt(o)
            if not os.path.isfile(os.path.join(o, "model.bin")):
                messagebox.showwarning(titel(), t("dlg.keine_modelbin"))
        kurz = simpledialog.askstring(titel(), t("dlg.kurzname"), parent=self,
                                      initialvalue=m.get("kurz") or os.path.basename(E.expand(m["ordner"]))[:8])
        if kurz is None:
            return None
        name = simpledialog.askstring(titel(), t("dlg.anzeigename"), parent=self,
                                      initialvalue=m.get("name") or os.path.basename(E.expand(m["ordner"])))
        if name is None:
            return None
        m.update(kurz=kurz.strip(), name=name.strip())
        return m

    def _auswahl(self):
        s = self.baum.selection()
        return int(s[0]) if s else None

    def modell_neu(self):
        m = self._modell_dialog()
        if m:
            self.modelle.append(m)
            if not self.std_modell:
                self.std_modell = m["kurz"] or m["name"]
            self.baum_fuellen(); self.markiere()

    def modell_bearbeiten(self):
        i = self._auswahl()
        if i is None:
            return
        m = self._modell_dialog(self.modelle[i])
        if m:
            war_std = self.std_modell in (self.modelle[i].get("kurz"), self.modelle[i].get("name"))
            self.modelle[i] = m
            if war_std:
                self.std_modell = m["kurz"] or m["name"]
            self.baum_fuellen(); self.markiere()

    def modell_entfernen(self):
        i = self._auswahl()
        if i is not None and messagebox.askyesno(titel(), t("dlg.modell_entfernen", name=self.modelle[i].get("name"))):
            del self.modelle[i]; self.baum_fuellen(); self.markiere()

    def modell_standard(self):
        i = self._auswahl()
        if i is not None:
            self.std_modell = self.modelle[i].get("kurz") or self.modelle[i].get("name")
            self.baum_fuellen(); self.markiere()

    # --- Prüfung
    def pruefen_im_hintergrund(self, anzeigen=False):
        profil = self.aus_formular() if anzeigen else self.profil
        self.einrichtung.config(text=t("kopf.wird_geprueft"), foreground=GRAU)

        def arbeit():
            try:
                erg = E.pruefen(profil)
            except Exception as e:
                erg = [("pruefung", t("kopf.pruefung"), False, str(e))]
            self.q.put(("PRUEFUNG", erg, anzeigen))  # Rückgabe über die Warteschlange (thread-sicher)
        threading.Thread(target=arbeit, daemon=True).start()

    def pruefung_fertig(self, erg, anzeigen):
        fehler = [b for _, b, ok, _ in erg if ok is False]
        self.einrichtung.config(text=(t("kopf.einrichtung_ok") if not fehler
                                      else t("kopf.einrichtung_fehler", bereiche=", ".join(fehler))),
                                foreground=GRUEN if not fehler else ROT)
        status = {i: ok for i, _, ok, _ in erg}
        self.p_python.ampel_setzen(status.get("python", status.get("programm")))
        self.p_ffmpeg.ampel_setzen(status.get("ffmpeg"))
        if self.p_ziel.var.get():
            self.p_ziel.ampel_setzen(status.get("zielordner"))
        if self.p_begriffe.var.get():
            self.p_begriffe.ampel_setzen(status.get("begriffsdatei"))
        if anzeigen or fehler:
            self.pruef_text.delete("1.0", "end")
            for _, b, ok, text in erg:
                tag = {True: "ok", False: "fehler", None: "hinweis"}[ok]
                self.pruef_text.insert("end", f"{'✓' if ok else ('!' if ok is None else '✗')} {b}: {text}\n", tag)

    def pruefen_anzeigen(self):
        self.pruefen_im_hintergrund(anzeigen=True)

    # ================================================================ Reiter Info
    def bau_info(self):
        f = self.tab_info
        ttk.Label(f, text=titel(), font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Label(f, text=t("info.version", version=__version__) + (" (Exe)" if E.frozen() else "")).pack(anchor="w")
        ttk.Label(f, text=t("info.beschreibung")).pack(anchor="w", pady=(2, 10))
        ttk.Label(f, text=f"© {JAHR} {AUTOR}").pack(anchor="w")
        kz = ttk.Frame(f); kz.pack(anchor="w", pady=2)
        ttk.Label(kz, text=t("info.kontakt") + " ").pack(side="left")
        link = ttk.Label(kz, text=KONTAKT, foreground=LINK, cursor="hand2"); link.pack(side="left")
        link.bind("<Button-1>", lambda e: webbrowser.open(f"mailto:{KONTAKT}?subject={titel()} {__version__}"))
        ttk.Label(f, text=t("info.lizenz")).pack(anchor="w", pady=(2, 2))
        qz = ttk.Frame(f); qz.pack(anchor="w", pady=(0, 2))
        ttk.Label(qz, text=t("info.quellcode") + " ").pack(side="left")
        rl = ttk.Label(qz, text=REPO_URL, foreground=LINK, cursor="hand2"); rl.pack(side="left")
        rl.bind("<Button-1>", lambda e: webbrowser.open(REPO_URL))
        iz = ttk.Frame(f); iz.pack(anchor="w", pady=(0, 10))
        ttk.Label(iz, text=t("info.issues") + " ").pack(side="left")
        il = ttk.Label(iz, text=ISSUES_URL, foreground=LINK, cursor="hand2"); il.pack(side="left")
        il.bind("<Button-1>", lambda e: webbrowser.open(ISSUES_URL))
        ttk.Label(f, text=t("info.datenschutz"), wraplength=int(820 * self.skala)).pack(anchor="w", pady=(0, 10))
        ttk.Label(f, text=t("info.komponenten"), font=("Segoe UI", 10, "bold")).pack(anchor="w")
        for n, l, u in KOMPONENTEN:
            ttk.Label(f, text=f"• {text_oder_schluessel(n)} – {text_oder_schluessel(l)}" + (f" – {u}" if u else "")
                      ).pack(anchor="w")
        ttk.Label(f, text=t("info.orte"), font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 0))
        self.info_orte = ttk.Label(f, text="", wraplength=int(900 * self.skala), justify="left")
        self.info_orte.pack(anchor="w")
        kn = ttk.Frame(f); kn.pack(anchor="w", pady=10)
        ttk.Button(kn, text=t("info.anleitung"), command=lambda: oeffnen(self.anleitung())).pack(side="left")
        ttk.Button(kn, text=t("info.lizenz_oeffnen"), command=lambda: oeffnen(os.path.join(E.TOOLS, "LICENSE"))).pack(side="left", padx=4)
        ttk.Button(kn, text=t("info.programmordner"), command=lambda: oeffnen(E.TOOLS)).pack(side="left")
        ttk.Button(kn, text=t("info.sprachordner"), command=self.sprachordner_oeffnen).pack(side="left", padx=4)

    @staticmethod
    def anleitung():
        """Anleitung in der Sprache der Oberfläche (Kopfzeile „manual“ der Sprachdatei).
        Exe: Datei neben der Exe (Anleitung.md, Manual_en.md …). Python-Fassung: Deutsch → docs\\Anleitung_Python.md,
        andere Sprachen → docs\\<manual> (Bedienung ist in beiden Fassungen gleich)."""
        man = S.kopf("manual", "Anleitung.md")
        if E.frozen():
            p = os.path.join(E.TOOLS, man)
            return p if os.path.isfile(p) else os.path.join(E.TOOLS, "Anleitung.md")
        p = os.path.join(E.TOOLS, "docs", man)
        if S.code() != S.REFERENZ and os.path.isfile(p):
            return p
        return os.path.join(E.TOOLS, "docs", "Anleitung_Python.md")

    def info_orte_aktualisieren(self):
        """Orte im Info-Reiter – wird bei jedem Laden/Speichern/Wechsel eines Profils neu gesetzt."""
        if not hasattr(self, "info_orte"):
            return
        p = self.profil
        if E.frozen():
            lauf = t("info.ort_exe", pfad=sys.executable)
        else:
            lauf = E.expand(p.get("python")) or sys.executable
        sp = next((x for x in self.sprachen if x[0] == S.code()), None)
        zeilen = [
            t("info.ort_profil", name=p["name"], pfad=E._dateiname(p["name"])),
            t("info.ort_lauf", pfad=lauf),
            f"ffmpeg: {E.expand(p.get('ffmpeg')) or '–'}",
            t("info.ort_profilordner", pfad=E.profil_dir()),
            t("info.ort_zustand", pfad=E.zustand_pfad()),
            t("info.ort_programm", pfad=E.TOOLS),
            t("info.ort_sprache", pfad=(sp[2] + (" " + t("info.eingebaut") if sp[2].startswith(S.EINGEBAUT) else ""))
              if sp else "–"),
            t("info.ort_anleitung", pfad=self.anleitung()),
        ]
        self.info_orte.config(text="\n".join(zeilen))

    def sprachordner_oeffnen(self):
        """Zusätzlicher Sprachordner ist optional: öffnen, wenn vorhanden, sonst nur Hinweis (nicht anlegen)."""
        if os.path.isdir(S.ORDNER[0]):
            oeffnen(S.ORDNER[0])
        else:
            messagebox.showinfo(titel(), t("dlg.sprachordner_fehlt", ordner=S.ORDNER[0]))

    # ================================================================ Fenster
    def standard_fenster(self):
        """Feste Standardposition, die immer funktioniert: mittig auf dem Hauptbildschirm, an dessen Größe angepasst."""
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(int(980 * self.skala), sw - 80), min(int(800 * self.skala), sh - 120)
        return f"{w}x{h}+{(sw - w) // 2}+{max(0, (sh - h) // 3)}"

    @staticmethod
    def sichtbar(x, y, w):
        """Liegt die Titelleiste (links und rechts) auf einem angeschlossenen Bildschirm?"""
        try:
            import ctypes
            from ctypes import wintypes
            u = ctypes.windll.user32
            u.MonitorFromPoint.restype = wintypes.HANDLE
            return all(u.MonitorFromPoint(wintypes.POINT(px, y + 10), 0) for px in (x + 60, x + max(w - 60, 60)))
        except Exception:
            return 0 <= x and 0 <= y

    def fenster_setzen(self, geo):
        m = re.fullmatch(r"(\d+)x(\d+)\+(-?\d+)\+(-?\d+)", geo or "")
        if m:
            w, h, x, y = map(int, m.groups())
            if w >= 400 and h >= 300 and self.sichtbar(x, y, w):
                self.geometry(geo); return
        self.geometry(self.standard_fenster())

    # ================================================================ Sprache der Oberfläche
    def oberflaeche_wechseln(self, name):
        code = next((c for c, n, _ in self.sprachen if n == name), None)
        if not code or code == S.code():
            return
        self.zustand["oberflaeche"] = code
        try:
            E.speichere_zustand(self.zustand)
        except OSError:
            pass
        if self.proc:
            messagebox.showinfo(titel(), t("dlg.sprache_spaeter")); return
        if messagebox.askyesno(titel(), t("dlg.sprache_neustart")):
            self.neustart = True
            if not self.schliessen():
                self.neustart = False  # Schließen wurde abgebrochen

    # ================================================================ Zustand
    def letzte_werte_setzen(self):
        lw = self.zustand.get("letzte", {})
        if lw.get("profil") != self.profil["name"]:
            return
        self._laden = True
        if lw.get("modell") in self.modell.cget("values"):
            self.modell.set(lw["modell"])
        for var, key in ((self.sprache, "sprache"),):
            if lw.get(key):
                var.set(lw[key])
        self.begriffsdatei.set(lw.get("begriffsdatei", self.begriffsdatei.get()))
        self.begriffe.set(lw.get("begriffe", ""))
        self.kontext.set(lw.get("kontext", self.kontext.get()))
        self.raster.delete(0, "end"); self.raster.insert(0, lw.get("raster", ""))
        self.woerter.set(lw.get("woerter", False))
        if lw.get("zielordner") and os.path.isdir(lw["zielordner"]):
            self.ziel_setzen(lw["zielordner"])
        self._laden = False
        self.tokens_anzeigen()

    def letzte_werte_merken(self):
        self.zustand["profil"] = self.profil["name"]
        self.zustand.setdefault("oberflaeche", S.code())
        self.zustand["letzte"] = {"profil": self.profil["name"], "modell": self.modell.get(), "sprache": self.sprache.get(),
                                  "begriffsdatei": self.begriffsdatei.get(), "begriffe": self.begriffe.get(),
                                  "kontext": self.kontext.get(), "raster": self.raster.get(),
                                  "woerter": self.woerter.get(), "zielordner": self.zielpfad or ""}
        zustand = self.state()
        if zustand == "normal":  # minimiert: nichts speichern (Windows meldet dann −32000/−32000)
            self.zustand["fenster"] = self.geometry(); self.zustand["maximiert"] = False
        elif zustand == "zoomed":
            self.zustand["maximiert"] = True
        try:
            E.speichere_zustand(self.zustand)
        except OSError:
            pass

    def schliessen(self):
        if self.proc and not messagebox.askyesno(titel(), t("dlg.lauf_aktiv")):
            return False
        if not self.ungesichert_fragen():
            return False
        if self.proc:
            self.proc.terminate()
        self.letzte_werte_merken()
        try:
            self.after_cancel(self._poll_id)
        except (AttributeError, tk.TclError):
            pass
        self.destroy()
        return True


def main():
    """Fenster starten; nach einem Sprachwechsel mit Neustart wird es in der neuen Sprache neu aufgebaut."""
    while True:
        S.waehlen()  # gemerkt (zustand.json) → Windows-Sprache → Englisch → Deutsch
        app = App()
        app.mainloop()
        if not app.neustart:
            break


if __name__ == "__main__":
    main()
