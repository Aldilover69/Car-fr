import streamlit as st

st.set_page_config(page_title="Auto-Konfigurator", page_icon="🚗", layout="wide")

# ---------------------------------------------------------
# DATEN
# ---------------------------------------------------------

MODELLE = {
    "Modell Sport": {
        "beschreibung": "Sportliche Limousine mit dynamischem Design.",
        "basispreis": 32000,
        "bild": "🚗",
    },
    "Modell Comfort": {
        "beschreibung": "Geräumiger Kombi für Familie und Alltag.",
        "basispreis": 29000,
        "bild": "🚙",
    },
    "Modell Explorer": {
        "beschreibung": "Robuster SUV für jedes Terrain.",
        "basispreis": 38000,
        "bild": "🚐",
    },
}

FARBEN = {
    "Weiß": 0,
    "Schwarz Metallic": 650,
    "Silber Metallic": 650,
    "Blau Metallic": 750,
    "Rot (Sonderlackierung)": 1200,
}

FELGEN = {
    "16 Zoll Stahlfelgen": 0,
    "17 Zoll Leichtmetallfelgen": 500,
    "18 Zoll Leichtmetallfelgen": 900,
    "19 Zoll Sportfelgen": 1500,
}

INNENAUSSTATTUNG = {
    "Stoff Standard": 0,
    "Stoff/Leder Kombination": 800,
    "Vollleder": 1800,
    "Vollleder mit Sitzheizung & -belüftung": 2600,
}

MOTOREN = {
    "1.5 Benziner (110 PS)": 0,
    "2.0 Benziner (150 PS)": 1500,
    "2.0 Diesel (150 PS)": 1900,
    "Plug-in-Hybrid (204 PS)": 4500,
    "Vollelektrisch (aWD, 300 PS)": 7500,
}

PAKETE = {
    "Sound-Paket (Premium-Soundsystem)": 700,
    "Assistenz-Paket (Spurhalte-, Notbremsassistent, Tempomat)": 1100,
    "Komfort-Paket (Klimaautomatik, Sitzverstellung elektrisch)": 950,
    "Winter-Paket (beheizbares Lenkrad, Frontscheibe)": 400,
    "Panorama-Glasdach": 1300,
}

# ---------------------------------------------------------
# HILFSFUNKTIONEN
# ---------------------------------------------------------

def format_preis(betrag: float) -> str:
    return f"{betrag:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------
# SIDEBAR: KONFIGURATION
# ---------------------------------------------------------

st.sidebar.title("🔧 Konfiguration")

modell_name = st.sidebar.selectbox("Modell wählen", list(MODELLE.keys()))
modell = MODELLE[modell_name]

st.sidebar.markdown("---")

farbe = st.sidebar.selectbox("Farbe & Lackierung", list(FARBEN.keys()))
felgen = st.sidebar.selectbox("Felgen", list(FELGEN.keys()))
innenausstattung = st.sidebar.selectbox("Innenausstattung", list(INNENAUSSTATTUNG.keys()))
motor = st.sidebar.selectbox("Motor/Antrieb", list(MOTOREN.keys()))

st.sidebar.markdown("---")
st.sidebar.subheader("Zusatzpakete")
gewaehlte_pakete = []
for paket, preis in PAKETE.items():
    if st.sidebar.checkbox(f"{paket} (+{format_preis(preis)})", key=paket):
        gewaehlte_pakete.append(paket)

# ---------------------------------------------------------
# HAUPTBEREICH
# ---------------------------------------------------------

st.title("🚗 Auto-Konfigurator")
st.caption("Stellen Sie sich Ihr individuelles Fahrzeug zusammen.")

col_left, col_right = st.columns([1.3, 1])

with col_left:
    st.markdown(f"## {modell['bild']} {modell_name}")
    st.write(modell["beschreibung"])

    st.markdown("### Ihre Konfiguration")
    st.write(f"**Farbe:** {farbe}")
    st.write(f"**Felgen:** {felgen}")
    st.write(f"**Innenausstattung:** {innenausstattung}")
    st.write(f"**Motor:** {motor}")

    if gewaehlte_pakete:
        st.write("**Zusatzpakete:**")
        for p in gewaehlte_pakete:
            st.write(f"- {p}")
    else:
        st.write("**Zusatzpakete:** keine ausgewählt")

with col_right:
    st.markdown("### 💶 Preisübersicht")

    basispreis = modell["basispreis"]
    preis_farbe = FARBEN[farbe]
    preis_felgen = FELGEN[felgen]
    preis_innen = INNENAUSSTATTUNG[innenausstattung]
    preis_motor = MOTOREN[motor]
    preis_pakete = sum(PAKETE[p] for p in gewaehlte_pakete)

    zeilen = [
        ("Basispreis", basispreis),
        ("Farbe/Lackierung", preis_farbe),
        ("Felgen", preis_felgen),
        ("Innenausstattung", preis_innen),
        ("Motor/Antrieb", preis_motor),
    ]
    if preis_pakete > 0:
        zeilen.append(("Zusatzpakete", preis_pakete))

    for bezeichnung, betrag in zeilen:
        c1, c2 = st.columns([2, 1])
        c1.write(bezeichnung)
        c2.write(format_preis(betrag) if betrag > 0 else "inklusive")

    gesamtpreis = basispreis + preis_farbe + preis_felgen + preis_innen + preis_motor + preis_pakete

    st.markdown("---")
    st.markdown(f"## Gesamtpreis: {format_preis(gesamtpreis)}")

    st.button("🛒 Konfiguration anfragen", use_container_width=True, type="primary")

st.markdown("---")
st.caption("Hinweis: Alle Preise sind unverbindliche Beispielpreise (Netto- bzw. Bruttoangabe je nach Konfiguration).")
