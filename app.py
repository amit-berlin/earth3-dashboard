import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import plotly.express as px
import datetime

# ---------------------------------------------------
# BASIC PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(page_title="Earth 3.0 Dashboard", layout="wide")
st.title("🌍 Earth 3.0 — FACES ESG + Supply-Chain Stability Dashboard")
st.caption("Board-level prototype: Finance (F), AI Ethics (A), Climate (C), Equity (E), Sustainability (S). Built for free-tier Streamlit deployment.")

# ---------------------------------------------------
# HELPER: Safe fetch wrapper
# ---------------------------------------------------
def safe_get_json(url):
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

# ---------------------------------------------------
# SAMPLE DATA CREATION
# ---------------------------------------------------
def create_sample_faces():
    data = {
        "Organization": ["Unilever PLC", "Microsoft Corp", "Siemens AG", "Gov. of Singapore"],
        "Finance": [78, 91, 83, 88],
        "AI_Governance": [85, 92, 80, 75],
        "Climate": [62, 71, 67, 81],
        "Equity": [71, 79, 74, 83],
        "Sustainability": [77, 84, 76, 89]
    }
    df = pd.DataFrame(data)
    df["Earth3_Index"] = df[["Finance", "AI_Governance", "Climate", "Equity", "Sustainability"]].mean(axis=1)
    return df

# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------
@st.cache_data
def load_faces_data():
    try:
        return pd.read_csv("faces_sample.csv")
    except Exception:
        return create_sample_faces()

df = load_faces_data()

# ---------------------------------------------------
# SIDEBAR CONTROLS
# ---------------------------------------------------
st.sidebar.header("Data source")
use_sample = st.sidebar.button("Use sample data", help="Load sample FACES ESG data")
if use_sample:
    df = create_sample_faces()

selected_org = st.sidebar.selectbox("Choose Organisation", df["Organization"].unique())
weights = {
    "Finance": st.sidebar.slider("Finance weight", 0.0, 1.0, 0.2),
    "AI_Governance": st.sidebar.slider("AI Governance weight", 0.0, 1.0, 0.2),
    "Climate": st.sidebar.slider("Climate weight", 0.0, 1.0, 0.2),
    "Equity": st.sidebar.slider("Equity weight", 0.0, 1.0, 0.2),
    "Sustainability": st.sidebar.slider("Sustainability weight", 0.0, 1.0, 0.2)
}
total_weight = sum(weights.values())
if total_weight == 0:
    total_weight = 1
for k in weights:
    weights[k] /= total_weight

toggle_realtime = st.sidebar.checkbox("Enable real-time global data", value=True)

# ---------------------------------------------------
# FACES SCORES
# ---------------------------------------------------
org_row = df[df["Organization"] == selected_org].iloc[0]
scores = {k: org_row[k] for k in ["Finance", "AI_Governance", "Climate", "Equity", "Sustainability"]}
faces_index = sum(scores[k] * weights[k] for k in weights.keys())

# ---------------------------------------------------
# KPI DISPLAY
# ---------------------------------------------------
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Finance (F)", f"{scores['Finance']:.1f}")
col2.metric("AI Governance (A)", f"{scores['AI_Governance']:.1f}")
col3.metric("Climate (C)", f"{scores['Climate']:.1f}")
col4.metric("Equity (E)", f"{scores['Equity']:.1f}")
col5.metric("Sustainability (S)", f"{scores['Sustainability']:.1f}")

st.subheader(f"Earth 3.0 Index — {selected_org}: {faces_index:.1f}")
status_color = "GREEN" if faces_index >= 70 else "YELLOW" if faces_index >= 40 else "RED"
st.success(f"Status: {status_color} — Governance & resilience score ({faces_index:.1f})")

# ---------------------------------------------------
# REAL-TIME GLOBAL DATA
# ---------------------------------------------------
st.markdown("---")
st.subheader("Global events (light real-time layer)")

if toggle_realtime:
    with st.spinner("Refreshing real-time feeds..."):
        eq_data = safe_get_json("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson")
        covid_data = safe_get_json("https://disease.sh/v3/covid-19/all")
        weather_data = safe_get_json("https://api.open-meteo.com/v1/forecast?latitude=0&longitude=0&current_weather=true")

    if covid_data:
        cov_cases = covid_data.get("cases", 0)
        cov_today = covid_data.get("todayCases", 0)
        cov_updated = covid_data.get("updated", 0)
        try:
            updated_time = datetime.datetime.utcfromtimestamp(cov_updated / 1000)
            updated_str = updated_time.strftime("%Y-%m-%d %H:%M UTC")
        except Exception:
            updated_str = "N/A"
    else:
        cov_cases, cov_today, updated_str = 0, 0, "N/A"

    colcov1, colcov2, colcov3 = st.columns(3)
    colcov1.metric("Global total cases", f"{cov_cases:,}")
    colcov2.metric("Cases today", f"{cov_today:,}")
    colcov3.metric("Updated (UTC)", updated_str)

    # Earthquake map
    if eq_data and "features" in eq_data:
        eq_df = pd.DataFrame([
            {
                "lon": f["geometry"]["coordinates"][0],
                "lat": f["geometry"]["coordinates"][1],
                "mag": f["properties"].get("mag", 0)
            }
            for f in eq_data["features"] if f.get("geometry") and f["geometry"]["coordinates"]
        ])
        st.map(eq_df[["lat", "lon"]])
        st.caption(f"Showing {len(eq_df)} recent global earthquakes.")

    # Weather
    if weather_data and "current_weather" in weather_data:
        temp = weather_data["current_weather"].get("temperature", "N/A")
        wind = weather_data["current_weather"].get("windspeed", "N/A")
        st.info(f"🌦️ Global mean temperature: {temp}°C | Wind speed: {wind} km/h")

else:
    st.warning("Real-time layer disabled to save resources.")

# ---------------------------------------------------
# DOWNLOAD BUTTON
# ---------------------------------------------------
st.markdown("---")
st.subheader("Export current FACES data")
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("Download CSV", csv, "faces_scores.csv", "text/csv")

st.success("✅ Earth 3.0 dashboard ready — lightweight and future-safe for Streamlit free tier.")
