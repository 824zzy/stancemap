import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import pandas as pd

# Sample stance data
data = {
    "Tweet": ["Tweet A", "Tweet B", "Tweet C"],
    "City": ["Austin", "Dallas", "Houston"],
    "Stance": ["Positive", "Neutral", "Negative"],
    "Latitude": [30.2672, 32.7767, 29.7604],
    "Longitude": [-97.7431, -96.7970, -95.3698],
}
stance_df = pd.DataFrame(data)

# Build folium map
m = folium.Map(location=[31, -97], zoom_start=6)
marker_cluster = MarkerCluster().add_to(m)

# Add markers
for _, row in stance_df.iterrows():
    lat, lon = row["Latitude"], row["Longitude"]
    stance = row["Stance"]
    color = {"Positive": "green", "Neutral": "orange", "Negative": "red"}.get(
        stance, "gray"
    )

    if pd.notnull(lat) and pd.notnull(lon):
        popup = (
            f"{row['Tweet']}<br><b>City:</b> {row['City']}<br><b>Stance:</b> {stance}"
        )
        folium.Marker(
            location=[lat, lon], popup=popup, icon=folium.Icon(color=color)
        ).add_to(marker_cluster)

# Render in Streamlit
st_folium(m, height=600, width=1000)
