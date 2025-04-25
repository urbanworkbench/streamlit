import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

st.title("Monte Carlo Simulation of Peak Discharge with Wildfire Effects")

with st.expander("ℹ️ About this app"):
    st.markdown("""
    This st.page_link("https://streamlit.io/", label="Streamlit", icon="🌎") app simulates the impact of wildfires on runoff and peak discharge over a design lifespan.
    It uses a Monte Carlo approach to account for variability in runoff coefficients before and after wildfires,
    incorporating probabilistic wildfire occurrence and hydrological response.
    
    Key features:
    - Adjustable runoff parameters and rainfall intensity
    - Control over wildfire probability, fire effect duration, and design life
    - Histogram comparison of peak discharge with and without wildfires
    - Sensitivity analysis of wildfire effect duration
    - Downloadable simulation results for further analysis
    """)

# Sidebar inputs
mean_C_baseline = st.sidebar.slider("Mean Runoff Coefficient (Baseline)", 0.1, 0.5, 0.25, 0.01, help="Typical C value for pre-wildfire conditions")
std_C_baseline = st.sidebar.slider("Std Dev of Runoff Coefficient (Baseline)", 0.01, 0.2, 0.05, 0.01, help="Variability in C for baseline conditions")
mean_C_post_wildfire = st.sidebar.slider("Mean Runoff Coefficient (Post-Wildfire)", 0.2, 0.8, 0.40, 0.01, help="Expected C value after wildfire events")
std_C_post_wildfire = st.sidebar.slider("Std Dev of Runoff Coefficient (Post-Wildfire)", 0.01, 0.3, 0.10, 0.01, help="Variability in C after wildfires")

rainfall_intensity = st.sidebar.slider("Rainfall Intensity (mm/hr)", 10, 100, 50, 1, help="Design rainfall intensity in mm/hr")
drainage_area = st.sidebar.slider("Drainage Area (hectares)", 0.5, 1000.0, 100.0, 0.5, help="Catchment area contributing to runoff")

prob_wildfire_percent = st.sidebar.slider("Annual Probability of Wildfire (%)", 0.0, 10.0, 1.5, 0.1, help="Annual chance of a wildfire occurring in a given year")
prob_wildfire_annual = prob_wildfire_percent / 100

design_lifespan_years = st.sidebar.slider("Design Lifespan (years)", 10, 200, 70, 5, help="Number of years for the simulation/design life")
fire_effect_duration = st.sidebar.slider("Fire Effect Duration (years)", 1, 50, 15, 1, help="Number of years wildfire effects persist on runoff")

num_simulations = 10000

# Generate random samples
C_baseline_samples = np.random.normal(mean_C_baseline, std_C_baseline, (num_simulations, design_lifespan_years))
C_post_wildfire_samples = np.random.normal(mean_C_post_wildfire, std_C_post_wildfire, (num_simulations, design_lifespan_years))

# Convert units
drainage_area_m2 = drainage_area * 10000
rainfall_intensity_m_s = rainfall_intensity / 3600000

# Simulate wildfire effects
wildfire_occurrences = np.random.binomial(1, prob_wildfire_annual, (num_simulations, design_lifespan_years))
Q_samples = np.zeros((num_simulations, design_lifespan_years))

for sim in range(num_simulations):
    C_values = np.copy(C_baseline_samples[sim])
    for year in range(design_lifespan_years):
        if wildfire_occurrences[sim, year] == 1:
            end_effect_year = min(year + fire_effect_duration, design_lifespan_years)
            C_values[year:end_effect_year] = C_post_wildfire_samples[sim, year:end_effect_year]
    Q_samples[sim, :] = C_values * rainfall_intensity_m_s * drainage_area_m2

Q_baseline_discharge = C_baseline_samples * rainfall_intensity_m_s * drainage_area_m2
Q_avg_lifespan = np.mean(Q_samples, axis=1)
Q_avg_baseline = np.mean(Q_baseline_discharge, axis=1)

confidence_level = 0.85
lower_percentile = (1 - confidence_level) / 2 * 100
upper_percentile = (1 + confidence_level) / 2 * 100

Q_avg_lower = np.percentile(Q_avg_lifespan, lower_percentile)
Q_avg_upper = np.percentile(Q_avg_lifespan, upper_percentile)
Q_baseline_lower = np.percentile(Q_avg_baseline, lower_percentile)
Q_baseline_upper = np.percentile(Q_avg_baseline, upper_percentile)

avg_num_wildfires = np.mean(np.sum(wildfire_occurrences, axis=1))

