import streamlit as st
import streamlit.components.v1 as components
import requests
import time
import os
import random
from datetime import datetime
from html import escape
from string import Template

try:
    import psutil
    PSUTIL_OK = True
except ImportError:
    PSUTIL_OK = False

try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_OK = True
except ImportError:
    AUTOREFRESH_OK = False

try:
    import pynvml
    pynvml.nvmlInit()
    GPU_HANDLE = pynvml.nvmlDeviceGetHandleByIndex(0)
    GPU_OK = True
except Exception:
    GPU_OK = False
    GPU_HANDLE = None

# ---------- Constants ----------

CYAN = "#22d3ee"
CYAN_BRIGHT = "#67e8f9"
DIM = "#5b7a8a"
TEXT = "#cffafe"
BORDER = "rgba(56,189,248,0.25)"
PANEL_BG = "rgba(8,20,34,0.55)"
MODEL = "claude-sonnet-5"
DEFAULT_LAT, DEFAULT_LON = 48.7758, 9.1829  # Stuttgart – hier eigene Koordinaten eintragen
MAX_NET_MBPS = 100  # Referenzwert (Mbit/s) fuer die NET-Anzeige in % – an deine Verbindung anpassen
SYSTEM_PROMPT = ("Du bist J.A.R.V.I.S., ein ruhiger, hochentwickelter KI-Assistent in einer futuristischen "
                  "HUD-Oberflaeche. Antworte knapp in 2-4 Saetzen, hoeflich und leicht formell. Nutze die "
                  "Websuche fuer aktuelle oder faktenbasierte Fragen. Antworte in der Sprache der Anfrage.")

GLOBAL_CSS = Template("""
<style>
  .stApp {
    background: radial-gradient(ellipse at 50% 20%, #0a1622 0%, #050b14 70%);
  }
  html, body, [class*="css"], p, span, div {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    color: $text;
  }
  .block-container { padding-top: 2rem; padding-bottom: 6rem; max-width: 1400px; }
  [data-testid="stChatInput"] { background: rgba(5,11,20,0.9); border-top: 1px solid $border; }
  [data-testid="stSidebar"] { background: #050b14; border-right: 1px solid $border; }
  [data-testid="stToggle"] label { color: $text !important; font-size: 12px; }
  footer { visibility: hidden; }
</style>
""")

ORB_TEMPLATE = Template("""
<html><head><style>
  body { margin:0; background:transparent; display:flex; flex-direction:column; align-items:center;
         font-family: ui-monospace, Menlo, Consolas, monospace; overflow:hidden; }
  .wrap { position:relative; width:220px; height:220px; display:flex; align-items:center; justify-content:center; margin-top:6px; }
  .glow { position:absolute; width:220px; height:220px; border-radius:50%;
          background:radial-gradient(circle, rgba(34,211,238,$glowfrac) 0%, transparent 70%); filter:blur(10px); }
  .ring1 { position:absolute; animation: spin $speed linear infinite; }
  .ring2 { position:absolute; animation: spinrev 10s linear infinite; }
  @keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
  @keyframes spinrev { from{transform:rotate(360deg)} to{transform:rotate(0deg)} }
  .core { position:relative; width:92px; height:92px; border-radius:50%;
          background:radial-gradient(circle, rgba(8,20,34,0.9), rgba(5,11,20,0.95));
          border:1px solid rgba(56,189,248,0.5); box-shadow:0 0 $glowshadow rgba(34,211,238,$glow);
          display:flex; align-items:center; justify-content:center; color:#67e8f9;
          font-size:13px; letter-spacing:0.1em; font-weight:600; }
  .lbl { margin-top:10px; font-size:11px; letter-spacing:0.3em; color:#22d3ee; }
  .wave { display:flex; align-items:center; justify-content:center; gap:2px; height:22px; margin-top:8px; }
  .bar { width:2px; background:#22d3ee; border-radius:2px; opacity:$op; animation:wavebar 0.9s ease-in-out infinite; animation-play-state:$play; }
  @keyframes wavebar { 0%,100%{height:4px} 50%{height:20px} }
</style></head><body>
  <div class="wrap">
    <div class="glow"></div>
    <svg class="ring1" width="220" height="220" viewBox="0 0 220 220">
      <circle cx="110" cy="110" r="98" fill="none" stroke="rgba(34,211,238,0.15)" stroke-width="1"/>
      <circle cx="110" cy="110" r="86" fill="none" stroke="#22d3ee" stroke-width="1.5" stroke-dasharray="4 10" opacity="0.6"/>
      <circle cx="110" cy="110" r="74" fill="none" stroke="rgba(34,211,238,0.25)" stroke-width="6" stroke-dasharray="50 260" stroke-linecap="round"/>
    </svg>
    <svg class="ring2" width="220" height="220" viewBox="0 0 220 220">
      <circle cx="110" cy="110" r="58" fill="none" stroke="#67e8f9" stroke-width="2" stroke-dasharray="26 8 4 8" opacity="0.7"/>
    </svg>
    <div class="core">JARVIS</div>
  </div>
  <div class="lbl">$label</div>
  <div class="wave">$bars</div>
</body></html>
""")

