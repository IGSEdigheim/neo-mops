# Neo-MOPS – Spezifikation

Neo-MOPS ist eine eigenständige Neuimplementierung des Modellrechners MOPS (Marco Haase, Version 1.04) als eine
einzige HTML-Datei für den Browser und für Moodle (SCORM 1.2). Jede Anforderung hat eine Kennung, damit sie am
Ende einzeln geprüft werden kann.

Grundlage: Anleitung `mops-1.04.pdf`, Bildschirmfoto des Originals, die Beispielprogramme in `MOPS Beispiele/` und
das beobachtete Verhalten des Original-Assemblers (an Grenzfällen ausprobiert).

## 1 Ziele und Abgrenzung

| Nr. | Anforderung |
|---|---|
| Z1 | **Harte Vorgabe:** Jeder Quelltext, den MOPS 1.04 fehlerfrei übersetzt, wird auch von Neo-MOPS übersetzt und liefert dieselben Ausgaben. |
| Z2 | **Harte Vorgabe:** Alle 15 Befehle mit allen 23 Varianten (Adresse/Wert) werden unterstützt. |
| Z3 | Eine Datei `index.html` mit eingebettetem CSS und JavaScript, keine Fremddateien, läuft offline und in Moodle. |
| Z4 | Kein getrenntes Lehrer- und Schülerprogramm. Der Lehrermodus wird mit Strg + Umschalt + L umgeschaltet. |
| Z5 | Kein Knopf „Kodieren“: Der Quelltext wird beim Tippen laufend übersetzt. |
| Z6 | Zwei Ansichten: **Einfach** (wenig auf dem Bildschirm) und **Fortgeschritten** (vollständiger Von-Neumann-Rechner). |
| Z7 | Auf Bildschirmen ab 1000 × 600 Pixel gibt es keine Scrollleiste der Seite. Die Rechnerdarstellung skaliert mit dem Fenster. |
| Z8 | Flüssige Animation: Werte wandern sichtbar über die Leitungen, Quelle und Ziel werden hervorgehoben. |
| Z9 | Der Befehlszähler zählt je Befehl um **1** weiter (im Original um 2). |

Bewusst **nicht** übernommen: Menüleiste, Knopf „Kodieren“, die Datei `mops.cfg` für eigene Befehlsnamen, das Verbot
eingerückter Befehle.

## 2 Rechnermodell

| Nr. | Anforderung |
|---|---|
| M1 | Der Speicher hat 72 Zellen mit den Adressen 00 bis 71. Die Zellen 00 bis 63 nehmen das Programm auf, die Zellen 64 bis 71 sind die Datenzellen mit den festen Namen a bis h. |
| M2 | **Ein Befehl belegt genau eine Speicherzelle.** Eine Programmzelle enthält ein Befehlswort aus Befehlscode (zweistellig) und Operand (vierstellig mit Vorzeichen), zum Beispiel `11 0005` für `ld 5`. Damit zählt der Befehlszähler um 1, und die Adresse eines Befehls ist seine laufende Nummer (ab 0). |
| M3 | Sprungziele im Maschinencode sind Speicheradressen der Zielbefehle. |
| M4 | Ein Programm darf bis zu 64 Befehle haben (Original: 32). |
| M5 | Zahlenbereich aller Werte: ganze Zahlen von −9999 bis 9999. |
| M6 | Register: Befehlszähler, Befehlsregister (Code und Operand), Akku, Operandenregister, Ergebnisregister, Vergleichsregister (`<`, `=`, `>` oder leer), Eingaberegister, Ausgaberegister. |
| M7 | Befehlscodes wie im Original: ld 10/11, st 12, in 20, out 22/23, add 30/31, sub 32/33, mul 34/35, div 36/37, mod 38/39, cmp 40/41, jmp 50, jlt 52, jeq 54, jgt 56, end 60 (gerade = Adresse, ungerade = Wert). |
| M8 | `div` und `mod` rechnen wie das Original (abrunden nach unten): −7 div 2 = −4, −7 mod 2 = 1. Für nicht negative Zahlen ist das die gewohnte Division mit Rest. |
| M9 | Laufzeitfehler halten das Programm mit einer Meldung an: Bereichsüberschreitung (Ergebnis außerhalb ±9999), Division durch null, bedingter Sprung bei leerem Vergleichsregister. |
| M10 | `cmp` vergleicht den Akku mit dem Operanden und setzt nur das Vergleichsregister. Der Akku bleibt unverändert. Bedingte Sprünge lesen das Vergleichsregister (jlt: Akku kleiner, jeq: gleich, jgt: größer). |
| M11 | `in` wartet in jeder Einstellung, bis eine gültige ganze Zahl (−9999 bis 9999) eingegeben wurde. |
| M12 | Beim Start und beim Zurücksetzen sind alle Register 0, das Vergleichsregister ist leer, der Befehlszähler steht auf 00. Der **Datenspeicher a bis h bleibt stehen** wie bei einem echten Rechner: über Zurücksetzen, Neustart, Änderungen am Quelltext und das Laden eines anderen Programms hinweg. Die Schüler sollen lernen, ihre Variablen selbst vorzubelegen. Leer (alles 0) ist er nur nach dem Laden der Seite. |

