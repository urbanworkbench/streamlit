import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import random

# --- Time of Concentration Methods ---
def kirpich_tc(length, slope):
    return 0.01947 * (length ** 0.77) * (slope ** -0.385)

def nrcs_sheetflow_tc(length, slope, n, p2):
    return ((0.007 * n * length) ** 0.8) / (p2 ** 0.5 * (slope ** 0.4))

def manning_tc(length, slope, n):
    return (1.44 * (length ** 0.6) * (n ** 0.6)) / (slope ** 0.3)

def bransby_williams_tc(area, slope):
    return 58.5 * ((area * 1e6) ** 0.1) * (slope ** -0.2)

def airport_tc(area):
    return 1.8 * ((area * 1e6) ** 0.5) / 1000 - 0.5

def kerby_hathaway_tc(length, slope, n):
    return 0.946 * (length ** 0.77) * ((slope / n) ** -0.385)

def izzard_tc(length, slope, n, k):
    return k * (length ** 0.9) * (slope ** -0.6) * (n ** 0.4)

# --- Monte Carlo ---
def monte_carlo_analysis(length_range, slope_range, roughness_range, area_range, iterations, p2, izzard_k):
    results = {
        'Kirpich': [],
        'NRCS (Sheet Flow)': [],
        'Manning-KWA': [],
        'Bransby-Williams': [],
        'Airport': [],
        'Kerby-Hathaway': [],
        'Izzard': []
    }

    for _ in range(iterations):
        L = random.uniform(*length_range)
        S = random.uniform(*slope_range)
        n = random.uniform(*roughness_range)
        A = random.uniform(*area_range)

        results['Kirpich'].append(kirpich_tc(L, S))
        results['NRCS (Sheet Flow)'].append(nrcs_sheetflow_tc(L, S, n, p2))
        results['Manning-KWA'].append(manning_tc(L, S, n))
        results['Bransby-Williams'].append(bransby_williams_tc(A, S))
        results['Airport'].append(airport_tc(A))
        results['Kerby-Hathaway'].append(kerby_hathaway_tc(L, S, n))
        results['Izzard'].append(izzard_tc(L, S, n, izzard_k))

    return results

# --- Streamlit UI ---
st.set_page_config(page_title="Time of Concentration App", layout="wide")
st.title("\U0001F300 Monte Carlo Time of Concentration (Tc) - SI Units")

# Catchment type selection
catchment_type = st.selectbox("\U0001F30E Select Catchment Type", ["Rural Farmland", "Forested", "Urban"])

# Izzard calibration (only for Urban)
izzard_k = 0.00025
if catchment_type == "Urban":
    izzard_k = st.slider("\U0001F527 Izzard calibration constant (k)", 0.0001, 0.0010, 0.00025, step=0.00005)

st.markdown("---")

# Input ranges
st.header("\U0001F4E5 Input Ranges for Monte Carlo Simulation")

length_range = st.slider("Flowpath Length (m)", 10.0, 500.0, (30.0, 100.0))
slope_range = st.slider("Slope (m/m)", 0.001, 0.1, (0.01, 0.03))
roughness_range = st.slider("Manning's n", 0.01, 0.2, (0.03, 0.06))
area_range = st.slider("Catchment Area (km²)", 0.01, 5.0, (0.1, 1.0))
p2 = st.slider("2-yr Rainfall Depth (mm)", 10, 100, 25)
iterations = st.slider("Iterations", 100, 5000, 1000, step=100)

# Run simulation
if st.button("\U0001F680 Run Monte Carlo Simulation"):
    st.info("Running simulation...")
    results = monte_carlo_analysis(length_range, slope_range, roughness_range, area_range, iterations, p2, izzard_k)

    # Logic for method display
    show_izzard = catchment_type == "Urban"
    show_nrcs = length_range[1] <= 100

    excluded = []
    if not show_izzard: excluded.append("Izzard (Urban only)")
    if not show_nrcs: excluded.append("NRCS Sheet Flow (flowpath > 100m)")

    if excluded:
        st.warning("\u26A0\uFE0F Methods not shown: " + ", ".join(excluded))

    # Recommended methods guidance
    recommended_map = {
        "Rural Farmland": ["Kirpich", "Bransby-Williams"],
        "Forested": ["NRCS (Sheet Flow)"],
        "Urban": ["Manning-KWA", "NRCS (Sheet Flow)"]
    }
    recommended = recommended_map.get(catchment_type, [])

    # Filter results
    filtered_results = {}
    for method, values in results.items():
        if method == "Izzard" and not show_izzard:
            continue
        if method == "NRCS (Sheet Flow)" and not show_nrcs:
            continue
        filtered_results[method] = values

    # Show results
    st.markdown("---")
    st.header("\U0001F4CA Simulation Results")

    for method, values in filtered_results.items():
        arr = np.array(values)
        st.subheader(f"{'\u2B50 ' if method in recommended else ''}{method}")
        st.write(f"**Mean:** {np.mean(arr):.2f} min")
        st.write(f"**Std Dev:** {np.std(arr):.2f} min")
        st.write(f"**Min:** {np.min(arr):.2f} | Max: {np.max(arr):.2f}")

        fig, ax = plt.subplots()
        ax.hist(arr, bins=30, color='orange' if method in recommended else 'skyblue', edgecolor='black')
        ax.set_title(f"{method} Distribution")
        ax.set_xlabel("Time of Concentration (min)")
        ax.set_ylabel("Frequency")
        st.pyplot(fig)
