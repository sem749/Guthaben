# Agenten in diesem Projekt

Agenten liegen als Dateien in `.claude/agents/`. Der Agent `agenten-pruefer`
kontrolliert und optimiert alle anderen.

- Wird ein Agent neu angelegt oder geändert, schlag vor, ihn mit
  `/agent-optimieren <name>` zu testen und zu optimieren.
- Sicherungen alter Fassungen liegen in `.claude/agent-backups/`. Das ist kein
  Agenten-Ordner, leg dort nie aktive Agenten ab.
