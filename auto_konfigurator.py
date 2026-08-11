import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Auto-Konfigurator", page_icon="🚗", layout="wide")

# ---------------------------------------------------------
# DATEN
# ---------------------------------------------------------

MODELLE = {
    "Modell Sport": {
        "beschreibung": "Sportliche Limousine mit dynamischem Design.",
        "basispreis": 32000,
        "bild": "🚗",
        "form": "sport",
    },
    "Modell Comfort": {
        "beschreibung": "Geräumiger Kombi für Familie und Alltag.",
        "basispreis": 29000,
        "bild": "🚙",
        "form": "kombi",
    },
    "Modell Explorer": {
        "beschreibung": "Robuster SUV für jedes Terrain.",
        "basispreis": 38000,
        "bild": "🚐",
        "form": "suv",
    },
}

FARBEN = {
    "Weiß": 0,
    "Schwarz Metallic": 650,
    "Silber Metallic": 650,
    "Blau Metallic": 750,
    "Rot (Sonderlackierung)": 1200,
}
FARBEN_HEX = {
    "Weiß": "#f2f2f2",
    "Schwarz Metallic": "#1c1c1e",
    "Silber Metallic": "#b8bcc2",
    "Blau Metallic": "#2b4c7e",
    "Rot (Sonderlackierung)": "#a3221f",
}

FELGEN = {
    "16 Zoll Stahlfelgen": 0,
    "17 Zoll Leichtmetallfelgen": 500,
    "18 Zoll Leichtmetallfelgen": 900,
    "19 Zoll Sportfelgen": 1500,
}
FELGEN_ZOLL = {
    "16 Zoll Stahlfelgen": 16,
    "17 Zoll Leichtmetallfelgen": 17,
    "18 Zoll Leichtmetallfelgen": 18,
    "19 Zoll Sportfelgen": 19,
}
FELGEN_FARBE = {
    "16 Zoll Stahlfelgen": "#9aa0a6",
    "17 Zoll Leichtmetallfelgen": "#c9ccd1",
    "18 Zoll Leichtmetallfelgen": "#e2e4e8",
    "19 Zoll Sportfelgen": "#3a3a3c",
}

