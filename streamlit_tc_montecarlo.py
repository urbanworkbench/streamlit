import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import random

# --- Time of Concentration Methods (SI) ---

def kirpich_tc(length, slope):
    return 0.01947 * (length ** 0.77) * (slope ** -0.385)

def nrcs_sheetflow_tc(length, slope, n, p2):
    return ((0.007 * n * length) ** 0.8) / ((p2) ** 0.5 * (slope ** 0.4))

def manning_kwa_tc(length, slope, n, intensity):
    i = intensity / 3600  # mm/h to mm/s
    return (0.94 * (length ** 0.6) * (n ** 0.6)) / ((i ** 0.4) * (slope ** 0.3))

def bransby_williams_tc(area_km2, slope):
    area_ha = area_km2 * 100
    return 58.5 * (area_ha ** 0.1) * (slope ** -0.2)

def airport_tc(area_km2):
    area_ha = area_km2 * 100
    return 0.76 * (area_ha ** 0.5) - 0.5

def kerby_hathaway_tc(length, slope, n):
    return 0.946 * (length ** 0.77) * ((slope / n) ** -0.385)

def izzard_tc(length, slope, n):
    return 0.00013 * (length ** 0.9) * (slope ** -0.6) * (n ** 0.4)

# --- Monte Carlo Simulation ---
def monte_carlo_analysis(length_range, slope_range, roughness_range, area_range, intensity_range, p2_range, iterations=1000):
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
        length = random.uniform(*length_range)
        slope = random.uniform(*slope_range)
        n = random.uniform(*roughness_range)
        area = random.uniform(*area_range)
        intensity = random.uniform(*intensity_range)
        p2 = random.uniform(*p2_range)

        results['Kirpich'].append(kirpich_tc(length, slope))
        results['NRCS (Sheet Flow)'].append(nrcs_sheetflow_tc(length, slope, n, p2))
        results['Manning-KWA'].append(manning_kwa_tc(length, slope, n, intensity))
        results['Bransby-Williams'].append(bransby_williams_tc(area, slope))
        results['Airport'].append(airport_tc(area))
        results['Kerby-Hathaway'].append(kerby_hathaway_tc(length, slope, n))
        results['Izzard'].append(izzard_tc(length, slope, n))

    return results

# --- Streamlit UI ---
st.title("🌀 Monte Carlo Time of Concentration (Tc) - SI Units")

st.sidebar.header("Input Parameter Ranges")

length_range = st.sidebar.slider("Flowpath Length (m)", 1.0, 2000.0, (50.0, 200.0))
slope_range = st.sidebar.slider("Slope (m/m)", 0.001, 0.2, (0.01, 0.05))
roughness_range = st.sidebar.slider("Manning’s n", 0.01, 0.2, (0.03, 0.06))
area_range = st.sidebar.slider("Catchment Area (km²)", 0.01, 10.0, (0.1, 1.0))
intensity_range = st.sidebar.slider("Rainfall Intensity (mm/h)", 5.0, 100.0, (20.0, 40.0))
p2_range = st.sidebar.slider("P2 - 2-year 24-hr Rainfall (mm)", 10.0, 150.0, (30.0, 80.0))
iterations = st.sidebar.slider("Monte Carlo Iterations", 100, 5000, 1000)

if st.button("Run Simulation"):
    with st.spinner("Running Monte Carlo Simulation..."):
        results = monte_carlo_analysis(
            length_range, slope_range, roughness_range,
            area_range, intensity_range, p2_range, iterations
        )

    st.success("Simulation complete!")

    for method, values in results.items():
        arr = np.array(values)
        st.subheader(f"{method}")
        st.write(f"**Mean:** {np.mean(arr):.2f} min")
        st.write(f"**Std Dev:** {np.std(arr):.2f} min")
        st.write(f"**Min:** {np.min(arr):.2f} | Max: {np.max(arr):.2f}")

        fig, ax = plt.subplots()
        ax.hist(arr, bins=30, color='skyblue', edgecolor='black')
        ax.set_title(f"{method} Distribution")
        ax.set_xlabel("Time of Concentration (min)")
        ax.set_ylabel("Frequency")
        st.pyplot(fig)
