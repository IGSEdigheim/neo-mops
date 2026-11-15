#!/usr/bin/env python3
"""Prüft die Oberfläche von Neo-MOPS in einem echten Firefox (ohne Fenster):  python3 tests/oberflaeche.py
Braucht mn.py aus dem Skill lernsimulation. Getestet wird an einer Kopie in einem temporären Ordner."""
import json, os, shutil, sys, tempfile, time
sys.path.insert(0, os.path.expanduser("~/.claude/skills/lernsimulation/scripts"))
from mn import FF, STRG, UMSCHALT

HIER = os.path.dirname(os.path.abspath(__file__))
ENTER, F5, F6, ESC = "", "", "", ""
tmp = tempfile.mkdtemp(prefix="neomops", dir=os.environ.get("TMPDIR"))
shutil.copy(os.path.join(HIER, "..", "index.html"), tmp)
# Nachgebautes Moodle: Rahmenseite mit SCORM-Schnittstelle, die alles mitschreibt
open(os.path.join(tmp, "moodle.html"), "w").write("""<!DOCTYPE html><meta charset=utf-8><script>
var D = JSON.parse(localStorage.getItem('lms') || '{"cmi.core.student_id":"s1"}'), LOG = [];
var API = { LMSInitialize: () => "true", LMSFinish: () => "true", LMSCommit: () => { localStorage.setItem('lms', JSON.stringify(D)); return "true"; },
  LMSGetValue: k => D[k] || "", LMSSetValue: (k, v) => { D[k] = v; LOG.push(k); return "true"; }, LMSGetLastError: () => "0", LMSGetErrorString: () => "", LMSGetDiagnostic: () => "" };
</script><iframe src="index.html" style="position:fixed;inset:0;width:100%;height:100%;border:0"></iframe>""")
URL = "file://" + tmp + "/index.html"

gut = schlecht = 0
def pruefe(name, bed, info=""):
    global gut, schlecht
    if bed: gut += 1
    else: schlecht += 1; print("FEHLER:", name, info)

ff = FF(); P = ff.page
def bis(bed, t=25):
    for _ in range(int(t / 0.05)):
        if P("return !!(" + bed + ")"): return True
        time.sleep(0.05)
    print("FEHLER: Zeit abgelaufen bei", bed); return False
def lade(url=URL, leer=True):
    ff.go(url); time.sleep(0.4)
    if leer: ff.js("localStorage.clear()"); ff.go(url); time.sleep(0.4)
    P("window.__err=[]; addEventListener('error',e=>__err.push(e.message)); addEventListener('unhandledrejection',e=>__err.push(String(e.reason)))")
def quelle(text): P("ladeQuelltext(%s)" % json.dumps(text))
def eingabe(v): bis("lauf==='eingabe'"); ff.type("#einFeld", str(v)); ff.keys(ENTER)
def tippe(text):   # echtes Tippen ins fokussierte Feld (ff.type leert vorher und nimmt dabei den Fokus weg)
    ff.keys(STRG, "a")
    for z in text: ff.keys(z)
def ruhe(): bis("!pumpt && lauf!=='laeuft'")
SICHTBAR = "(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0})"

