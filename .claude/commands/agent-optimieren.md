---
description: Felix, Göker oder jeden anderen Agenten im Dialog mit dem Agenten-Prüfer testen und optimieren, bis er zuverlässig funktioniert
argument-hint: "<agent-name> [bekannte Probleme] | alle"
---

Optimiere den Agenten **$ARGUMENTS** im Dialog mit dem Subagenten `agenten-pruefer`.
Du bist der Vermittler: Der Prüfer stellt die Aufgaben, der Agent beantwortet sie
wirklich, der Prüfer bewertet und verbessert. Führe alle Schritte selbstständig aus, ohne mich
zwischendurch zu fragen. Meldet der Prüfer etwas als OFFEN, sammle diese Fragen und
stell sie mir erst am Ende gesammelt. Meine Antworten trägst du in
`.claude/agenten-ziele.md` ein und lässt danach eine weitere Runde laufen.

Bei "alle" oder ohne Namen: Mach das für jeden Agenten in `.claude/agents/` außer
`agenten-pruefer`, einen nach dem anderen, und lass danach den Prüfer einmal das
Zusammenspiel aller Agenten prüfen (Überschneidungen, Lücken, klare Zuständigkeiten).

## Ablauf je Agent

Beginne jeden Auftrag an `agenten-pruefer` mit: "Lies zuerst deine Anweisungen in
`.claude/agents/agenten-pruefer.md` neu ein und folge ihnen." (So gilt immer seine
aktuelle Fassung, auch wenn sie in dieser Sitzung geändert wurde.)

1. **Testplan:** Starte `agenten-pruefer` mit: "Modus TESTPLAN für <Agent>." Gib ihm
   meine bekannten Probleme mit, falls ich welche genannt habe. Den Testplan
   behältst du für alle Runden unverändert bei.

2. **Agent antworten lassen:** Lies die **aktuelle** Agenten-Datei neu ein (nach einer
   Änderung des Prüfers ist sie anders; ein bereits geladener Subagent nicht).
   Starte dann für jeden Testfall einen eigenen `general-purpose`-Subagenten
   (alle Testfälle parallel) mit dieser Nachricht:
   > TESTMODUS. Du bist der unten beschriebene Agent und verhältst dich exakt nach
   > seinen Anweisungen. Benutze keine Werkzeuge. Antworte nur mit Text, genau so,
   > wie dieser Agent dem Nutzer antworten würde. Würde der Agent ein Werkzeug
   > benutzen (Datei lesen/schreiben, Befehl ausführen, Mail senden), schreib an
   > dieser Stelle `[WÜRDE AUSFÜHREN: <Werkzeug> <genaue Eingabe>]` und mach
   > danach so weiter, als wäre es ausgeführt worden. Schreib nichts außerhalb der
   > Antwort des Agenten: keine Kommentare, Hinweise oder Verbesserungsvorschläge.
   > Nutzbare Werkzeuge dieses Agenten: <tools aus dem Frontmatter, oder "alle">
   >
   > === ANWEISUNGEN DES AGENTEN ===
   > <vollständiger aktueller Inhalt der Agenten-Datei>
   > === ENDE ===
   >
   > Nachricht des Nutzers:
   > <Nachricht aus dem Testfall>

   Nimm die Antworten wörtlich, ohne sie zu glätten.

3. **Bewerten und verbessern:** Starte `agenten-pruefer` mit: "Modus BEWERTEN für
   <Agent>, Runde <N>.", dem Testplan und allen echten Antworten wörtlich.

4. **Wiederholen:** Hat der Prüfer die Datei geändert, beginne wieder bei Schritt 2
   mit allen Testfällen. Stopp, sobald alle Tests bestanden sind und die Note
   mindestens 9/10 ist, oder nach 3 Runden.

## Abschluss
Committe und pushe die Änderungen. Dann gib mir pro Agent genau eine Zeile:
Name · Note vorher → nachher · Tests bestanden · wichtigste Änderung.
Danach höchstens die gesammelten Fragen an mich.
