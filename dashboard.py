import streamlit as st
import requests
import uuid
import pandas as pd

# 1. Configuration & Session Setup
# Update this with your actual Render URL
API_URL = "https://fs-inf-slope.onrender.com" 

st.set_page_config(page_title="Peru Geotech Pro", layout="wide")

# Language Dictionary
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
        "calc_btn": "Run Calculation",
        "history_title": "Your Recent Calculations",
        "session_info": "Private to your current browser",
        "no_data": "No calculations yet. Use the sidebar to start.",
        "guide_title": "Reference Guide",
        "thresholds": "**Stability Thresholds:**",
        "formula": "Formula used: Infinite Slope (Effective Stress).",
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
        "calc_btn": "Ejecutar Cálculo",
        "history_title": "Sus Cálculos Recientes",
        "session_info": "Privado para su navegador actual",
        "no_data": "Aún no hay cálculos. Use la barra lateral.",
        "guide_title": "Guía de Referencia",
        "thresholds": "**Umbrales de Estabilidad:**",
        "formula": "Fórmula: Talud Infinito (Esfuerzos Efectivos).",
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
    soil_options = {
        1: "Relave Cicloneado (Arenas)" if lang == "Spanish" else "Cyclone Tailings (Sands)",
        2: "Grava Aluvial (Costa)" if lang == "Spanish" else "Alluvial Gravel (Coast)",
        3: "Arcilla Limosa (Sierra)" if lang == "Spanish" else "Silty Clay (Highlands)",
        4: "Relleno Estructural" if lang == "Spanish" else "Structural Fill"
    }
    
    selected_soil_id = st.selectbox(
        t[lang]["soil_label"], 
        options=list(soil_options.keys()),
        format_func=lambda x: soil_options[x]
    )
    
    slope_angle = st.slider(t[lang]["slope_label"], 10.0, 45.0, 25.0)
    z_depth = st.number_input(t[lang]["depth_label"], 1.0, 50.0, 5.0)
    water_ratio = st.slider(t[lang]["water_label"], 0.0, 1.0, 0.2)
    
    if st.button(t[lang]["calc_btn"], type="primary"):
        payload = {
            "session_id": st.session_state['session_id'],
            "soil_id": selected_soil_id,
            "slope_angle": slope_angle,
            "z_depth": z_depth,
            "water_table_ratio": water_ratio
        }
        try:
            requests.post(f"{API_URL}/calculate", json=payload)
            st.success("OK!")
        except:
            st.error("Error")

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
                # Translate column headers for display
                df.columns = ["Material", "Project", "Fs", "Status"] if lang == "English" else ["Material", "Proyecto", "Fs", "Estado"]
                st.table(df)
                
                latest_fs = history_data[0]['fs']
                st.metric(label=t[lang]["latest"], value=latest_fs)
            else:
                st.write(t[lang]["no_data"])
    except:
        st.warning("Connect to API...")

with col2:
    st.subheader(t[lang]["guide_title"])
    st.markdown(t[lang]["thresholds"])
    st.markdown("- 🟢 **Fs > 1.5**: Permanent \n- 🟡 **1.0 < Fs < 1.5**: Temporary \n- 🔴 **Fs < 1.0**: Failure")
    st.caption(t[lang]["formula"])
    # Add a simple diagram placeholder
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Slope_stability_analysis.png/300px-Slope_stability_analysis.png", 
             caption="Typical Failure Surface")

# --- FOOTER / DEVELOPER INFO ---
st.sidebar.divider()
st.sidebar.markdown(f"**Developer:** MSc Juan Avalos Carrión")
st.sidebar.markdown(f"Geophysics + Data Science Specialist")
st.sidebar.markdown(f"https://www.linkedin.com/in/juan-a-c-01457674/")
st.sidebar.caption(" 2026 ")