try:
    lade(); ff.viewport(1366, 768)
    # ---------- Z3, Z5, L1: Datei ----------
    html = open(os.path.join(tmp, "index.html"), encoding="utf-8").read()
    pruefe("L1 Schalter in Zeile 6", html.split("\n")[5] == "const LEHRERMODUS = false;")
    pruefe("Z3 keine Fremddateien", not any(x in html for x in ['src="http', "href=\"http", "@import", "url(http"]))
    pruefe("Z5 kein Knopf Kodieren", "odieren" not in P("return document.body.innerText").replace("Dekodieren", ""))
    pruefe("Z4/L1 kein Knopf für den Lehrermodus", P("return [...document.querySelectorAll('button')].every(b=>!/lehrer/i.test(b.textContent+b.id))"))

    # ---------- Z7, U1: kein Scrollen der Seite, Zeichnung im Fenster ----------
    for mode in ("ein", "adv"):
        P("setzeAnsicht('%s')" % mode)
        for w, h in ((1000, 600), (1280, 620), (1366, 768), (1600, 900), (1920, 1080)):
            ff.viewport(w, h); time.sleep(0.25)
            m = P("const d=document.documentElement, s=document.getElementById('svg').getBoundingClientRect(), k=document.querySelector('.steuer').getBoundingClientRect();"
                  "return [d.scrollWidth<=innerWidth, d.scrollHeight<=innerHeight, s.right<=innerWidth && s.bottom<=innerHeight && s.height>250, k.bottom<=innerHeight, k.height<70,"
                  "[...document.querySelectorAll('.steuer > *')].filter(e=>getComputedStyle(e).display!=='none').every(e=>e.getBoundingClientRect().right<=k.right+1)]")
            pruefe(f"Z7 {mode} {w}x{h}: kein Scrollen, alles sichtbar, Steuerleiste einzeilig", all(m), str(m))
    ff.viewport(1366, 768)

    # ---------- E1, E2: einfache Ansicht ----------
    P("setzeAnsicht('ein')")
    pruefe("E1 keine Zusatzregister", P("return !K.opd && !K.erg && !K.alu && !K.pillen && !!K.pc && !!K.ir && !!K.acc && !!K.vgl && !!K.ein && !!K.aus"))
    pruefe("E1 Schrittweite und Ausgabestopp verborgen", P("return getComputedStyle(document.getElementById('gran').parentNode).display==='none' && getComputedStyle(document.getElementById('ausStopp').parentNode).display==='none'"))
    pruefe("E2 Programmzellen lesbar", P("return K['mem:3'].txt.textContent") == "add b")
    quelle("in a\nld a :m\nsub 1\ncmp 0\njgt m\nend")
    pruefe("E2 Sprung mit Zieladresse", P("return K['mem:4'].txt.textContent") == "jgt 01")

    # ---------- U2–U4, A13: Editor und Meldungen ----------
    quelle("in a\nlad a\nend")
    pruefe("U3 Fehler gemeldet", P("return document.getElementById('chip').textContent") == "1 Fehler" and "Meintest du „ld“" in P("return document.getElementById('meld').textContent"))
    pruefe("U2 fehlerhafte Zeile markiert", P("return [...document.querySelectorAll('#farbe .z')].map(z=>z.classList.contains('err'))") == [False, True, False] and P("return document.querySelectorAll('#rinne .err').length") == 1)
    pruefe("U4 Start gesperrt", P("return document.getElementById('startBtn').disabled && document.getElementById('schrittBtn').disabled"))
    ff.click("#meld button"); pruefe("U3 Klick springt in die Zeile", P("const s=document.getElementById('src'); return s.value.slice(s.selectionStart,s.selectionEnd)") == "lad a")
    ff.click("#src"); ff.js("document.getElementById('src').select()"); ff.cmd("WebDriver:ElementSendKeys", {"id": ff.find("#src"), "text": "ld 5\nst a\nout a\nend"})
    pruefe("Z5 Tippen übersetzt sofort", P("return [U.ok, U.zellen.length, document.getElementById('chip').textContent]") == [True, 4, "✓ 4 Befehle"])
    pruefe("U2 Farben", P("return ['t-k','t-n','t-v'].every(c=>document.querySelector('#farbe .'+c))"))
    ff.js("document.getElementById('src').select()"); ff.cmd("WebDriver:ElementSendKeys", {"id": ff.find("#src"), "text": "fo"})
    pruefe("U3 Fehler erst nach Tipppause", P("return [U.ok, document.getElementById('chip').textContent]") == [False, "…"], str(P("return document.getElementById('chip').textContent")))
    time.sleep(1.1); pruefe("U3 Fehler nach Tipppause sichtbar", "Fehler" in P("return document.getElementById('chip').textContent"))
    quelle("ld 1\nst a :x\nend\nld 2")
    pruefe("A11 Warnungen angezeigt", P("return document.querySelectorAll('#meld .wrn').length") == 2 and P("return U.ok"))
    quelle(""); pruefe("leerer Editor: Hinweis statt Fehler", P("return document.getElementById('chip').textContent") == "leer" and P("return document.querySelectorAll('#meld .err').length") == 0)

    # ---------- E3, E4, U7–U9, N1, N2, N4: Lauf in der einfachen Ansicht ----------
    P("ladeQuelltext(BEISPIELE[0].src); Z.tempo=2")
    ff.click("#schrittBtn"); time.sleep(0.5)
    tok = P("const t=document.querySelector('.tok'); return t ? [t.getAttribute('transform'), document.querySelectorAll('.trace').length, document.querySelectorAll('.reg.quelle').length, t.textContent] : null")
    pruefe("N1 Marke wandert über leuchtende Leitung", bool(tok) and tok[1] >= 1 and tok[3] == "in a", str(tok))
    pruefe("N2 Quelle hervorgehoben", bool(tok) and tok[2] == 1)
    time.sleep(0.12); pruefe("N1 Marke bewegt sich", P("const t=document.querySelector('.tok'); return t && t.getAttribute('transform')") != (tok or [0])[0])
    pruefe("U2 bearbeitete Zeile markiert", P("return [...document.querySelectorAll('#farbe .z')].findIndex(z=>z.classList.contains('cur'))") == 1)
    eingabe("abc"); pruefe("U8 falsche Eingabe abgelehnt", P("return lauf==='eingabe' && /ganze Zahl/.test(document.getElementById('text').textContent)"))
    ff.type("#einFeld", "10000"); ff.keys(ENTER); pruefe("U8 zu große Eingabe abgelehnt", P("return lauf") == "eingabe")
    pos = P("const a=document.getElementById('einFeld').getBoundingClientRect(), b=K.ein.box.getBoundingClientRect(); return [Math.abs(a.left-b.left)<6, Math.abs(a.top+a.height/2-b.top-b.height/2)<6, document.activeElement.id]")
    pruefe("U8 Eingabefeld am Eingaberegister mit Fokus", pos == [True, True, "einFeld"], str(pos))
    ff.type("#einFeld", "3"); ff.keys(ENTER); ruhe()
    pruefe("E3 Schritt = genau ein Befehl", P("return [M.anzahl, M.pc, M.daten[0], lauf]") == [1, 1, 3, "pause"], str(P("return [M.anzahl, M.pc, M.daten[0], lauf]")))
    z = P("return [K.zeiger.style.transform, K.zpos[1]]"); pruefe("N4 Zeiger steht an der Zelle des Befehlszählers", z[0].replace(" ", "") == f"translate({z[1][0]}px,{z[1][1]}px)", str(z))
    P("Z.tempo=5"); ff.click("#schrittBtn"); eingabe(4); ruhe(); ff.click("#schrittBtn"); ruhe(); ff.click("#schrittBtn"); ruhe()
    pruefe("E4 Erklärzeile mit Werten", "add b: 3 + 4 = 7" in P("return document.getElementById('text').textContent"), P("return document.getElementById('text').textContent"))
    pruefe("E4 Rechnung neben dem Akku", P("return K.rechnung.textContent") == "3 + 4 = 7" and P("return K.acc.txt.textContent") == "7")
    ff.click("#startBtn"); bis("lauf==='ende'")
    pruefe("U9 Ausgabe und Ende", P("return [M.ausgaben, K.aus.txt.textContent, /Fertig/.test(document.getElementById('text').textContent)]") == [[7], "7", True])
    pruefe("Knopf heißt Neu starten", "Neu starten" in P("return document.getElementById('startBtn').textContent"))
    ff.click("#resetBtn"); pruefe("M12 Zurücksetzen", P("return [lauf, M.pc, M.acc, M.vgl, M.ausgaben.length]") == ["bereit", 0, 0, "", 0])
    quelle("out 1\nout 2\nout 3\nend"); ff.click("#startBtn"); bis("lauf==='ende'")
    pruefe("U9 Verlauf der Ausgaben", P("return K.verlauf.textContent") == "Verlauf: 1 · 2 · 3")

    # ---------- N3: Pause mitten in der Bewegung ----------
    P("ladeQuelltext('ld 5\\nst a\\nend'); Z.tempo=1"); ff.click("#startBtn"); time.sleep(0.6); ff.click("#startBtn")
    a = P("return [lauf, document.querySelector('.tok') && document.querySelector('.tok').getAttribute('transform')]"); time.sleep(0.4)
    b = P("return document.querySelector('.tok') && document.querySelector('.tok').getAttribute('transform')")
    pruefe("N3 Pause friert die Marke ein", a[0] == "pause" and a[1] and a[1] == b, str([a, b]))
    ff.click("#startBtn"); time.sleep(0.3); pruefe("N3 Weiter setzt die Bewegung fort", P("const t=document.querySelector('.tok'); return !t || t.getAttribute('transform')") != b)
    P("Z.tempo=5"); bis("lauf==='ende'"); pruefe("N3 Tempo wirkt sofort", P("return M.daten[0]") == 5)

    # ---------- N5: Sofort und Endlosschleife ----------
    P("ladeQuelltext('ld 0\\nadd 1 :m\\nsub 1\\njmp m\\nend'); Z.tempo=5"); ff.click("#startBtn"); time.sleep(0.6)
    n1 = P("return M.anzahl"); time.sleep(0.3); n2 = P("return M.anzahl")
    pruefe("N5 Endlosschleife läuft, Seite bleibt bedienbar", n2 > n1 > 1000 and P("return lauf") == "laeuft", str([n1, n2]))
    ff.click("#startBtn"); time.sleep(0.2); n3 = P("return M.anzahl"); time.sleep(0.2)
    pruefe("N5 Pause hält die Schleife an", P("return [lauf, M.anzahl===%d]" % n3) == ["pause", True])
    ff.click("#resetBtn"); pruefe("N5 Zurücksetzen bricht ab", P("return [lauf, M.anzahl, pumpt]") == ["bereit", 0, False])

    # ---------- M9: Laufzeitfehler ----------
    quelle("ld 9999\nadd 1\nend"); ff.click("#startBtn"); bis("lauf==='fehler'")
    pruefe("M9 Überlauf wird gemeldet", P("return document.getElementById('zeile').classList.contains('fehler') && /Zahlenbereich/.test(document.getElementById('text').textContent)"))
    quelle("ld 1\ndiv 0\nend"); ff.click("#startBtn"); bis("lauf==='fehler'"); pruefe("M9 Division durch null", "null" in P("return document.getElementById('text').textContent"))

    # ---------- F1–F3, M13–M15: fortgeschrittene Ansicht ----------
    ff.click("#modAdv")
    pruefe("F1 alle Bauteile", P("return ['pc','ir','dek','opd','acc','alu','erg','vgl','ein','aus'].every(n=>K[n]) && K.zellenZahl===64 && !!K['mem:71'] && document.querySelectorAll('.pille').length===3 && /Adressbus/.test(document.getElementById('svg').textContent)"))
    P("ladeQuelltext('in a\\nadd a\\nout a\\nend'); Z.tempo=5")
    pruefe("F1/M2 Maschinencode in den Zellen", P("return [K['mem:0'].txt.textContent, K['mem:1'].txt.textContent, K['mem:3'].txt.textContent, K['mem:4'].txt.textContent]") == ["20 0064", "30 0064", "60 0000", "00 0000"])
    pruefe("F2/F3 Schrittweite und Ausgabestopp sichtbar", P(f"return {SICHTBAR}(document.getElementById('gran')) && {SICHTBAR}(document.getElementById('ausStopp'))"))
    ff.js("const g=document.getElementById('gran'); g.value='mikro'; g.dispatchEvent(new Event('change'))")
    ff.click("#schrittBtn"); ruhe(); pruefe("M13 Mikroschritt 1: Adresse an den Speicher", P("return [M.sel, M.ir, M.pc, phase]") == [0, None, 0, "F"])
    ff.click("#schrittBtn"); ruhe(); pruefe("M13 Mikroschritt 2: Zelle ins Befehlsregister", P("return [M.ir.op, M.pc, K.ir.txt.textContent, K.irArg.txt.textContent]") == [20, 0, "20", "0064"])
    ff.click("#schrittBtn"); ruhe(); pruefe("M13/Z9 Mikroschritt 3: Befehlszähler + 1", P("return [M.pc, K.pc.txt.textContent]") == [1, "01"])
    ff.click("#schrittBtn"); ruhe(); pruefe("M14 Dekodierer in Worten", P("return [phase, K.dek.txt.textContent]") == ["D", "Lies eine Eingabe und speichere sie in a"])
    pruefe("F1 Phasenanzeige", P("return K.pillen.D.classList.contains('an') && !K.pillen.F.classList.contains('an')"))
    ff.js("const g=document.getElementById('gran'); g.value='befehl'; g.dispatchEvent(new Event('change'))")
    ff.click("#schrittBtn"); eingabe(6); ruhe(); pruefe("F2 Schrittweite Befehl", P("return [M.anzahl, M.daten[0], lauf]") == [1, 6, "pause"])
    ff.js("const g=document.getElementById('gran'); g.value='phase'; g.dispatchEvent(new Event('change'))")
    ff.click("#schrittBtn"); ruhe(); pruefe("F2 Phase: nach dem Holen", P("return [M.ir.op, M.pc, M.dek]") == [30, 2, ""])
    ff.click("#schrittBtn"); ruhe(); pruefe("F2 Phase: nach dem Dekodieren", P("return [M.dek, M.opd]") == ["Addiere den Wert von a zum Akku", 0])
    ff.js("const g=document.getElementById('gran'); g.value='mikro'; g.dispatchEvent(new Event('change'))")
    soll = [("M.sel", 64), ("M.opd", 6), ("M.alu", "+"), ("M.erg", 6), ("M.acc", 6)]
    for i, (was, wert) in enumerate(soll):
        ff.click("#schrittBtn"); ruhe(); pruefe(f"M15 add a, Schritt {i + 1}: {was}", P("return " + was) == wert, str(P("return " + was)))
    pruefe("M15 Anzeige im Rechenwerk", P("return [K.opd.txt.textContent, K.alu.txt.textContent, K.erg.txt.textContent, K.acc.txt.textContent]") == ["0006", "+", "0006", "0006"])
    ff.click("#resetBtn"); P("ladeQuelltext('out 1\\nout 2\\nend')"); ff.click("#ausStopp"); ff.click("#startBtn"); ruhe()
    pruefe("F3 Halt nach der ersten Ausgabe", P("return [lauf, M.ausgaben]") == ["pause", [1]])
    ff.click("#startBtn"); ruhe(); pruefe("F3 Halt nach der zweiten Ausgabe", P("return [lauf, M.ausgaben]") == ["pause", [1, 2]])
    ff.click("#ausStopp"); ff.click("#startBtn"); bis("lauf==='ende'")
    # Animation der Mikroschritte: Adressbus und Datenbus
    P("ladeQuelltext('ld a\\nend'); Z.tempo=2"); ff.click("#schrittBtn"); time.sleep(0.35)
    pruefe("N1 Adressbus-Marke", P("return !!document.querySelector('.tok.a') && !!document.querySelector('.trace.a')")); ruhe()
    ff.click("#schrittBtn"); time.sleep(0.35); pruefe("N1 Datenbus-Marke mit Befehlswort", P("const t=document.querySelector('.tok.d'); return t && t.textContent") == "10 0064"); ruhe()
    ff.click("#resetBtn")

    # ---------- F2: Beschriftung des Schrittknopfs, F4: Busse, U5: Tempo „Schnell“ ----------
    for g, t in (("mikro", "1 Mikroschritt"), ("phase", "1 Phase"), ("befehl", "1 Befehl")):
        ff.js("const g=document.getElementById('gran'); g.value='%s'; g.dispatchEvent(new Event('change'))" % g)
        pruefe("F2 Schrittknopf heißt " + t, P("return document.getElementById('schrittBtn').textContent.trim()") == t)
    kreuz = P("""const seg=[]; for(const b of ['a','d']) for(const p of document.querySelectorAll('#svg .bus.'+b)){const n=p.getAttribute('d').match(/-?[\\d.]+/g).map(Number);
      const pts=[]; for(let i=0;i<n.length;i+=2) pts.push([n[i],n[i+1]]); for(let i=1;i<pts.length;i++) seg.push([b,pts[i-1],pts[i]]);}
      let k=0; for(const [b1,p,q] of seg) for(const [b2,r,s] of seg){ if(b1>=b2) continue;
        const d=(a,b,c)=>(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]); if(d(p,q,r)*d(p,q,s)<0 && d(r,s,p)*d(r,s,q)<0) k++; } return [k, seg.length]""")
    pruefe("F4 Adress- und Datenbus kreuzen sich nicht", kreuz[0] == 0 and kreuz[1] > 8, str(kreuz))
    P("ladeQuelltext('ld 40\\nsub 1 :m\\ncmp 0\\njgt m\\nend'); Z.tempo=4; zeigeEinstellungen()"); ff.click("#startBtn"); time.sleep(1.0)
    n = P("return [M.anzahl, document.querySelectorAll('.tok').length, lauf]"); pruefe("U5 Schnell (fortgeschritten): mehrere Befehle je Sekunde, keine Marken", n[0] >= 5 and n[1] == 0 and n[2] == "laeuft", str(n))
    ff.click("#resetBtn"); ff.click("#modEin"); ff.click("#startBtn"); time.sleep(1.0)
    n = P("return [M.anzahl, document.querySelectorAll('.tok').length]"); pruefe("U5 Schnell (einfach): mindestens 6 Befehle je Sekunde", n[0] >= 6 and n[1] == 0, str(n))
    ff.click("#resetBtn"); ff.click("#modAdv")

    # ---------- U5, U6: Tasten ----------
    P("document.activeElement.blur(); ladeQuelltext('in a\\nout a\\nend'); Z.tempo=5")
    ff.keys(STRG, ENTER); pruefe("U6 Strg+Enter startet", bis("lauf==='eingabe'", 3)); eingabe(2); bis("lauf==='ende'")
    ff.keys(ESC); pruefe("U6 Esc setzt zurück", P("return lauf") == "bereit")
    P("Z.gran='befehl'"); ff.keys(F6); bis("lauf==='eingabe'", 3); ff.keys(ESC); pruefe("U6 F6 Schritt, Esc auch während der Eingabe", P("return [lauf, document.getElementById('eingabe').hidden]") == ["bereit", True])
    P("ladeQuelltext('ld 1 :m\\njmp m\\nend'); Z.tempo=1; document.activeElement.blur()"); ff.js("document.body.focus()")
    ff.keys(" "); time.sleep(0.3); pruefe("U6 Leertaste startet", P("return lauf") == "laeuft")
    ff.keys(" "); time.sleep(0.1); pruefe("U6 Leertaste pausiert", P("return lauf") == "pause")
    ff.click("#src"); ff.keys(" "); pruefe("U6 Leertaste im Editor tippt nur", P("return [lauf, document.getElementById('src').value.length]") == ["bereit", 18], str(P("return [lauf, document.getElementById('src').value, document.activeElement.id]")))
    ff.keys(STRG, ENTER); time.sleep(0.2); pruefe("U6 Strg+Enter startet aus dem Editor", P("return lauf") == "laeuft"); ff.keys(ESC)
    ff.js("const t=document.getElementById('tempo'); t.value=4; t.dispatchEvent(new Event('input'))")
    pruefe("U5 Temporegler", P("return [Z.tempo, document.getElementById('tempoTxt').textContent]") == [4, "Schnell"])

    # ---------- U10–U12: Beispiele, Hilfe, Design ----------
    P("ladeQuelltext(BEISPIELE[0].src)")
    ff.click("#bspBtn"); pruefe("U10 drei Beispiele, keine Lösungen", P("return document.querySelectorAll('#bspListe button').length") == 3)
    ff.click("#bspListe button:nth-child(2)"); pruefe("U10 Beispiel geladen", P("return U.ok && /größere/.test(document.getElementById('src').value)"))
    for i in range(3):
        P("ladeQuelltext(BEISPIELE[%d].src)" % i); pruefe(f"U10 Beispiel {i + 1} fehlerfrei", P("return U.ok && !U.warnungen.length"))
    pruefe("U10 Öffnen und Speichern vorhanden", P(f"return {SICHTBAR}(document.getElementById('oeffnenBtn')) && {SICHTBAR}(document.getElementById('speichernBtn')) && document.getElementById('datei').accept.includes('.ass')"))
    ff.click("#hilfeBtn"); pruefe("U11 Befehlsübersicht mit 15 Befehlen", P("return document.getElementById('hilfe').open && document.querySelectorAll('#hilfeInhalt tbody tr').length") == 15); ff.click("#hilfeZu")
    ff.click("#themaBtn"); pruefe("U12 dunkles Design", P("return document.documentElement.dataset.theme") == "dark")

    # ---------- S1: Speichern im Browser ----------
    P("ladeQuelltext('ld 42\\nend')"); time.sleep(0.5); lade(leer=False)
    pruefe("S1 Quelltext, Ansicht, Tempo und Design bleiben", P("return [Z.src, Z.mode, Z.tempo, document.documentElement.dataset.theme]") == ["ld 42\nend", "adv", 4, "dark"])
    ff.click("#themaBtn")

    # ---------- L1–L3: Lehrermodus ----------
    ff.keys(STRG, UMSCHALT, "L")
    pruefe("L1 Kürzel schaltet ein", P(f"return lehrer && {SICHTBAR}(document.getElementById('lehrerMarke')) && {SICHTBAR}(document.getElementById('tabProt'))"))
    ff.click("#bspBtn"); pruefe("L2 Lösungen im Menü", P("return document.querySelectorAll('#bspListe button').length") == 9)
    for i in range(6):
        P("ladeQuelltext(LOESUNGEN[%d].src)" % i); pruefe(f"L2 Lösung {i + 1} fehlerfrei", P("return U.ok"), str(P("return U.fehler")))
    ff.click("#bspListe button:nth-child(10)"); P("Z.tempo=5")
    ff.click("#startBtn"); eingabe(12); eingabe(18); bis("lauf==='ende'"); pruefe("L2 ggT-Lösung rechnet richtig", P("return M.ausgaben") == [6])
    ff.click("#tabProt"); pruefe("L2 Ablaufprotokoll", P("return document.querySelectorAll('#prot tbody tr').length === M.anzahl && M.anzahl>10 && document.querySelector('#prot tbody tr').children.length===14"))
    time.sleep(0.6); pruefe("L3 im Lehrermodus wird nichts gespeichert", "ld 42" in ff.js("return localStorage.getItem('neomops-1')"))
    ff.keys(STRG, UMSCHALT, "L")
    pruefe("L3 Ausschalten bringt den Schülerstand zurück", P(f"return [lehrer, Z.src, document.getElementById('src').value, !{SICHTBAR}(document.getElementById('lehrerMarke')), !document.getElementById('editor').hidden]") == [False, "ld 42\nend", "ld 42\nend", True, True])
    ff.click("#bspBtn"); pruefe("L2 Lösungen wieder weg", P("return document.querySelectorAll('#bspListe button').length") == 3); ff.keys(ESC)
    pruefe("keine JavaScript-Fehler", P("return __err") == [], str(P("return __err")))

    # ---------- Startwerte der Variablen, Dateien der Kollegin, ruhige Erklärzeile ----------
    lade(); ff.click("#modAdv"); quelle("ld a\nadd 1\nst b\nout b\nend"); P("Z.tempo=5; K['mem:64'].txt.id='tA'; K['mem:65'].txt.id='tB'")
    ff.click("#tA"); pruefe("M16 Klick auf a öffnet ein Feld mit dem Wert", P(f"return [{SICHTBAR}(document.getElementById('wert')), document.getElementById('wertFeld').value]") == [True, "0"])
    tippe("abc"); ff.keys(ENTER); pruefe("M16 Unsinn wird abgelehnt", P("return [document.getElementById('wert').hidden, M.daten[0]]") == [False, 0])
    tippe("41"); ff.keys(ENTER)
    pruefe("M16 Wert gesetzt", P("return [document.getElementById('wert').hidden, M.daten[0], K['mem:64'].txt.textContent, lauf]") == [True, 41, "0041", "bereit"])
    ff.click("#startBtn"); bis("lauf==='ende'"); pruefe("M16 Programm rechnet mit dem Wert", P("return M.ausgaben") == [42])
    ff.click("#resetBtn"); pruefe("M16 Zurücksetzen lässt den Datenspeicher stehen", P("return [lauf, M.acc, M.pc, M.daten[0], M.daten[1], document.getElementById('resetBtn').disabled]") == ["bereit", 0, 0, 41, 42, True])
    P("document.activeElement.blur()"); ff.keys(ESC); pruefe("M16 Esc löscht nichts", P("return M.daten.slice(0,2)") == [41, 42])
    P("src.value += '\\n'; quelltextGeaendert(true)"); pruefe("M16 Tippen im Editor lässt den Datenspeicher stehen", P("return M.daten.slice(0,2)") == [41, 42])
    ff.click("#startBtn"); bis("lauf==='ende'"); pruefe("M16 Neustart rechnet mit den alten Werten weiter", P("return [M.ausgaben, M.daten[1]]") == [[42], 42])
    ff.click("#tA"); ff.keys(ESC); pruefe("M16 Esc im Feld bricht ab", P("return [document.getElementById('wert').hidden, M.daten[0], lauf]") == [True, 41, "ende"])
    ff.click("#tA"); tippe("7"); ff.keys(ENTER); pruefe("M16 Ändern nach dem Ende lässt den Lauf stehen", P("return [lauf, M.daten[0], M.ausgaben]") == ["ende", 7, [42]])
    ff.click("#resetBtn"); P("Z.gran='befehl'"); ff.click("#schrittBtn"); ruhe(); ff.click("#tA"); tippe("-5"); ff.keys(ENTER)
    pruefe("M16 Ändern in der Pause", P("return [lauf, M.daten[0], M.acc]") == ["pause", -5, 7])
    ff.click("#startBtn"); time.sleep(0.05); ff.click("#tB"); pruefe("M16 kein Ändern im Lauf", P("return lauf==='laeuft' ? document.getElementById('wert').hidden : true"))
    bis("lauf==='ende'"); ff.click("#resetBtn")
    P("""const dt=new DataTransfer(); dt.items.add(new File([JSON.stringify({format:'mops-offline-project',version:1,source:'in a\\nin b\\nld a\\nadd b\\nst c\\nout c\\nend',startData:[8,0,0,0,0,0,1,0]})],'addition.mops.json'));
      src.value=BEISPIELE[0].src; const d=document.getElementById('datei'); d.files=dt.files; d.dispatchEvent(new Event('change'))"""); time.sleep(0.4)
    pruefe("E5 Projektdatei der Kollegin geladen", P("return [Z.src.split('\\n').length, U.ok, M.daten.join(',')]") == [7, True, "8,0,0,0,0,0,1,0"])
    P("ladeQuelltext(BEISPIELE[0].src)"); pruefe("M16 ein anderes Programm findet die alten Werte vor", P("return M.daten.join(',')") == "8,0,0,0,0,0,1,0")
    P("Z.tempo=1; Z.gran='mikro'"); ff.click("#schrittBtn"); time.sleep(0.2)
    links = set()
    for _ in range(14):
        ruhe(); links.add(round(P("return document.getElementById('text').getBoundingClientRect().left"))); P("Z.tempo=5"); ff.click("#schrittBtn")
        if P("return lauf==='eingabe'"): break
    pruefe("U14 Erklärtext steht still, wenn die Phase wechselt", len(links) == 1 and P("return document.getElementById('phase').scrollWidth <= document.getElementById('phase').clientWidth"), str(links))
    ff.click("#resetBtn"); pruefe("keine JavaScript-Fehler (Startwerte)", P("return __err") == [], str(P("return __err")))

    # ---------- Griff: Breite des Programmbereichs ----------
    lade(); ff.viewport(1600, 900); time.sleep(0.3)
    LB = "Math.round(document.querySelector('.links').getBoundingClientRect().width)"
    b0 = P("return " + LB); gx, gy = P("const r=document.getElementById('griff').getBoundingClientRect(); return [Math.round(r.left+r.width/2), Math.round(r.top+r.height/2)]")
    def ziehe(dx):
        x, y = P("const r=document.getElementById('griff').getBoundingClientRect(); return [Math.round(r.left+r.width/2), Math.round(r.top+r.height/2)]")
        dx = max(2, min(P("return innerWidth") - 2, x + dx)) - x   # die Maus bleibt im Fenster
        ff.cmd("WebDriver:PerformActions", {"actions": [{"type": "pointer", "id": "maus", "parameters": {"pointerType": "mouse"}, "actions": [
            {"type": "pointerMove", "x": x, "y": y, "duration": 0}, {"type": "pointerDown", "button": 0},
            {"type": "pointerMove", "x": x + dx // 2, "y": y, "duration": 60}, {"type": "pointerMove", "x": x + dx, "y": y, "duration": 60}, {"type": "pointerUp", "button": 0}]}]})
        ff.cmd("WebDriver:ReleaseActions"); time.sleep(0.2)
    ziehe(200); pruefe("U15 Griff verbreitert den Programmbereich", P("return [" + LB + ", Z.breite]") == [b0 + 200, b0 + 200], str(P("return [" + LB + ", Z.breite]")))
    ziehe(-2000); pruefe("U15 kleinste Breite 200", P("return " + LB) == 200)
    ziehe(3000); r = P("const s=document.querySelector('.steuer'), z=document.getElementById('szene').getBoundingClientRect(); return [Math.round(document.querySelector('.rechts').getBoundingClientRect().width), s.scrollWidth<=s.clientWidth, document.documentElement.scrollWidth<=innerWidth, Z.breite===" + LB + "]")
    pruefe("U15 rechts bleibt genug Platz", r[0] >= 690 and r[1] and r[2] and r[3], str(r))
    ff.click("#modAdv"); time.sleep(0.3)
    for w in (1000, 1100, 1250, 1300, 1500, 1600, 1920):
        ff.viewport(w, 800); time.sleep(0.25)
        r = P("const s=document.querySelector('.steuer'); return [s.scrollWidth<=s.clientWidth, document.documentElement.scrollWidth<=innerWidth, [...s.children].every(e=>e.getBoundingClientRect().right<=s.getBoundingClientRect().right+0.5)]")
        pruefe(f"U15 Steuerleiste passt bei breitestem Programmbereich ({w}px)", all(r), str(r))
    ff.viewport(1600, 900); time.sleep(0.3); time.sleep(0.4); ff.go(URL); time.sleep(0.6)
    pruefe("U15 Breite wird gemerkt", P("return Z.breite > 300 && " + LB + " === Z.breite"))
    P("document.getElementById('griff').dispatchEvent(new MouseEvent('dblclick', {bubbles: true}))"); pruefe("U15 Doppelklick stellt zurück", P("return [Z.breite, " + LB + "]") == [0, b0])

    # ---------- S2: Moodle ----------
    ff.go("file://" + tmp + "/moodle.html"); time.sleep(0.6); ff.js("localStorage.clear()"); ff.go("file://" + tmp + "/moodle.html"); time.sleep(0.8)
    ff.cmd("WebDriver:SwitchToFrame", {"id": 0})
    pruefe("S2 Status incomplete", ff.js("return parent.D['cmi.core.lesson_status']") == "incomplete")
    pruefe("S2 Speicher je Schüler", P("return STORE") == "neomops-1-s1")
    P("ladeQuelltext('ld 7\\nst a\\nout a\\nend'); Z.tempo=5"); time.sleep(2)
    sd = ff.js("return parent.D['cmi.suspend_data']"); pruefe("S2 Stand in suspend_data", bool(sd) and json.loads(sd)["src"].startswith("ld 7"), str(sd))
    ff.click("#startBtn"); bis("lauf==='ende'"); time.sleep(2)
    pruefe("S2 nach dem ersten Lauf completed", ff.js("return parent.D['cmi.core.lesson_status']") == "completed")
    P("ladeQuelltext('; ' + 'x'.repeat(4100) + '\\nend')"); time.sleep(2)
    pruefe("S2 zu langer Quelltext bleibt nur im Browser", len(ff.js("return parent.D['cmi.suspend_data']")) <= 4000 and len(ff.js("return localStorage.getItem('neomops-1-s1')")) > 4000)
    ff.cmd("WebDriver:SwitchToParentFrame")
    ff.js("localStorage.removeItem('neomops-1-s1'); D['cmi.suspend_data']=JSON.stringify({src:'ld 3\\nend',mode:'adv',t:Date.now()}); API.LMSCommit('')")
    ff.go("file://" + tmp + "/moodle.html"); time.sleep(0.8); ff.cmd("WebDriver:SwitchToFrame", {"id": 0})
    pruefe("S2 Stand aus Moodle auf neuem Gerät", P("return [Z.src, Z.mode]") == ["ld 3\nend", "adv"])
finally:
    ff.close(); shutil.rmtree(tmp, ignore_errors=True)
print(f"\n{gut} Prüfungen bestanden, {schlecht} fehlgeschlagen.")
sys.exit(1 if schlecht else 0)
