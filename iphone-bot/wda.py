"""Kleiner Client für WebDriverAgent (WDA), der auf dem iPhone läuft.

WDA nimmt Screenshots auf und tippt auf den Bildschirm. Der Bot spricht es
über HTTP an (Standard: http://localhost:8100, per USB weitergeleitet).
"""
import base64

import cv2
import numpy as np
import requests


class WDAFehler(Exception):
    pass


class WDA:
    def __init__(self, url="http://localhost:8100"):
        self.url = url.rstrip("/")
        self.http = requests.Session()
        self.sid = None

    def _anfrage(self, methode, pfad, daten=None, timeout=30):
        antwort = self.http.request(methode, self.url + pfad, json=daten, timeout=timeout)
        try:
            inhalt = antwort.json()
        except ValueError:
            antwort.raise_for_status()
            raise WDAFehler(f"Unerwartete Antwort von WDA: {antwort.text[:200]}")
        wert = inhalt.get("value") if isinstance(inhalt, dict) else None
        if antwort.status_code >= 400 or (isinstance(wert, dict) and "error" in wert):
            fehler = wert.get("error") if isinstance(wert, dict) else antwort.status_code
            nachricht = wert.get("message", "") if isinstance(wert, dict) else antwort.text[:200]
            raise WDAFehler(f"{fehler}: {nachricht}")
        return inhalt if wert is None else wert

    def _sitzung(self, methode, pfad, daten=None):
        """Anfrage innerhalb einer WDA-Sitzung; legt bei Bedarf eine neue an."""
        for versuch in range(2):
            if not self.sid:
                antwort = self._anfrage("POST", "/session", {"capabilities": {"alwaysMatch": {}}})
                self.sid = antwort.get("sessionId") or antwort.get("value", {}).get("sessionId")
            try:
                return self._anfrage(methode, f"/session/{self.sid}{pfad}", daten)
            except WDAFehler as fehler:
                if versuch == 0 and "session" in str(fehler).lower():
                    self.sid = None
                    continue
                raise

    def status(self):
        return self._anfrage("GET", "/status", timeout=5)

    def screenshot(self):
        """Bildschirm als OpenCV-Bild (BGR, echte Pixel)."""
        daten = base64.b64decode(self._anfrage("GET", "/screenshot"))
        bild = cv2.imdecode(np.frombuffer(daten, np.uint8), cv2.IMREAD_COLOR)
        if bild is None:
            raise WDAFehler("Screenshot konnte nicht gelesen werden")
        return bild

    def fenstergroesse(self):
        """Bildschirmgröße in Punkten (darin werden Tipp-Koordinaten angegeben)."""
        groesse = self._sitzung("GET", "/window/size")
        return groesse["width"], groesse["height"]

    def tippe(self, x, y):
        """Kurzer Fingertipp an (x, y) in Punkten."""
        self._sitzung("POST", "/actions", {"actions": [{
            "type": "pointer", "id": "finger1", "parameters": {"pointerType": "touch"},
            "actions": [
                {"type": "pointerMove", "duration": 0, "x": int(x), "y": int(y)},
                {"type": "pointerDown", "button": 0},
                {"type": "pause", "duration": 80},
                {"type": "pointerUp", "button": 0},
            ],
        }]})

    def aktive_app(self):
        info = self._anfrage("GET", "/wda/activeAppInfo")
        return info.get("bundleId", "") if isinstance(info, dict) else ""

    def app_aktivieren(self, bundle_id):
        """Holt die App in den Vordergrund (startet sie, falls sie nicht läuft)."""
        self._sitzung("POST", "/wda/apps/activate", {"bundleId": bundle_id})

    def app_beenden(self, bundle_id):
        self._sitzung("POST", "/wda/apps/terminate", {"bundleId": bundle_id})

    def app_starten(self, bundle_id):
        self._sitzung("POST", "/wda/apps/launch", {"bundleId": bundle_id})
