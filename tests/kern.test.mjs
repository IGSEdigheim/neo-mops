// Prüft Assembler und Rechner ohne Browser:  node tests/kern.test.mjs
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const hier = path.dirname(fileURLToPath(import.meta.url));
const html = fs.readFileSync(path.join(hier, "..", "index.html"), "utf8");
const kern = html.split("/* <KERN>")[1].split("/* </KERN> */")[0].replace(/^[^\n]*\n/, "");
const { uebersetze, Rechner, BEFEHLE } = new Function(kern + "\nreturn { uebersetze, Rechner, BEFEHLE };")();

let ok = 0, schlecht = 0;
function pruefe(name, bed, info = "") { if (bed) ok++; else { schlecht++; console.log("FEHLER:", name, info); } }
const gleich = (a, b) => JSON.stringify(a) === JSON.stringify(b);

// Lässt ein Programm laufen. Liefert Ausgaben, Rechner und die Zahl der Schritte.
function lauf(quelle, eingaben = [], maxSchritte = 200000) {
  const u = uebersetze(quelle);
  if (!u.ok) return { fehler: u.fehler };
  const m = new Rechner(u.zellen), ein = eingaben.slice();
  let n = 0, pcVorher = [], schritte = [];
  while (!m.fertig && !m.fehler && n < maxSchritte) {
    const pc0 = m.pc;
    for (const s of m.befehl()) {
      n++; schritte.push(s);
      if (s.eingabe) { if (!ein.length) return { aus: m.ausgaben, m, wartet: true }; s.set(ein.shift()); } else if (s.set) s.set();
      if (m.fehler) break;
    }
    pcVorher.push([pc0, m.pc]);
  }
  return { aus: m.ausgaben, m, n, pcs: pcVorher, schritte, lzf: m.fehler, u };
}

// ---------- Z2 / M7: alle 15 Befehle, 23 Codes ----------
const alle = `ld a\nld 1\nst a\nin a\nout a\nout 1\nadd a\nadd 1\nsub a\nsub 1\nmul a\nmul 1\ndiv a\ndiv 1\nmod a\nmod 1\ncmp a\ncmp 1\njmp #1\njlt #1\njeq #1\njgt #1\nend`;
const ua = uebersetze(alle);
pruefe("23 Varianten übersetzt", ua.ok && ua.zellen.length === 23, JSON.stringify(ua.fehler));
pruefe("Befehlscodes wie im Original", gleich(ua.zellen.map(c => c.op), [10, 11, 12, 20, 22, 23, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 50, 52, 54, 56, 60]));
pruefe("15 Befehle", Object.keys(BEFEHLE).length === 15);

// ---------- Z1: Beispielprogramme des Lehrers ----------
const bsp = path.join(hier, "..", "..", "MOPS Beispiele");
const lies = f => { const b = fs.readFileSync(path.join(bsp, f)); try { return new TextDecoder("utf-8", { fatal: true }).decode(b); } catch { return new TextDecoder("windows-1252").decode(b); } };
const ggT = (a, b) => (b ? ggT(b, a % b) : a);
const faelle = [
  ["addition.txt", [3, 4], [7]], ["addition.txt", [-5, 2], [-3]],
  ["A3_Lsg.txt", [3], []], ["CountDown.txt", [4], []],
  ["euklid/euklid.txt", [12, 18], [6]], ["euklid/euklid.txt", [0, 5], [5]], ["euklid/euklid.txt", [7, 0], [7]],
  ["euklid/euklid_mitMarken.txt", [48, 36], [12]], ["euklid/euklid_mitMarken.txt", [17, 5], [1]],
  ["kleiner Gauß/gaus_mit_kommentaren.txt", [50], [1275]], ["kleiner Gauß/gaus.ass", [4], [10]],
  ["kleiner Gauß/summe_fußgesteuert.txt", [5], [15]], ["kleiner Gauß/summe_kopfgesteuert.txt", [5], [15]],
];
for (const [f, ein, soll] of faelle) {
  const r = lauf(lies(f), ein);
  pruefe(`${f} ${ein}`, !r.fehler && !r.lzf && r.m.fertig && gleich(r.aus, soll), JSON.stringify(r.fehler || r.lzf || r.aus));
}
pruefe("euklid_minimal übersetzt", uebersetze(lies("euklid/euklid_minimal.txt")).ok);
pruefe("A3: a endet bei 0", lauf(lies("A3_Lsg.txt"), [3]).m.daten[0] === 0);
for (let a = 1; a < 30; a += 3) for (let b = 1; b < 30; b += 4) pruefe(`ggT ${a},${b}`, gleich(lauf(lies("euklid/euklid_mitMarken.txt"), [a, b]).aus, [ggT(a, b)]));

