# -*- coding: utf-8 -*-
"""
AFTERHOURS – Selbsttest.

  python afterhours.py --selbsttest

Prüft auf deinem Rechner:
  1. Python-Version
  2. die Geschichte (viele automatische Durchläufe)
  3. die Grafikversion mit echtem pygame (unsichtbares Fenster, Bildschirmfotos)
  4. die Verbindung zur Claude-API (nur wenn ein API-Schlüssel eingerichtet ist)

Dein Spielstand und dein KI-Verlauf werden dabei nicht verändert.
"""
import os
import random
import shutil
import sys
import tempfile
import time
import traceback

import engine

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ERGEBNISSE = []
BILDER = os.path.join(engine.BASIS, "selbsttest_bilder")


def melde(name, status, info=""):
    marke = {"ok": "[OK]        ", "fehler": "[FEHLER]    ", "warnung": "[WARNUNG]   ",
             "skip": "[ÜBERSPRUNGEN]"}[status]
    ERGEBNISSE.append((name, status, info))
    print(f"{marke} {name}" + (f"\n               {info}" if info else ""))


class _TestUI(engine.UI):
    def __init__(self, rng):
        self.rng = rng

    def title(self, s): pass
    def ort(self, t): pass
    def say(self, t): pass
    def talk(self, w, t): pass
    def note(self, k, t): pass
    def pause(self): pass
    def ask_text(self, p, secret=False): return ""
    def stream_begin(self): pass
    def stream(self, c): pass
    def stream_end(self): pass

    def choose(self, opts, Z, save=False):
        if not opts:
            raise AssertionError("Auswahl ohne Optionen")
        return self.rng.randrange(len(opts))


def test_python():
    v = sys.version_info
    if v >= (3, 8):
        melde(f"Python {v.major}.{v.minor}.{v.micro}", "ok")
    else:
        melde(f"Python {v.major}.{v.minor}", "fehler", "Bitte Python 3.8 oder neuer installieren.")


def test_geschichte(tmp, n=300):
    alt = engine.SPIELSTAND
    engine.SPIELSTAND = os.path.join(tmp, "spielstand_test.json")
    try:
        enden = 0
        for s in range(n):
            random.seed(s)
            Z = engine.spiel(_TestUI(random.Random(s + 1)), engine.neu())
            if Z["kapitel"] == 4 or Z.get("phase") == "spielende":
                enden += 1
        if enden == n:
            melde(f"Geschichte: {n} zufällige Durchläufe durch alle drei Kapitel", "ok")
        else:
            melde("Geschichte", "fehler", f"Nur {enden} von {n} Durchläufen kamen ans Ende.")
    except Exception:
        melde("Geschichte", "fehler", traceback.format_exc().strip().splitlines()[-1])
        traceback.print_exc()
    finally:
        engine.SPIELSTAND = alt


