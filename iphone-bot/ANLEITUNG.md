# iPhone-Video-Bot

Der Bot läuft auf dem PC und steuert das per USB angeschlossene iPhone:

1. Er schaut auf den Bildschirm (Screenshot) und sucht den Knopf „Video ansehen“.
2. Er tippt darauf, wartet, bis das Video vorbei ist, und tippt auf **X**.
3. Er tippt auf „Belohnung abholen“ o. Ä., falls das Spiel danach noch fragt.
4. Das wiederholt er, bis du **Strg+C** drückst.
5. Kommen keine Videos mehr, startet er das Spiel neu (Standard: bis zu 2-mal).
   Kommt danach immer noch nichts, wechselt er zum nächsten Spiel oder piept
   und meldet „Keine Videos mehr“.

Öffnet eine Werbung Safari oder den App Store, holt er das Spiel zurück. Findet er
nach 75 Sekunden kein X, tippt er auf die Ecken, wo X-Knöpfe meistens sitzen.

> **Hinweis:** Viele Spiele verbieten in ihren Nutzungsbedingungen automatisiertes
> Ansehen von Werbung. Wird es erkannt, kann das Konto gesperrt werden. Nutzung auf
> eigenes Risiko.

---

## Einrichtung (einmalig, Windows)

Ein iPhone lässt sich nicht so einfach vom PC fernsteuern wie ein Android-Handy.
Man braucht dafür **WebDriverAgent** (WDA), eine kleine Test-App von Apple-Entwickler-Werkzeugen,
die auf dem iPhone läuft und Screenshots + Tipps erlaubt.

### 1. Programme installieren
- **Python 3.10+** von python.org (beim Installieren „Add Python to PATH“ anhaken).
- **Apple Geräte** (Microsoft Store) oder **iTunes** – liefert den USB-Treiber.
- In diesem Ordner: `pip install -r requirements.txt`

