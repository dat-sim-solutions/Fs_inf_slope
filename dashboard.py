import streamlit as st
import requests
import uuid
import pandas as pd

# 1. Configuration & Session Setup
API_URL = "https://fs-inf-slope.onrender.com" 

st.set_page_config(page_title="Peru Geotech Pro", layout="wide")

# Updated Language Dictionary with Seismic terms
t = {
    "English": {
        "title": "🇵🇪 Slope Stability Quick-Check",
        "subtitle": "Professional Factor of Safety (Fs) calculator for Andean Engineering.",
        "settings": "Settings",
        "lang_label": "Language / Idioma",
        "soil_label": "Select Soil Profile",
        "slope_label": "Slope Angle (β)°",
        "depth_label": "Failure Depth (z) meters",
        "water_label": "Water Table Ratio (u)",
        "seismic_label": "Seismic Coeff. (kh)",
        "calc_btn": "Run Calculation",
        "history_title": "Your Recent Calculations",
        "session_info": "Private to your current browser",
        "no_data": "No calculations yet. Use the sidebar to start.",
        "guide_title": "Reference Guide",
        "thresholds": "**Stability Thresholds:**",
        "formula": "Formula: Infinite Slope (Seismic Pseudostatic).",
        "latest": "Latest Factor of Safety"
    },
    "Spanish": {
        "title": "🇵🇪 Chequeo Rápido de Taludes",
        "subtitle": "Calculadora profesional de Factor de Seguridad (Fs) para ingeniería andina.",
        "settings": "Configuración",
        "lang_label": "Idioma / Language",
        "soil_label": "Seleccionar Perfil de Suelo",
        "slope_label": "Ángulo del Talud (β)°",
        "depth_label": "Profundidad de Falla (z) metros",
        "water_label": "Relación de Nivel Freático (u)",
        "seismic_label": "Coef. Sísmico (kh)",
        "calc_btn": "Ejecutar Cálculo",
        "history_title": "Sus Cálculos Recientes",
        "session_info": "Privado para su navegador actual",
        "no_data": "Aún no hay cálculos. Use la barra lateral.",
        "guide_title": "Guía de Referencia",
        "thresholds": "**Umbrales de Estabilidad:**",
        "formula": "Fórmula: Talud Infinito (Seismo-Pseudoestático).",
        "latest": "Último Factor de Seguridad"
    }
}

# Persistent Session ID
if 'session_id' not in st.session_state:
    st.session_state['session_id'] = str(uuid.uuid4())

# 2. Language Selection
with st.sidebar:
    lang = st.radio("Language / Idioma", ["Spanish", "English"], horizontal=True)
    st.divider()
    st.header(t[lang]["settings"])

# 3. Sidebar Inputs
with st.sidebar:
    # Updated list matching your Neon Database Seed
    soil_options = {
        1: "Grava Aluvial (Costa)" if lang == "Spanish" else "Alluvial Gravel (Coast)",
        2: "Arena Eólica (Costa)" if lang == "Spanish" else "Eolian Sand (Coast)",
        3: "Suelos Coluviales (Sierra)" if lang == "Spanish" else "Colluvial Soils (Sierra)",
        4: "Suelos Residuales (Sierra)" if lang == "Spanish" else "Residual Soils (Sierra)",
        5: "Suelo Laterítico (Selva)" if lang == "Spanish" else "Lateritic Soil (Jungle)",
        6: "Relave de Cobre (SM)" if lang == "Spanish" else "Copper Tailings (SM)",
        7: "Relave Polimetálico (ML)" if lang == "Spanish" else "Polymetallic Tailings (ML)",
        8: "Relave de Oro" if lang == "Spanish" else "Gold Tailings"
    }
    
    selected_soil_id = st.selectbox(
        t[lang]["soil_label"], 
        options=list(soil_options.keys()),
        format_func=lambda x: soil_options[x]
    )
    
    slope_angle = st.slider(t[lang]["slope_label"], 10.0, 45.0, 25.0)
    z_depth = st.number_input(t[lang]["depth_label"], 1.0, 50.0, 5.0)
    water_ratio = st.slider(t[lang]["water_label"], 0.0, 1.0, 0.0, help="0 = Dry; 1 = Saturated")
    
    # NEW: Seismic Coefficient Input
    kh_seismic = st.number_input(t[lang]["seismic_label"], 0.0, 0.3, 0.0, step=0.05, 
                                 help="Peruvian Zones: Z4=0.15, Z3=0.10, Z2=0.05")
    
    if st.button(t[lang]["calc_btn"], type="primary"):
        payload = {
            "session_id": st.session_state['session_id'],
            "soil_id": selected_soil_id,
            "project_id": 1,
            "slope_angle": slope_angle,
            "z_depth": z_depth,
            "water_table_ratio": water_ratio,
            "kh_seismic": kh_seismic  # Sent to API
        }
        try:
            res = requests.post(f"{API_URL}/calculate", json=payload)
            if res.status_code == 200:
                st.success("Calculation Saved!")
            else:
                st.error(f"API Error: {res.text}")
        except:
            st.error("Connection Failed")

# 4. Main Display
st.title(t[lang]["title"])
st.markdown(t[lang]["subtitle"])

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(t[lang]["history_title"])
    st.caption(f"Session ID: {st.session_state['session_id'][:8]}... ({t[lang]['session_info']})")
    
    try:
        history_res = requests.get(f"{API_URL}/history/{st.session_state['session_id']}")
        if history_res.status_code == 200:
            history_data = history_res.json().get("recent_calculations", [])
            if history_data:
                df = pd.DataFrame(history_data)
                # Ensure columns match what API returns
                df.columns = ["Material", "Project", "kh", "Fs", "Status"] if lang == "English" else ["Material", "Proyecto", "kh", "Fs", "Estado"]
                st.table(df)
                
                latest_fs = history_data[0]['fs']
                # Determine threshold based on seismic or static
                limit = 1.1 if history_data[0]['kh'] > 0 else 1.5
                st.metric(label=t[lang]["latest"], value=latest_fs, 
                          delta="SAFE" if latest_fs > limit else "CRITICAL",
                          delta_color="normal" if latest_fs > limit else "inverse")
            else:
                st.write(t[lang]["no_data"])
    except Exception as e:
        st.warning(f"Waiting for API data...")

with col2:
    st.subheader(t[lang]["guide_title"])
    st.markdown(t[lang]["thresholds"])
    st.markdown("Static Condition:")
    st.markdown("- 🟢 **Fs > 1.5**: Stable \n- 🔴 **Fs < 1.5**: Risk")
    st.markdown("Seismic Condition ($k_h > 0$):")
    st.markdown("- 🟢 **Fs > 1.1**: Stable \n- 🔴 **Fs < 1.1**: Risk")
    st.caption(t[lang]["formula"])

# --- FOOTER ---
st.sidebar.divider()
st.sidebar.markdown(f"**Developer:** MSc Juan Avalos Carrión")
st.sidebar.caption("Geotechnical Data Science | 2026")
st.sidebar.markdown(f"https://www.linkedin.com/in/juan-a-c-01457674/")
