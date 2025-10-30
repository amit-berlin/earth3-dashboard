# app.py
# Earth 3.0 — FACES ESG + Global Supply-Chain Stability Dashboard
# Lightweight, free-tier friendly (Streamlit Cloud)
# Requirements: streamlit, pandas, numpy, requests, plotly, pydeck
# pip install streamlit pandas numpy requests plotly pydeck

import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import io
from datetime import datetime, timedelta
import plotly.express as px
import pydeck as pdk

st.set_page_config(page_title="Earth 3.0 FACES Dashboard", layout="wide")

# -----------------------
# Utilities: sample CSV
# -----------------------
SAMPLE_CSV = """org,metric_finance,metric_ai,metric_climate,metric_equity,metric_sustain
Unilever,0.78,0.85,0.62,0.71,0.77
Microsoft,0.91,0.96,0.40,0.81,0.88
Siemens,0.84,0.78,0.55,0.64,0.73
SingaporeGov,0.88,0.70,0.30,0.90,0.82
"""

def load_sample_df():
    df = pd.read_csv(io.StringIO(SAMPLE_CSV))
    # Ensure numeric and in 0-1 range
    for c in ['metric_finance','metric_ai','metric_climate','metric_equity','metric_sustain']:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).clip(0,1)
    return df

# -----------------------
# Scoring functions
# -----------------------
def compute_faces_scores(df, weights=None):
    # Expect metrics 0..1, convert to 0..100
    df = df.copy()
    df['F'] = (df['metric_finance'] * 100).round(1)
    df['A'] = (df['metric_ai'] * 100).round(1)
    df['C'] = (df['metric_climate'] * 100).round(1)
    df['E'] = (df['metric_equity'] * 100).round(1)
    df['S'] = (df['metric_sustain'] * 100).round(1)
    if weights is None:
        weights = {'F':0.25,'A':0.20,'C':0.20,'E':0.20,'S':0.15}
    df['Earth3_Index'] = (df['F']*weights['F'] + df['A']*weights['A'] + df['C']*weights['C'] + df['E']*weights['E'] + df['S']*weights['S']).round(1)
    return df

# -----------------------
# Real-time feeds (light)
# -----------------------
def fetch_earthquakes(limit=50):
    try:
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
        r = requests.get(url, timeout=8)
        data = r.json()
        features = data.get('features', [])[:limit]
        rows = []
        for f in features:
            props = f.get('properties', {})
            geom = f.get('geometry', {})
            coords = geom.get('coordinates', [None, None])
            rows.append({
                'place': props.get('place'),
                'mag': props.get('mag'),
                'time': datetime.utcfromtimestamp(props.get('time')/1000.0) if props.get('time') else None,
                'lon': coords[0],
                'lat': coords[1]
            })
        return pd.DataFrame(rows)
    except Exception as e:
        return pd.DataFrame(columns=['place','mag','time','lon','lat'])

def fetch_covid_summary():
    try:
        url = "https://disease.sh/v3/covid-19/all"
        r = requests.get(url, timeout=6)
        data = r.json()
        return {
            'cases': data.get('cases'),
            'todayCases': data.get('todayCases'),
            'deaths': data.get('deaths'),
            'todayDeaths': data.get('todayDeaths'),
            'updated': datetime.utcfromtimestamp(data.get('updated')/1000.0) if data.get('updated') else None
        }
    except Exception as e:
        return {}

def fetch_weather_for(place_lat, place_lon):
    # Uses open-meteo public API (no key)
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={place_lat}&longitude={place_lon}&current_weather=true"
        r = requests.get(url, timeout=6)
        return r.json().get('current_weather', {})
    except Exception as e:
        return {}

# -----------------------
# Supply Chain Stability Indicator
# -----------------------
def compute_supply_chain_indicator(eq_df, covid_summary):
    score = 100.0
    # If any earthquake magnitude >= 6 in last day, reduce score
    if not eq_df.empty and eq_df['mag'].max() is not None:
        max_mag = eq_df['mag'].max()
        if max_mag >= 7.0:
            score -= 40
        elif max_mag >= 6.0:
            score -= 25
        elif max_mag >= 5.0:
            score -= 10
    # COVID impact: if today cases high, reduce
    today_cases = covid_summary.get('todayCases') or 0
    if today_cases > 500000:
        score -= 30
    elif today_cases > 100000:
        score -= 15
    return max(0, round(score,1))

# -----------------------
# Trend generator (7-day)
# -----------------------
def generate_7day_trend(base_index):
    rng = np.random.default_rng(seed=42)
    days = [ (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6,-1,-1) ]
    variations = rng.normal(loc=0.0, scale=1.5, size=7).cumsum()
    trend = [ max(0, min(100, base_index + v)) for v in variations ]
    return pd.DataFrame({'date': days, 'index': [round(x,1) for x in trend]})

# -----------------------
# UI: Sidebar controls
# -----------------------
st.title("🌍 Earth 3.0 — FACES ESG + Supply-Chain Stability Dashboard")
st.markdown("Board-level prototype: Finance (F), AI Ethics (A), Climate (C), Equity (E), Sustainability (S). Built for free-tier Streamlit deployment.")

# File uploader or sample
st.sidebar.header("Data source")
uploaded = st.sidebar.file_uploader("Upload faces_sample.csv (optional)", type=['csv'])
use_sample = st.sidebar.button("Use sample data")
if uploaded:
    try:
        df_raw = pd.read_csv(uploaded)
    except Exception as e:
        st.sidebar.error("Could not read uploaded CSV; using sample.")
        df_raw = load_sample_df()
elif use_sample or uploaded is None:
    df_raw = load_sample_df()
else:
    df_raw = load_sample_df()