### Befehlszyklus (Ansicht „Fortgeschritten“)

| Nr. | Anforderung |
|---|---|
| M13 | **Holen:** (1) Befehlszähler → Adresse an den Speicher, (2) Speicherzelle → Befehlsregister, (3) Befehlszähler + 1. |
| M14 | **Dekodieren:** Der Dekodierer zeigt den Befehl in Worten. |
| M15 | **Ausführen:** je nach Befehl einzelne Schritte, z. B. bei `add a`: Adresse an den Speicher, Speicher → Operand, Rechnen im Rechenwerk (Akku und Operand → Ergebnis), Ergebnis → Akku. |
| M16 | **Variablen von Hand ändern:** Ein Klick auf den Wert einer Variablen a bis h öffnet dort ein Eingabefeld; der neue Wert steht danach im Datenspeicher. Das geht vor dem Start, in einer Pause und nach dem Ende, nicht im Lauf. Der Datenspeicher wird nicht gespeichert (weder in der Datei noch im Browser noch in Moodle). |

## 3 Assembler

| Nr. | Anforderung |
|---|---|
| A1 | Ein Befehl je Zeile, Befehl und Operand durch Leerzeichen oder Tabulatoren getrennt. Leerzeilen sind erlaubt. |
| A2 | Alles hinter einem Semikolon ist Kommentar. |
| A3 | Groß- und Kleinschreibung wird nirgends unterschieden (Befehle, Variablen, Marken). |
| A4 | Adressen: `$64` bis `$71`, gleichwertig die Variablen `a` bis `h`. Andere Adressen sind ein Fehler. Auch `$064` und `$ 64` werden wie im Original angenommen. |
| A5 | Werte: ganze Zahlen von −9999 bis 9999, ein Pluszeichen ist erlaubt. |
| A6 | `st` und `in` verlangen eine Adresse, die Sprungbefehle ein Sprungziel, `end` hat keinen Operanden, alle übrigen nehmen Adresse oder Wert. |
| A7 | Sprungziel als Zeilennummer `#n`: gemeint ist die n-te Zeile des Quelltexts (Kommentar- und Leerzeilen zählen mit). In der Zeile muss ein Befehl stehen. |
| A8 | Sprungziel als Marke: Definition rechts vom Befehl mit Doppelpunkt (`st b :weiter`), Verwendung ohne Doppelpunkt (`jeq weiter`). Marken bestehen aus Buchstaben (ohne Umlaute) und Ziffern und beginnen mit einem Buchstaben. Die Marke darf direkt am Operanden kleben (`ld a:x`) und darf wie eine Variable oder ein Befehl heißen (`a`, `end`). |
| A9 | Der Quelltext endet am ersten `end` ohne Operand. Was danach kommt, wird nicht übersetzt (Warnung). Fehlt dieses `end`, ist das ein Fehler. Eigenheit des Originals, die übernommen wird: Ein `end` mit Operand hält das Programm zur Laufzeit an, schließt den Quelltext aber nicht ab (Warnung). |
| A10 | Fehler (wie im Original): unbekannter Befehl, fehlender oder fehlerhafter Operand, Wert zu groß oder zu klein, Adresse außerhalb 64–71, Marke doppelt, ohne Namen, ohne Befehl oder mit unzulässigen Zeichen, Sprungziel nicht definiert, Sprungziel ohne Befehl, bedingter Sprung in einem Programm ganz ohne `cmp`, Programm zu lang, kein Befehl vorhanden. |
| A11 | Warnungen: Marke wird nie angesprungen, Befehle nach `end`. |
| A12 | Großzügiger als das Original: Befehle dürfen eingerückt sein, und vor einem Markennamen dürfen Leerzeichen stehen (`: weiter`). |
| A13 | Fehlermeldungen nennen die Zeile, sind für Schüler formuliert und schlagen bei Tippfehlern den nächstliegenden Befehl vor. |

## 4 Oberfläche