INNENAUSSTATTUNG = {
    "Stoff Standard": 0,
    "Stoff/Leder Kombination": 800,
    "Vollleder": 1800,
    "Vollleder mit Sitzheizung & -belüftung": 2600,
}
INNEN_HEX = {
    "Stoff Standard": "#4a4a4a",
    "Stoff/Leder Kombination": "#5c4433",
    "Vollleder": "#2e1f16",
    "Vollleder mit Sitzheizung & -belüftung": "#1f1512",
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


def render_3d_car(karosserie_farbe, felgen_farbe, felgen_zoll, innen_farbe,
                   hat_spoiler, hat_glasdach, form):
    """Erzeugt ein interaktives Three.js-Auto, das auf die Konfiguration reagiert."""

    # Karosserie-Maße je nach Fahrzeugform
    geometrie = {
        "sport":  dict(body_h=0.55, body_len=4.2, cabin_h=0.5, ground_clear=0.32, roof_len=1.6),
        "kombi":  dict(body_h=0.68, body_len=4.4, cabin_h=0.62, ground_clear=0.36, roof_len=2.2),
        "suv":    dict(body_h=0.85, body_len=4.3, cabin_h=0.72, ground_clear=0.55, roof_len=2.0),
    }[form]

    wheel_radius = 0.28 + (felgen_zoll - 16) * 0.025

    spoiler_js = ""
    if hat_spoiler:
        spoiler_js = """
        var spoilerMat = new THREE.MeshStandardMaterial({color: bodyColor, metalness:0.4, roughness:0.4});
        var spoilerBase = new THREE.Mesh(new THREE.BoxGeometry(0.08,0.05,0.9), spoilerMat);
        spoilerBase.position.set(-geo.body_len/2*0.92, geo.body_h + 0.28, 0);
        carGroup.add(spoilerBase);
        var spoilerWing = new THREE.Mesh(new THREE.BoxGeometry(0.5,0.05,1.05), spoilerMat);
        spoilerWing.position.set(-geo.body_len/2*0.92, geo.body_h + 0.42, 0);
        carGroup.add(spoilerWing);
        """

    glasdach_js = ""
    if hat_glasdach:
        glasdach_js = """
        var glassMat = new THREE.MeshPhysicalMaterial({color:0x224466, transparent:true, opacity:0.55, metalness:0.2, roughness:0.05});
        var glassRoof = new THREE.Mesh(new THREE.BoxGeometry(geo.roof_len*0.95, 0.03, 1.42), glassMat);
        glassRoof.position.set(0.1, geo.body_h + geo.cabin_h + 0.01, 0);
        carGroup.add(glassRoof);
        """

    html = f"""
    <div id="car-container" style="width:100%; height:430px; border-radius:12px; overflow:hidden; background:linear-gradient(180deg,#dfe7ee 0%,#f6f8fa 60%);"></div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script>
    (function() {{
        var container = document.getElementById('car-container');
        var scene = new THREE.Scene();
        var camera = new THREE.PerspectiveCamera(38, container.clientWidth/container.clientHeight, 0.1, 100);
        camera.position.set(4.2, 2.1, 4.6);
        camera.lookAt(0,0.4,0);

        var renderer = new THREE.WebGLRenderer({{antialias:true, alpha:true}});
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.shadowMap.enabled = true;
        container.appendChild(renderer.domElement);

        // Licht
        var hemi = new THREE.HemisphereLight(0xffffff, 0x666666, 1.1);
        scene.add(hemi);
        var dir = new THREE.DirectionalLight(0xffffff, 1.0);
        dir.position.set(5,8,3);
        dir.castShadow = true;
        dir.shadow.mapSize.set(1024,1024);
        scene.add(dir);

        // Boden
        var groundMat = new THREE.MeshStandardMaterial({{color:0xe4e8ec, roughness:0.9}});
        var ground = new THREE.Mesh(new THREE.CircleGeometry(6,48), groundMat);
        ground.rotation.x = -Math.PI/2;
        ground.receiveShadow = true;
        scene.add(ground);

        var geo = {{
            body_h: {geometrie['body_h']},
            body_len: {geometrie['body_len']},
            cabin_h: {geometrie['cabin_h']},
            ground_clear: {geometrie['ground_clear']},
            roof_len: {geometrie['roof_len']}
        }};

        var carGroup = new THREE.Group();
        var bodyColor = new THREE.Color("{karosserie_farbe}");

        // Karosserie (unten)
        var bodyMat = new THREE.MeshStandardMaterial({{color: bodyColor, metalness:0.55, roughness:0.35}});
        var body = new THREE.Mesh(new THREE.BoxGeometry(geo.body_len, geo.body_h, 1.85), bodyMat);
        body.position.y = geo.ground_clear + geo.body_h/2;
        body.castShadow = true;
        carGroup.add(body);

        // Kabine (oben)
        var cabin = new THREE.Mesh(new THREE.BoxGeometry(geo.roof_len, geo.cabin_h, 1.6), bodyMat);
        cabin.position.set(0.1, geo.ground_clear + geo.body_h + geo.cabin_h/2, 0);
        cabin.castShadow = true;
        carGroup.add(cabin);

        // Fenster (Innenfarbe scheint leicht durch)
        var interiorColor = new THREE.Color("{innen_farbe}");
        var windowMat = new THREE.MeshStandardMaterial({{color: interiorColor, metalness:0.1, roughness:0.2}});
        var windowBand = new THREE.Mesh(new THREE.BoxGeometry(geo.roof_len*1.001, geo.cabin_h*0.5, 1.62), windowMat);
        windowBand.position.set(0.1, geo.ground_clear + geo.body_h + geo.cabin_h*0.28, 0);
        carGroup.add(windowBand);

        {glasdach_js}
        {spoiler_js}

        // Räder
        var wheelR = {wheel_radius};
        var rimColor = new THREE.Color("{felgen_farbe}");
        var tireMat = new THREE.MeshStandardMaterial({{color:0x111111, roughness:0.9}});
        var rimMat = new THREE.MeshStandardMaterial({{color: rimColor, metalness:0.8, roughness:0.25}});

        function createWheel(x, z) {{
            var wheelGroup = new THREE.Group();
            var tire = new THREE.Mesh(new THREE.CylinderGeometry(wheelR, wheelR, 0.28, 24), tireMat);
            tire.rotation.z = Math.PI/2;
            tire.castShadow = true;
            wheelGroup.add(tire);
            var rim = new THREE.Mesh(new THREE.CylinderGeometry(wheelR*0.55, wheelR*0.55, 0.29, 6), rimMat);
            rim.rotation.z = Math.PI/2;
            wheelGroup.add(rim);
            wheelGroup.position.set(x, wheelR, z);
            return wheelGroup;
        }}

        var axleX = geo.body_len*0.32;
        carGroup.add(createWheel(axleX, 0.95));
        carGroup.add(createWheel(axleX, -0.95));
        carGroup.add(createWheel(-axleX, 0.95));
        carGroup.add(createWheel(-axleX, -0.95));

        scene.add(carGroup);

        // Interaktion: Ziehen zum Drehen, automatische Rotation wenn inaktiv
        var isDragging = false;
        var prevX = 0;
        var rotationY = 0.5;
        var autoRotate = true;

        container.addEventListener('pointerdown', function(e) {{
            isDragging = true; autoRotate = false; prevX = e.clientX;
        }});
        window.addEventListener('pointerup', function() {{ isDragging = false; }});
        window.addEventListener('pointermove', function(e) {{
            if (isDragging) {{
                var delta = e.clientX - prevX;
                rotationY += delta * 0.01;
                prevX = e.clientX;
            }}
        }});

        function animate() {{
            requestAnimationFrame(animate);
            if (autoRotate) {{ rotationY += 0.004; }}
            carGroup.rotation.y = rotationY;
            renderer.render(scene, camera);
        }}
        animate();

        window.addEventListener('resize', function() {{
            camera.aspect = container.clientWidth/container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        }});
    }})();
    </script>
    """
    components.html(html, height=450)


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
st.caption("Stellen Sie sich Ihr individuelles Fahrzeug zusammen – ziehen Sie am 3D-Modell, um es zu drehen.")

hat_spoiler = (modell["form"] == "sport")
hat_glasdach = "Panorama-Glasdach" in gewaehlte_pakete

render_3d_car(
    karosserie_farbe=FARBEN_HEX[farbe],
    felgen_farbe=FELGEN_FARBE[felgen],
    felgen_zoll=FELGEN_ZOLL[felgen],
    innen_farbe=INNEN_HEX[innenausstattung],
    hat_spoiler=hat_spoiler,
    hat_glasdach=hat_glasdach,
    form=modell["form"],
)

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
st.caption("Hinweis: Alle Preise sind unverbindliche Beispielpreise. Das 3D-Modell ist eine stilisierte Visualisierung, kein maßstabsgetreues CAD-Modell.")
