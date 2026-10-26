"""Testet den Bot gegen ein simuliertes iPhone (ohne echtes Gerät).

Aufruf: python -m pytest iphone-bot/tests   oder   python iphone-bot/tests/test_bot.py
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bot  # noqa: E402

BREITE, HOEHE = 1170, 2532  # Pixel, wie ein iPhone 13/14
MASSSTAB = 3                # Pixel pro Punkt


def knopf_video():
    b = np.full((120, 360, 3), (40, 160, 40), np.uint8)
    cv2.putText(b, "VIDEO", (40, 85), cv2.FONT_HERSHEY_SIMPLEX, 2.2, (255, 255, 255), 5)
    cv2.circle(b, (320, 60), 25, (0, 220, 255), -1)
    return b


def knopf_x():
    b = np.full((90, 90, 3), (60, 60, 60), np.uint8)
    cv2.circle(b, (45, 45), 40, (230, 230, 230), 4)
    cv2.line(b, (25, 25), (65, 65), (230, 230, 230), 6)
    cv2.line(b, (65, 25), (25, 65), (230, 230, 230), 6)
    return b


def knopf_abholen():
    b = np.full((110, 420, 3), (0, 140, 230), np.uint8)
    cv2.putText(b, "ABHOLEN", (25, 78), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (255, 255, 255), 5)
    return b


class FalschesIPhone:
    """Spiel mit Menü -> Werbung (X nach 15 s) -> Belohnung -> Menü."""

    def __init__(self, videos, nach_neustart=0, bundle="com.test.spiel"):
        self.zeit = 0.0
        self.videos = videos
        self.nach_neustart = nach_neustart
        self.bundle = bundle
        self.zustand = "menue"
        self.werbung_seit = 0
        self.vordergrund = bundle
        self.knoepfe = {}
        self.neustarts = 0
        self.sid = None

    def schlafen(self, s):
        self.zeit += s

    def uhr(self):
        return self.zeit

    def _setze(self, bild, name, knopf, x, y):
        h, w = knopf.shape[:2]
        bild[y:y + h, x:x + w] = knopf
        self.knoepfe[name] = (x, y, w, h)

    def screenshot(self):
        self.knoepfe = {}
        if self.zustand == "menue":
            bild = np.full((HOEHE, BREITE, 3), (90, 50, 20), np.uint8)
            cv2.putText(bild, "MEIN SPIEL", (250, 400), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 6)
            if self.videos > 0:
                self._setze(bild, "video", knopf_video(), 400, 1800)
        elif self.zustand == "werbung":
            bild = np.full((HOEHE, BREITE, 3), (200, 200, 200), np.uint8)
            cv2.rectangle(bild, (100, 700), (1070, 1700), (30, 30, 180), -1)
            if self.zeit - self.werbung_seit >= 15:
                self._setze(bild, "x", knopf_x(), 1050, 120)
        else:  # belohnung
            bild = np.full((HOEHE, BREITE, 3), (90, 50, 20), np.uint8)
            self._setze(bild, "abholen", knopf_abholen(), 375, 1500)
        return bild

    def fenstergroesse(self):
        return BREITE // MASSSTAB, HOEHE // MASSSTAB

    def tippe(self, x, y):
        px, py = x * MASSSTAB, y * MASSSTAB
        for name, (kx, ky, kw, kh) in self.knoepfe.items():
            if kx <= px <= kx + kw and ky <= py <= ky + kh:
                if name == "video":
                    self.zustand, self.werbung_seit = "werbung", self.zeit
                elif name == "x":
                    self.zustand = "belohnung"
                elif name == "abholen":
                    self.zustand = "menue"
                    self.videos -= 1
                    self.belohnungen = getattr(self, "belohnungen", 0) + 1
                return

    def aktive_app(self):
        return self.vordergrund

    def app_aktivieren(self, bundle):
        self.vordergrund = bundle

    def app_beenden(self, bundle):
        self.vordergrund = "com.apple.springboard"

    def app_starten(self, bundle):
        self.neustarts += 1
        self.vordergrund = bundle
        self.zustand = "menue"
        self.videos += self.nach_neustart
        self.nach_neustart = 0


def lege_spiel_an(tmp_path, bundle="com.test.spiel"):
    bot.SPIELE = tmp_path
    ordner = tmp_path / "testspiel"
    for art in bot.ORDNER:
        (ordner / art).mkdir(parents=True)
    cv2.imwrite(str(ordner / "video" / "video.png"), knopf_video())
    cv2.imwrite(str(ordner / "schliessen" / "x.png"), knopf_x())
    cv2.imwrite(str(ordner / "schliessen" / "abholen.png"), knopf_abholen())
    (ordner / "spiel.json").write_text(json.dumps({"bundle_id": bundle, "start_wartezeit_sek": 5}))
    return bot.Spiel("testspiel")


def test_schaut_alle_videos_und_startet_neu(tmp_path):
    spiel = lege_spiel_an(tmp_path)
    iphone = FalschesIPhone(videos=3, nach_neustart=2)
    b = bot.Bot(iphone, schlafen=iphone.schlafen, uhr=iphone.uhr)
    b.lauf([spiel])
    assert iphone.belohnungen == 5          # 3 Videos + 2 nach dem ersten Neustart
    assert b.videos == {"testspiel": 5}
    assert iphone.neustarts == 3            # 1 erfolgreicher + 2 erfolglose, dann Ende


def test_holt_spiel_zurueck_wenn_werbung_safari_oeffnet(tmp_path):
    spiel = lege_spiel_an(tmp_path)
    iphone = FalschesIPhone(videos=1)
    iphone.vordergrund = "com.apple.mobilesafari"
    b = bot.Bot(iphone, schlafen=iphone.schlafen, uhr=iphone.uhr)
    b.lauf([spiel])
    assert iphone.belohnungen == 1


def test_ohne_bundle_id_kein_neustart(tmp_path):
    spiel = lege_spiel_an(tmp_path, bundle="")
    iphone = FalschesIPhone(videos=2, nach_neustart=5)
    b = bot.Bot(iphone, schlafen=iphone.schlafen, uhr=iphone.uhr)
    b.lauf([spiel])
    assert iphone.belohnungen == 2 and iphone.neustarts == 0


if __name__ == "__main__":
    import tempfile
    for test in (test_schaut_alle_videos_und_startet_neu,
                 test_holt_spiel_zurueck_wenn_werbung_safari_oeffnet,
                 test_ohne_bundle_id_kein_neustart):
        with tempfile.TemporaryDirectory() as d:
            test(Path(d))
        print("OK", test.__name__)