| Nr. | Anforderung |
|---|---|
| U1 | Aufbau: Kopfzeile, links der Editor, rechts der Rechner, darunter Erklärzeile und Steuerleiste. Alles passt ohne Scrollen ins Fenster (Z7). Lange Quelltexte scrollen nur innerhalb des Editors. |
| U2 | Editor mit Zeilennummern, farbiger Hervorhebung (Befehl, Zahl, Variable, Marke, Kommentar), Markierung der gerade bearbeiteten Zeile und Markierung fehlerhafter Zeilen. |
| U3 | Unter dem Editor steht der Zustand der Übersetzung: bereit mit Zahl der Befehle oder die Fehler und Warnungen. Ein Klick auf eine Meldung springt in die Zeile. |
| U4 | Wird der Quelltext geändert, wird sofort neu übersetzt und der Rechner zurückgesetzt. Bei Fehlern ist der Start gesperrt. |
| U5 | Steuerung: Start/Pause, Schritt, Zurücksetzen, Tempo in fünf Stufen: Langsam, Normal und Zügig mit wandernden Marken, „Schnell“ ohne Marken (nur die Werte ändern sich sichtbar, mehrere Befehle je Sekunde), „Sofort“ ohne jede Animation. |
| U6 | Tasten: Strg + Enter Start/Weiter (F5 bleibt beim Browser und lädt die Seite neu), F6 Schritt, Leertaste Pause/Weiter (außerhalb von Eingabefeldern), Esc Zurücksetzen. |
| U7 | Eine Erklärzeile sagt in jedem Schritt in einem Satz, was gerade passiert. |
| U8 | Eingabe: Bei `in` erscheint das Eingabefeld direkt am Eingaberegister und bekommt den Fokus. Ungültige Eingaben werden mit Hinweis abgelehnt. |
| U9 | Ausgabe: Das Ausgaberegister zeigt den letzten Wert, daneben steht der Verlauf aller Ausgaben des Laufs. |
| U10 | Beispielprogramme lassen sich laden. Quelltexte lassen sich als Datei öffnen (.ass, .txt) und speichern (.ass). |
| U11 | Eine Befehlsübersicht mit allen 15 Befehlen ist jederzeit aufrufbar. |
| U12 | Helles und dunkles Design, umschaltbar, die Wahl bleibt erhalten. |
| U13 | Sprache: Deutsch, Anrede „du“, generisches Maskulinum. |
| U14 | Die Phasenangabe in der Erklärzeile ist immer gleich breit, der Text daneben verrutscht beim Phasenwechsel nicht. |
| U15 | Zwischen Programmbereich und Rechner sitzt ein senkrechter Griff. Ziehen ändert die Breite des Programmbereichs (mindestens 200 px; rechts bleiben mindestens rund 700 px für den Rechner), Doppelklick stellt die automatische Breite wieder her, mit Fokus auf dem Griff gehen auch die Pfeiltasten. Die Breite wird mit den Einstellungen gemerkt. In der gestapelten Ansicht für kleine Fenster gibt es den Griff nicht. |

### Ansicht „Einfach“

| Nr. | Anforderung |
|---|---|
| E1 | Zu sehen sind nur: Programmspeicher, Datenzellen a–h, Befehlszähler, Befehlsregister, Akku, Vergleich, Eingabe, Ausgabe. |
| E2 | Programmzellen und Befehlsregister zeigen den Befehl lesbar (`add a`, Sprünge mit Zieladresse), nicht als Zahlencode. |
| E3 | Je Befehl höchstens zwei Animationen: Befehl holen, Befehl ausführen. „Schritt“ führt genau einen Befehl aus. |
| E4 | Die Erklärzeile beschreibt den Befehl mit den tatsächlichen Werten, z. B. „add a: 5 + 7 = 12“. |
| E5 | „Öffnen“ liest auch die Projektdateien des MOPS-Nachbaus einer Kollegin (`*.mops.json`, Format `mops-offline-project`): Der Quelltext kommt in den Editor, `startData` wird in den Datenspeicher a bis h geschrieben. Gespeichert wird weiterhin nur der Quelltext als Textdatei. |

### Ansicht „Fortgeschritten“

| Nr. | Anforderung |
|---|---|
| F4 | Adressbus und Datenbus sind farblich unterscheidbar und kreuzen sich nicht. |
| F1 | Zusätzlich zu sehen: alle 72 Zellen mit Maschinencode, Speicherlogik, Dekodierer, Operand, Rechenwerk mit Rechenzeichen, Ergebnis, Adressbus und Datenbus, Anzeige der Phase (Holen, Dekodieren, Ausführen). |
| F2 | Schrittweite wählbar: Mikroschritt, Phase, Befehl. Sie gilt nur für den Schrittknopf, der die gewählte Weite als Beschriftung trägt („1 Mikroschritt“, „1 Phase“, „1 Befehl“). „Start“ läuft immer durch. |
| F3 | Schalter „Bei Ausgabe anhalten“ (entspricht dem Ausgabestopp des Originals). |

### Animation