# Plot histogram
fig_hist, ax = plt.subplots(figsize=(12, 6))
ax.hist(Q_avg_lifespan, bins=50, alpha=0.7, label='With Wildfires')
ax.hist(Q_avg_baseline, bins=100, alpha=0.5, label='No Wildfires', color='orange')

ax.axvline(np.mean(Q_avg_lifespan), color='red', linestyle='--', label='Mean (Wildfires)')
ax.axvline(Q_avg_lower, color='green', linestyle=':', label='85% CI Lower (Wildfires)')
ax.axvline(Q_avg_upper, color='green', linestyle=':', label='85% CI Upper (Wildfires)')

ax.axvline(np.mean(Q_avg_baseline), color='blue', linestyle='--', label='Mean (No Wildfires)')
ax.axvline(Q_baseline_lower, color='purple', linestyle=':', label='85% CI Lower (No Wildfires)')
ax.axvline(Q_baseline_upper, color='purple', linestyle=':', label='85% CI Upper (No Wildfires)')

ax.set_xlabel("Average Peak Discharge (m³/s)")
ax.set_ylabel("Frequency")
ax.set_title("Simulation of Average Peak Discharge with and without Wildfires")
ax.legend()
ax.grid(True)
st.pyplot(fig_hist)

st.write(f"**Baseline (No Wildfires)**: Mean = {np.mean(Q_avg_baseline):.2f}, Std Dev = {np.std(Q_avg_baseline):.2f}, 85% CI = ({Q_baseline_lower:.2f}, {Q_baseline_upper:.2f})")
st.write(f"**With Wildfires**: Mean = {np.mean(Q_avg_lifespan):.2f}, Std Dev = {np.std(Q_avg_lifespan):.2f}, 85% CI = ({Q_avg_lower:.2f}, {Q_avg_upper:.2f})")
st.write(f"**Avg Wildfires Over Lifespan**: {avg_num_wildfires:.2f}")

# Wildfire timelines
st.subheader("Example Wildfire Occurrence Timelines")
num_examples = st.slider("Number of Simulations to Display", 1, 10, 3)
fig_occ, ax_occ = plt.subplots(num_examples, 1, figsize=(10, 2.5 * num_examples), sharex=True)
if num_examples == 1:
    ax_occ = [ax_occ]

for i in range(num_examples):
    sim_index = np.random.randint(num_simulations)
    years = np.arange(design_lifespan_years)
    ax_occ[i].bar(years, wildfire_occurrences[sim_index], color='firebrick')
    ax_occ[i].set_title(f"Simulation #{sim_index + 1}")
    ax_occ[i].set_ylabel("Wildfire")
    ax_occ[i].set_yticks([0, 1])
    ax_occ[i].set_ylim(-0.1, 1.1)
ax_occ[-1].set_xlabel("Year")
st.pyplot(fig_occ)

# Sensitivity plot
st.subheader("Sensitivity: Fire Effect Duration vs. Avg Peak Discharge")
durations = list(range(1, 31, 2))
mean_discharge_vs_duration = []

for duration in durations:
    temp_Q_samples = np.zeros((num_simulations, design_lifespan_years))
    for sim in range(num_simulations):
        C_vals = np.copy(C_baseline_samples[sim])
        for year in range(design_lifespan_years):
            if wildfire_occurrences[sim, year] == 1:
                end_effect = min(year + duration, design_lifespan_years)
                C_vals[year:end_effect] = C_post_wildfire_samples[sim, year:end_effect]
        temp_Q_samples[sim, :] = C_vals * rainfall_intensity_m_s * drainage_area_m2
    avg_discharge = np.mean(temp_Q_samples, axis=1)
    mean_discharge_vs_duration.append(np.mean(avg_discharge))

fig_sens, ax_sens = plt.subplots()
ax_sens.plot(durations, mean_discharge_vs_duration, marker='o', color='teal')
ax_sens.set_xlabel("Fire Effect Duration (years)")
ax_sens.set_ylabel("Mean Avg Peak Discharge (m³/s)")
ax_sens.set_title("Sensitivity to Fire Effect Duration")
ax_sens.grid(True)
st.pyplot(fig_sens)

# Export results
st.subheader("Export Simulation Results")
export_df = pd.DataFrame({
    "Avg Discharge With Wildfires": Q_avg_lifespan,
    "Avg Discharge Baseline": Q_avg_baseline,
    "Num Wildfires": np.sum(wildfire_occurrences, axis=1)
})
csv_data = export_df.to_csv(index=False)
st.download_button("Download Results as CSV", data=csv_data, file_name="wildfire_discharge_simulation.csv", mime="text/csv")