# Organization selector
orgs = df_raw['org'].tolist()
org_select = st.sidebar.selectbox("Select organisation", orgs, index=0)

# Weights sliders
st.sidebar.header("Adjust FACES weights (sum normalized automatically)")
wF = st.sidebar.slider("Finance (F)", 0.0, 1.0, 0.25, 0.01)
wA = st.sidebar.slider("AI Governance (A)", 0.0, 1.0, 0.20, 0.01)
wC = st.sidebar.slider("Climate (C)", 0.0, 1.0, 0.20, 0.01)
wE = st.sidebar.slider("Equity (E)", 0.0, 1.0, 0.20, 0.01)
wS = st.sidebar.slider("Sustainability (S)", 0.0, 1.0, 0.15, 0.01)
# Normalize
total = wF + wA + wC + wE + wS
weights = {'F': wF/total, 'A': wA/total, 'C': wC/total, 'E': wE/total, 'S': wS/total}

# Real-time toggle
real_time = st.sidebar.checkbox("Enable real-time global data layer (Earthquake / COVID / Weather)", value=True)
refresh = st.sidebar.button("Refresh real-time data")

# -----------------------
# Compute scores
# -----------------------
df_scores = compute_faces_scores(df_raw, weights=weights)
selected_row = df_scores[df_scores['org'] == org_select].iloc[0]

# KPI cards
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Finance (F)", f"{selected_row['F']}", delta=None)
col2.metric("AI Governance (A)", f"{selected_row['A']}", delta=None)
col3.metric("Climate (C)", f"{selected_row['C']}", delta=None)
col4.metric("Equity (E)", f"{selected_row['E']}", delta=None)
col5.metric("Sustainability (S)", f"{selected_row['S']}", delta=None)

# Earth3 index card
st.markdown("---")
st.subheader(f"Earth 3.0 Index — {org_select}: {selected_row['Earth3_Index']}")
idx = selected_row['Earth3_Index']

# Trend
trend_df = generate_7day_trend(idx)
fig_trend = px.line(trend_df, x='date', y='index', title="7-Day Earth 3.0 Index Trend", range_y=[0,100])
st.plotly_chart(fig_trend, use_container_width=True)

# Color-coded interpretation
if idx >= 70:
    st.success(f"Status: GREEN — Governance & resilience strong (Index {idx})")
elif idx >= 40:
    st.warning(f"Status: YELLOW — Improvement recommended (Index {idx})")
else:
    st.error(f"Status: RED — Immediate action required (Index {idx})")

# -----------------------
# Real-time global map (light)
# -----------------------
st.markdown("### Global events (light real-time layer)")
eq_df = pd.DataFrame()
cov_summary = {}
if real_time:
    if refresh:
        st.info("Refreshing real-time feeds...")
    eq_df = fetch_earthquakes(limit=100)
    cov_summary = fetch_covid_summary()
else:
    st.info("Real-time layer disabled; showing static demo values.")
    eq_df = fetch_earthquakes(limit=20)
    cov_summary = fetch_covid_summary()

# Map: plot earthquakes with plotly scatter_geo
if not eq_df.empty:
    # Filter to points with lat/lon
    map_df = eq_df.dropna(subset=['lat','lon'])
    # Plot top N by magnitude
    topn = map_df.sort_values('mag', ascending=False).head(75)
    fig_map = px.scatter_geo(topn, lat='lat', lon='lon', hover_name='place', size='mag',
                             size_max=10, projection="natural earth",
                             title="Recent earthquakes (past day)")
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.info("No earthquake data available.")

# Show COVID summary
cov_col1, cov_col2, cov_col3 = st.columns(3)
cov_col1.metric("Global total cases", cov_summary.get('cases', 'N/A'))
cov_col2.metric("Cases today", cov_summary.get('todayCases', 'N/A'))
cov_col3.metric("Updated (UTC)", cov_summary.get('updated', 'N/A'))

# Supply-chain stability indicator
sci = compute_supply_chain_indicator(eq_df, cov_summary)
st.markdown(f"### Supply-Chain Stability Indicator: **{sci} / 100**")
st.caption("Drops with large earthquakes (mag ≥6) or very high global COVID surge.")

# -----------------------
# Simple organisation map (weather) using coords
# -----------------------
org_coords = {
    'Unilever': (51.5074, -0.1278),       # London approx
    'Microsoft': (47.6062, -122.3321),    # Seattle approx
    'Siemens': (48.1351, 11.5820),        # Munich approx
    'SingaporeGov': (1.3521, 103.8198)    # Singapore
}
lat, lon = org_coords.get(org_select, (0,0))
weather = fetch_weather_for(lat, lon)
st.markdown(f"**Local sample weather for {org_select}:** {weather if weather else 'N/A'}")

# -----------------------
# Download / Export / Synthetic generator
# -----------------------
st.markdown("---")
colL, colR = st.columns([3,1])
with colL:
    st.markdown("#### Export current scores")
    csv_buf = df_scores.to_csv(index=False).encode('utf-8')
    st.download_button("Download FACES scores CSV", data=csv_buf, file_name="faces_scores.csv", mime="text/csv")
with colR:
    st.markdown("#### Generate sample CSV")
    if st.button("Show sample CSV contents"):
        st.code(SAMPLE_CSV, language='csv')

st.markdown("##### Data table (scores)")
st.dataframe(df_scores[['org','F','A','C','E','S','Earth3_Index']].set_index('org'))

st.markdown("### Notes & limitations")
st.write("""
- This is a lightweight board-level prototype. Scores are illustrative and based on the sample metrics included.
- For production: connect verified ESG, finance, AI governance, and HR sources; add third-party assurance; align emissions scope (1/2/3) to benchmark.
- Designed to run on Streamlit Cloud free tier. Keep dataset sizes small to remain within free CPU/memory limits.
""")
