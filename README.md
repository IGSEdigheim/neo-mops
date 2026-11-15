# Neo-MOPS

Ein Modellrechner nach von Neumann für den Informatikunterricht, als einzelne HTML-Seite für den Browser.
Neo-MOPS versteht die Assemblersprache des Modellrechners MOPS von Marco Haase (Version 1.04) und zeigt Schritt für
Schritt, wie ein Programm im Rechner abläuft. Es ist eine eigenständige Neuentwicklung, vom Original wurde kein
Quelltext übernommen.

## Benutzen

`index.html` im Browser öffnen. Es wird nichts installiert, die Seite läuft ohne Netz.

- Zwei Ansichten: „Einfach“ und „Fortgeschritten“ (mit Maschinencode, Bussen und den Phasen Holen, Dekodieren, Ausführen)
- Das Programm wird beim Tippen übersetzt, Fehler werden unter dem Editor erklärt
- Start, Einzelschritt, Zurücksetzen, fünf Tempostufen
- Die Variablen a bis h lassen sich durch Anklicken ändern; der Datenspeicher bleibt beim Zurücksetzen stehen
- Lehrermodus mit Lösungen und Ablaufprotokoll: Strg + Umschalt + L

Mit `imsmanifest.xml` lässt sich die Seite auch als SCORM-1.2-Lernpaket in Moodle einbinden.

## Dateien

- `index.html` – das ganze Programm
- `SPEZIFIKATION.md` – Anforderungen, Abweichungen vom Original, Stand der Prüfung
- `tests/kern.test.mjs` – Assembler und Rechner ohne Browser (`node tests/kern.test.mjs`)
- `tests/oberflaeche.py` – Oberfläche in einem Firefox ohne Fenster; braucht ein Hilfsskript, das nicht in diesem Repo liegt

## Lizenz

MIT, siehe `LICENSE`. © 2026 Pascal Deneaux
