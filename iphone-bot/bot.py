"""Video-Bot fürs iPhone: Belohnungsvideos starten, mit X schließen, wiederholen.

Befehle (Details in ANLEITUNG.md):
  python bot.py verbindung           prüft, ob das iPhone/WDA erreichbar ist
  python bot.py app                  zeigt die Bundle-ID der gerade offenen App
  python bot.py neu <spiel>          legt die Ordner für ein neues Spiel an
  python bot.py bild <spiel>         speichert einen Screenshot (zum Ausschneiden der Knöpfe)
  python bot.py test <spiel>         zeigt, welche Knöpfe gerade erkannt werden
  python bot.py start <spiel> [...]  startet den Bot (Stopp: Strg+C)
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2
import requests

from erkennung import bewerte, finde, lade_vorlagen
from wda import WDA, WDAFehler

HIER = Path(__file__).resolve().parent
SPIELE = HIER / "spiele"
ORDNER = {
    "video": "Knöpfe, die ein Belohnungsvideo starten",
    "schliessen": "X-Knöpfe, 'Schließen', 'Belohnung abholen' usw.",
    "weg": "optional: Knöpfe, die zum Video-Angebot führen (z. B. 'Shop')",
    "leer": "optional: Anzeige 'keine Videos mehr verfügbar'",
}
STANDARD = {
    "bundle_id": "",              # z. B. "com.firma.spiel" (mit 'python bot.py app' herausfinden)
    "schwelle": 0.85,             # wie genau ein Knopf passen muss (0..1)
    "intervall_sek": 1.5,         # Pause zwischen zwei Blicken auf den Bildschirm
    "werbung_min_sek": 5,         # so lange nach dem Start nicht nach X suchen
    "werbung_max_sek": 75,        # danach Notfall-Tipps auf übliche X-Stellen
    "max_runden_ohne_video": 20,  # so viele Runden ohne Video = "keine Videos mehr"
    "max_neustarts": 2,           # so oft das Spiel neu starten, bevor gemeldet wird
    "start_wartezeit_sek": 20,    # Ladezeit des Spiels nach einem Neustart
    # Stellen (Anteil von Breite/Höhe), an denen X-Knöpfe meistens sitzen
    "notfall_punkte": [[0.93, 0.06], [0.07, 0.06], [0.93, 0.10], [0.07, 0.10]],
}


class Spiel:
    def __init__(self, name):
        self.name = name
        self.ordner = SPIELE / name
        if not self.ordner.is_dir():
            raise SystemExit(f"Spiel '{name}' gibt es nicht. Anlegen mit: python bot.py neu {name}")
        self.cfg = dict(STANDARD)
        datei = self.ordner / "spiel.json"
        if datei.exists():
            self.cfg.update(json.loads(datei.read_text(encoding="utf-8")))
        self.vorlagen = {art: lade_vorlagen(self.ordner / art) for art in ORDNER}

    def __getattr__(self, schluessel):
        try:
            return self.__dict__["cfg"][schluessel]
        except KeyError:
            raise AttributeError(schluessel) from None


def log(text):
    print(f"[{datetime.now():%H:%M:%S}] {text}", flush=True)


def melden(text):
    log(f"*** {text} ***")
    try:
        import winsound
        for _ in range(3):
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            time.sleep(0.4)
    except ImportError:
        print("\a", end="", flush=True)


class Bot:
    def __init__(self, wda, schlafen=time.sleep, uhr=time.monotonic):
        self.wda = wda
        self.schlafen = schlafen
        self.uhr = uhr
        self.massstab = None  # Screenshot-Pixel pro Punkt
        self.videos = {}

    # --- Grundfunktionen -------------------------------------------------

    def bildschirm(self):
        bild = self.wda.screenshot()
        if self.massstab is None:
            breite, hoehe = self.wda.fenstergroesse()
            sx, sy = bild.shape[1] / breite, bild.shape[0] / hoehe
            if abs(sx - sy) > 0.1:
                log(f"Warnung: Screenshot ({bild.shape[1]}x{bild.shape[0]}) passt nicht zur "
                    f"Bildschirmgröße ({breite}x{hoehe}) – Tipps könnten danebengehen.")
            self.massstab = (sx, sy)
        return bild

    def tippe_pixel(self, x, y):
        sx, sy = self.massstab
        self.wda.tippe(x / sx, y / sy)

    def tippe_anteil(self, ax, ay):
        breite, hoehe = self.wda.fenstergroesse()
        self.wda.tippe(ax * breite, ay * hoehe)

    def im_spiel_halten(self, spiel):
        """Hat eine Werbung z. B. Safari oder den App Store geöffnet, zurück ins Spiel."""
        if not spiel.bundle_id:
            return
        aktiv = self.wda.aktive_app()
        if aktiv and aktiv != spiel.bundle_id:
            log(f"Andere App im Vordergrund ({aktiv}) – zurück zu {spiel.name}")
            self.wda.app_aktivieren(spiel.bundle_id)
            self.schlafen(2)

    def neustart(self, spiel):
        log(f"Starte {spiel.name} neu ...")
        self.wda.app_beenden(spiel.bundle_id)
        self.schlafen(2)
        self.wda.app_starten(spiel.bundle_id)
        self.massstab = None
        self.schlafen(spiel.start_wartezeit_sek)

    # --- Ablauf -----------------------------------------------------------

    def werbung_abwarten(self, spiel):
        """Wartet, bis das Video vorbei ist, und tippt auf X. True = geschlossen."""
        beginn = self.uhr()
        self.schlafen(spiel.werbung_min_sek)
        notfall = 0
        while True:
            self.im_spiel_halten(spiel)
            bild = self.bildschirm()
            treffer = finde(bild, spiel.vorlagen["schliessen"], spiel.schwelle)
            if treffer:
                log(f"  X gefunden ({treffer.name}) – schließe")
                self.tippe_pixel(treffer.x, treffer.y)
                return True
            if finde(bild, spiel.vorlagen["video"], spiel.schwelle):
                log("  Video-Knopf wieder sichtbar – Video lief wohl nicht")
                return False
            if self.uhr() - beginn > spiel.werbung_max_sek:
                punkte = spiel.notfall_punkte
                if notfall >= 2 * len(punkte):
                    log("  Kein X gefunden – gebe dieses Video auf")
                    return False
                ax, ay = punkte[notfall % len(punkte)]
                log(f"  Kein X erkannt – Notfall-Tipp bei {ax:.0%}/{ay:.0%}")
                self.tippe_anteil(ax, ay)
                notfall += 1
            self.schlafen(1)

    def spiel_abarbeiten(self, spiel):
        """Schaut Videos in einem Spiel, bis keine mehr kommen. Gibt die Anzahl zurück."""
        log(f"=== {spiel.name} ===")
        if spiel.bundle_id:
            self.wda.app_aktivieren(spiel.bundle_id)
            self.schlafen(2)
        gesehen = neustarts = ohne_video = 0
        while True:
            self.im_spiel_halten(spiel)
            bild = self.bildschirm()
            leer = False
            treffer = finde(bild, spiel.vorlagen["schliessen"], spiel.schwelle)
            if treffer:
                log(f"Schließe ({treffer.name})")
                self.tippe_pixel(treffer.x, treffer.y)
            elif finde(bild, spiel.vorlagen["leer"], spiel.schwelle):
                log("Spiel zeigt: keine Videos mehr")
                leer = True
            elif treffer := finde(bild, spiel.vorlagen["video"], spiel.schwelle):
                log(f"Starte Video ({treffer.name})")
                self.tippe_pixel(treffer.x, treffer.y)
                ohne_video = neustarts = 0
                if self.werbung_abwarten(spiel):
                    gesehen += 1
                    self.videos[spiel.name] = self.videos.get(spiel.name, 0) + 1
                    log(f"Video fertig – {gesehen} in {spiel.name}, {sum(self.videos.values())} insgesamt")
                self.schlafen(spiel.intervall_sek)
                continue
            elif treffer := finde(bild, spiel.vorlagen["weg"], spiel.schwelle):
                log(f"Tippe auf {treffer.name}")
                self.tippe_pixel(treffer.x, treffer.y)

            ohne_video += 1
            if leer or ohne_video >= spiel.max_runden_ohne_video:
                if spiel.bundle_id and neustarts < spiel.max_neustarts:
                    neustarts += 1
                    ohne_video = 0
                    log(f"Keine Videos gefunden (Neustart {neustarts}/{spiel.max_neustarts})")
                    self.neustart(spiel)
                    continue
                log(f"{spiel.name}: keine Videos mehr ({gesehen} geschaut)")
                return gesehen
            self.schlafen(spiel.intervall_sek)

    def lauf(self, spiele, pause_min=0):
        fehler_am_stueck = 0
        while True:
            for spiel in spiele:
                while True:
                    try:
                        self.spiel_abarbeiten(spiel)
                        fehler_am_stueck = 0
                        break
                    except (requests.RequestException, WDAFehler) as fehler:
                        fehler_am_stueck += 1
                        if fehler_am_stueck >= 12:
                            melden("Verbindung zum iPhone verloren – Bot stoppt")
                            return
                        log(f"Verbindungsproblem ({fehler}) – neuer Versuch in 5 s")
                        self.wda.sid = None
                        self.massstab = None
                        self.schlafen(5)
            if pause_min <= 0:
                melden("Keine Videos mehr in allen Spielen – Bot ist fertig")
                return
            melden(f"Keine Videos mehr – warte {pause_min} Minuten und versuche es dann erneut")
            self.schlafen(pause_min * 60)


# --- Befehle -----------------------------------------------------------------

def befehl_neu(args):
    ordner = SPIELE / args.spiel
    for art, beschreibung in ORDNER.items():
        (ordner / art).mkdir(parents=True, exist_ok=True)
        (ordner / art / "LIESMICH.txt").write_text(beschreibung + "\n", encoding="utf-8")
    datei = ordner / "spiel.json"
    if not datei.exists():
        datei.write_text(json.dumps({"bundle_id": args.bundle_id or ""}, indent=2) + "\n", encoding="utf-8")
    print(f"Angelegt: {ordner}\nJetzt Knopf-Bilder in die Unterordner legen (siehe ANLEITUNG.md).")


def befehl_bild(args, wda):
    ordner = SPIELE / args.spiel / "bilder"
    ordner.mkdir(parents=True, exist_ok=True)
    pfad = ordner / f"{datetime.now():%Y%m%d-%H%M%S}.png"
    cv2.imencode(".png", wda.screenshot())[1].tofile(str(pfad))
    print(f"Gespeichert: {pfad}")


def befehl_test(args, wda):
    spiel = Spiel(args.spiel)
    bild = wda.screenshot()
    markiert = bild.copy()
    print(f"Schwelle: {spiel.schwelle}  (ab diesem Wert gilt ein Knopf als gefunden)")
    for art, vorlagen in spiel.vorlagen.items():
        for t in bewerte(bild, vorlagen):
            gefunden = t.wert >= spiel.schwelle
            print(f"  {art:10} {t.name:25} {t.wert:.2f}  {'GEFUNDEN' if gefunden else '-'}")
            if gefunden:
                cv2.circle(markiert, (int(t.x), int(t.y)), 40, (0, 0, 255), 6)
                cv2.putText(markiert, f"{art}:{t.name}", (int(t.x) - 40, int(t.y) - 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
    pfad = spiel.ordner / "bilder" / "test.png"
    pfad.parent.mkdir(exist_ok=True)
    cv2.imencode(".png", markiert)[1].tofile(str(pfad))
    print(f"Markiertes Bild: {pfad}")


def main():
    parser = argparse.ArgumentParser(description="Video-Bot fürs iPhone")
    parser.add_argument("--wda", default="http://localhost:8100", help="Adresse von WebDriverAgent")
    unter = parser.add_subparsers(dest="befehl", required=True)
    unter.add_parser("verbindung", help="prüft die Verbindung zum iPhone")
    unter.add_parser("app", help="zeigt die Bundle-ID der offenen App")
    p = unter.add_parser("neu", help="legt ein neues Spiel an")
    p.add_argument("spiel")
    p.add_argument("--bundle-id")
    for name, hilfe in (("bild", "speichert einen Screenshot"), ("test", "zeigt erkannte Knöpfe")):
        unter.add_parser(name, help=hilfe).add_argument("spiel")
    p = unter.add_parser("start", help="startet den Bot (Stopp mit Strg+C)")
    p.add_argument("spiele", nargs="+", help="ein oder mehrere Spiele, werden nacheinander abgearbeitet")
    p.add_argument("--pause", type=float, default=0,
                   help="wenn alles leer: so viele Minuten warten und neu versuchen (0 = aufhören)")
    args = parser.parse_args()

    if args.befehl == "neu":
        return befehl_neu(args)

    wda = WDA(args.wda)
    try:
        wda.status()
    except requests.RequestException:
        raise SystemExit(f"iPhone nicht erreichbar unter {args.wda}.\n"
                         "Läuft WebDriverAgent und die Weiterleitung? (siehe ANLEITUNG.md, Schritt 5)")

    if args.befehl == "verbindung":
        breite, hoehe = wda.fenstergroesse()
        print(f"Verbunden. Bildschirm: {breite}x{hoehe} Punkte, offene App: {wda.aktive_app()}")
    elif args.befehl == "app":
        print(wda.aktive_app())
    elif args.befehl == "bild":
        befehl_bild(args, wda)
    elif args.befehl == "test":
        befehl_test(args, wda)
    elif args.befehl == "start":
        spiele = [Spiel(name) for name in args.spiele]
        for spiel in spiele:
            if not spiel.vorlagen["video"] or not spiel.vorlagen["schliessen"]:
                raise SystemExit(f"{spiel.name}: in 'video' und 'schliessen' muss je mindestens ein Bild liegen.")
        bot = Bot(wda)
        beginn = time.monotonic()
        log("Bot läuft. Zum Aufhören Strg+C drücken.")
        try:
            bot.lauf(spiele, args.pause)
        except KeyboardInterrupt:
            log("Gestoppt.")
        minuten = (time.monotonic() - beginn) / 60
        log(f"Videos geschaut: {sum(bot.videos.values())} in {minuten:.0f} Minuten {bot.videos or ''}")


if __name__ == "__main__":
    sys.exit(main())
