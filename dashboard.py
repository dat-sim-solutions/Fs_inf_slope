import streamlit as st
import requests
import uuid
import pandas as pd

# 1. Configuration & Session Setup
# REPLACE this with your actual Render API URL after deployment
API_URL = "https://fs-inf-slope.onrender.com/calculate" 

st.set_page_config(page_title="Peru Slope Safety Pro", layout="wide")

# Initialize a persistent Session ID for the user
if 'session_id' not in st.session_state:
    st.session_state['session_id'] = str(uuid.uuid4())

st.title("🇵🇪 Slope Stability Quick-Check")
st.markdown("Professional Factor of Safety (Fs) calculator for Andean Geotechnical Engineering.")

# 2. Sidebar - Input Parameters
with st.sidebar:
    st.header("Settings")
    
    # Material Selection - In a real app, you'd fetch this from GET /soils
    # For now, we match the IDs we inserted into Neon
    soil_options = {
        1: "Relave Cicloneado (Arenas)",
        2: "Grava Aluvial (Costa)",
        3: "Arcilla Limosa (Sierra)",
        4: "Relleno Estructural"
    }
    
    selected_soil_id = st.selectbox(
        "Select Soil Profile", 
        options=list(soil_options.keys()),
        format_func=lambda x: soil_options[x]
    )
    
    slope_angle = st.slider("Slope Angle (β)°", 10.0, 45.0, 25.0)
    z_depth = st.number_input("Failure Depth (z) meters", 1.0, 50.0, 5.0)
    water_ratio = st.slider("Water Table Ratio (u)", 0.0, 1.0, 0.2, help="0 = Dry, 1 = Fully Saturated")
    
    if st.button("Run Calculation", type="primary"):
        payload = {
            "session_id": st.session_state['session_id'],
            "soil_id": selected_soil_id,
            "slope_angle": slope_angle,
            "z_depth": z_depth,
            "water_table_ratio": water_ratio
        }
        
        try:
            response = requests.post(f"{API_URL}/calculate", json=payload)
            if response.status_code == 200:
                st.success("Calculation Saved to Cloud!")
            else:
                st.error(f"API Error: {response.text}")
        except Exception as e:
            st.error(f"Could not connect to API: {e}")

# 3. Main Display - Results & History
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Your Recent Calculations")
    st.info(f"Session ID: {st.session_state['session_id'][:8]}... (Private to your current browser)")
    
    try:
        history_res = requests.get(f"{API_URL}/history/{st.session_state['session_id']}")
        if history_res.status_code == 200:
            history_data = history_res.json().get("recent_calculations", [])
            
            if history_data:
                df = pd.DataFrame(history_data)
                
                # Apply conditional styling to the Fs column
                def color_fs(val):
                    color = 'red' if val < 1.0 else 'orange' if val < 1.5 else 'green'
                    return f'color: {color}; font-weight: bold'

                st.table(df) 
                
                # Show a visual gauge for the most recent result
                latest_fs = history_data[0]['fs']
                st.metric(label="Latest Factor of Safety", value=latest_fs, 
                          delta="SAFE" if latest_fs > 1.5 else "CRITICAL", 
                          delta_color="normal" if latest_fs > 1.5 else "inverse")
            else:
                st.write("No calculations yet. Use the sidebar to start.")
    except:
        st.warning("Waiting for API connection...")

with col2:
    st.subheader("Reference Guide")
    st.markdown("""
    **Stability Thresholds:**
    - 🟢 **Fs > 1.5**: Permanent slopes.
    - 🟡 **1.0 < Fs < 1.5**: Temporary/Marginal.
    - 🔴 **Fs < 1.0**: Failure imminent.
    
    *Formula used: Infinite Slope (Effective Stress).*
    """)
    
    # Add a simple diagram placeholder
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Slope_stability_analysis.png/300px-Slope_stability_analysis.png", 
             caption="Typical Failure Surface")
