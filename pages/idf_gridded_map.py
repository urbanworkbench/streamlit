import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
import folium
import zipfile
import os

# Title
st.set_page_config(page_title="Gridded Precip Viewer", layout="wide")
st.title("📍 Gridded Precipitation Explorer")

# Unzip and load CSV
if not os.path.exists("data"):
    with zipfile.ZipFile("GriddedDataSet.zip", 'r') as zip_ref:
        zip_ref.extractall("data")

csv_file = [f for f in os.listdir("data") if f.endswith(".csv")][0]
df = pd.read_csv(f"data/{csv_file}")

# Map setup
st.subheader("1. Click a location on the map")
m = folium.Map(location=[df["lat"].mean(), df["lon"].mean()], zoom_start=6)
m.add_child(folium.LatLngPopup())
map_data = st_folium(m, width=700, height=500)

# Handle map click
if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.markdown(f"**Selected location:** {lat:.4f}, {lon:.4f}")

    # Find nearest grid point
    df["distance"] = ((df["lat"] - lat)**2 + (df["lon"] - lon)**2)**0.5
    nearest_point = df.loc[df["distance"].idxmin()]
    nearest_lat, nearest_lon = nearest_point["lat"], nearest_point["lon"]

    # Filter for that grid cell
    local_df = df[(df["lat"] == nearest_lat) & (df["lon"] == nearest_lon)]

    # Show available RPs for that location
    available_rps = sorted(local_df["RP"].unique())
    selected_rp = st.selectbox("2. Select Return Period (years)", available_rps)

    # Filter by RP
    rp_data = local_df[local_df["RP"] == selected_rp].copy()
    rp_data["intensity_mm_hr"] = rp_data["precip_mm"] / (rp_data["duration"] / 60)  # assuming duration in minutes

    # Display results
    st.subheader(f"📊 Precipitation Data for RP {selected_rp} years")
    st.dataframe(
        rp_data[["duration", "precip_mm", "intensity_mm_hr"]]
        .sort_values("duration")
        .rename(columns={
            "duration": "Duration (min)",
            "precip_mm": "Total Precip (mm)",
            "intensity_mm_hr": "Intensity (mm/hr)"
        }),
        use_container_width=True
    )
else:
    st.info("Click on the map to begin.")
