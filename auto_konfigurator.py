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
        # Optional: eigene .glb-Datei hier eintragen (siehe Hinweis unten im Code)
        "glb_exterior": "",
        "glb_interior": "",
    },
    "Modell Comfort": {
        "beschreibung": "Geräumiger Kombi für Familie und Alltag.",
        "basispreis": 29000,
        "bild": "🚙",
        "form": "kombi",
        "glb_exterior": "",
        "glb_interior": "",
    },
    "Modell Explorer": {
        "beschreibung": "Robuster SUV für jedes Terrain.",
        "basispreis": 38000,
        "bild": "🚐",
        "form": "suv",
        "glb_exterior": "",
        "glb_interior": "",
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
INNEN_MATERIAL = {
    "Stoff Standard": "Stoff",
    "Stoff/Leder Kombination": "Stoff/Leder",
    "Vollleder": "Leder",
    "Vollleder mit Sitzheizung & -belüftung": "Leder (beheizt/belüftet)",
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
                   hat_spoiler, hat_glasdach, form, glb_exterior_url, glb_interior_url):
    """Erzeugt ein interaktives Three.js-Auto (Außen- und Innenansicht),
    das auf die Konfiguration reagiert. Wenn glb_exterior_url / glb_interior_url
    gesetzt sind, wird stattdessen das echte 3D-Modell per GLTFLoader geladen."""

    geometrie = {
        "sport":  dict(body_h=0.55, body_len=4.2, cabin_h=0.5,  ground_clear=0.32, roof_len=1.6),
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
        exteriorGroup.add(spoilerBase);
        var spoilerWing = new THREE.Mesh(new THREE.BoxGeometry(0.5,0.05,1.05), spoilerMat);
        spoilerWing.position.set(-geo.body_len/2*0.92, geo.body_h + 0.42, 0);
        exteriorGroup.add(spoilerWing);
        """

    glasdach_js = ""
    if hat_glasdach:
        glasdach_js = """
        var glassMat = new THREE.MeshPhysicalMaterial({color:0x224466, transparent:true, opacity:0.55, metalness:0.2, roughness:0.05});
        var glassRoof = new THREE.Mesh(new THREE.BoxGeometry(geo.roof_len*0.95, 0.03, 1.42), glassMat);
        glassRoof.position.set(0.1, geo.body_h + geo.cabin_h + 0.01, 0);
        exteriorGroup.add(glassRoof);
        var glassRoofInterior = new THREE.Mesh(new THREE.BoxGeometry(1.05, 0.02, 1.15), glassMat.clone());
        glassRoofInterior.position.set(0.05, 1.28, 0);
        interiorGroup.add(glassRoofInterior);
        """

    html = f"""
    <div id="car-wrap" style="position:relative; width:100%;">
      <div id="car-container" style="width:100%; height:460px; border-radius:12px; overflow:hidden; background:linear-gradient(180deg,#dfe7ee 0%,#f6f8fa 60%);"></div>
      <div id="view-toggle" style="position:absolute; top:12px; left:12px; z-index:5; display:flex; gap:6px;">
        <button id="btn-exterior" style="padding:6px 14px; border-radius:20px; border:none; background:#1c1c1e; color:white; font-size:13px; cursor:pointer;">Außenansicht</button>
        <button id="btn-interior" style="padding:6px 14px; border-radius:20px; border:1px solid #1c1c1e; background:white; color:#1c1c1e; font-size:13px; cursor:pointer;">Innenansicht</button>
      </div>
      <div id="loading-msg" style="position:absolute; bottom:10px; left:12px; z-index:5; font-size:11px; color:#666;">Ziehen zum Drehen</div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
    <script>
    (function() {{
        var container = document.getElementById('car-container');
        var scene = new THREE.Scene();
        var camera = new THREE.PerspectiveCamera(42, container.clientWidth/container.clientHeight, 0.05, 100);

        var exteriorCamPos = new THREE.Vector3(4.2, 2.1, 4.6);
        var exteriorLookAt = new THREE.Vector3(0, 0.4, 0);
        var interiorCamPos = new THREE.Vector3(-0.15, 1.15, 0.05);
        var interiorLookAt = new THREE.Vector3(-1.6, 1.05, 0.1);

        camera.position.copy(exteriorCamPos);
        camera.lookAt(exteriorLookAt);
        var currentLookAt = exteriorLookAt.clone();

        var renderer = new THREE.WebGLRenderer({{antialias:true, alpha:true}});
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.shadowMap.enabled = true;
        container.appendChild(renderer.domElement);

        var hemi = new THREE.HemisphereLight(0xffffff, 0x666666, 1.1);
        scene.add(hemi);
        var dir = new THREE.DirectionalLight(0xffffff, 1.0);
        dir.position.set(5,8,3);
        dir.castShadow = true;
        dir.shadow.mapSize.set(1024,1024);
        scene.add(dir);
        var interiorLight = new THREE.PointLight(0xfff2d9, 0.6);
        interiorLight.position.set(0, 1.6, 0);
        scene.add(interiorLight);

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
        var exteriorGroup = new THREE.Group();
        var interiorGroup = new THREE.Group();
        carGroup.add(exteriorGroup);
        carGroup.add(interiorGroup);
        scene.add(carGroup);

        var bodyColor = new THREE.Color("{karosserie_farbe}");
        var interiorColor = new THREE.Color("{innen_farbe}");
        var extExternalUrl = "{glb_exterior_url}";
        var intExternalUrl = "{glb_interior_url}";

        // ============================================================
        // ECHTE 3D-MODELLE (glTF/GLB) EINBINDEN
        // Wenn du eigene, lizenzierte .glb-Dateien hast: URL oben in
        // Python bei MODELLE[...]["glb_exterior"] / ["glb_interior"]
        // eintragen. Dieser Block lädt sie dann automatisch anstelle
        // des prozeduralen Platzhaltermodells.
        // ============================================================
        var usingRealExterior = false;
        var usingRealInterior = false;

        if (extExternalUrl.length > 0) {{
            var loader1 = new THREE.GLTFLoader();
            loader1.load(extExternalUrl, function(gltf) {{
                var model = gltf.scene;
                model.traverse(function(node) {{
                    if (node.isMesh) {{
                        node.castShadow = true;
                        // Falls das Modell ein Material namens "Body"/"Paint" hat, einfärben:
                        if (node.material && /body|paint|karosserie/i.test(node.material.name || "")) {{
                            node.material.color = bodyColor;
                        }}
                    }}
                }});
                exteriorGroup.add(model);
                usingRealExterior = true;
            }}, undefined, function(err) {{
                console.warn("Externes Exterieur-Modell konnte nicht geladen werden, nutze Platzhalter.", err);
                buildPlaceholderExterior();
            }});
        }} else {{
            buildPlaceholderExterior();
        }}

        if (intExternalUrl.length > 0) {{
            var loader2 = new THREE.GLTFLoader();
            loader2.load(intExternalUrl, function(gltf) {{
                var model = gltf.scene;
                model.traverse(function(node) {{
                    if (node.isMesh && node.material && /seat|leather|innen|sitz/i.test(node.material.name || "")) {{
                        node.material.color = interiorColor;
                    }}
                }});
                interiorGroup.add(model);
                usingRealInterior = true;
            }}, undefined, function(err) {{
                console.warn("Externes Interieur-Modell konnte nicht geladen werden, nutze Platzhalter.", err);
                buildPlaceholderInterior();
            }});
        }} else {{
            buildPlaceholderInterior();
        }}

        // ============================================================
        // PLATZHALTER-MODELLE (prozedural, laufen garantiert offline)
        // ============================================================
        function buildPlaceholderExterior() {{
            var bodyMat = new THREE.MeshStandardMaterial({{color: bodyColor, metalness:0.55, roughness:0.35}});
            var body = new THREE.Mesh(new THREE.BoxGeometry(geo.body_len, geo.body_h, 1.85), bodyMat);
            body.position.y = geo.ground_clear + geo.body_h/2;
            body.castShadow = true;
            exteriorGroup.add(body);

            var cabin = new THREE.Mesh(new THREE.BoxGeometry(geo.roof_len, geo.cabin_h, 1.6), bodyMat);
            cabin.position.set(0.1, geo.ground_clear + geo.body_h + geo.cabin_h/2, 0);
            cabin.castShadow = true;
            exteriorGroup.add(cabin);

            var windowMat = new THREE.MeshStandardMaterial({{color:0x223344, metalness:0.1, roughness:0.15, transparent:true, opacity:0.85}});
            var windowBand = new THREE.Mesh(new THREE.BoxGeometry(geo.roof_len*1.001, geo.cabin_h*0.5, 1.62), windowMat);
            windowBand.position.set(0.1, geo.ground_clear + geo.body_h + geo.cabin_h*0.28, 0);
            exteriorGroup.add(windowBand);

            {glasdach_js}
            {spoiler_js}

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
            exteriorGroup.add(createWheel(axleX, 0.95));
            exteriorGroup.add(createWheel(axleX, -0.95));
            exteriorGroup.add(createWheel(-axleX, 0.95));
            exteriorGroup.add(createWheel(-axleX, -0.95));
        }}

        function buildPlaceholderInterior() {{
            var seatMat = new THREE.MeshStandardMaterial({{color: interiorColor, roughness:0.7}});
            var dashMat = new THREE.MeshStandardMaterial({{color:0x2a2a2a, roughness:0.5}});
            var trimMat = new THREE.MeshStandardMaterial({{color: interiorColor.clone().offsetHSL(0,0,-0.08), roughness:0.6}});

            // Armaturenbrett
            var dash = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.35, 1.5), dashMat);
            dash.position.set(-1.55, 1.0, 0);
            interiorGroup.add(dash);

            // Lenkrad
            var wheelRing = new THREE.Mesh(new THREE.TorusGeometry(0.17, 0.02, 12, 24), dashMat);
            wheelRing.rotation.y = Math.PI/2;
            wheelRing.position.set(-1.3, 1.05, 0.35);
            interiorGroup.add(wheelRing);
            var wheelHub = new THREE.Mesh(new THREE.CylinderGeometry(0.03,0.03,0.15,12), dashMat);
            wheelHub.rotation.z = Math.PI/2;
            wheelHub.position.set(-1.35, 1.05, 0.35);
            interiorGroup.add(wheelHub);

            // Sitze (Fahrer + Beifahrer)
            function createSeat(z) {{
                var seatGroup = new THREE.Group();
                var cushion = new THREE.Mesh(new THREE.BoxGeometry(0.5,0.12,0.5), seatMat);
                cushion.position.set(0, 0.55, 0);
                seatGroup.add(cushion);
                var backrest = new THREE.Mesh(new THREE.BoxGeometry(0.12,0.6,0.48), seatMat);
                backrest.position.set(-0.22, 0.85, 0);
                seatGroup.add(backrest);
                var headrest = new THREE.Mesh(new THREE.BoxGeometry(0.12,0.15,0.3), seatMat);
                headrest.position.set(-0.22, 1.22, 0);
                seatGroup.add(headrest);
                seatGroup.position.set(-0.55, 0, z);
                return seatGroup;
            }}
            interiorGroup.add(createSeat(0.35));
            interiorGroup.add(createSeat(-0.35));

            // Türverkleidung / Mittelkonsole
            var console_ = new THREE.Mesh(new THREE.BoxGeometry(0.9,0.35,0.18), trimMat);
            console_.position.set(-0.7, 0.62, 0);
            interiorGroup.add(console_);

            var doorLeft = new THREE.Mesh(new THREE.BoxGeometry(1.6,0.55,0.08), trimMat);
            doorLeft.position.set(-0.55, 0.85, 0.78);
            interiorGroup.add(doorLeft);
            var doorRight = doorLeft.clone();
            doorRight.position.z = -0.78;
            interiorGroup.add(doorRight);

            // Dachhimmel
            var headliner = new THREE.Mesh(new THREE.BoxGeometry(2.0,0.05,1.5), new THREE.MeshStandardMaterial({{color:0xe8e8e8, roughness:0.9}}));
            headliner.position.set(-0.5, 1.42, 0);
            interiorGroup.add(headliner);
        }}

        // ============================================================
        // ANSICHT UMSCHALTEN (Außen / Innen)
        // ============================================================
        var mode = "exterior";
        var btnExt = document.getElementById('btn-exterior');
        var btnInt = document.getElementById('btn-interior');
        var loadingMsg = document.getElementById('loading-msg');

        function setMode(newMode) {{
            mode = newMode;
            if (mode === "exterior") {{
                btnExt.style.background = "#1c1c1e"; btnExt.style.color = "white"; btnExt.style.border = "none";
                btnInt.style.background = "white"; btnInt.style.color = "#1c1c1e"; btnInt.style.border = "1px solid #1c1c1e";
                exteriorGroup.visible = true;
                interiorGroup.visible = false;
                loadingMsg.textContent = "Ziehen zum Drehen";
            }} else {{
                btnInt.style.background = "#1c1c1e"; btnInt.style.color = "white"; btnInt.style.border = "none";
                btnExt.style.background = "white"; btnExt.style.color = "#1c1c1e"; btnExt.style.border = "1px solid #1c1c1e";
                exteriorGroup.visible = false;
                interiorGroup.visible = true;
                loadingMsg.textContent = "Ziehen zum Umschauen";
            }}
        }}
        btnExt.addEventListener('click', function() {{ setMode("exterior"); }});
        btnInt.addEventListener('click', function() {{ setMode("interior"); }});
        setMode("exterior");

        // ============================================================
        // INTERAKTION: Ziehen zum Drehen / Umschauen
        // ============================================================
        var isDragging = false;
        var prevX = 0, prevY = 0;
        var rotationY = 0.5;
        var lookYaw = 0, lookPitch = 0;
        var autoRotate = true;

        container.addEventListener('pointerdown', function(e) {{
            isDragging = true; autoRotate = false; prevX = e.clientX; prevY = e.clientY;
        }});
        window.addEventListener('pointerup', function() {{ isDragging = false; }});
        window.addEventListener('pointermove', function(e) {{
            if (!isDragging) return;
            var dx = e.clientX - prevX;
            var dy = e.clientY - prevY;
            prevX = e.clientX; prevY = e.clientY;
            if (mode === "exterior") {{
                rotationY += dx * 0.01;
            }} else {{
                lookYaw -= dx * 0.005;
                lookPitch = Math.max(-0.5, Math.min(0.5, lookPitch - dy * 0.005));
            }}
        }});

        function animate() {{
            requestAnimationFrame(animate);
            if (mode === "exterior") {{
                if (autoRotate) {{ rotationY += 0.004; }}
                carGroup.rotation.y = rotationY;
                camera.position.copy(exteriorCamPos);
                camera.lookAt(exteriorLookAt);
            }} else {{
                carGroup.rotation.y = 0;
                camera.position.copy(interiorCamPos);
                var lookTarget = new THREE.Vector3(
                    interiorCamPos.x + Math.cos(lookYaw) * -1.5,
                    interiorCamPos.y + lookPitch,
                    interiorCamPos.z + Math.sin(lookYaw) * 1.5
                );
                camera.lookAt(lookTarget);
            }}
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
    components.html(html, height=500)


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

with st.sidebar.expander("ℹ️ Eigene 3D-Modelle einbinden"):
    st.write(
        "Um echte glTF/GLB-Automodelle zu nutzen, trage im Code bei "
        "`MODELLE[...]['glb_exterior']` und `['glb_interior']` die URL "
        "deiner eigenen, lizenzierten Datei ein (z. B. gehostet auf "
        "GitHub Pages, S3 o. Ä.). Ohne URL wird automatisch das "
        "eingebaute Platzhaltermodell verwendet."
    )

# ---------------------------------------------------------
# HAUPTBEREICH
# ---------------------------------------------------------

st.title("🚗 Auto-Konfigurator")
st.caption("Stellen Sie sich Ihr individuelles Fahrzeug zusammen – wechseln Sie zwischen Außen- und Innenansicht.")

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
    glb_exterior_url=modell["glb_exterior"],
    glb_interior_url=modell["glb_interior"],
)

col_left, col_right = st.columns([1.3, 1])

with col_left:
    st.markdown(f"## {modell['bild']} {modell_name}")
    st.write(modell["beschreibung"])

    st.markdown("### Ihre Konfiguration")
    st.write(f"**Farbe:** {farbe}")
    st.write(f"**Felgen:** {felgen}")
    st.write(f"**Innenausstattung:** {innenausstattung} ({INNEN_MATERIAL[innenausstattung]})")
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
st.caption("Hinweis: Alle Preise sind unverbindliche Beispielpreise. Ohne eigene .glb-Dateien wird eine stilisierte Platzhalter-Visualisierung angezeigt.")
