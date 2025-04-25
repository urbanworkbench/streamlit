import streamlit as st
import numpy as np
import random
import matplotlib.pyplot as plt

# Time of Concentration methods
def kirpich_tc(length, slope):
    return 0.01947 * (length ** 0.77) * (slope ** -0.385)

def nrcs_tc(length, slope):
    return (length / (0.13 * (slope ** 0.5))) ** 0.77

def manning_overland_tc(length, slope, n):
    return (1.44 * (length ** 0.6) * (n ** 0.6)) / (slope ** 0.3)

def bransby_williams_tc(area, slope):
    return 58.5 * ((area * 1e6) ** 0.1) * (slope ** -0.2)

def airport_tc(area):
    return 1.8 * ((area * 1e6) ** 0.5) / 1000 - 0.5

def kerby_hathaway_tc(length, slope, n):
    return 0.946 * (length ** 0.77) * ((slope / n) ** -0.385)

def izzard_tc(length, slope, n):
    return (0.00013 * (length ** 0.9) * (slope ** -0.6) * (n ** 0.4))

def velocity_method_tc(length, velocity):
    return (length / velocity) / 60  # convert seconds to minutes

def rational_method_tc(intensity, area, c):
    return (area * c * 360) / (intensity * 1000)  # in minutes

# Monte Carlo simulation
def monte_carlo_tc(length_range, slope_range, roughness_range, area_range,
                   velocity_range, intensity_range, c_range, iterations):
    results = {
        'Kirpich': [],
        'NRCS': [],
        'Manning': [],
        'Bransby-Williams': [],
        'Airport': [],
        'Kerby-Hathaway': [],
        'Izzard': [],
        'Velocity': [],
        'Rational': []
    }

    for _ in range(iterations):
        length = random.uniform(*length_range)
        slope = random.uniform(*slope_range)
        roughness = random.uniform(*roughness_range)
        area = random.uniform(*area_range)
        velocity = random.uniform(*velocity_range)
        intensity = random.uniform(*intensity_range)
        c = random.uniform(*c_range)

        results['Kirpich'].append(kirpich_tc(length, slope))
        results['NRCS'].append(nrcs_tc(length, slope))
        results['Manning'].append(manning_overland_tc(length, slope, roughness))
        results['Bransby-Williams'].append(bransby_williams_tc(area, slope))
        results['Airport'].append(airport_tc(area))
        results['Kerby-Hathaway'].append(kerby_hathaway_tc(length, slope, roughness))
        results['Izzard'].append(izzard_tc(length, slope, roughness))
        results['Velocity'].append(velocity_method_tc(length, velocity))
        results['Rational'].append(rational_method_tc(intensity, area, c))

    return results

# Streamlit UI
st.title("🌀 Monte Carlo Time of Concentration Calculator (SI Units)")

st.sidebar.header("Input Ranges")

length_range = st.sidebar.slider("Flowpath Length (m)", 10.0, 1000.0, (50.0, 300.0))
slope_range = st.sidebar.slider("Slope (decimal)", 0.001, 0.2, (0.01, 0.05))
roughness_range = st.sidebar.slider("Manning's n", 0.01, 0.2, (0.03, 0.06))
area_range = st.sidebar.slider("Catchment Area (km²)", 0.01, 10.0, (0.1, 2.0))
velocity_range = st.sidebar.slider("Flow Velocity (m/s)", 0.1, 5.0, (0.3, 2.0))
intensity_range = st.sidebar.slider("Rainfall Intensity (mm/h)", 10.0, 200.0, (30.0, 100.0))
c_range = st.sidebar.slider("Runoff Coefficient (C)", 0.1, 1.0, (0.3, 0.8))
iterations = st.sidebar.slider("Monte Carlo Iterations", 100, 5000, 1000)

if st.button("Run Simulation"):
    with st.spinner("Running Monte Carlo analysis..."):
        results = monte_carlo_tc(length_range, slope_range, roughness_range,
                                 area_range, velocity_range, intensity_range,
                                 c_range, iterations)

    st.success("Simulation complete!")

    for method, times in results.items():
        arr = np.array(times)
        st.subheader(f"{method} Method")
        st.write(f"**Mean Tc:** {np.mean(arr):.2f} min")
        st.write(f"**Standard Deviation:** {np.std(arr):.2f} min")
        st.write(f"**Min:** {np.min(arr):.2f} min  |  **Max:** {np.max(arr):.2f} min")
        
        # Plot histogram
        fig, ax = plt.subplots()
        ax.hist(arr, bins=30, color='skyblue', edgecolor='black')
        ax.set_title(f"{method} Distribution")
        ax.set_xlabel("Time of Concentration (minutes)")
        ax.set_ylabel("Frequency")
        st.pyplot(fig)
