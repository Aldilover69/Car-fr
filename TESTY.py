# -*- coding: utf-8 -*-
"""
AFTERHOURS – Streamlit-Version.

  streamlit run streamlit_app.py

Die Geschichte (kapitel1–3) ist als durchlaufender Python-Code geschrieben, der
bei jeder Entscheidung ui.choose() aufruft. Streamlit dagegen führt das Skript
bei jedem Klick neu aus. Deshalb merkt sich die App nur den Zufallsstartwert und
die Liste deiner bisherigen Entscheidungen und spielt die Geschichte bei jedem
Klick bis zur nächsten offenen Entscheidung blitzschnell nach.
"""
import copy
import html
import json
import os
import random
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st  # noqa: E402

import audio  # noqa: E402
import buehne  # noqa: E402
import engine  # noqa: E402
import kapitel1  # noqa: E402
import kapitel2  # noqa: E402
import kapitel3  # noqa: E402
import ki  # noqa: E402
from engine import FRAGEN, KAPITEL_TITEL, SKILL, TEAM  # noqa: E402

st.set_page_config(page_title="AFTERHOURS – Vesper City", page_icon="🌧️", layout="wide")

ss = st.session_state
ss.setdefault("modus", "menu")
ss.setdefault("seed", 0)
ss.setdefault("antworten", [])
ss.setdefault("ki", None)
ss.setdefault("ki_gefahr", None)
ss.setdefault("vorlesen", True)
ss.setdefault("autoplay", True)
ss.setdefault("optionen_vorlesen", False)
ss.setdefault("animation", True)
ss.setdefault("api_key", "")
ss.setdefault("ki_lage", None)

st.markdown("""
<style>
.stApp { background: radial-gradient(ellipse at top, #1b2433 0%, #0d1118 60%, #07090d 100%); }
.ah-titel { font-family: Georgia, serif; letter-spacing: .35em; font-size: 2.6rem; margin: 0; color: #f0c674; }
.ah-unter { color: #8a97ab; letter-spacing: .1em; margin-top: -.3rem; }
.ah-kapitel { font-family: Georgia, serif; color: #f0c674; font-size: 1.7rem; margin: 1.2rem 0 .2rem; }
.ah-szene { font-family: Georgia, serif; color: #dfe6f0; font-size: 1.25rem; margin: 1.1rem 0 .1rem;
            border-bottom: 1px solid #2b3545; padding-bottom: .2rem; }
.ah-ort { color: #6fb3d2; font-size: .9rem; margin-bottom: .6rem; }
.ah-say { color: #d7dde6; line-height: 1.65; font-size: 1.04rem; margin: .45rem 0; }
.ah-talk { border-left: 3px solid #f0c674; background: rgba(240,198,116,.06); padding: .45rem .8rem;
           margin: .45rem 0; border-radius: 0 6px 6px 0; line-height: 1.6; color: #e6e9ee; }
.ah-talk b { color: #f0c674; margin-right: .35rem; }
.ah-info { color: #8a97ab; font-size: .92rem; margin: .35rem 0; }
.ah-wahl { color: #6fb3d2; font-style: italic; margin: .5rem 0 .8rem; font-size: .95rem; }
.ah-tod { color: #ff8a80; font-weight: 600; }
[data-testid="stMain"] [data-testid="stButton"] button { justify-content: flex-start; text-align: left; }
[data-testid="stMain"] [data-testid="stButton"] button * { text-align: left; justify-content: flex-start; }
</style>
""", unsafe_allow_html=True)


# ───────────────────────────── Nachspielen der Geschichte ─────────────────────────────

class Warten(Exception):
    """Die Geschichte wartet auf eine Eingabe, die noch nicht getroffen wurde."""

    def __init__(self, art, optionen=None):
        super().__init__(art)
        self.art, self.optionen = art, optionen


class StreamlitUI(engine.UI):
    """Sammelt alle Ausgaben als Ereignisse und beantwortet Auswahlen aus der Liste."""

    def __init__(self, antworten):
        self.antworten = antworten
        self.pos = 0
        self.ereignisse = []

    def _e(self, *ev):
        self.ereignisse.append(ev)

    def title(self, sub):
        self._e("title", sub)

    def ort(self, text):
        self._e("ort", text)

    def say(self, text):
        self._e("say", text)

    def talk(self, who, text):
        self._e("talk", who, text)

    def note(self, kind, text):
        self._e("note", kind, text)

    def _warte(self, art, optionen):
        if self.pos < len(self.antworten):
            a = self.antworten[self.pos]
            self.pos += 1
            if optionen:
                a = max(0, min(a, len(optionen) - 1))
            self._e("wahl", art, optionen, a)
            return a
        raise Warten(art, optionen)

    def pause(self):
        self._warte("pause", None)

    def choose(self, options, Z, save=False):
        return self._warte("choose", list(options))

    def ask_text(self, prompt, secret=False):
        return ""

    def stream_begin(self):
        pass

    def stream(self, chunk):
        pass

    def stream_end(self):
        pass