st.set_page_config(page_title="JARVIS OS", page_icon="\U0001F537", layout="wide")
st.markdown(GLOBAL_CSS.substitute(text=TEXT, border=BORDER), unsafe_allow_html=True)

# ---------- Helpers ----------

def panel_html(title, content, height=None):
    h = f"height:{height}px;" if height else ""
    return f"""
    <div style="background:{PANEL_BG}; border:1px solid {BORDER}; border-radius:10px; padding:12px;
                box-shadow:0 0 24px rgba(34,211,238,0.06); {h} display:flex; flex-direction:column; margin-bottom:12px;">
      <div style="display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid {BORDER};
                  padding-bottom:8px; margin-bottom:8px;">
        <span style="font-size:10px; letter-spacing:0.15em; color:{CYAN};">{title}</span>
        <span style="width:4px; height:4px; border-radius:50%; background:rgba(34,211,238,0.35);"></span>
      </div>
      <div style="flex:1; overflow:auto;">{content}</div>
    </div>
    """

def radial_gauge_html(value, label, size=64, stroke=5):
    value = max(0, min(100, value))
    r = (size - stroke * 2) / 2
    circ = 2 * 3.14159265 * r
    offset = circ - (value / 100) * circ
    c = size / 2
    return f"""
    <div style="display:flex; flex-direction:column; align-items:center; gap:3px;">
      <div style="position:relative; width:{size}px; height:{size}px;">
        <svg width="{size}" height="{size}" style="position:absolute; transform:rotate(-90deg);">
          <circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="rgba(34,211,238,0.15)" stroke-width="{stroke}"/>
          <circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="{CYAN}" stroke-width="{stroke}"
            stroke-linecap="round" stroke-dasharray="{circ:.2f}" stroke-dashoffset="{offset:.2f}"
            style="transition: stroke-dashoffset 1s ease;"/>
        </svg>
        <div style="position:absolute; top:0; left:0; width:100%; height:100%; display:flex;
                    align-items:center; justify-content:center; font-size:11px; color:{CYAN_BRIGHT};">{value:.0f}%</div>
      </div>
      <div style="font-size:9px; color:{DIM}; letter-spacing:0.05em;">{label}</div>
    </div>
    """

def sparkline_svg(values, width=100, height=40):
    if not values:
        return ""
    vmax, vmin = max(values), min(values)
    rng = (vmax - vmin) or 1
    pts = " ".join(f"{(i/(len(values)-1))*width:.1f},{height-((v-vmin)/rng)*height:.1f}" for i, v in enumerate(values))
    return f'<svg viewBox="0 0 {width} {height}" style="flex:1; height:{height}px;"><polyline fill="none" stroke="{CYAN}" stroke-width="1.5" points="{pts}"/></svg>'

