---
description: Lässt einen oder alle Agenten vom Agenten-Prüfer kritisch hinterfragen und optimieren
argument-hint: "[agent-name … | alle]"
---

Prüfe folgende Agenten: **$ARGUMENTS** (leer oder "alle" = alle Agenten in
`.claude/agents/` außer `agenten-pruefer` selbst).

1. Starte für jeden Agenten den Subagenten `agenten-pruefer` (bei mehreren parallel).
2. Zeig mir je Agent die Gesamtnote vorher/nachher und die Befunde der Schwere
   Kritisch und Hoch.
3. Frag mich, ob die verbesserte Fassung übernommen werden soll. Erst nach meinem
   Ja überschreibst du die Agenten-Datei mit der verbesserten Fassung.
4. Nach dem Übernehmen: Lass `agenten-pruefer` die neue Datei noch einmal prüfen,
   bis sie mindestens 9/10 erreicht oder nur noch Punkte offen sind, die meine
   Entscheidung brauchen (höchstens 3 Runden).