@st.cache_resource
def _sperre():
    # engine.random ist modulweit – gleichzeitige Spieler dürfen sich nicht in die Quere kommen
    return threading.Lock()


def nachspielen(seed, antworten):
    ui = StreamlitUI(list(antworten))
    Z = engine.neu()
    warten = ende = None
    kap = {1: kapitel1.spielen, 2: kapitel2.spielen, 3: kapitel3.spielen}
    with _sperre():
        alt = engine.random
        engine.random = random.Random(seed)
        try:
            while Z["kapitel"] in kap:
                kap[Z["kapitel"]](ui, Z)
        except Warten as w:
            warten = w
        except engine.Spielende as e:
            ende = str(e)
            Z["phase"] = "spielende"
        finally:
            engine.random = alt
    return ui, Z, warten, ende


# ───────────────────────────── Aktionen (Callbacks) ─────────────────────────────

def neues_spiel():
    ss.seed = random.randrange(1 << 30)
    ss.antworten = []
    ss.modus = "spiel"


def antworte(i):
    ss.antworten.append(i)


def zurueck():
    if ss.antworten:
        ss.antworten.pop()


def ins_menue():
    ss.modus = "menu"


def ki_start(Z=None):
    stand = copy.deepcopy(Z) if Z else engine.neu()
    ss.ki = {"modell": ki_modell(), "stand": stand,
             "messages": [{"role": "user", "content": ki.start_nachricht(stand)}]}
    ss.ki_gefahr = None
    ss.ki_lage = None
    ss.modus = "ki"