// Beispiel aus der Anleitung (Kapitel 5)
const anleitung = `; Gerade Zahlen rückwärts\nin a\n; gerade machen\nld a\nmod 2\ncmp 0\nld a\njeq weiter\nsub 1\n; rückwärts zählen\nst b :weiter\nout b\nsub 2\ncmp 0\njgt weiter\nend`;
pruefe("Anleitung: 7", gleich(lauf(anleitung, [7]).aus, [6, 4, 2]));
pruefe("Anleitung: 6", gleich(lauf(anleitung, [6]).aus, [6, 4, 2]));

// ---------- A1–A12: Schreibweise ----------
const gut = [
  "ld 1\nend", "LD 1 :A\nJMP a\nEND", "ld\t1\nend", "  ld 1\n\tend", "ld $64\nend", "ld $064\nend", "ld $ 64\nend", "ld A\nend",
  "ld 9999\nend", "ld -9999\nend", "ld +5\nend", "ld a:x\njmp x\nend", "ld 1:x\njmp x\nend", "ld 1 : x\njmp x\nend",
  "ld 1 :end\njmp end\nend", "cmp 0\njeq end; x\nout c :end\nend", "ld 1 :a\njmp a\nend", "ld 1;x\nend", "end", "ld 1\nend\nquatsch hier",
  "; c\njmp #2\nend", "jmp #01\nend", "\n\nld 1\n\nend\n\n", "jmp e\nend :e\nld 1", "ld 1 :Xy9\njmp xY9\nend", "ld 1\r\nend\r\n",
  Array(63).fill("ld 1").join("\n") + "\nend",
];
for (const q of gut) { const u = uebersetze(q); pruefe("soll gehen: " + JSON.stringify(q).slice(0, 50), u.ok, JSON.stringify(u.fehler)); }
const schlechtQ = [
  ["ld 1", /end/], ["", /keinen Befehl/], ["; x", /keinen Befehl/], ["ld a\nst 5\nend", /keine Zahl/], ["in 5\nend", /keine Zahl/],
  ["ld $63\nend", /Adresse/], ["ld $72\nend", /Adresse/], ["ld 10000\nend", /zu groß/], ["ld -10000\nend", /zu klein/],
  ["jmp #3\nend", /kein Befehl/], ["; c\njmp #1\nend", /kein Befehl/], ["jeq x\nend :x", /cmp/], ["ld 1 :x\nld 2 :x\njmp x\nend", /gibt es schon/],
  ["ld 1 :1x\njmp x\nend", /Buchstaben/], ["ld 1 :äx\nend", /Buchstaben/], ["ld 1 :\nend", /Name/], [":x\nend", /fehlt der Befehl/],
  ["ld\nend", /fehlt der Operand/], ["foo 1\nend", /gibt es nicht/], ["end 1", /fehlt der Befehl end/], ["ld 1 2\nend", /nichts anfangen/],
  ["ld i\nend", /a bis h/], ["ld 1.5\nend", /nichts anfangen/], ["jmp a\nend", /Marke/], ["jmp 3\nend", /#3/], ["jmp $64\nend", /Sprungziel/],
  ["cmp 1\njlt #4\nend\nend", /kein Befehl/], [Array(64).fill("ld 1").join("\n") + "\nend", /zu lang/], ["lad 1\nend", /Meintest du „ld“/],
  ["load a\nend", /Meintest du „ld“/], ["jmp x\nfoo 1 :x\nend", /^(?!.*Marke „x“ gibt es nicht)/],
];
for (const [q, muster] of schlechtQ) { const u = uebersetze(q); pruefe("soll scheitern: " + JSON.stringify(q).slice(0, 50), !u.ok && u.fehler.some(f => muster.test(f.text)), JSON.stringify(u.fehler)); }
pruefe("Warnung: Marke unbenutzt", uebersetze("ld 1 :x\nend").warnungen.length === 1);
pruefe("Warnung: nach end", uebersetze("ld 1\nend\nld 2").warnungen.length === 1 && uebersetze("ld 1\nend\nld 2").zellen.length === 2);
pruefe("end mit Operand wie im Original", uebersetze("ld 1\nend 5\nld 2\nend").zellen.map(c => c.op).join() === "11,60,11,60" && gleich(lauf("out 1\nend 5\nout 2\nend").aus, [1]));
pruefe("Fehler nennt Zeile", uebersetze("ld 1\n\nfoo\nend").fehler[0].zeile === 3);

// ---------- M2/M3/Z9: ein Befehl je Zelle, Befehlszähler +1, Sprungziel = Befehlsnummer ----------
const u1 = uebersetze("; k\nin a\n\nld a :m\ncmp 1\njgt m\njmp #2\nend");
pruefe("eine Zelle je Befehl", u1.zellen.length === 6);
pruefe("Sprungziel Marke = Befehlsnummer", u1.zellen[3].arg === 1);
pruefe("Sprungziel #2 = Befehlsnummer", u1.zellen[4].arg === 0);
const r1 = lauf("ld 1\nadd 2\nst a\nout a\nend");
pruefe("Befehlszähler zählt um 1", gleich(r1.pcs, [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5]]), JSON.stringify(r1.pcs));