def orb_component(state):
    speed = {"thinking": "2.2s", "speaking": "7s"}.get(state, "20s")
    glow = {"idle": 0.15, "thinking": 0.55, "speaking": 0.75}.get(state, 0.15)
    label = {"idle": "BEREIT", "thinking": "VERARBEITET...", "speaking": "SPRICHT..."}.get(state, "BEREIT")
    play = "running" if state in ("thinking", "speaking") else "paused"
    op = 0.9 if state in ("thinking", "speaking") else 0.25
    bars = "".join(f'<span class="bar" style="animation-delay:{i*0.045:.3f}s;"></span>' for i in range(26))
    return ORB_TEMPLATE.substitute(
        speed=speed,
        glowfrac=f"{glow*0.3:.3f}",
        glow=f"{glow:.3f}",
        glowshadow=f"{round(20+glow*40)}px",
        op=f"{op}",
        play=play,
        label=label,
        bars=bars,
    )

@st.cache_data(ttl=600)
def get_weather(lat=DEFAULT_LAT, lon=DEFAULT_LON):
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m"},
            timeout=5,
        )
        cur = r.json().get("current", {})
        return {
            "temp": round(cur.get("temperature_2m", 22)),
            "humidity": round(cur.get("relative_humidity_2m", 40)),
            "pressure": round(cur.get("surface_pressure", 1013)),
            "wind": round(cur.get("wind_speed_10m", 12)),
        }
    except Exception:
        return {"temp": 22, "humidity": 40, "pressure": 1013, "wind": 12}

def get_api_key():
    return os.environ.get("ANTHROPIC_API_KEY") or st.session_state.get("api_key_input", "")

def call_jarvis_api(messages):
    api_key = get_api_key()
    if not api_key:
        return "Kein API-Schluessel hinterlegt. Bitte in der Seitenleiste eintragen oder ANTHROPIC_API_KEY setzen."
    messages = messages[-20:]
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={
                "model": MODEL,
                "max_tokens": 1000,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": m["role"], "content": m["text"]} for m in messages],
                "tools": [{"type": "web_search_20250305", "name": "web_search"}],
            },
            timeout=45,
        )
        data = resp.json()
        if resp.status_code != 200:
            return f"API-Fehler ({resp.status_code}): {data.get('error', {}).get('message', 'unbekannt')}"
        texts = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
        return "\n".join(texts).strip() or "Keine Antwort erhalten."
    except Exception as e:
        return f"Verbindung zum Kernsystem unterbrochen ({e})."

def get_disk_percent():
    try:
        root = os.path.abspath(os.sep)
        return psutil.disk_usage(root).percent
    except Exception:
        return 0.0

def get_net_percent_and_rate():
    io = psutil.net_io_counters()
    now_bytes = io.bytes_sent + io.bytes_recv
    now_time = time.time()
    prev_bytes, prev_time = st.session_state.get("net_prev", (now_bytes, now_time))
    dt = max(now_time - prev_time, 0.5)
    rate_mbps = ((now_bytes - prev_bytes) * 8 / 1_000_000) / dt
    st.session_state.net_prev = (now_bytes, now_time)
    pct = max(0.0, min(100.0, (rate_mbps / MAX_NET_MBPS) * 100))
    return pct, max(0.0, rate_mbps)

def get_gpu_percent():
    if GPU_OK:
        try:
            util = pynvml.nvmlDeviceGetUtilizationRates(GPU_HANDLE)
            return float(util.gpu), "GPU"
        except Exception:
            pass
    return get_disk_percent(), "DISK"

# ---------- Session state ----------

