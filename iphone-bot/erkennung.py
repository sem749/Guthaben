"""Findet Knöpfe (Video starten, X, ...) per Bildvergleich im Screenshot."""
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

# Screenshots werden für die Suche auf diese Breite verkleinert (schneller).
ARBEITSBREITE = 540
# Vorlagen werden zusätzlich leicht verkleinert/vergrößert gesucht, weil
# X-Knöpfe je nach Werbung etwas anders groß sind.
SKALEN = (1.0, 0.85, 1.15)
BILDENDUNGEN = (".png", ".jpg", ".jpeg")


@dataclass
class Vorlage:
    name: str
    bild: np.ndarray  # Graustufen, in Original-Pixeln des Screenshots


@dataclass
class Treffer:
    name: str
    x: float  # Mitte des Knopfs in Screenshot-Pixeln
    y: float
    wert: float  # 0..1, wie gut die Vorlage passt


def lade_vorlagen(ordner):
    ordner = Path(ordner)
    vorlagen = []
    if not ordner.is_dir():
        return vorlagen
    for pfad in sorted(ordner.iterdir()):
        if pfad.suffix.lower() not in BILDENDUNGEN:
            continue
        # np.fromfile statt cv2.imread, damit Umlaute im Windows-Pfad gehen
        bild = cv2.imdecode(np.fromfile(str(pfad), np.uint8), cv2.IMREAD_GRAYSCALE)
        if bild is None:
            raise ValueError(f"Bild kann nicht gelesen werden: {pfad}")
        vorlagen.append(Vorlage(pfad.stem, bild))
    return vorlagen


def graustufen(bild):
    return bild if bild.ndim == 2 else cv2.cvtColor(bild, cv2.COLOR_BGR2GRAY)


def bewerte(screenshot, vorlagen):
    """Bester Treffer je Vorlage, egal wie gut (für den Test-Befehl)."""
    grau = graustufen(screenshot)
    faktor = min(1.0, ARBEITSBREITE / grau.shape[1])
    klein = cv2.resize(grau, None, fx=faktor, fy=faktor, interpolation=cv2.INTER_AREA)
    ergebnisse = []
    for vorlage in vorlagen:
        bester = None
        for skala in SKALEN:
            g = faktor * skala
            t = cv2.resize(vorlage.bild, None, fx=g, fy=g,
                           interpolation=cv2.INTER_AREA if g < 1 else cv2.INTER_LINEAR)
            th, tw = t.shape
            if th < 6 or tw < 6 or th > klein.shape[0] or tw > klein.shape[1]:
                continue
            karte = cv2.matchTemplate(klein, t, cv2.TM_CCOEFF_NORMED)
            karte[~np.isfinite(karte)] = 0
            _, wert, _, (lx, ly) = cv2.minMaxLoc(karte)
            if bester is None or wert > bester.wert:
                bester = Treffer(vorlage.name, (lx + tw / 2) / faktor, (ly + th / 2) / faktor, float(wert))
        if bester:
            ergebnisse.append(bester)
    return ergebnisse


def finde(screenshot, vorlagen, schwelle):
    """Bester Treffer über alle Vorlagen, oder None wenn keiner gut genug passt."""
    if not vorlagen:
        return None
    treffer = [t for t in bewerte(screenshot, vorlagen) if t.wert >= schwelle]
    return max(treffer, key=lambda t: t.wert) if treffer else None
