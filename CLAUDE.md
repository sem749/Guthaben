# Agenten in diesem Projekt

Agenten liegen als Dateien in `.claude/agents/`. Der Agent `agenten-pruefer`
kontrolliert und optimiert alle anderen.

- Sagt der Nutzer "kontrolliere <Name>", "prüf <Name>", "optimier <Name>" oder
  "kontrolliere alle", führe sofort den Ablauf aus `.claude/commands/agent-optimieren.md`
  für diesen Agenten aus (Prüfer und Agent im echten Dialog, selbstständig bis zum Ende).
- Ziele und Pflicht-Anforderungen je Agent stehen in `.claude/agenten-ziele.md`.
  Beantwortet der Nutzer eine Frage zu einem Agenten, trag die Antwort dort ein.
- Wird ein Agent neu angelegt oder geändert, schlag vor, ihn zu kontrollieren.
- Sicherungen alter Fassungen liegen in `.claude/agent-backups/`. Das ist kein
  Agenten-Ordner, leg dort nie aktive Agenten ab.