### 2. go-ios installieren
go-ios spricht mit dem iPhone. Neueste Version von
https://github.com/danielpaulus/go-ios/releases (Datei für Windows) laden, `ios.exe`
z. B. nach `C:\go-ios\` entpacken und den Ordner zum PATH hinzufügen.
Test: iPhone anstecken, „Vertrauen“ bestätigen, dann `ios list` – das iPhone muss erscheinen.

### 3. Entwicklermodus am iPhone (iOS 16 und neuer)
`ios devmode enable` ausführen **oder** am iPhone *Einstellungen → Datenschutz & Sicherheit →
Entwicklermodus* einschalten. Das iPhone startet neu, danach „Einschalten“ bestätigen.

### 4. WebDriverAgent aufs iPhone bringen
*Ohne Mac* (mit kostenloser Apple-ID):
1. Von https://github.com/appium/WebDriverAgent/releases die Datei
   `WebDriverAgentRunner-Runner.zip` (Build für echte Geräte) laden.
2. Entpacken. Einen Ordner `Payload` anlegen, `WebDriverAgentRunner-Runner.app` hineinlegen,
   `Payload` als ZIP packen und die Datei in `WDA.ipa` umbenennen.
3. **Sideloadly** (sideloadly.io) installieren, `WDA.ipa` hineinziehen, mit Apple-ID anmelden,
   „Start“.
4. Am iPhone: *Einstellungen → Allgemein → VPN & Geräteverwaltung →* deine Apple-ID → „Vertrauen“.
5. `ios apps` ausführen und die Bundle-ID von WebDriverAgent notieren. Weicht sie von
   `com.facebook.WebDriverAgentRunner.xctrunner` ab, oben in `wda-starten.bat` eintragen.

Mit einer kostenlosen Apple-ID läuft die Signatur nach **7 Tagen** ab → dann Schritt 4.3 wiederholen.

*Mit Mac:* WebDriverAgent-Projekt in Xcode öffnen, unter „Signing“ dein Team wählen,
Schema `WebDriverAgentRunner` auf dem iPhone mit *Product → Test* starten. Weiter mit Schritt 6
(statt `wda-starten.bat` reicht `iproxy 8100 8100`).

### 5. WDA starten (jedes Mal, bevor der Bot läuft)
`wda-starten.bat` doppelklicken und das Fenster offen lassen.
In einem zweiten Fenster: `python bot.py verbindung` → muss „Verbunden“ zeigen.

### 6. iPhone vorbereiten
- *Einstellungen → Anzeige & Helligkeit → Automatische Sperre → Nie* (sonst geht der Bildschirm aus).
- Stummschalten, wenn die Werbung nicht laut sein soll.

---

## Ein Spiel einrichten

1. Spiel am iPhone öffnen, dann am PC:
   ```
   python bot.py app                 → zeigt z. B. com.firma.meinspiel
   python bot.py neu meinspiel --bundle-id com.firma.meinspiel
   ```
2. **Knopf-Bilder sammeln.** Zum Bildschirm mit dem Video-Knopf gehen und
   `python bot.py bild meinspiel` ausführen. Der Screenshot liegt in `spiele/meinspiel/bilder/`.
   Mit dem Snipping Tool oder Paint **nur den Knopf** eng ausschneiden und als PNG speichern:

   | Ordner | Was hinein gehört |
   |---|---|
   | `spiele/meinspiel/video/` | Knopf, der ein Belohnungsvideo startet (Pflicht) |
   | `spiele/meinspiel/schliessen/` | X-Knöpfe der Werbungen, „Schließen“, „Abholen“, „Weiter“ (Pflicht) |
   | `spiele/meinspiel/weg/` | optional: Knöpfe auf dem Weg zum Video-Angebot (z. B. „Shop“) |
   | `spiele/meinspiel/leer/` | optional: Anzeige „Keine Videos verfügbar“ |

   Werbungen haben unterschiedliche X-Knöpfe. Während ein Video läuft, mehrmals `bild` machen
   und jedes neue X ausschneiden. Je mehr X-Bilder, desto zuverlässiger.
3. Prüfen: `python bot.py test meinspiel` listet jeden Knopf mit einem Wert von 0 bis 1.
   Ab 0.85 gilt er als gefunden. Das markierte Bild liegt in `spiele/meinspiel/bilder/test.png`.

## Bot starten

```
python bot.py start meinspiel
python bot.py start spielA spielB            → erst A leer schauen, dann B
python bot.py start meinspiel --pause 60     → wenn alles leer: 60 Min warten, dann weiter
```
Aufhören: **Strg+C**. Am Ende steht, wie viele Videos geschaut wurden.

## Einstellungen pro Spiel (`spiele/<spiel>/spiel.json`)

Nur eintragen, was vom Standard abweichen soll, z. B.:
```json
{
  "bundle_id": "com.firma.meinspiel",
  "werbung_max_sek": 90,
  "max_neustarts": 3
}
```

| Einstellung | Standard | Bedeutung |
|---|---|---|
| `bundle_id` | – | Spiel-ID; ohne sie kein Neustart und kein Zurückholen aus Safari |
| `schwelle` | 0.85 | Wie genau ein Bild passen muss. Tippt er daneben: erhöhen; findet er nichts: senken |
| `intervall_sek` | 1.5 | Pause zwischen zwei Blicken auf den Bildschirm |
| `werbung_min_sek` | 5 | So lange nach dem Video-Start nicht nach X suchen |
| `werbung_max_sek` | 75 | Danach Notfall-Tipps auf übliche X-Stellen |
| `max_runden_ohne_video` | 20 | So viele Runden ohne Video = „keine Videos mehr“ |
| `max_neustarts` | 2 | So oft neu starten, bevor gemeldet bzw. zum nächsten Spiel gewechselt wird |
| `start_wartezeit_sek` | 20 | Ladezeit des Spiels nach einem Neustart |
| `notfall_punkte` | Ecken oben | Stellen (Anteil von Breite/Höhe) für Notfall-Tipps |

## Wenn etwas nicht klappt

- **„iPhone nicht erreichbar“** – läuft `wda-starten.bat`? iPhone entsperrt? Bei 7 Tage alter
  WDA-Signatur neu mit Sideloadly installieren.
- **Bleibt bei einer Werbung hängen** – `python bot.py bild meinspiel`, das X ausschneiden,
  in `schliessen/` legen.
- **Tippt auf falsche Stellen** – `test` ausführen; ein Bild mit hohem Wert an falscher Stelle
  enger ausschneiden oder `schwelle` erhöhen.

## Test ohne iPhone
`python tests/test_bot.py` spielt den ganzen Ablauf mit einem simulierten iPhone durch.