| Nr. | Anforderung |
|---|---|
| N1 | Jede Übertragung zeigt eine Marke mit dem Wert, die mit weichem Anfahren und Abbremsen über die Leitung von der Quelle zum Ziel läuft. Die benutzte Leitung leuchtet auf. |
| N2 | Die Quelle ist während der Übertragung hervorgehoben, das Ziel reagiert bei der Ankunft sichtbar. |
| N3 | Pause hält die Animation mitten in der Bewegung an und setzt sie an derselben Stelle fort. Tempoänderungen wirken sofort. |
| N4 | Ein Zeiger am Programmspeicher zeigt die Zelle, auf die der Befehlszähler zeigt, und gleitet beim Weiterzählen mit. |
| N5 | „Sofort“ rechnet ohne Animation. Auch eine Endlosschleife lässt die Oberfläche bedienbar. |

## 5 Lehrermodus, Speichern, Moodle

| Nr. | Anforderung |
|---|---|
| L1 | Strg + Umschalt + L schaltet den Lehrermodus an und aus. In Zeile 6 der Datei steht der Schalter `const LEHRERMODUS = false;` für dauerhaften Lehrermodus. Es gibt keinen Knopf dafür. |
| L2 | Im Lehrermodus gibt es zusätzlich: Lösungsprogramme im Beispielmenü (Countdown, Gauß, Euklid) und ein Ablaufprotokoll (je Befehl: Adresse, Befehl, Akku, Vergleich, a–h, Ausgabe) zum Kopieren. |
| L3 | Mit dem Tastenkürzel wird nichts gespeichert. Beim Ausschalten kommt der Quelltext des Schülers zurück. |
| S1 | Quelltext und Einstellungen (Ansicht, Tempo, Schrittweite) werden im Browser gespeichert und beim nächsten Öffnen wiederhergestellt. |
| S2 | Als SCORM-1.2-Paket: Der Stand liegt zusätzlich in `cmi.suspend_data` (bis 4000 Zeichen), je Schüler getrennt, der neuere Stand gilt. Status `incomplete`, nach dem ersten bis `end` gelaufenen Programm `completed`. |
| S3 | Außerhalb von Moodle läuft die Datei ohne Einschränkung. |

## 6 Abweichungen vom Original im Überblick

| Thema | MOPS 1.04 | Neo-MOPS |
|---|---|---|
| Zellen je Befehl | 2 (Code, Operand), `end` 1 | 1 (Befehlswort) |
| Befehlszähler | + 2 | + 1 |
| Sprungziel im Speicher | Adresse der Code-Zelle (gerade Zahl) | Nummer des Befehls |
| Höchstlänge | 32 Befehle | 64 Befehle |
| Befehlszähler erhöhen | in der Dekodierphase | am Ende der Holphase |
| Übersetzen | Knopf „Kodieren“ | laufend beim Tippen |
| Eingerückte Befehle | Fehler | erlaubt |

Die Quelltexte bleiben gleich (Z1). Nur der erzeugte Maschinencode sieht anders aus.

## 7 Prüfung (Stand 15.11.2026)

| Prüfung | Ergebnis | Deckt ab |
|---|---|---|
| `node tests/kern.test.mjs` (Assembler und Rechner ohne Browser) | 197 von 197 bestanden | Z1, Z2, Z9, M1–M15, A1–A13, E3 |
| Vergleich mit dem Original-Assembler von MOPS 1.04 an 12 023 Quelltexten (alle Beispielprogramme und zufällig erzeugte) | Alle 1618 Quelltexte, die das Original übersetzt, übersetzt auch Neo-MOPS, mit gleichen Befehlen, Operanden und Sprungzielen. Zusätzlich angenommen werden nur eingerückte Befehle und Leerzeichen vor Markennamen (A12). | Z1 |
| `python3 tests/oberflaeche.py` (echter Firefox ohne Fenster, echte Klicks und Tasten, nachgebautes Moodle) | 143 von 143 bestanden | Z3–Z7, M16, U1–U12, U14, U15, E1–E5, F1–F4, N1–N5, L1–L3, S1–S3 |
| Bildschirmfotos in beiden Ansichten, hell und dunkel, von 1000 × 600 bis 1920 × 1080 angesehen | keine Überlappungen, keine Scrollleiste der Seite | Z7, U1 |
| Bildrate während einer Übertragung gemessen | 17 ms zwischen zwei Bildern (rund 60 Bilder je Sekunde) | Z8 |

Nicht automatisch geprüft: der Dateidialog beim Öffnen und der Download beim Speichern (U10), das Kopieren des
Protokolls in die Zwischenablage (L2), echtes Moodle, Chrome, Safari und Tablets. Das Laufzeitverhalten des Originals
(Rechnen, Vergleichen) wurde nicht Programm gegen Programm verglichen, sondern aus dem Original abgelesen (Abrunden bei
`div` und `mod`, Bereichsprüfung) und mit eigenen Erwartungswerten getestet.