defaults = {
    "messages": [{"role": "assistant", "text": "Guten Tag, wie kann ich Ihnen heute helfen?"}],
    "ai_state": "idle",
    "last_speak_time": 0.0,
    "needs_response": False,
    "logs": ["> INITIALIZING SYSTEM...", "> LOADING CORE MODULES...", "> CONNECTING TO DEVICES...",
             "> SYSTEM CHECK... OK", "> ALL SYSTEMS OPERATIONAL"],
    "chart": [45, 50, 48, 55, 60, 58, 62, 59, 65, 61, 68, 64, 70, 66, 72, 69, 74, 71, 76, 73],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------- Real-time PC stats (computed once per run, reused everywhere below) ----------

cpu = psutil.cpu_percent(interval=None) if PSUTIL_OK else 42.0
ram = psutil.virtual_memory().percent if PSUTIL_OK else 68.0
if PSUTIL_OK:
    net_pct, net_rate = get_net_percent_and_rate()
    gpu_pct, gpu_label = get_gpu_percent()
else:
    net_pct, net_rate, gpu_pct, gpu_label = 31.0, 0.0, 57.0, "GPU"

# ---------- Live ticking ----------

tick = st_autorefresh(interval=2000, key="hud_tick") if AUTOREFRESH_OK else 0
if tick > 0:
    st.session_state.chart = st.session_state.chart[1:] + [round(cpu, 1)]
    if tick % 4 == 0:
        opts = ["ROUTINE SCAN COMPLETE", "MEMORY OPTIMIZED", f"NETWORK LATENCY: {random.randint(8,28)}MS",
                "SECURITY SWEEP OK", "CACHE CLEARED", "SENSOR ARRAY NOMINAL"]
        st.session_state.logs = st.session_state.logs[-6:] + [f"> {random.choice(opts)}"]
    if st.session_state.ai_state == "speaking" and time.time() - st.session_state.last_speak_time > 3:
        st.session_state.ai_state = "idle"

# ---------- Chat input (Streamlit pins this to the page bottom) ----------

user_msg = st.chat_input("Frag JARVIS etwas...")
if user_msg and user_msg.strip() and st.session_state.ai_state != "thinking":
    st.session_state.messages.append({"role": "user", "text": user_msg.strip()})
    st.session_state.ai_state = "thinking"
    st.session_state.needs_response = True

# ---------- Top bar ----------

tcol1, tcol2 = st.columns([3, 1])
with tcol1:
    st.markdown(
        f'<span style="font-size:26px; letter-spacing:0.2em; color:{CYAN_BRIGHT}; font-weight:700;">JARVIS OS</span>'
        f'<span style="font-size:11px; padding:2px 8px; border-radius:4px; border:1px solid {BORDER}; color:{DIM}; margin-left:10px;">v2.7.1 &middot; Streamlit</span>',
        unsafe_allow_html=True,
    )
with tcol2:
    st.markdown(
        f'<div style="font-size:15px; letter-spacing:0.15em; text-align:right; padding-top:6px;">{datetime.now().strftime("%H:%M:%S")}</div>',
        unsafe_allow_html=True,
    )
st.markdown(f'<hr style="border-color:{BORDER}; margin:10px 0 18px 0;">', unsafe_allow_html=True)

# ---------- Main layout ----------

left, center, right = st.columns([1, 1.15, 1])

with left:
    gauges = "".join([
        radial_gauge_html(cpu, "CPU"), radial_gauge_html(ram, "RAM"),
        radial_gauge_html(net_pct, "NET"), radial_gauge_html(gpu_pct, gpu_label),
    ])
    net_note = f'<div style="font-size:9px; color:{DIM}; text-align:center; margin-top:6px;">NET: {net_rate:.1f} Mbit/s</div>'
    st.markdown(panel_html("SYSTEM STATUS", f'<div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; justify-items:center;">{gauges}</div>{net_note}'), unsafe_allow_html=True)

    log_lines = "".join(f'<div style="font-size:10px; color:{DIM}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{escape(l)}</div>' for l in st.session_state.logs)
    st.markdown(panel_html("SYSTEM LOG", f'<div style="display:flex; flex-direction:column; gap:4px;">{log_lines}</div>'), unsafe_allow_html=True)

    w = get_weather()
    env = (f'<div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; font-size:11px;">'
           f'<div>&#127777;&#65039; {w["temp"]}&deg;C</div><div>&#128167; {w["humidity"]}%</div>'
           f'<div>&#9202;&#65039; {w["pressure"]} hPa</div><div>&#127788;&#65039; {w["wind"]} km/h</div></div>')
    st.markdown(panel_html("ENVIRONMENT", env), unsafe_allow_html=True)

with center:
    components.html(orb_component(st.session_state.ai_state), height=320)
    if not AUTOREFRESH_OK or not PSUTIL_OK:
        st.caption("Hinweis: siehe Seitenleiste fuer optionale Pakete.")

with right:
    msgs_html = ""
    for m in st.session_state.messages[-8:]:
        color = CYAN_BRIGHT if m["role"] == "assistant" else DIM
        who = "JARVIS" if m["role"] == "assistant" else "DU"
        msgs_html += f'<div style="font-size:11px; line-height:1.5; margin-bottom:6px;"><span style="color:{color};">{who}:</span> {escape(m["text"])}</div>'
    if st.session_state.ai_state == "thinking":
        msgs_html += f'<div style="font-size:10px; color:{DIM};">JARVIS denkt nach...</div>'
    st.markdown(panel_html("CONVERSATION", msgs_html, height=240), unsafe_allow_html=True)

    chart_row = f'<div style="display:flex; align-items:center; gap:10px;">{sparkline_svg(st.session_state.chart)}{radial_gauge_html(st.session_state.chart[-1], "LOAD", size=52)}</div>'
    st.markdown(panel_html("DATA ANALYSIS", chart_row), unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:{PANEL_BG}; border:1px solid {BORDER}; border-radius:10px; padding:12px 12px 2px 12px;
                box-shadow:0 0 24px rgba(34,211,238,0.06);">
      <div style="display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid {BORDER}; padding-bottom:8px; margin-bottom:2px;">
        <span style="font-size:10px; letter-spacing:0.15em; color:{CYAN};">SYSTEM CONTROL</span>
      </div>
    """, unsafe_allow_html=True)
    st.toggle("Kameras", value=True, key="tg_cam")
    st.toggle("Sensoren", value=True, key="tg_sen")
    st.toggle("Netzwerk", value=True, key="tg_net")
    st.toggle("Sicherheit", value=True, key="tg_sec")
    st.toggle("Strom", value=True, key="tg_pow")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Bottom row ----------

st.markdown("<div style='margin-top:4px;'></div>", unsafe_allow_html=True)
bcol1, bcol2 = st.columns(2)
with bcol1:
    if PSUTIL_OK:
        delta = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
        hh, rem = divmod(int(delta.total_seconds()), 3600)
        mm, ss = divmod(rem, 60)
        uptime_str = f"{hh:02d}:{mm:02d}:{ss:02d}"
    else:
        uptime_str = "--:--:--"
    st.markdown(panel_html("SYSTEM UPTIME", f'<div style="font-size:22px; letter-spacing:0.1em; color:{CYAN_BRIGHT};">{uptime_str}</div>'), unsafe_allow_html=True)
with bcol2:
    notif = (f'<div style="font-size:10px; color:{DIM}; display:flex; flex-direction:column; gap:4px;">'
             f'<div>&bull; System-Update verfuegbar</div><div>&bull; Backup abgeschlossen</div>'
             f'<div>&bull; {len(st.session_state.messages)-1} Nachrichten ausgetauscht</div></div>')
    st.markdown(panel_html("NOTIFICATIONS", notif), unsafe_allow_html=True)

# ---------- Sidebar ----------

with st.sidebar:
    st.markdown(f'<span style="color:{CYAN_BRIGHT}; font-size:14px; letter-spacing:0.1em;">JARVIS &middot; EINSTELLUNGEN</span>', unsafe_allow_html=True)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.text_input("Anthropic API-Schluessel", type="password", key="api_key_input",
                       help="Alternativ als Umgebungsvariable ANTHROPIC_API_KEY setzen.")
        st.caption("Der Schluessel bleibt lokal in dieser Sitzung.")
    else:
        st.caption("API-Schluessel aus Umgebungsvariable geladen.")
    if not AUTOREFRESH_OK:
        st.info("Fuer Live-Updates: pip install streamlit-autorefresh")
    if not PSUTIL_OK:
        st.info("Fuer echte CPU/RAM-Werte: pip install psutil")
    if PSUTIL_OK and not GPU_OK:
        st.caption("Kein NVIDIA-GPU/pynvml erkannt - GPU-Gauge zeigt stattdessen die Festplattenbelegung.")

# ---------- Handle pending API call (after everything above has rendered) ----------

if st.session_state.needs_response:
    st.session_state.needs_response = False
    reply = call_jarvis_api(st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "text": reply})
    st.session_state.ai_state = "speaking"
    st.session_state.last_speak_time = time.time()
    st.rerun()