// ---------- M5–M12: Rechnen ----------
const rech = (q, ein) => lauf(q + "\nst a\nout a\nend", ein).aus[0];
pruefe("add", rech("ld 5\nadd 7") === 12); pruefe("sub", rech("ld 5\nsub 7") === -2); pruefe("mul", rech("ld -5\nmul 7") === -35);
pruefe("div", rech("ld 17\ndiv 5") === 3); pruefe("mod", rech("ld 17\nmod 5") === 2);
pruefe("div negativ wie Original", rech("ld -7\ndiv 2") === -4); pruefe("mod negativ wie Original", rech("ld -7\nmod 2") === 1);
pruefe("mod negativer Teiler wie Original", rech("ld 7\nmod -2") === -1); pruefe("div negativer Teiler", rech("ld 7\ndiv -2") === -4);
pruefe("add Adresse", gleich(lauf("in a\nin b\nld a\nadd b\nmul b\nst c\nout c\nend", [2, 3]).aus, [15]));
pruefe("Überlauf", /Zahlenbereich/.test(lauf("ld 9999\nadd 1\nend").lzf)); pruefe("Unterlauf", /Zahlenbereich/.test(lauf("ld -9999\nsub 1\nend").lzf));
pruefe("9999 geht", rech("ld 9998\nadd 1") === 9999); pruefe("mul Überlauf", /Zahlenbereich/.test(lauf("ld 100\nmul 100\nend").lzf));
pruefe("div durch 0", /null/.test(lauf("ld 1\ndiv 0\nend").lzf)); pruefe("mod durch 0", /null/.test(lauf("in a\nld 1\nmod a\nend", [0]).lzf));
pruefe("Sprung ohne Vergleich zur Laufzeit", /cmp/.test(lauf("jmp #3\ncmp 1\njeq #4\nend").lzf));
const vgl = (a, b, j) => lauf(`ld ${a}\ncmp ${b}\n${j} ja\nout 0\njmp e\nout 1 :ja\nend :e`).aus[0];
pruefe("jlt", vgl(1, 2, "jlt") === 1 && vgl(2, 2, "jlt") === 0 && vgl(3, 2, "jlt") === 0);
pruefe("jeq", vgl(1, 2, "jeq") === 0 && vgl(2, 2, "jeq") === 1 && vgl(3, 2, "jeq") === 0);
pruefe("jgt", vgl(1, 2, "jgt") === 0 && vgl(2, 2, "jgt") === 0 && vgl(3, 2, "jgt") === 1);
const rc = lauf("ld 5\ncmp 3\nst a\nout a\nend"); pruefe("cmp lässt Akku unverändert", rc.aus[0] === 5 && rc.m.vgl === ">");
pruefe("out Wert", gleich(lauf("out 42\nout -3\nend").aus, [42, -3]));
pruefe("in wartet", lauf("in a\nend", []).wartet === true);
pruefe("alle Datenzellen", gleich(lauf("ld 1\nst a\nadd 1\nst b\nadd 1\nst c\nadd 1\nst d\nadd 1\nst e\nadd 1\nst f\nadd 1\nst g\nadd 1\nst $71\nend").m.daten, [1, 2, 3, 4, 5, 6, 7, 8]));
const m0 = new Rechner([]); pruefe("Startzustand", m0.pc === 0 && m0.acc === 0 && m0.vgl === "" && m0.daten.every(v => v === 0));

// ---------- M13–M15, E3: Schritte ----------
const sch = lauf("in a\nadd a\nend", [7]).schritte;
const add = sch.filter(s => true).slice(sch.findIndex((s, i) => i > 3 && s.ph === "F"));
pruefe("Holen hat 3 Schritte, dann Dekodieren", gleich(add.slice(0, 4).map(s => s.ph), ["F", "F", "F", "D"]));
pruefe("add a: 5 Ausführungsschritte", add.filter(s => s.ph === "X").length === 5 + 1, String(add.filter(s => s.ph === "X").length));
for (const q of [alle.replace(/jmp #1\njlt #1\njeq #1\njgt #1/, "jlt #23\njeq #23\njgt #23\njmp #23")]) {
  const R = lauf(q, [1]), s = R.schritte; let proBefehl = 0, max = 0, enden = 0;
  for (const x of s) { if (x.einfach && !x.eingabe) proBefehl++; if (x.ende) { max = Math.max(max, proBefehl); proBefehl = 0; enden++; } }
  pruefe("einfach: höchstens 2 Animationen je Befehl", max === 2, String(max));
  pruefe("jeder Befehl endet mit ende", enden === R.pcs.length && enden >= 19, String(enden));
  pruefe("jeder Schritt hat Text", s.every(x => x.txt && (!x.einfach || x.stxt || x.txt)));
}
// Endlosschleife bleibt abbrechbar
pruefe("Endlosschleife läuft begrenzt", lauf("jmp #1\nend", [], 5000).n >= 5000);

console.log(`\n${ok} Prüfungen bestanden, ${schlecht} fehlgeschlagen.`);
process.exit(schlecht ? 1 : 0);