def test_grafik(tmp):
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    try:
        import pygame
    except ImportError:
        melde("Grafik: pygame", "fehler", "pygame ist nicht installiert. Befehl:  pip install pygame")
        return
    ver = getattr(pygame.version, "vernum", (0,))
    if tuple(ver)[:1] < (2,):
        melde(f"Grafik: pygame {pygame.version.ver}", "fehler", "Die Grafikversion braucht pygame 2.  pip install --upgrade pygame")
        return
    melde(f"Grafik: pygame {pygame.version.ver} gefunden", "ok")

    import ki
    import gui
    alt = (engine.SPIELSTAND, ki.VERLAUF, ki.KONFIG)
    engine.SPIELSTAND = os.path.join(tmp, "spielstand_gui.json")
    ki.VERLAUF = os.path.join(tmp, "ki_verlauf_gui.json")
    ki.KONFIG = os.path.join(tmp, "einstellungen_gui.json")
    shutil.rmtree(BILDER, ignore_errors=True)
    os.makedirs(BILDER, exist_ok=True)
    bilder = []
    try:
        pygame.init()
        screen = pygame.display.set_mode((gui.W, gui.H))
        gui.schriften_laden()

        # Fehlen Zeichen in der gewählten Schrift?
        zeichen = "„“‚‘–…·•ÄÖÜäöüß"
        fehlend = []
        for name in ("body", "bold", "note"):
            m = gui.F[name].metrics(zeichen)
            fehlend += [c for c, x in zip(zeichen, m or []) if x is None]
        if fehlend:
            melde("Grafik: Schrift", "warnung", "In der Systemschrift fehlen Zeichen: " + "".join(sorted(set(fehlend))))
        else:
            melde("Grafik: Schrift mit allen Sonderzeichen (Umlaute, Anführungszeichen)", "ok")

        app = gui.App(screen)
        E = pygame.event.Event

        def frames(n=1, dt=1 / 60):
            for _ in range(n):
                app.update(dt)
                app.draw()

        def settle(timeout=10):
            t0 = time.time()
            while time.time() - t0 < timeout:
                frames(1, 0.5)
                time.sleep(0.003)
                if app.state == "game" and app.pending and app.alles_gezeigt():
                    frames(1)
                    return app.pending
            raise RuntimeError(f"Grafik reagiert nicht (wartet auf: {app.pending!r})")

        def taste(k):
            app.handle(E(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0))
            frames(1)

        def foto(name):
            app.draw()
            pfad = os.path.join(BILDER, name + ".png")
            pygame.image.save(screen, pfad)
            bilder.append(pfad)

        frames(3)
        foto("1_menue")
        neu = [i for i, (k, _) in enumerate(app.menue) if k == "neu"][0]
        taste(pygame.K_1 + neu)
        settle()
        taste(pygame.K_SPACE)
        settle()
        taste(pygame.K_SPACE)
        p = settle()
        foto("2_auswahl")
        taste(pygame.K_1)
        settle()
        taste(pygame.K_a)
        foto("3_fallakte")
        taste(pygame.K_ESCAPE)
        taste(pygame.K_t)
        foto("4_team")
        taste(pygame.K_ESCAPE)
        rng = random.Random(5)
        for _ in range(25):                       # ein Stück weiterspielen, inkl. Maus und Mausrad
            p = settle()
            if p[0] == "pause":
                app.handle(E(pygame.MOUSEBUTTONDOWN, button=1, pos=gui.MAIN.center))
                frames(1)
            elif p[0] == "choose":
                app.handle(E(pygame.MOUSEWHEEL, x=0, y=1, flipped=False))
                taste(pygame.K_1 + rng.randrange(len(p[1])))
        foto("5_spielverlauf")
        taste(pygame.K_ESCAPE)
        frames(2)
        if app.state != "menu":
            raise RuntimeError("Esc führt nicht zurück ins Hauptmenü")
        melde("Grafik: Menü, Auswahl, Fallakte, Team, 25 Spielschritte, Rückkehr ins Menü", "ok",
              f"Bildschirmfotos zum Ansehen: {BILDER}")
    except Exception:
        melde("Grafik", "fehler", traceback.format_exc().strip().splitlines()[-1])
        traceback.print_exc()
    finally:
        engine.SPIELSTAND, ki.VERLAUF, ki.KONFIG = alt
        try:
            pygame.quit()
        except Exception:
            pass


def test_api():
    import ki
    cfg = ki.konfig_laden()
    schluessel = os.environ.get("ANTHROPIC_API_KEY") or cfg.get("api_key")
    try:
        ki.system_bloecke(engine.neu())
        melde("KI: Projektprompt prompt_afterhours.md gefunden", "ok")
    except ki.KIFehler as e:
        melde("KI: Projektprompt", "fehler", str(e))
    if not schluessel:
        melde("KI: Verbindung zur Claude-API", "skip",
              "Kein API-Schlüssel eingerichtet. Setze ANTHROPIC_API_KEY oder starte einmal den KI-Erzähler im Spiel.")
        return
    mod = ki.modell(cfg)
    alt = ki.MAX_TOKENS
    ki.MAX_TOKENS = 20
    t0 = time.time()
    try:
        antwort = "".join(ki.anfrage(schluessel, mod,
                                     [{"type": "text", "text": "Antworte mit genau einem deutschen Wort."}],
                                     [{"role": "user", "content": "Sag: bereit"}])).strip()
        melde(f"KI: Claude-API antwortet (Modell {mod}, {time.time() - t0:.1f} s)", "ok", f"Antwort: {antwort!r}")
    except ki.KIFehler as e:
        melde(f"KI: Claude-API (Modell {mod})", "fehler", str(e))
    finally:
        ki.MAX_TOKENS = alt


def main():
    print("AFTERHOURS – Selbsttest\n")
    tmp = tempfile.mkdtemp(prefix="afterhours_test_")
    try:
        test_python()
        test_geschichte(tmp)
        test_grafik(tmp)
        test_api()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    fehler = [n for n, s, _ in ERGEBNISSE if s == "fehler"]
    print()
    if fehler:
        print(f"{len(fehler)} Test(s) fehlgeschlagen: " + ", ".join(fehler))
        print("Kopiere diese Ausgabe in den Chat, dann behebe ich es.")
    else:
        print("Alles in Ordnung. Viel Spaß in Vesper City.")
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
