import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.express as px

# ---------------------------------------------------
# BASIC PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(page_title="Earth 3.0 Dashboard", layout="wide")
st.title("🌍 Earth 3.0 — FACES ESG + Supply-Chain Stability Dashboard")
st.caption("Board-level prototype: Finance (F), AI Ethics (A), Climate (C), Equity (E), Sustainability (S). Fully self-contained, Streamlit free-tier ready.")

# ---------------------------------------------------
# SAMPLE DATA CREATION (INLINE)
# ---------------------------------------------------
@st.cache_data
def create_faces_data():
    data = {
        "Organization": [
            "Unilever PLC", 
            "Microsoft Corp", 
            "Siemens AG", 
            "Gov. of Singapore", 
            "BlackRock Inc."
        ],
        "Finance": [78, 91, 83, 88, 95],
        "AI_Governance": [85, 92, 80, 75, 90],
        "Climate": [62, 71, 67, 81, 70],
        "Equity": [71, 79, 74, 83, 88],
        "Sustainability": [77, 84, 76, 89, 92]
    }
    df = pd.DataFrame(data)
    df["Earth3_Index"] = df[["Finance","AI_Governance","Climate","Equity","Sustainability"]].mean(axis=1)
    return df

df = create_faces_data()

# ---------------------------------------------------
# SIDEBAR CONTROLS
# ---------------------------------------------------
st.sidebar.header("Board Controls & Weights")
selected_org = st.sidebar.selectbox("Choose Organisation", df["Organization"].tolist())

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

toggle_realtime = st.sidebar.checkbox("Enable light real-time global layer", value=True)

# ---------------------------------------------------
# FACES SCORES
# ---------------------------------------------------
org_row = df[df["Organization"] == selected_org].iloc[0]
scores = {k: org_row[k] for k in ["Finance","AI_Governance","Climate","Equity","Sustainability"]}
faces_index = sum(scores[k]*weights[k] for k in weights.keys())

# ---------------------------------------------------
# KPI DISPLAY (BOARD VIEW)
# ---------------------------------------------------
st.subheader(f"🌐 Board Dashboard — {selected_org}")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Finance (F)", f"{scores['Finance']:.1f}")
col2.metric("AI Governance (A)", f"{scores['AI_Governance']:.1f}")
col3.metric("Climate (C)", f"{scores['Climate']:.1f}")
col4.metric("Equity (E)", f"{scores['Equity']:.1f}")
col5.metric("Sustainability (S)", f"{scores['Sustainability']:.1f}")

st.subheader(f"Earth 3.0 Index — {faces_index:.1f}")
status_color = "🟢 GREEN" if faces_index >= 70 else "🟡 YELLOW" if faces_index >= 40 else "🔴 RED"
st.success(f"Status: {status_color} — Governance & resilience score ({faces_index:.1f})")

# ---------------------------------------------------
# WORLD MAP & 3D GLOBE (CEO BOARD VIEW)
# ---------------------------------------------------
# Simulated country-level ESG data
country_data = pd.DataFrame({
    "Country": ["United States", "Germany", "Singapore", "United Kingdom", "India"],
    "ISO_Code": ["USA","DEU","SGP","GBR","IND"],
    "Earth3_Index": [85, 78, 81, 77, 65]
})

# Choropleth map
st.subheader("🌎 Global ESG / FACES Heatmap")
fig_map = px.choropleth(
    country_data,
    locations="ISO_Code",
    color="Earth3_Index",
    hover_name="Country",
    color_continuous_scale=["red","yellow","green"],
    range_color=[0,100],
    labels={"Earth3_Index":"Earth 3.0 Index"}
)
fig_map.update_layout(
    geo=dict(showframe=False, showcoastlines=True),
    margin=dict(l=0,r=0,t=0,b=0),
    coloraxis_colorbar=dict(title="Earth3 Index")
)
st.plotly_chart(fig_map, use_container_width=True)

# 3D Globe with company HQ / supply-chain
st.subheader("🛰️ Global HQ / Supply-Chain Globe")
company_locations = pd.DataFrame({
    "Company":["Unilever","Microsoft","Siemens","Gov. Singapore","BlackRock"],
    "Lat":[51.5074, 47.6062, 48.1351, 1.3521, 40.7128],
    "Lon":[-0.1278, -122.3321, 11.5820, 103.8198, -74.0060],
    "Earth3_Index":[78,91,83,88,95]
})
fig_globe = px.scatter_geo(
    company_locations,
    lat="Lat",
    lon="Lon",
    hover_name="Company",
    hover_data={"Earth3_Index":True},
    size="Earth3_Index",
    projection="orthographic",
    color="Earth3_Index",
    color_continuous_scale=["red","yellow","green"],
)
fig_globe.update_geos(showcoastlines=True, showland=True)
st.plotly_chart(fig_globe, use_container_width=True)

# ---------------------------------------------------
# SIMULATED GLOBAL EVENTS (BOARD VIEW)
# ---------------------------------------------------
st.markdown("---")
st.subheader("🌐 Light real-time global layer (simulated)")

if toggle_realtime:
    cov_cases = 780_000_000
    cov_today = 420_000
    updated_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    
    colcov1, colcov2, colcov3 = st.columns(3)
    colcov1.metric("Global total cases", f"{cov_cases:,}")
    colcov2.metric("Cases today", f"{cov_today:,}")
    colcov3.metric("Updated (UTC)", updated_str)
    
    # Simulated earthquakes
    eq_df = pd.DataFrame({
        "lat": np.random.uniform(-60, 60, 10),
        "lon": np.random.uniform(-180, 180, 10),
        "magnitude": np.random.uniform(4, 8, 10)
    })
    st.map(eq_df[["lat","lon"]])
    st.caption("Simulated recent global earthquakes (magnitude 4-8).")
    
    # Simulated weather
    temp = 15 + np.random.rand()*20
    wind = 5 + np.random.rand()*15
    st.info(f"🌦️ Global mean temperature: {temp:.1f}°C | Wind speed: {wind:.1f} km/h")
else:
    st.warning("Real-time layer disabled to save resources.")

# ---------------------------------------------------
# DOWNLOAD BUTTON
# ---------------------------------------------------
st.markdown("---")
st.subheader("Export current FACES data")
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("Download CSV", csv, "faces_scores.csv", "text/csv")

st.success("✅ Earth 3.0 dashboard ready — self-contained, Fortune 500 CEO / Board UX, Streamlit free-tier safe.")
