#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AFTERHOURS – Kapitel: Die Reservierung
Interaktive Superhelden-Geschichte in Vesper City (Text-Adventure).
Nur Python-Standardbibliothek (3.8+).  Start:  python afterhours.py
"""
import json
import os
import random
import sys
import textwrap

SAVE = "afterhours_save.json"
W = 80
os.system("")  # ANSI-Farben auch unter Windows aktivieren


def _f(code, t):
    return f"\033[{code}m{t}\033[0m"


bold = lambda t: _f("1", t)
dim = lambda t: _f("2", t)
red = lambda t: _f("31", t)
green = lambda t: _f("32", t)
yellow = lambda t: _f("33", t)
cyan = lambda t: _f("36", t)

# ───────────────────────────── Kanon-Daten ─────────────────────────────

TEAM = {
    "Daniel": "Daniel Mercer / Recoil",
    "Mara": "Mara Ortiz / Latch",
    "Nico": "Nico Bell / Skid",
    "Asha": "Asha Okafor / Hush",
    "Imani": "Imani Darrow / Switch",
    "Leila": "Leila Chen / Lifeline",
    "Juno": "Juno Park / Apex",
}
SKILL = {
    "Daniel": "nimmt kinetische Energie auf, gibt sie gerichtet ab",
    "Mara": "verankert berührte Objekte an ihrer Position",
    "Nico": "steuert Reibung: Halt oder Rutschfläche",
    "Asha": "dämpft und fokussiert Schall",
    "Imani": "lenkt oder unterbricht Strom über Leitungen",
    "Leila": "bioelektrische Stabilisierung per Berührung",
    "Juno": "kurzlebige Trittflächen, Überblick von oben",
}
ROLLEN_MORGEN = {"Fluchtwege": ["Nico", "Mara"], "Schutz": ["Daniel", "Leila"],
                 "Überblick": ["Juno", "Asha", "Imani"]}
ROLLEN_HALLE = {"Statik": ["Mara", "Daniel", "Asha"], "Wasser/Strom": ["Imani", "Nico"],
                "Rettung": ["Leila", "Juno"]}

MORGEN_ZEILE = {
    "Daniel": "Daniel steht am Hallentor, den Schock eines möglichen Rammversuchs schon im Körper gespeichert.",
    "Mara": "Mara verankert das Rolltor in offener Position – niemand kann sich einsperren oder aussperren.",
    "Nico": "Nico macht die Zufahrt für jedes Fluchtfahrzeug zur Rutschbahn.",
    "Asha": "Asha dämpft das Dröhnen des Tors und hört im Hof einen zweiten Motor anspringen.",
    "Imani": "Imani hält den Torantrieb unter Kontrolle, damit niemand die Halle von innen versiegeln kann.",
    "Leila": "Leila wartet hinter den Fahrzeugen, die Hände frei für jeden, der im Weg steht.",
    "Juno": "Juno liegt auf dem Dach der Gießerei und überblickt Hof und Zufahrt.",
}
HALLE_ZEILE = {
    "Daniel": "Daniel nimmt den herabrieselnden Putz als kinetische Last auf – Stück für Stück.",
    "Mara": "Mara verankert den Mittelträger der Zwischendecke an seiner jetzigen Position.",
    "Nico": "Nico macht die Kellertreppe griffig, wo das Wasser sie in eine Rutschbahn verwandelt hat.",
    "Asha": "Asha fokussiert den Schall und hört das Gebälk knacken, bevor es sichtbar wird.",
    "Imani": "Imani unterbricht den uralten Verteiler, bevor Wasser und Strom zueinanderfinden.",
    "Leila": "Leila bleibt dicht hinter dem Trupp, bereit, jeden zu stabilisieren.",
    "Juno": "Juno prüft von oben die Fluchtwege der Galerie, Tritt für Tritt.",
}
TOD_ZEILE = {
    "Daniel": "Daniel fängt die Last der stürzenden Decke auf – mehr, als er speichern kann.",
    "Mara": "Mara hält den Träger einen Atemzug länger, als sie sollte. Dann gibt der Boden unter ihr nach.",
    "Nico": "Nico rutscht im Wasser der Kellertreppe in die Dunkelheit. Halt gibt es dort keinen mehr.",
    "Asha": "Asha hört das Geräusch als Erste. Sie schafft es noch, die anderen zu warnen – sich selbst nicht.",
    "Imani": "Der Verteiler bricht durch, als Imani noch an der Leitung ist.",
    "Leila": "Leila hält einen Kollegen am Leben, bis die Decke fällt – und bleibt bei ihm.",
    "Juno": "Juno springt. Die Trittfläche trägt, die Landung nicht.",
}

FRAGEN = {
    "ev": "Wer steckt hinter dem Kürzel „E. V.“?",
    "org": "Wer hat Diebstahl und Transport der Glocke tatsächlich organisiert?",
    "dane": "Wusste Dane vor dem Diebstahl von einer rechtswidrigen Beschaffung?",
    "morrow": "Was wusste Elias Morrow über den Inhalt der Kiste?",
    "cairn": "Wusste jemand bei Cairn von der späteren Beschaffung?",
    "depot": "Wer fragte im Straßenbahndepot nach dem Reparaturzeichen?",
}


def neu():
    return {
        "phase": "intro", "uhr": 22 * 60 + 15, "slots": 3, "done": [], "tier": "",
        "fakten": {
            "glocke": "Die Hafenglocke wurde bei Kellan Rusk in einer Transportkiste sichergestellt und polizeilich gesichert.",
            "dane": "Marek Dane wurde am überwachten Übergabepunkt Tor 4 nach einem Fluchtversuch festgesetzt.",
            "halter": "Harborlight, Lagerplatz N-14: Eine maßgefertigte Holzhalterung passt zur Kiste der Glocke; Rechnung über „Sicherung und Umlagerung eines historischen Metallobjekts“, bezahlt über Danes Vermittlungscode im Namen von Morrow Acquisitions Services.",
            "cairn": "Cairn Maritime Holdings zahlte Corvin Daal sechs Tage vor dem Diebstahl 3.200 VC für „historische Objektidentifizierung – Katalog B-17“.",
        },
        "aussagen": {
            "voss": "Gerrit Voss (Harborlight): Die Lagerung organisierte ein „M. Dane“; Identität nicht geprüft, vom Inhalt nichts gewusst.",
            "morrow0": "Elias Morrow: habe nur eine Lagerung für einen Kunden organisiert, den Inhalt nicht gekannt.",
            "chat": "Chat auf Danes Telefon: Das Gegenüber schreibt „Ich habe dem Transport zugestimmt, nicht dem Diebstahl“ – Identität unbestätigt.",
        },
        "fragen": {k: ["offen", ""] for k in FRAGEN},
        "tot": [], "log": [], "ergebnis": "",
    }


# ───────────────────────────── Hilfsfunktionen ─────────────────────────────

def ask(prompt="> "):
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print("\nSpiel beendet.")
        sys.exit(0)


def pause():
    ask(dim("   ⏎ weiter "))
    print()


def say(text):
    for para in text.strip().split("\n"):
        print(textwrap.fill(para, W) if para.strip() else "")
    print()


def talk(who, text):
    print(textwrap.fill(f"{bold(who)}: „{text}“", W, subsequent_indent="    "))
    print()


def titel(sub):
    print("\n" + bold("█ AFTERHOURS") + f" – {sub}")
    print(dim("─" * W) + "\n")


def uhr(Z):
    return f"{Z['uhr'] // 60 % 24:02d}:{Z['uhr'] % 60:02d}"


def fakt(Z, k, t):
    if k not in Z["fakten"]:
        Z["fakten"][k] = t
        print(textwrap.fill(green("  ✚ Beweis: ") + t, W, subsequent_indent="    ") + "\n")


def aussage(Z, k, t):
    if k not in Z["aussagen"]:
        Z["aussagen"][k] = t
        print(textwrap.fill(yellow("  ✚ Aussage: ") + t, W, subsequent_indent="    ") + "\n")


def frage(Z, k, status, t=""):
    if Z["fragen"][k] == [status, t]:
        return
    Z["fragen"][k] = [status, t]
    print(textwrap.fill(cyan(f"  ◆ Frage [{status}]: ") + FRAGEN[k] + (f" → {t}" if t else ""),
                        W, subsequent_indent="    ") + "\n")


def ident(Z):
    return "mietvertrag" in Z["fakten"] or "halle" in Z["fakten"]


def ev_geklaert(Z):
    frage(Z, "ev", "geklärt", "Mieterin des Zielorts ist Elise Vardon (Cairn Maritime Holdings) – „E. V.“ damit hinreichend belegt. Ob sie vom Diebstahl wusste, ist offen.")
    if "daal" in Z["aussagen"]:
        frage(Z, "cairn", "teilweise", "Vardon beauftragte die Identifizierung persönlich, ließ nach dem Diebstahl erneut prüfen und mietete später das Zielobjekt – Mitwissen vor dem Diebstahl ist nicht belegt, der Verdacht verdichtet sich.")
    else:
        frage(Z, "cairn", "teilweise", "Eine Cairn-Führungskraft handelte nach dem Diebstahl privat – Mitwissen vorher nicht belegt.")


def akte(Z):
    def block(kopf, items, farbe):
        print("\n" + farbe(bold(kopf)))
        for t in items:
            print(textwrap.fill("• " + t, W, subsequent_indent="  "))
    print("\n" + bold("═" * 22 + " FALLAKTE: HAFENGLOCKE " + "═" * 22))
    block("BEWIESENE FAKTEN", Z["fakten"].values(), green)
    block("AUSSAGEN (nicht bewiesen)", Z["aussagen"].values(), yellow)
    print("\n" + red(bold("OFFENE FRAGEN")))
    for k, txt in FRAGEN.items():
        st, note = Z["fragen"][k]
        farbe = {"offen": red, "teilweise": yellow, "geklärt": green}[st]
        print(textwrap.fill(f"• [{farbe(st)}] {txt}" + (f" → {note}" if note else ""), W, subsequent_indent="  "))
    print()


def team(Z):
    print("\n" + bold("═══ MERCER UNIT ═══"))
    for k, n in TEAM.items():
        st = red("† gefallen    ") if k in Z["tot"] else green("einsatzbereit")
        print(f" {n:<24} {st}  {dim(SKILL[k])}")
    print(" Theo Alvarez / Relay     Einsatzunterstützung (nicht im Feld)")
    print(dim(" In Erinnerung: Priya Nair / Liminal.\n"))


def speichern(Z):
    with open(SAVE, "w", encoding="utf-8") as fh:
        json.dump(Z, fh, ensure_ascii=False, indent=1)
    print(green("  Spielstand gespeichert.\n"))


def choose(opts, Z, save=False):
    print()
    for i, o in enumerate(opts, 1):
        print(textwrap.fill(f"{bold(str(i))}) {o}", W, initial_indent="  ", subsequent_indent="     "))
    print(dim("\n  [a] Fallakte  [t] Team" + ("  [s] Speichern" if save else "") + "  [q] Beenden"))
    while True:
        e = ask("\n> ").strip().lower()
        if e.isdigit() and 1 <= int(e) <= len(opts):
            print()
            return int(e) - 1
        if e == "a":
            akte(Z)
        elif e == "t":
            team(Z)
        elif e == "s" and save:
            speichern(Z)
        elif e == "q":
            print("Bis zum nächsten Mal.")
            sys.exit(0)


def auswahl(Z, rollen, n=3):
    lebend = [k for k in TEAM if k not in Z["tot"]]
    n = min(n, len(lebend))
    say(f"Wähle {n} Einsatzkräfte. Profile: " +
        " · ".join(f"{r}: {', '.join(m for m in ms if m in lebend)}" for r, ms in rollen.items()))
    gew = []
    while len(gew) < n:
        frei = [k for k in lebend if k not in gew]
        ab = [r for r, ms in rollen.items() if any(m in gew for m in ms)]
        print(dim(f"  Gewählt: {', '.join(gew) or '–'} · abgedeckt: {', '.join(ab) or '–'}"))
        gew.append(frei[choose([f"{TEAM[k]} – {SKILL[k]}" for k in frei], Z)])
    return gew


# ───────────────────────────── Szenen ─────────────────────────────

def intro(Z):
    print(bold("\n   A F T E R H O U R S"))
    print(dim("   Vesper City · Eine interaktive Geschichte\n"))
    say("Du bist Daniel Mercer, genannt Recoil, 38, ehemaliger Eliteheld und Leiter der Mercer Unit – ein Team, das in der inoffiziellen Rangliste der Stadt irgendwo um Platz 38 von 40 herumdümpelt und trotzdem Dinge erledigt.")
    say("Bisher: Die gestohlene Hafenglocke ist wieder da. Kellan Rusk hatte sie in einer Transportkiste, Marek Dane lief am Tor 4 der Polizei in die Arme, und bei Harborlight Storage passte eine Holzhalterung exakt zur Kiste. Was fehlt, ist der Mensch am Ende der Kette.")
    say("Spielregeln: Wähle mit der Zahl. Mit a öffnest du die Fallakte, mit t das Team, mit s speicherst du (in der Lagebesprechung), mit q beendest du. Die Polizei führt den Fall – die Mercer Unit hilft nur, wenn Detective Wynn sie konkret anfragt.")
    pause()


def praesidium(Z):
    titel("Kapitel: Die Reservierung")
    print(cyan("  Präsidium Vesper · 22:15 Uhr\n"))
    say("Hinter der Glasscheibe sitzt Marek Dane, die Hände flach auf dem Tisch, neben ihm eine Anwältin, die seit vierzig Minuten kein Wort gesagt hat. Im Besprechungsraum nebenan breitet Detective Tarek Wynn Dispositionsprotokolle von Kaiweg Transport aus – freigegeben per Beschluss.")
    talk("Wynn", "Buchung 4471. Angelegt über Morrows Konto am Tag nach dem Diebstahl, 08:12 Uhr – rund anderthalb Stunden, nachdem das Museum den Einbruch gemeldet hat. Abholung morgen früh um 07:30 Uhr bei Harborlight, Lagerplatz N-14. Ziel: Weidenhof 7 am Nordring, ein Privatlager. Empfänger: ‚E. V.‘.")
    talk("Wynn", "Die Kisten aus N-14 liegen in der Asservatenkammer. Morgen früh stünde ein Transporter vor einem leeren Lagerplatz – oder ich lasse ihn fahren, mit einer Kiste, die nur so tut, als wäre sie schwer. Kontrollierte Lieferung. Das funktioniert aber nur, wenn ich weiß, wer am Zielort wartet.")
    talk("Wynn", "Ich habe Personal für drei Maßnahmen bis zum Morgengrauen. Die Entscheidungen treffe ich – aber ich frage dich, was du priorisieren würdest. Die Unit bleibt in Bereitschaft; wenn ich sie brauche, frage ich konkret an. Übrigens: Das Gebäudeamt führt Weidenhof 7 als baufällig, Obergeschoss gesperrt.")
    fakt(Z, "buchung", "Buchung 4471 (Kaiweg Transport): angelegt 08:12 Uhr am Tag nach dem Diebstahl, ca. 90 Minuten nach der Museumsmeldung; Abholung morgen 07:30 Uhr, Harborlight N-14 → Weidenhof 7 (Nordring); Empfänger „E. V.“.")
    fakt(Z, "amt", "Weidenhof 7 (alte Eisengießerei) gilt beim Gebäudeamt als baufällig; Obergeschoss gesperrt.")
    Z["phase"] = "hub"
    pause()


LEADS = {
    "mietvertrag": "Den Mietvertrag für Weidenhof 7 prüfen – Hausverwaltung und Grundbuch (Nachtbereitschaft)",
    "morrow": "Elias Morrow erneut vernehmen – Wynn hält ihm den Buchungszeitpunkt vor",
    "daal": "Corvin Daal vorladen und die Depot-Aufnahme mit ihm abgleichen",
    "halle": "⚠ Weidenhof 7 noch in der Nacht begehen – die Unit soll die Halle sichern (GEFÄHRLICH)",
    "dane": "Marek Dane vernehmen – gezielt mit dem Material, das bis dahin vorliegt",
}
ORDER = ["mietvertrag", "morrow", "daal", "halle", "dane"]


def lead_mietvertrag(Z):
    titel("Weidenhof 7")
    print(cyan(f"  {uhr(Z)} Uhr · Hausverwaltung, Nordring\n"))
    say("Das Grundbuchamt hat Nachtbereitschaft, die Hausverwaltung nicht – bis eine Streife den Verwalter Jens Holm aus dem Bett holt. Er erscheint im Anorak über dem Schlafanzug, einen Ordner unter dem Arm, der älter aussieht als er selbst.")
    talk("Holm", "Weidenhof 7, alte Eisengießerei. Erdgeschosshalle vermietet, Obergeschoss gesperrt, das Gutachten hängt am Tor. Neue Mieterin seit dem Tag nach dem Einbruch im Museum – unterschrieben um 16:40 Uhr, sechs Monate im Voraus bezahlt. Von einem Privatkonto.")
    talk("Wynn", "Name?")
    talk("Holm", "Elise Vardon. Privat, nicht über die Firma – aber ihre Visitenkarte steckt im Ordner: Cairn Maritime Holdings. Sie wollte Anlieferung früh am Morgen, ohne Besuchereintrag. Ich dachte: Sammlerin. Die sind eigen.")
    talk("Holm", "Und falls Sie heute Nacht rein wollen: vergessen Sie es. Im Keller steht das Wasser, die Verteiler sind von 1980, und die Zwischendecke hält nur, weil sie es gewohnt ist.")
    fakt(Z, "mietvertrag", "Mietvertrag Weidenhof 7: Mieterin Elise Vardon (privat; Visitenkarte Cairn Maritime Holdings), unterzeichnet am Tag nach dem Diebstahl um 16:40 Uhr, sechs Monate im Voraus vom Privatkonto bezahlt, Anlieferung „ohne Besuchereintrag“ gewünscht.")
    ev_geklaert(Z)


def lead_morrow(Z):
    titel("Vernehmungsraum 2")
    print(cyan(f"  {uhr(Z)} Uhr · Elias Morrow\n"))
    say("Elias Morrow sitzt sehr gerade, den Mantel gefaltet auf dem Schoß, als wäre das hier ein Beratungstermin. Sein Anwalt flüstert ihm etwas zu; Morrow winkt ab.")
    talk("Wynn", "Ihre Buchung 4471 wurde um 08:12 Uhr angelegt. Das Museum meldete den Einbruch um 06:40 Uhr. Das Radio berichtete um sieben.")
    talk("Morrow", "Ich höre morgens kein Radio.")
    talk("Wynn", "Sie fragen auch nicht, was in den Kisten ist.")
    talk("Morrow", "Das ist mein Geschäftsmodell, Herr Detective.")
    if ident(Z):
        talk("Wynn", "Weidenhof 7 ist an Elise Vardon vermietet, seit dem Tag nach dem Einbruch. Was hat Dane über ‚E. V.‘ gesagt?")
        say("Morrows Lächeln verrutscht um einen Millimeter. Sein Anwalt sagt ‚Keine Aussage‘, Morrow sagt: ‚Schon gut.‘")
        talk("Morrow", "Dane sprach von ‚der Käuferin‘. Sie wolle keine Namen in Papieren. Als ich gegen zehn von dem Einbruch hörte, dachte ich an die Glocke. Ich habe die Buchung nicht storniert – ich habe Dane angerufen. Er sagte: Verwechslung des Museums. Ich wollte ihm glauben. 2.400 VC Honorar machen das leicht.")
        aussage(Z, "morrow", "Morrow (bei Vorhalt des Mietvertrags): Dane sprach von „der Käuferin“, die „keine Namen in Papieren“ wolle; nach der Meldung gegen 10 Uhr habe er an die Glocke gedacht, die Buchung aber nicht storniert – Dane nannte es „Verwechslung des Museums“. Honorar: 2.400 VC.")
        frage(Z, "morrow", "teilweise", "Morrow hatte nach der Meldung zumindest einen Verdacht und buchte trotzdem – Kenntnis vor dem Diebstahl ist nicht belegt.")
    else:
        talk("Morrow", "Die Anweisung kam von Herrn Dane, über seinen Vermittlungscode. 2.400 VC für die Abwicklung. ‚E. V.‘ war ein Kürzel in einem Auftragsfeld. Mehr weiß ich nicht.")
        say("Der Anwalt beendet die Vernehmung. Wynn klappt die Mappe zu: ‚Er weiß mehr. Aber ohne Namen am Zielort hängt er sich nicht auf.‘")
        aussage(Z, "morrow_basic", "Morrow (ohne konkreten Vorhalt): Auftrag kam von Dane über den Vermittlungscode, 2.400 VC; „E. V.“ nur ein Kürzel; Inhalt der Kiste nie geprüft.")


def lead_daal(Z):
    titel("Brückgasse")
    print(cyan(f"  {uhr(Z)} Uhr · Corvin Daal\n"))
    say("Eine Streife holt Corvin Daal aus seinem Antiquitätenladen, in dem noch Licht brennt. Er kommt im Mantel über dem Schlafanzug, hält einen Aktenordner wie einen Schild vor der Brust und sagt auf dem ganzen Weg ins Präsidium kein Wort.")
    talk("Daal", "Ich habe nichts gestohlen. Ich identifiziere. Das ist ein legales Gewerbe, mit Rechnung und Umsatzsteuer.")
    say("Wynn legt das unscharfe Standbild aus dem Straßenbahndepot neben die Kopie des Kassenjournals, das der Depotverein noch am Abend herausgegeben hat: ein Verkauf um 16:52 Uhr, Vereinschronik, bar bezahlt. Die Aufnahme trägt den Zeitstempel 16:51 Uhr.")
    talk("Daal", "Das bin ich. Vier Tage vor dem Einbruch. Ich habe nach alten Hafenobjekten gefragt, nach dem Reparaturzeichen – drei Striche im Kreis. Weil ich dafür bezahlt wurde.")
    talk("Wynn", "Von wem?")
    talk("Daal", "Cairn. Genauer: von Elise Vardon, persönlich. Sie wollte wissen, ob das Zeichen unverwechselbar ist. Nach dem Einbruch rief sie noch einmal an: ‚gründlich vergleichen‘. Deshalb Quayline. Dane hat mich auf B-17 gebracht, ‚ein ernsthafter Interessent‘. Dass Vardon der Interessent war, habe ich mir gedacht. Von einem Diebstahl wusste ich nichts – sonst hätte ich nie eine Rechnung gestellt.")
    fakt(Z, "depot", "Depot-Kassenjournal (Verkauf 16:52 Uhr) und Überwachungsaufnahme (16:51 Uhr) passen zusammen; Corvin Daal bestätigt, die Person im Depot zu sein.")
    aussage(Z, "daal", "Daal: Der Cairn-Auftrag kam von Elise Vardon persönlich; sie fragte, ob das Zeichen „unverwechselbar“ sei, und bat nach dem Diebstahl um erneuten Vergleich (→ Quayline). Dane nannte einen „ernsthaften Interessenten“. Vom Diebstahl habe er nichts gewusst.")
    frage(Z, "depot", "geklärt", "Corvin Daal, im Rahmen des Cairn-Identifizierungsauftrags – Kassenjournal und Aussage stützen das.")
    if ident(Z):
        ev_geklaert(Z)
    else:
        frage(Z, "ev", "teilweise", "Verdacht: „E. V.“ = Elise Vardon – nicht belegt.")
        frage(Z, "cairn", "teilweise", "Der Cairn-Auftrag stammt von Elise Vardon persönlich; ob sie „E. V.“ ist, ist ungeklärt.")


def lead_dane(Z):
    titel("Vernehmungsraum 1")
    print(cyan(f"  {uhr(Z)} Uhr · Marek Dane\n"))
    a = Z["aussagen"]
    st = int(ident(Z)) + int("morrow" in a) + int("daal" in a)
    say("Marek Dane hat sich gefangen. Das Jackett hängt über der Stuhllehne, die Krawatte sitzt wieder, und neben ihm blättert seine Anwältin in einem Notizblock, auf dem nichts steht.")
    talk("Wynn", "‚Nach der Meldung darf sie nicht im Zollhof bleiben.‘ Das steht auf Ihrem Telefon. Nach der Meldung. Sie wussten also, dass die Glocke gestohlen war.")
    if st >= 2:
        say("Wynn legt nacheinander auf den Tisch, was die Nacht gebracht hat. Danes Anwältin hört auf zu blättern.")
        talk("Dane", "Gut. Ich sage es einmal, und Sie schreiben es auf. ‚E. V.‘ ist Elise Vardon. Sie wollte die Glocke – privat, nicht für Cairn. Ich sollte sie beschaffen. Beschaffen. Nicht stehlen.")
        talk("Dane", "Der Auftrag kam von jemandem, den ich nur als ‚Treuhänder‘ kenne: Messenger, kein Gesicht, bezahlt über meinen Vermittlungscode. Zuletzt schrieb er: ‚Objekt wird bereitgestellt.‘ Dass das ein Einbruch war, habe ich erst durch die Meldung begriffen.")
        talk("Wynn", "Und trotzdem haben Sie weitergemacht.")
        talk("Dane", "Ja. Rusk wollte nach der Meldung aussteigen. Ich habe ihn unter Druck gesetzt. Das war falsch – und strafbar, ich weiß.")
        aussage(Z, "dane", "Dane: „E. V.“ ist die Käuferin Elise Vardon (privat); er sollte „beschaffen“; Auftrag und Bezahlung kamen von einem unbekannten „Treuhänder“ per Messenger („Objekt wird bereitgestellt“); vom Einbruch habe er erst durch die Meldung erfahren; das Chat-Gegenüber war Rusk, den er danach unter Druck setzte.")
        frage(Z, "dane", "teilweise", "Dane räumt Mittäterschaft nach der Meldung ein und bestreitet Wissen vorher – der Messenger-Verlauf muss das stützen oder widerlegen.")
        frage(Z, "org", "teilweise", "Ein unbekannter „Treuhänder“ stellte das Objekt bereit – Identität und Einbrecher weiter offen.")
    elif st == 1:
        talk("Anwältin", "Mein Mandant bestätigt, B-17 an Herrn Daal weitergeleitet und eine Lagerung vermittelt zu haben. Von einem Diebstahl wusste er nichts. Weitere Angaben macht er nicht.")
        aussage(Z, "dane0", "Dane (über seine Anwältin): bestätigt Weitergabe von B-17 und Vermittlung der Lagerung; bestreitet Kenntnis eines Diebstahls; nennt keine Namen.")
    else:
        talk("Anwältin", "Mein Mandant äußert sich nicht zu Vorhalten ohne tragfähige Grundlage. Ich kündige Beschwerde an.")
        say("Draußen auf dem Flur sagt Wynn leise: ‚Zu früh. Wir hatten zu wenig in der Hand.‘")


def lead_halle(Z):
    titel("Weidenhof 7 – bei Nacht")
    print(cyan(f"  {uhr(Z)} Uhr · Nordring\n"))
    say("Die Gießerei liegt im Regen. Die Feuerwehr hat einen Zettel ans Tor geklebt: Betreten verboten. Wynn steht davor, die Kapuze tief im Gesicht.")
    talk("Wynn", "Wenn dort drin schon etwas für morgen vorbereitet ist, kann es bis 07:30 Uhr weg sein. Gefahr im Verzug – den Beschluss bekomme ich. Aber ich schicke keinen Beamten in diese Halle, bevor jemand Zwischendecke, Keller und Verteiler gesichert hat.")
    talk("Wynn", "Ich frage dich konkret an: Kann die Mercer Unit die Halle sichern, damit die Spurensicherung gefahrlos hinein kann? Ich sage es ehrlich – das ist kein Routineeinsatz. Es kann Tote geben. Auch bei euch.")
    say("Daniel kennt Zwischendecken. Er sagt es nicht laut.")
    if choose(["Ja – die Mercer Unit sichert die Halle  (GEFÄHRLICH: ausgewählte Teammitglieder können sterben)",
               "Nein – nicht ohne tragfähigen Plan; wir suchen einen anderen Weg"], Z) == 1:
        talk("Wynn", "Verstanden. Dann bleibt die Halle zu, bis es hell ist.")
        return False
    sel = auswahl(Z, ROLLEN_HALLE)
    cov = sum(any(m in sel for m in ms) for ms in ROLLEN_HALLE.values())
    p = max(0.10, 0.60 - 0.15 * cov)
    label = "hoch" if p >= 0.45 else "mittel" if p >= 0.3 else "gering"
    say(f"Abgedeckt: {cov} von 3 Gefahrenbereichen. Geschätztes Risiko: {label}.")
    pause()
    say("Der Trupp geht hinein. Wasser tropft von der Decke, irgendwo knackt Metall.")
    for m in sel:
        say(HALLE_ZEILE[m])
    if random.random() < p:
        k = 2 if (len(sel) > 1 and random.random() < 0.25) else 1
        opfer = random.sample(sel, k)
        say("Mitten in der Sicherung ändert sich das Geräusch im Gebälk.")
        for o in opfer:
            print(textwrap.fill(red(TOD_ZEILE[o]), W) + "\n")
            Z["tot"].append(o)
        Z["log"].append("Verlust in Weidenhof 7: " + ", ".join(TEAM[o] for o in opfer))
        if "Daniel" in opfer:
            Z["phase"] = "tot"
            return None
        say("Die Halle ist gesichert – zu einem Preis. Wynn sagt lange nichts. Dann geht die Spurensicherung hinein.")
    else:
        say("Es hält. Zentimeter für Zentimeter, aber es hält. Wynn nickt, und die Spurensicherung geht hinein – ihr bleibt draußen.")
    fakt(Z, "halle", "Weidenhof 7: Montagebock mit Gummipolster in Glockenform, Frachtschild „E. V. – Übergabe nach Prüfung“; daneben eine Mappe mit Kopie des Mietvertrags auf Elise Vardon (privat).")
    ev_geklaert(Z)
    return None


FUNKT = {"mietvertrag": lead_mietvertrag, "morrow": lead_morrow, "daal": lead_daal,
         "halle": lead_halle, "dane": lead_dane}


def hub(Z):
    while Z["slots"] > 0 and Z["phase"] == "hub":
        titel("Lagebesprechung")
        print(cyan(f"  {uhr(Z)} Uhr · noch {Z['slots']} Maßnahme(n) bis zur Lieferung um 07:30 Uhr\n"))
        if Z["done"]:
            talk("Wynn", "Was hat als Nächstes Vorrang?")
        else:
            talk("Wynn", "Wer ‚E. V.‘ ist, entscheidet, ob ich morgen früh jemanden festnehmen kann – oder nur zusehe, wie eine Buchung storniert wird. Was hat Vorrang?")
        avail = [k for k in ORDER if k not in Z["done"] and (k != "dane" or Z["done"])]
        k = avail[choose([LEADS[x] for x in avail], Z, save=True)]
        if FUNKT[k](Z) is False:
            continue
        Z["done"].append(k)
        Z["slots"] -= 1
        Z["uhr"] += 120
        if Z["phase"] == "hub":
            pause()


def punkte(Z):
    f, a = Z["fakten"], Z["aussagen"]
    p = 0
    if "mietvertrag" in f:
        p += 2
    if "halle" in f:
        p += 1 if "mietvertrag" in f else 2
    return p + int("morrow" in a) + int("daal" in a) + int("dane" in a)


def morgen(Z):
    titel("Kontrollierte Lieferung")
    Z["uhr"] = 5 * 60 + 40
    print(cyan("  05:40 Uhr · Weidenhof 7, Nordring\n"))
    say("Grauer Morgen über dem Nordring. Die alte Eisengießerei steht schwarz gegen den Himmel, das Rolltor einen Spalt offen. Wynn hat einen Kaiweg-Transporter organisiert: am Steuer ein Beamter in Arbeitskleidung, auf der Ladefläche eine Kiste voller Sandsäcke.")
    talk("Wynn", "Ich frage die Unit jetzt konkret an – drei Kräfte, drei Aufgaben: Fluchtwege an Tor und Zufahrt, Schutz für meine Leute, Überblick über Hof und Dach. Zugriff, Festnahme und Beweissicherung machen wir. Ihr sorgt dafür, dass dabei niemand zu Schaden kommt.")
    sel = auswahl(Z, ROLLEN_MORGEN)
    for m in sel:
        say(MORGEN_ZEILE[m])
    pts = punkte(Z)
    cov = {r: any(m in sel for m in ms) for r, ms in ROLLEN_MORGEN.items()}
    pause()
    if pts >= 4:
        Z["tier"] = "A"
        say("07:12 Uhr. Ein dunkler Wagen hält vor dem Tor. Elise Vardon steigt selbst aus – grauer Mantel, Handschuhe, in der Hand eine kleine Taschenlampe, als wolle sie ein Stück Geschichte begutachten. Der Transporter rollt rückwärts in die Halle. Sie wartet, bis die Kiste abgesetzt ist, tritt heran und hebt selbst den Deckel.")
        say("Sandsäcke. Sie erstarrt nur eine Sekunde. Dann tritt Wynn aus dem Schatten der Regale.")
        talk("Wynn", "Frau Vardon, Sie sind vorläufig festgenommen. Verdacht der Hehlerei.")
        talk("Vardon", "Ich möchte meinen Anwalt. Und ich möchte, dass etwas protokolliert wird: Ich habe diese Glocke nicht stehlen lassen.")
        talk("Wynn", "Ein Mietvertrag einen Tag nach der Meldung. Eine Cairn-Rechnung davor. Sie müssen mir erklären, wie sich das reimt.")
        talk("Vardon", "Das werde ich. Nicht hier.")
        Z["ergebnis"] = "Zugriff: Elise Vardon vorläufig festgenommen"
        fakt(Z, "festnahme", "Elise Vardon wurde am Zielort Weidenhof 7 vorläufig festgenommen (Verdacht der Hehlerei); ihr Telefon ist beschlagnahmt, die Auswertung angeordnet.")
        frage(Z, "cairn", "teilweise", "Vardon sitzt in Haft; ob sie vor dem Diebstahl von der Beschaffung wusste, ist weiter offen – das Telefon soll es zeigen.")
    elif pts >= 2:
        Z["tier"] = "B"
        say("07:20 Uhr. Elise Vardon kommt selbst – und sie kommt nicht allein: Ihr Anwalt steigt aus dem Fond, ruhig, mit Aktentasche. Als Wynn sich zu erkennen gibt, hebt sie die Hände, bevor er fragt.")
        talk("Vardon", "Ich begleite Sie freiwillig. Ich habe nichts zu verbergen – außer meiner Dummheit.")
        say("Im Präsidium sagt sie drei Stunden lang aus. Für eine Festnahme reicht die Lage nicht; sie verlässt das Haus mit ihrem Anwalt und einer Vorladung.")
        aussage(Z, "vardon", "Elise Vardon (freiwillig, Anwalt anwesend): Dane bot ihr die Glocke als Stück aus Privatbesitz an; die Museumsmeldung hielt sie für eine Verwechslung, was er bestätigte. Sie wollte nur einlagern, bis die Herkunft geklärt sei.")
        frage(Z, "cairn", "teilweise", "Vardon bestreitet Mitwissen; ein Gegenbeweis fehlt noch.")
        Z["ergebnis"] = "Befragung: Vardon bestreitet Mitwissen, nicht festgenommen"
    else:
        Z["tier"] = "C"
        say("06:51 Uhr. Der Disponent von Kaiweg Transport ruft Wynn an: Die Buchung 4471 sei soeben telefonisch storniert worden. Prepaid-Nummer, Funkzelle im Hafenbereich – der Anrufer nannte den Buchungscode korrekt.")
        say("Am Weidenhof 7 passiert nichts mehr. Niemand kommt. Der Transporter steht im Leerlauf vor der Halle.")
        talk("Wynn", "Wir sind einen Schritt zu spät. Aber den Code kannten nur Morrow, Dane und der Empfänger – oder jemand, dem einer von ihnen ihn gegeben hat.")
        fakt(Z, "storno", "Buchung 4471 wurde um 06:51 Uhr telefonisch storniert (Prepaid-Nummer, Funkzelle Hafenbereich); der Anrufer nannte den Buchungscode korrekt.")
        Z["ergebnis"] = "Fehlstart: Buchung storniert, Empfänger unbekannt"
        if not ident(Z):
            frage(Z, "ev", "offen", "Der Anrufer kannte den Code – er stammt aus dem engsten Umfeld.")
    if Z["tier"] in "AB":
        if not cov["Fluchtwege"]:
            say("Vardons Fahrer setzt rückwärts aus der Zufahrt, rammt einen Poller und flüchtet zu Fuß. Die Beamten holen ihn nach dreihundert Metern ein – ein Kollege stürzt dabei schwer.")
            Z["log"].append("Zwischenfall: Fahrer flüchtig, ein Beamter verletzt (keine Fluchtwegsicherung)")
        if not cov["Schutz"]:
            say("Beim Zugriff kippt ein Palettenregal. Ein Beamter wird eingeklemmt – Rippenbruch, er wird es überleben.")
            Z["log"].append("Zwischenfall: Beamter verletzt (kein Schutz)")
        if not cov["Überblick"]:
            say("Ein zweiter Mann, den niemand im Fond gesehen hat, verlässt die Halle durch den Hinterhof – mit einem Datenträger.")
            Z["log"].append("Zwischenfall: Mann mit Datenträger entkommen (kein Überblick)")
    pause()


WEITER = {
    "einbruch": ("Die Einbrecher aufspüren – Sanna Revik und Wynn gehen die Einbruchsspuren im Museum durch",
                 "Sanna Revik führt Wynn und dich durch die Sicherungsprotokolle des Stadtmuseums. Wer die Glocke herausholte, kannte die Schwachstellen und den Rhythmus des Wachmanns – Rusk war nur der Fahrer. Der eigentliche Täter hat noch kein Gesicht."),
    "rusk": ("Kellan Rusk erneut vernehmen lassen – von wem bekam er die Glocke?",
             "Wynn setzt eine weitere Vernehmung an. Rusks Anwalt signalisiert Gesprächsbereitschaft: Rusk hat dem Transport zugestimmt, nicht dem Diebstahl – und wer ihm die Kiste hinstellte, kann nur einer wissen: er."),
    "quist": ("Nella Quist zu den Vermittlern im Hintergrund befragen lassen",
              "Nella Quist kennt die Vermittlerszene der Stadt besser als manche Beamte. Wynn will wissen, wer sich in diesen Kreisen als Treuhänder für Spezialaufträge ausgibt – und wer es sich leisten kann, dass Quist darüber schweigt."),
    "cairn": ("Cairn von innen prüfen – Zahlungswege und Entscheidungsträger hinter dem Auftrag",
              "Wynn lässt die Zahlungswege bei Cairn Maritime Holdings prüfen: Wer zeichnete den Auftrag an Daal ab, wer kannte Vardons Privatkonto? Die Antwort entscheidet, ob sie allein handelte – oder ob im Haus noch jemand mitlas."),
    "storno": ("Den Anruf zurückverfolgen – wer kannte den Buchungscode und rief um 06:51 Uhr an?",
               "Wynn lässt die Funkzellendaten und die Stimmaufnahme des Kaiweg-Disponenten auswerten. Jemand wusste in dieser Nacht mehr, als er wissen durfte – und hat jetzt einen Vorsprung, den er nutzen wird."),
}


def epilog(Z):
    titel("Kapitelbilanz")
    print(bold("  " + Z["ergebnis"]) + "\n")
    geklaert = sum(1 for v in Z["fragen"].values() if v[0] == "geklärt")
    say(f"Beweise: {len(Z['fakten'])} · Aussagen: {len(Z['aussagen'])} · Fragen geklärt: {geklaert} von {len(FRAGEN)}")
    for l in Z["log"]:
        print(red("  ✖ " + l))
    if Z["log"]:
        print()
    akte(Z)
    pause()
    print(bold("Wie geht es weiter?"))
    keys = ["einbruch", "rusk", "quist", "storno" if Z["tier"] == "C" else "cairn"]
    k = keys[choose([WEITER[x][0] for x in keys], Z)]
    say(WEITER[k][1])
    print(bold("ENDE DES KAPITELS") + dim(" – Fortsetzung folgt. Deine Entscheidung wird im nächsten Kapitel aufgegriffen.\n"))


def ende_tot(Z):
    titel("Nachruf")
    say("Daniel Mercer / Recoil hat die Halle am Nordring nicht wieder verlassen.")
    say("Die Mercer Unit trägt seinen Namen weiter – wie, entscheidet sich in der nächsten Geschichte. Der Fall der Hafenglocke geht weiter, ohne ihn. Die Polizei führt ihn zu Ende; die Unit wird weiter helfen, wenn man sie anfragt.")
    if Z["log"]:
        for l in Z["log"]:
            print(red("  ✖ " + l))
        print()
    print(bold("ENDE") + dim(" – Starte neu, um einen anderen Weg zu wählen.\n"))


def main():
    Z = None
    if os.path.exists(SAVE):
        if ask("Spielstand gefunden. Laden? [j/n] ").strip().lower().startswith("j"):
            with open(SAVE, encoding="utf-8") as fh:
                Z = json.load(fh)
            if Z.get("phase") in ("ende", "tot"):
                Z = None
    Z = Z or neu()
    if Z["phase"] == "intro":
        intro(Z)
        Z["phase"] = "praesidium"
    if Z["phase"] == "praesidium":
        praesidium(Z)
    if Z["phase"] == "hub":
        hub(Z)
        if Z["phase"] == "hub":
            Z["phase"] = "morgen"
    if Z["phase"] == "tot":
        ende_tot(Z)
        return
    if Z["phase"] == "morgen":
        morgen(Z)
        epilog(Z)
        Z["phase"] = "ende"
        speichern(Z)


if __name__ == "__main__":
    main()
