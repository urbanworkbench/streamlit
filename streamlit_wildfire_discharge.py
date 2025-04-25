import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Streamlit settings
st.title("Monte Carlo Simulation: Wildfire Impacts on Peak Discharge")
st.markdown("Simulates average peak discharge over a 70-year design life, considering wildfire effects.")

# Sidebar inputs
st.sidebar.header("Simulation Parameters")

mean_C_baseline = st.sidebar.slider("Baseline Runoff Coefficient (Mean)", 0.1, 0.5, 0.25, 0.01)
std_C_baseline = st.sidebar.slider("Baseline Runoff Coefficient (Std Dev)", 0.01, 0.2, 0.05, 0.01)
mean_C_post_wildfire = st.sidebar.slider("Post-Wildfire Runoff Coefficient (Mean)", 0.2, 0.9, 0.40, 0.01)
std_C_post_wildfire = st.sidebar.slider("Post-Wildfire Runoff Coefficient (Std Dev)", 0.01, 0.3, 0.10, 0.01)

rainfall_intensity = st.sidebar.slider("Rainfall Intensity (mm/hr)", 10, 200, 50, 1)
drainage_area = st.sidebar.slider("Drainage Area (hectares)", 1, 1000, 100, 1)

prob_wildfire_annual = st.sidebar.slider("Annual Probability of Wildfire", 0.0, 0.1, 0.015, 0.001)
design_lifespan_years = 70
fire_effect_duration = 15
num_simulations = 10000

# Run simulation
st.write("Running Monte Carlo simulation...")

C_baseline_samples = np.random.normal(mean_C_baseline, std_C_baseline, (num_simulations, design_lifespan_years))
C_post_wildfire_samples = np.random.normal(mean_C_post_wildfire, std_C_post_wildfire, (num_simulations, design_lifespan_years))

drainage_area_m2 = drainage_area * 10000
rainfall_intensity_m_s = rainfall_intensity / 3600000

Q_samples = np.zeros((num_simulations, design_lifespan_years))
Q_baseline_discharge = np.zeros((num_simulations, design_lifespan_years))

wildfire_occurrences = np.random.binomial(1, prob_wildfire_annual, (num_simulations, design_lifespan_years))

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

# Plotting
fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(Q_avg_lifespan, bins=50, alpha=0.7, label='With Wildfires')
ax.hist(Q_avg_baseline, bins=50, alpha=0.5, label='Baseline (No Wildfires)', color='orange')

ax.axvline(np.mean(Q_avg_lifespan), color='red', linestyle='dashed', linewidth=1, label='Mean (With Wildfires)')
ax.axvline(Q_avg_lower, color='green', linestyle='dotted', linewidth=1, label='85% CI Lower (With Wildfires)')
ax.axvline(Q_avg_upper, color='green', linestyle='dotted', linewidth=1, label='85% CI Upper (With Wildfires)')

ax.axvline(np.mean(Q_avg_baseline), color='blue', linestyle='dashed', linewidth=1, label='Mean (No Wildfires)')
ax.axvline(Q_baseline_lower, color='purple', linestyle='dotted', linewidth=1, label='85% CI Lower (No Wildfires)')
ax.axvline(Q_baseline_upper, color='purple', linestyle='dotted', linewidth=1, label='85% CI Upper (No Wildfires)')

ax.set_xlabel('Average Peak Discharge (m³/s)')
ax.set_ylabel('Frequency')
ax.set_title('Simulation of Average Peak Discharge Over 70 Years')
ax.legend()
ax.grid(True)

st.pyplot(fig)

# Display results
st.subheader("Summary Statistics")

st.markdown(f"""
**Baseline (No Wildfires)**  
- Mean: `{np.mean(Q_avg_baseline):.2f}` m³/s  
- Std Dev: `{np.std(Q_avg_baseline):.2f}` m³/s  
- 85% CI: `({Q_baseline_lower:.2f}, {Q_baseline_upper:.2f})` m³/s

**With Wildfires**  
- Mean: `{np.mean(Q_avg_lifespan):.2f}` m³/s  
- Std Dev: `{np.std(Q_avg_lifespan):.2f}` m³/s  
- 85% CI: `({Q_avg_lower:.2f}, {Q_avg_upper:.2f})` m³/s

**Wildfire Stats**  
- Average Wildfires over 70 Years: `{avg_num_wildfires:.2f}`
""")
