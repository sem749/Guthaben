# Agenten in diesem Projekt

Agenten liegen als Dateien in `.claude/agents/`. Der Agent `agenten-pruefer`
kontrolliert und optimiert alle anderen.

- Sagt der Nutzer "kontrolliere <Name>", "prüf <Name>", "optimier <Name>" oder
  "kontrolliere alle", führe sofort den Ablauf aus `.claude/commands/agent-optimieren.md`
  für diesen Agenten aus (Prüfer und Agent im echten Dialog, selbstständig bis zum Ende).
- Ziele und Pflicht-Anforderungen je Agent stehen in `.claude/agenten-ziele.md`.
  Beantwortet der Nutzer eine Frage zu einem Agenten, trag die Antwort dort ein.
- Wird ein Agent in `.claude/agents/` neu angelegt oder geändert, kontrolliere ihn
  danach automatisch, ohne dass der Nutzer es sagen muss.
- Fragt der Nutzer nach Zielen für einen neuen Agenten oder nennt er sie, leg dafür
  einen eigenen Abschnitt in `.claude/agenten-ziele.md` an.
- Nach jeder Änderung an Agenten, Zielen oder Regeln: committen und auf den
  aktuellen Branch pushen, damit der tägliche Abgleich in der Cloud sie sieht.
- Sicherungen alter Fassungen liegen in `.claude/agent-backups/`. Das ist kein
  Agenten-Ordner, leg dort nie aktive Agenten ab.

## Agenten-Zentrale
Übersichtsseite aller Agenten: https://claude.ai/artifact/YSdyQT8V32xV8YDpHp2d63
Daten liegen in ihrer Datenbank (Sammlungen `agenten` und `vorschlaege`). Wird ein
Agent angelegt, geändert oder kontrolliert, aktualisiere seinen Eintrag (Status,
Note, Fähigkeiten, Grenzen, Datum). Ist eine Lücke geschlossen, lösch den Vorschlag;
fällt eine neue Lücke auf, trag sie ein. Geht das in dieser Sitzung nicht, sag es.