def spielstand_laden():
    f = ss.get("upload")
    if f is None:
        return
    try:
        d = json.loads(f.getvalue().decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        ss.ladefehler = "Die Datei ist kein gültiger AFTERHOURS-Spielstand."
        return
    ss.ladefehler = ""
    if d.get("typ") == "afterhours-ki" and d.get("messages"):
        stand = d.get("stand") or engine.neu()
        for k, v in engine.neu().items():
            stand.setdefault(k, v)
        ss.ki = {"modell": d.get("modell") or ki_modell(), "stand": stand, "messages": d["messages"]}
        ss.ki_gefahr = None
        ss.ki_lage = None
        ss.modus = "ki"
    elif d.get("typ") == "afterhours-spiel":
        ss.seed = int(d.get("seed", 0))
        ss.antworten = [int(x) for x in d.get("antworten", [])]
        ss.modus = "spiel"
    else:
        ss.ladefehler = "Die Datei ist kein gültiger AFTERHOURS-Spielstand."


# ───────────────────────────── Darstellung ─────────────────────────────

def esc(t):
    return html.escape(t).replace("\n", "<br>")


def md(t):
    """Text sicher in Streamlit-Markdown einsetzen ($ würde sonst als Formel gelesen)."""
    for z in "\\$*_~`":
        t = t.replace(z, "\\" + z)
    return t


def zeige(ereignisse):
    for e in ereignisse:
        art = e[0]
        if art == "title":
            klasse = "ah-kapitel" if e[1].startswith("Kapitel ") else "ah-szene"
            st.markdown(f"<div class='{klasse}'>{esc(e[1])}</div>", unsafe_allow_html=True)
        elif art == "ort":
            st.markdown(f"<div class='ah-ort'>📍 {esc(e[1])}</div>", unsafe_allow_html=True)
        elif art == "say":
            for absatz in e[1].strip().split("\n"):
                if absatz.strip():
                    st.markdown(f"<div class='ah-say'>{esc(absatz)}</div>", unsafe_allow_html=True)
        elif art == "talk":
            st.markdown(f"<div class='ah-talk'><b>{esc(e[1])}</b>„{esc(e[2])}“</div>", unsafe_allow_html=True)
        elif art == "note":
            kind, t = e[1], md(e[2])
            if kind == "fakt":
                st.success(f"**Beweis:** {t}", icon="🧾")
            elif kind == "aussage":
                st.info(f"**Aussage:** {t}", icon="🗣️")
            elif kind == "frage":
                st.info(f"**Frage:** {t}", icon="❓")
            elif kind == "warn":
                st.warning(t, icon="⚠️")
            elif kind == "tod":
                st.error(t, icon="🕯️")
            else:
                st.markdown(f"<div class='ah-info'>· {esc(e[2])}</div>", unsafe_allow_html=True)
        elif art == "wahl" and e[1] == "choose":
            st.markdown(f"<div class='ah-wahl'>➜ {esc(e[2][e[3]])}</div>", unsafe_allow_html=True)


def verlauf_html(ereignisse):
    teile = []
    for e in ereignisse:
        if e[0] == "title":
            teile.append(f"<div class='ah-szene'>{esc(e[1])}</div>")
        elif e[0] == "ort":
            teile.append(f"<div class='ah-ort'>📍 {esc(e[1])}</div>")
        elif e[0] == "say":
            teile.append(f"<div class='ah-say'>{esc(e[1])}</div>")
        elif e[0] == "talk":
            teile.append(f"<div class='ah-talk'><b>{esc(e[1])}</b>„{esc(e[2])}“</div>")
        elif e[0] == "note":
            teile.append(f"<div class='ah-info'>{'🕯️ ' if e[1] == 'tod' else '· '}{esc(e[2])}</div>")
        elif e[0] == "wahl" and e[1] == "choose":
            teile.append(f"<div class='ah-wahl'>➜ {esc(e[2][e[3]])}</div>")
    return "".join(teile)


def vorlesen(seg):
    """Spielt die Abschnitte als ein Audio ab (eigene Stimme je Figur)."""
    if not ss.vorlesen or not seg:
        return
    with st.spinner("Szene wird vertont …"):
        try:
            mp3 = audio.szene_mp3(seg)
        except Exception as e:  # Audio darf das Spiel nie blockieren
            st.caption(f"🔇 Audio nicht verfügbar: {e}")
            return
    if mp3:
        st.audio(mp3, format="audio/mpeg", autoplay=ss.autoplay)
    else:
        st.caption("🔇 Audio konnte nicht erzeugt werden (keine Verbindung zum Sprachdienst?).")


def team_seitenleiste(Z):
    st.sidebar.markdown("#### Mercer Unit")
    leitung = engine.leiter(Z)
    zeilen = []
    for k, name in TEAM.items():
        if k in Z["tot"]:
            zeilen.append(f"🕯️ ~~{name}~~")
        else:
            zeilen.append(f"🟢 {name}" + (" **(Leitung)**" if k == leitung else ""))
    st.sidebar.markdown("  \n".join(zeilen))


def fallakte(Z):
    f, a, fr = engine.akte_daten(Z)
    st.markdown("#### Bewiesene Fakten")
    for t in f:
        st.markdown(f"- {md(t)}")
    st.markdown("#### Aussagen (nicht bewiesen)")
    for t in a:
        st.markdown(f"- {md(t)}")
    st.markdown("#### Offene Fragen")
    farbe = {"offen": "🔴", "teilweise": "🟡", "geklärt": "🟢"}
    for status, txt, notiz in fr:
        st.markdown(f"- {farbe[status]} **{status}** – {md(txt)}" + (f"  \n  _{md(notiz)}_" if notiz else ""))
    if Z.get("log"):
        st.markdown("#### Ereignisse")
        for t in Z["log"]:
            st.markdown(f"- {md(t)}")


def team_ansicht(Z):
    leitung = engine.leiter(Z)
    for k, name in TEAM.items():
        status = "🕯️ gefallen" if k in Z["tot"] else "🟢 einsatzbereit"
        st.markdown(f"**{name}**{' · Leitung' if k == leitung else ''} — {status}  \n{SKILL[k]}")
    st.caption("Theo Alvarez / Relay: Technik und Kommunikation (nicht im Feld). In Erinnerung: Priya Nair / Liminal.")


def einstellungen_seitenleiste():
    st.sidebar.markdown("#### 🎬 Darstellung")
    st.sidebar.toggle("Animierte Bühne", key="animation",
                      help="Zeigt jede Szene als animierte Bühne: Schauplatz, sprechende Figuren, Beweise, Einsätze. "
                           "Text und Bilder laufen synchron zum Vorlesen.")
    st.sidebar.markdown("#### 🔊 Audio")
    st.sidebar.toggle("Texte vorlesen", key="vorlesen")
    st.sidebar.toggle("Automatisch abspielen", key="autoplay", disabled=not ss.vorlesen)
    st.sidebar.toggle("Auswahlmöglichkeiten mitlesen", key="optionen_vorlesen", disabled=not ss.vorlesen)


# ───────────────────────────── Bildschirme ─────────────────────────────

def menue():
    st.markdown("<p class='ah-titel'>AFTERHOURS</p><p class='ah-unter'>VESPER CITY · DIE GESTOHLENE HAFENGLOCKE</p>",
                unsafe_allow_html=True)
    st.markdown(
        "Du bist **Daniel Mercer / Recoil**, Leiter der Mercer Unit – Platz 38 von 40 in der inoffiziellen "
        "Heldenrangliste von Vesper City. Die gestohlene Hafenglocke ist wieder da. Jetzt geht es um die Menschen "
        "hinter dem Diebstahl.\n\n"
        "Drei Kapitel, echte Konsequenzen: Deine Entscheidungen bestimmen, welche Beweise du findest, wer entkommt "
        "und wie stark die Anklage am Ende ist. Bei Missionen mit **⚠️ GEFAHR** können Mitglieder deines Teams sterben.")
    c1, c2 = st.columns(2)
    c1.button("▶ Neues Spiel (Kapitel 1–3)", type="primary", use_container_width=True, on_click=neues_spiel)
    c2.button("✨ KI-Erzähler (frei weiterspielen)", use_container_width=True, on_click=ki_start)
    if ss.seed:
        st.button("⏯ Laufendes Spiel fortsetzen", use_container_width=True,
                  on_click=lambda: ss.update(modus="spiel"))
    if ss.ki:
        st.button("⏯ KI-Erzähler fortsetzen", use_container_width=True, on_click=lambda: ss.update(modus="ki"))
    st.divider()
    st.file_uploader("Spielstand laden (.json)", type=["json"], key="upload", on_change=spielstand_laden)
    if ss.get("ladefehler"):
        st.error(ss.ladefehler)
    st.caption("🔊 Alle Texte werden vorgelesen – Erzähler und jede Figur mit eigener Stimme. "
               "Einstellungen findest du links in der Seitenleiste.")


def spiel():
    ui, Z, warten, ende = nachspielen(ss.seed, ss.antworten)
    ev = ui.ereignisse

    # Szene = alles seit der letzten „Weiter“-Pause; neu = alles seit der letzten Eingabe
    pausen = [i for i, e in enumerate(ev) if e[0] == "wahl" and e[1] == "pause"]
    szene_start = pausen[-1] + 1 if pausen else 0
    wahlen = [i for i, e in enumerate(ev) if e[0] == "wahl"]
    neu_start = wahlen[-1] + 1 if wahlen else 0

    st.sidebar.markdown("<p class='ah-titel' style='font-size:1.4rem'>AFTERHOURS</p>", unsafe_allow_html=True)
    if Z["kapitel"] <= 3:
        st.sidebar.markdown(f"**Kapitel {Z['kapitel']}:** {KAPITEL_TITEL[Z['kapitel']]}")
    else:
        st.sidebar.markdown("**Fall abgeschlossen**")
    st.sidebar.progress(engine.geklaert_anzahl(Z) / len(FRAGEN),
                        text=f"Kernfragen geklärt: {engine.geklaert_anzahl(Z)} von {len(FRAGEN)}")
    team_seitenleiste(Z)
    einstellungen_seitenleiste()
    st.sidebar.markdown("#### 💾 Spielstand")
    st.sidebar.download_button(
        "Spielstand herunterladen", use_container_width=True, file_name="afterhours_spielstand.json",
        mime="application/json",
        data=json.dumps({"typ": "afterhours-spiel", "seed": ss.seed, "antworten": ss.antworten}))
    st.sidebar.button("↶ Einen Schritt zurück", use_container_width=True, on_click=zurueck,
                      disabled=not ss.antworten)
    st.sidebar.button("☰ Hauptmenü", use_container_width=True, on_click=ins_menue)

    t_szene, t_akte, t_team, t_verlauf = st.tabs(["🎬 Szene", "🗂️ Fallakte", "🦸 Team", "📜 Verlauf"])
    with t_akte:
        fallakte(Z)
    with t_team:
        team_ansicht(Z)
    with t_verlauf:
        if szene_start:
            st.markdown(verlauf_html(ev[:szene_start]), unsafe_allow_html=True)
        else:
            st.caption("Noch nichts – die Geschichte hat gerade erst begonnen.")

    with t_szene:
        if ss.animation:
            buehne.zeigen(buehne.spiel_szene(ev, szene_start, neu_start, Z, warten, ende, ss.vorlesen, ss.autoplay,
                                             ss.optionen_vorlesen, ss.seed, ss.antworten), key="buehne_spiel")
        else:
            optionen = warten.optionen if warten and warten.art == "choose" else None
            vorlesen(audio.segmente(ev[neu_start:], optionen if ss.optionen_vorlesen else None))
            zeige(ev[szene_start:])
        schritt = len(ss.antworten)
        if warten and warten.art == "pause":
            st.button("Weiter ▶", type="primary", key=f"weiter_{schritt}", on_click=antworte, args=(0,))
        elif warten:
            st.markdown("")
            for i, o in enumerate(warten.optionen):
                gefahr = "[GEFAHR]" in o
                text = o.replace("[GEFAHR]", "").strip()
                st.button(("⚠️ **GEFAHR** · " if gefahr else f"{i + 1}) ") + md(text),
                          key=f"wahl_{schritt}_{i}", on_click=antworte, args=(i,), use_container_width=True)
        elif ende:
            st.error(ende, icon="🕯️")
            st.button("Neues Spiel", type="primary", on_click=neues_spiel)
        else:
            st.markdown("<div class='ah-kapitel'>Der Fall der Hafenglocke ist abgeschlossen.</div>",
                        unsafe_allow_html=True)
            if Z.get("naechster_fall"):
                st.markdown(f"Dein nächster Handlungsstrang: _{md(Z['naechster_fall'])}_")
            c1, c2 = st.columns(2)
            c1.button("✨ Mit dem KI-Erzähler weiterspielen", type="primary", use_container_width=True,
                      on_click=ki_start, args=(Z,))
            c2.button("Neues Spiel", use_container_width=True, on_click=neues_spiel)


# ───────────────────────────── KI-Erzähler ─────────────────────────────

def _secret(name):
    try:
        return st.secrets.get(name)
    except Exception:
        return None


def ki_modell():
    m = _secret("AFTERHOURS_MODELL")
    return m or ki.modell(ki.konfig_laden())


def api_schluessel():
    return (_secret("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
            or ki.konfig_laden().get("api_key") or ss.api_key or "").strip()


def ki_waehle(nachricht):
    ss.ki["messages"].append({"role": "user", "content": nachricht})
    ss.ki_gefahr = None


def ki_text_ohne_optionen(text, opts):
    if not opts:
        return text
    zeilen = text.rstrip().splitlines()
    while zeilen and (ki.OPT_RE.match(zeilen[-1]) or not zeilen[-1].strip()):
        zeilen.pop()
    return "\n".join(zeilen)


def ki_erzaehler():
    d = ss.ki
    KZ, msgs = d["stand"], d["messages"]
    st.sidebar.markdown("<p class='ah-titel' style='font-size:1.4rem'>AFTERHOURS</p>", unsafe_allow_html=True)
    st.sidebar.markdown(f"**KI-Erzähler** · Modell `{d['modell']}`")
    team_seitenleiste(KZ)
    einstellungen_seitenleiste()
    st.sidebar.markdown("#### 💾 Spielstand")
    st.sidebar.download_button(
        "KI-Verlauf herunterladen", use_container_width=True, file_name="afterhours_ki_verlauf.json",
        mime="application/json", data=json.dumps({"typ": "afterhours-ki", **d}, ensure_ascii=False))
    st.sidebar.button("☰ Hauptmenü", use_container_width=True, on_click=ins_menue)

    schluessel = api_schluessel()
    if not schluessel:
        st.markdown("<div class='ah-kapitel'>KI-Erzähler einrichten</div>", unsafe_allow_html=True)
        st.markdown("Der KI-Erzähler braucht einen Claude-API-Schlüssel (console.anthropic.com → API Keys). "
                    "Die Nutzung wird pro Anfrage abgerechnet. Der Schlüssel gilt nur für diese Sitzung. "
                    "Auf Streamlit Cloud kannst du ihn dauerhaft unter *Settings → Secrets* als "
                    "`ANTHROPIC_API_KEY` hinterlegen.")
        st.text_input("API-Schlüssel (beginnt mit sk-ant-)", type="password", key="api_key")
        return

    t_szene, t_akte, t_verlauf = st.tabs(["🎬 Szene", "🗂️ Fallakte", "📜 Verlauf"])
    with t_akte:
        fallakte(KZ)
    with t_verlauf:
        frueher = [m["content"] for m in msgs[:-1] if m["role"] == "assistant"]
        for t in frueher:
            st.markdown(t.replace("$", "\\$"))
            st.divider()
        if not frueher:
            st.caption("Noch nichts.")

    with t_szene:
        if msgs[-1]["role"] == "user":
            if len(msgs) > 1:
                st.markdown(f"<div class='ah-wahl'>➜ {esc(msgs[-1]['content'].split(chr(10))[0])}</div>",
                            unsafe_allow_html=True)
            try:
                text = st.write_stream(ki.anfrage(schluessel, d["modell"], ki.system_bloecke(KZ), msgs))
            except ki.KIFehler as e:
                st.error(str(e))
                c1, c2 = st.columns(2)
                c1.button("Erneut versuchen", type="primary", use_container_width=True)
                if e.schluessel:
                    c2.button("Anderen API-Schlüssel eingeben", use_container_width=True,
                              on_click=lambda: ss.update(api_key=""))
                return
            text = (text if isinstance(text, str) else "".join(map(str, text))).strip()
            if not text:
                st.error("Die Antwort war leer.")
                st.button("Erneut versuchen", type="primary")
                return
            msgs.append({"role": "assistant", "content": text})
            st.rerun()

        letzte = msgs[-1]["content"]
        opts = ki.optionen(letzte)
        anzeige = ki_text_ohne_optionen(letzte, opts)
        if ss.animation:
            # Die Bühne der neuen Antwort beginnt dort, wo die vorige aufgehört hat
            lage = ss.ki_lage
            vorher = (lage["start"] if lage["n"] == len(msgs) else lage["ende"]) if lage else None
            args = buehne.ki_szene(anzeige, opts, KZ, msgs, ss.vorlesen, ss.autoplay, ss.optionen_vorlesen, vorher)
            ss.ki_lage = {"n": len(msgs), "start": vorher, "ende": args["ende"]}
            buehne.zeigen(args, key="buehne_ki")
        else:
            seg = audio.markdown_segmente(anzeige)
            if ss.optionen_vorlesen and opts:
                seg += audio.segmente([], opts)
            vorlesen(seg)
            st.markdown(anzeige.replace("$", "\\$"))

        if engine.leiter(KZ) is None:
            st.info("Die Geschichte der Mercer Unit ist zu Ende erzählt.")
            return

        if ss.ki_gefahr:
            st.warning(f"**Gefährliche Mission:** {md(ss.ki_gefahr.replace('[GEFAHR]', '').strip())}  \n"
                       "Bei dieser Mission können ein oder zwei der ausgewählten Einsatzkräfte sterben.", icon="⚠️")
            lv = engine.lebend(KZ)
            sel = st.multiselect("Einsatzkräfte (bis zu drei)", lv, max_selections=3,
                                 format_func=lambda k: f"{TEAM[k]} – {SKILL[k]}")
            c1, c2 = st.columns(2)
            c1.button("Mission antreten", type="primary", use_container_width=True, disabled=not sel,
                      on_click=lambda: ki_waehle(ki.wuerfel_nachricht(KZ, ss.ki_gefahr, sel)))
            c2.button("Doch nicht – zurück zur Auswahl", use_container_width=True,
                      on_click=lambda: ss.update(ki_gefahr=None))
            return

        for i, o in enumerate(opts):
            gefahr = "[GEFAHR]" in o.upper()
            text = o.replace("[GEFAHR]", "").strip()
            if gefahr:
                st.button("⚠️ **GEFAHR** · " + md(text), key=f"ki_{len(msgs)}_{i}", use_container_width=True,
                          on_click=lambda o=o: ss.update(ki_gefahr=o))
            else:
                st.button(f"{i + 1}) " + md(text), key=f"ki_{len(msgs)}_{i}", use_container_width=True,
                          on_click=ki_waehle, args=(f"Ich wähle: {o}",))
        eigen = st.chat_input("Eigene Aktion eingeben …")
        if eigen and eigen.strip():
            ki_waehle(f"Eigene Aktion: {eigen.strip()}")
            st.rerun()


# ───────────────────────────── Start ─────────────────────────────

if ss.modus == "spiel":
    spiel()
elif ss.modus == "ki" and ss.ki:
    ki_erzaehler()
else:
    einstellungen_seitenleiste()
    menue()
