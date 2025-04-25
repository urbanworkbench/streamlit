import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import optimize

# Set page config
st.set_page_config(page_title="HEC-22 Inlet Capacity Calculator", layout="wide")

# Title and introduction
st.title("HEC-22 Inlet Capacity Calculator")
st.markdown("""
This application calculates the interception capacity of inlets based on the HEC-22 (4th edition) methodology.
""")

# Create tabs for different inlet types
tab1, tab2 = st.tabs(["Grate Inlets on Grade", "Grate Inlets in Sag"])

# Tab 1: Grate Inlets on Grade
with tab1:
    st.header("Grate Inlets on Grade")
    
    st.markdown("""
    This calculator determines the interception capacity of grate inlets on continuous grades using the methods described in HEC-22.
    """)
    
    # Input parameters - create two columns for inputs
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Gutter Parameters")
        unit_system = st.radio("Unit System", ["US Customary", "SI (metric)"])
        
        if unit_system == "US Customary":
            length_unit = "ft"
            flow_unit = "ft³/s"
            Ku_splash = 0.09
            Ku_side = 0.15
            Ku_gutter = 0.56
            Ku_velocity = 1.11
        else:
            length_unit = "m"
            flow_unit = "m³/s"
            Ku_splash = 0.295
            Ku_side = 0.0828
            Ku_gutter = 0.376
            Ku_velocity = 0.752
        
        n = st.number_input(f"Manning's n", 0.010, 0.050, 0.016, 0.001)
        Sx = st.number_input(f"Cross Slope (Sx) ({length_unit}/{length_unit})", 0.01, 0.10, 0.025, 0.001, format="%.3f")
        SL = st.number_input(f"Longitudinal Slope (SL) ({length_unit}/{length_unit})", 0.001, 0.10, 0.03, 0.001, format="%.3f")
        T = st.number_input(f"Spread (T) ({length_unit})", 1.0, 20.0, 8.0, 0.1)
        
        # Calculate gutter flow using Manning's equation
        Q = (Ku_gutter/n) * Sx**(1.67) * SL**(0.5) * T**(2.67)
        
        # Calculate velocity
        V = (Ku_velocity/n) * SL**(0.5) * Sx**(0.67) * T**(0.67)
        
        st.metric("Total Gutter Flow (Q)", f"{Q:.3f} {flow_unit}")
        st.metric("Flow Velocity (V)", f"{V:.2f} {length_unit}/s")
    
    with col2:
        st.subheader("Grate Parameters")
        
        grate_type = st.selectbox("Grate Type", [
            "P-1-7/8", "P-1-7/8-4", "P-1-1/8", "Curved Vane", 
            "45° Tilt-Bar", "30° Tilt-Bar", "Reticuline"
        ])
        
        # Define splash-over velocities based on Figure 7.8
        splash_over_velocities = {
            "P-1-7/8": {"2ft": 8.2, "4ft": 12.0},
            "P-1-7/8-4": {"2ft": 8.0, "4ft": 11.9},
            "P-1-1/8": {"2ft": 6.5, "4ft": 9.8},
            "Curved Vane": {"2ft": 7.4, "4ft": 10.9},
            "45° Tilt-Bar": {"2ft": 6.4, "4ft": 9.4},
            "30° Tilt-Bar": {"2ft": 5.8, "4ft": 8.6},
            "Reticuline": {"2ft": 6.3, "4ft": 9.2}
        }
        
        # Get the grate dimensions
        grate_width = st.number_input(f"Grate Width (W) ({length_unit})", 1.0, 5.0, 2.0, 0.1)
        grate_length = st.number_input(f"Grate Length (L) ({length_unit})", 1.0, 10.0, 2.0, 0.1)
        
        # Show grate-specific information
        st.markdown("### Grate Properties")
        
        # Convert length to categorical value for splash-over velocity lookup
        length_category = "2ft" if grate_length <= 3.0 else "4ft"
        
        # Get splash-over velocity for the selected grate
        Vo = splash_over_velocities[grate_type][length_category]
        
        # Adjust if using SI units
        if unit_system == "SI (metric)":
            Vo = Vo * 0.3048  # Convert from ft/s to m/s
            
        # Show splash-over velocity
        st.metric("Splash-over Velocity (Vo)", f"{Vo:.2f} {length_unit}/s")
        
        # Show efficiency values from Table 7.2 (if needed)
        st.markdown("#### Debris Handling Efficiency")
        debris_handling = {
            "Curved Vane": "Highest",
            "30° Tilt-Bar": "Very Good",
            "45° Tilt-Bar": "Good",
            "P-1-7/8": "Moderate",
            "P-1-7/8-4": "Fair",
            "45° Tilt-Bar": "Fair",
            "Reticuline": "Poor",
            "P-1-1/8": "Poor"
        }
        st.info(f"Debris Handling: {debris_handling.get(grate_type, 'Unknown')}")
        
        # Show bicycle safety from Table 7.3 (if needed)
        bicycle_safety = {
            "P-1-7/8-4": "Excellent",
            "Reticuline": "Very Good",
            "P-1-1/8": "Good",
            "45° Tilt-Bar": "Good",
            "Curved Vane": "Fair",
            "30° Tilt-Bar": "Fair",
            "P-1-7/8": "Poor - Not bicycle safe"
        }
        st.info(f"Bicycle Safety: {bicycle_safety.get(grate_type, 'Unknown')}")
        
        clogging_factor = st.slider("Clogging Factor (%)", 0, 50, 0, 5) / 100
    
    # Calculation section
    st.header("Calculations")
    
    # Calculate frontal flow ratio (Eo)
    Eo = 1 - (1 - min(grate_width/T, 1.0))**2.67
    
    # Calculate frontal flow interception efficiency (Rf)
    if V < Vo:
        Rf = 1.0
    else:
        Rf = 1 - Ku_splash * (V - Vo)
        Rf = max(0.0, min(1.0, Rf))  # Limit Rf between 0 and 1
    
    # Calculate side flow interception efficiency (Rs)
    Rs = 1 / (1 + (Ku_side * V**1.8) / (Sx * grate_length**2.3))
    
    # Calculate total interception efficiency
    E = Rf * Eo + Rs * (1 - Eo)
    
    # Calculate interception capacity
    Qi = Q * E
    
    # Calculate bypass flow
    Qb = Q - Qi
    
    # Apply clogging reduction if specified
    if clogging_factor > 0:
        Qi_clogged = Qi * (1 - clogging_factor)
        Qb_clogged = Q - Qi_clogged
    else:
        Qi_clogged = Qi
        Qb_clogged = Qb
    
    # Create columns for results
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Interception Efficiency")
        st.metric("Frontal Flow Ratio (Eo)", f"{Eo:.3f}")
        st.metric("Frontal Flow Efficiency (Rf)", f"{Rf:.3f}")
        st.metric("Side Flow Efficiency (Rs)", f"{Rs:.3f}")
        st.metric("Total Efficiency (E)", f"{E:.3f}")
    
    with col2:
        st.subheader("Flow Results")
        st.metric("Intercepted Flow (Qi)", f"{Qi_clogged:.3f} {flow_unit}")
        st.metric("Bypass Flow (Qb)", f"{Qb_clogged:.3f} {flow_unit}")
        st.metric("Interception Efficiency", f"{(Qi_clogged/Q)*100:.1f}%")
    
    # Create a visual representation
    st.header("Visual Representation")
    
    # Create a simple visualization
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot the gutter cross-section
    x_gutter = np.linspace(0, T, 100)
    y_gutter = Sx * x_gutter
    
    # Plot the water surface and gutter
    ax.plot(x_gutter, y_gutter, 'b-', linewidth=2)
    ax.fill_between(x_gutter, 0, y_gutter, color='blue', alpha=0.3)
    
    # Plot the grate
    grate_x = [0, grate_width, grate_width, 0, 0]
    grate_y = [0, Sx*grate_width, Sx*grate_width, 0, 0]
    ax.plot(grate_x, grate_y, 'k-', linewidth=2)
    
    # Fill the grate area
    ax.fill_between([0, grate_width], 0, [0, Sx*grate_width], color='gray', alpha=0.5)
    
    # Add flow arrows
    arrow_x = T * 0.7
    arrow_y = Sx * arrow_x * 0.5
    ax.arrow(arrow_x, arrow_y, -0.3, 0, head_width=0.02, head_length=0.1, fc='black', ec='black')
    
    # Add labels
    ax.set_xlabel(f'Width ({length_unit})')
    ax.set_ylabel(f'Depth ({length_unit})')
    ax.set_title('Gutter Cross-Section with Grate Inlet')
    ax.grid(True)
    
    # Set equal aspect ratio
    ax.set_aspect('equal')
    
    # Show plot
    st.pyplot(fig)
    
    with st.expander("💡 Why Efficiency Is Important"):
        st.markdown("""
        ### Efficiency and Flow Interception
        
        The efficiency of a grate inlet determines how much of the approaching flow is captured versus how much bypasses the inlet. This is critical for designing drainage systems that effectively manage stormwater runoff.
        
        ### Key Factors Affecting Efficiency:
        - **Frontal Flow**: Flow directly approaching the front of the grate
        - **Side Flow**: Flow passing along the side of the grate
        - **Splash-over**: At higher velocities, water can splash over the grate, reducing efficiency
        - **Clogging**: Debris accumulation can significantly reduce interception capacity
        
        ### Why It Matters:
        - Designing inlets with inadequate efficiency can lead to excess bypass flow
        - Bypassed flow might contribute to flooding further downstream
        - Properly sized inlets help maintain safe roadway conditions during storm events
        """)
    
    with st.expander("ℹ️ About the Equations"):
        st.markdown(r"""
        ### 📘 Manning's Equation for Gutter Flow:
        
        $$Q = \frac{K_u}{n} S_x^{1.67} S_L^{0.5} T^{2.67}$$
        
        Where:
        - $Q$ = Total gutter flow (ft³/s or m³/s)
        - $K_u$ = Unit conversion constant (0.56 for US units, 0.376 for SI)
        - $n$ = Manning's roughness coefficient
        - $S_x$ = Cross slope (ft/ft or m/m)
        - $S_L$ = Longitudinal slope (ft/ft or m/m)
        - $T$ = Spread width (ft or m)
        
        ### Frontal Flow Ratio:
        
        $$E_o = \frac{Q_w}{Q} = 1 - \left(1 - \frac{W}{T}\right)^{2.67}$$
        
        Where:
        - $E_o$ = Frontal flow ratio
        - $W$ = Width of grate (ft or m)
        - $T$ = Total spread width (ft or m)
        
        ### Frontal Flow Interception Efficiency:
        
        $$R_f = 1 - K_u(V - V_o)$$
        
        Where:
        - $R_f$ = Frontal flow interception efficiency
        - $K_u$ = Unit conversion constant (0.09 for US units, 0.295 for SI)
        - $V$ = Velocity of flow in the gutter (ft/s or m/s)
        - $V_o$ = Splash-over velocity (ft/s or m/s)
        
        ### Side Flow Interception Efficiency:
        
        $$R_s = \frac{1}{1 + \frac{K_u V^{1.8}}{S_x L^{2.3}}}$$
        
        Where:
        - $R_s$ = Side flow interception efficiency
        - $K_u$ = Unit conversion constant (0.15 for US units, 0.0828 for SI)
        - $L$ = Length of grate (ft or m)
        
        ### Total Interception Efficiency:
        
        $$E = R_f E_o + R_s(1 - E_o)$$
        
        ### Interception Capacity:
        
        $$Q_i = Q \times E$$
        
        Where:
        - $Q_i$ = Intercepted flow (ft³/s or m³/s)
        """)

# Tab 2: Grate Inlets in Sag
with tab2:
    st.header("Grate Inlets in Sag Locations")
    
    st.markdown("""
    This calculator determines the interception capacity of grate inlets at sag points (low points) where water ponds.
    In sag locations, inlets operate as weirs under low-depth conditions and as orifices at greater depths.
    """)
    
    # Input parameters - create two columns for inputs
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Gutter Parameters")
        unit_system_sag = st.radio("Unit System", ["US Customary", "SI (metric)"], key="sag_units")
        
        if unit_system_sag == "US Customary":
            length_unit_sag = "ft"
            flow_unit_sag = "ft³/s"
            g = 32.2  # ft/s²
        else:
            length_unit_sag = "m"
            flow_unit_sag = "m³/s"
            g = 9.81  # m/s²
        
        Sx_sag = st.number_input(f"Cross Slope (Sx) ({length_unit_sag}/{length_unit_sag})", 0.01, 0.10, 0.025, 0.001, format="%.3f", key="Sx_sag")
        Sw_sag = st.number_input(f"Gutter Depression Slope (Sw) ({length_unit_sag}/{length_unit_sag})", 0.00, 0.10, 0.05, 0.001, format="%.3f", key="Sw_sag")
        Q_sag = st.number_input(f"Design Flow (Q) ({flow_unit_sag})", 0.1, 20.0, 5.0, 0.1, key="Q_sag")
        d_curb = st.number_input(f"Depth at Curb (d) ({length_unit_sag})", 0.05, 1.0, 0.33, 0.01, key="d_curb")
        
        # Calculate water spread based on depth at curb
        T_sag = d_curb / Sx_sag
        st.metric("Calculated Spread (T)", f"{T_sag:.2f} {length_unit_sag}")
    
    with col2:
        st.subheader("Grate Parameters")
        
        grate_type_sag = st.selectbox("Grate Type", [
            "P-1-7/8", "P-1-7/8-4", "P-1-1/8", "Curved Vane", 
            "45° Tilt-Bar", "30° Tilt-Bar", "Reticuline"
        ], key="grate_type_sag")
        
        # Get the grate dimensions
        grate_width_sag = st.number_input(f"Grate Width (W) ({length_unit_sag})", 1.0, 5.0, 2.0, 0.1, key="grate_width_sag")
        grate_length_sag = st.number_input(f"Grate Length (L) ({length_unit_sag})", 1.0, 10.0, 3.0, 0.1, key="grate_length_sag")
        
        # Define opening ratios based on Table 7.5
        opening_ratios = {
            "P-1-7/8": 0.9, 
            "P-1-7/8-4": 0.8, 
            "P-1-1/8": 0.6, 
            "Curved Vane": 0.35, 
            "45° Tilt-Bar": 0.34, 
            "30° Tilt-Bar": 0.34, 
            "Reticuline": 0.8
        }
        
        opening_ratio = opening_ratios[grate_type_sag]
        
        # Calculate clear opening area
        clear_area = grate_width_sag * grate_length_sag * opening_ratio
        
        st.metric("Opening Ratio", f"{opening_ratio:.2f}")
        st.metric("Clear Opening Area", f"{clear_area:.2f} {length_unit_sag}²")
        
        # Include clogging factor for sag condition
        clogging_factor_sag = st.slider("Clogging Factor (%)", 0, 50, 0, 5, key="clogging_sag") / 100
        
        # Calculate effective perimeter and area with clogging
        effective_perimeter = (1 - clogging_factor_sag) * (grate_length_sag + 2 * grate_width_sag)
        effective_area = (1 - clogging_factor_sag) * clear_area
        
        st.metric("Effective Perimeter", f"{effective_perimeter:.2f} {length_unit_sag}")
        st.metric("Effective Area", f"{effective_area:.2f} {length_unit_sag}²")
    
    # Calculation section for sag inlet
    st.header("Calculations")
    
    # Calculate average depth over grate
    d_avg = d_curb - (grate_width_sag/2) * Sw_sag
    
    # Calculate weir coefficient
    Cw = 0.37  # Typical value per HEC-22
    
    # Calculate orifice coefficient
    Co = 0.67  # Typical value per HEC-22
    
    # Calculate capacity under weir conditions (Equation 7.14)
    Qi_weir = Cw * (2*g)**0.5 * effective_perimeter * d_avg**1.5
    
    # Calculate capacity under orifice conditions (Equation 7.15)
    Qi_orifice = Co * effective_area * (2*g*d_avg)**0.5
    
    # Determine which flow regime controls
    if Qi_weir < Qi_orifice:
        flow_regime = "Weir Flow"
        Qi_sag = Qi_weir
    else:
        flow_regime = "Orifice Flow"
        Qi_sag = Qi_orifice
    
    # Create columns for results
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Flow Regime")
        st.info(f"Controlling Flow Regime: **{flow_regime}**")
        st.metric("Average Depth Over Grate", f"{d_avg:.3f} {length_unit_sag}")
        st.metric("Weir Flow Capacity", f"{Qi_weir:.3f} {flow_unit_sag}")
        st.metric("Orifice Flow Capacity", f"{Qi_orifice:.3f} {flow_unit_sag}")
    
    with col2:
        st.subheader("Flow Results")  
        st.metric("Inlet Capacity", f"{Qi_sag:.3f} {flow_unit_sag}")
        
        # Check if inlet is adequate
        if Qi_sag >= Q_sag:
            st.success(f"✓ Inlet is adequate - Capacity exceeds design flow")
            adequacy_pct = (Qi_sag / Q_sag) * 100
            st.metric("Capacity vs. Design Flow", f"{adequacy_pct:.1f}%")
        else:
            st.error(f"✗ Inlet is inadequate - Capacity is less than design flow")
            adequacy_pct = (Qi_sag / Q_sag) * 100
            st.metric("Capacity vs. Design Flow", f"{adequacy_pct:.1f}%")
            
            # Calculate spread for ponding
            # This would need a numerical solution of the weir/orifice equations
            st.warning("Additional inlet capacity needed")
    
    # Create a visual representation
    st.header("Visual Representation")
    
    # Create a simple visualization of the sag inlet
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot the gutter cross-section
    x_gutter = np.linspace(0, T_sag, 100)
    y_gutter = Sx_sag * x_gutter
    
    # Plot the water surface and gutter
    ax.plot(x_gutter, y_gutter, 'b-', linewidth=2)
    ax.fill_between(x_gutter, 0, y_gutter, color='blue', alpha=0.3)
    
    # Plot the grate
    grate_x = [0, grate_width_sag, grate_width_sag, 0, 0]
    grate_y = [0, Sx_sag*grate_width_sag, Sx_sag*grate_width_sag, 0, 0]
    ax.plot(grate_x, grate_y, 'k-', linewidth=2)
    
    # Fill the grate area
    ax.fill_between([0, grate_width_sag], 0, [0, Sx_sag*grate_width_sag], color='gray', alpha=0.5)
    
    # Add flow arrows for sag (converging from both sides)
    arrow_x1 = T_sag * 0.7
    arrow_y1 = Sx_sag * arrow_x1 * 0.5
    ax.arrow(arrow_x1, arrow_y1, -0.3, 0, head_width=0.02, head_length=0.1, fc='blue', ec='blue')
    
    arrow_x2 = T_sag * 0.3
    arrow_y2 = Sx_sag * arrow_x2 * 0.5
    ax.arrow(arrow_x2, arrow_y2, 0.3, 0, head_width=0.02, head_length=0.1, fc='blue', ec='blue')
    
    # Add labels
    ax.set_xlabel(f'Width ({length_unit_sag})')
    ax.set_ylabel(f'Depth ({length_unit_sag})')
    ax.set_title('Sag Inlet Cross-Section')
    ax.grid(True)
    
    # Set equal aspect ratio
    ax.set_aspect('equal')
    
    # Show plot
    st.pyplot(fig)
    
    # Add expandable information sections
    with st.expander("💡 Why Sag Inlets Are Critical"):
        st.markdown("""
        ### Critical Importance of Sag Inlets
        
        Inlets in sag locations (low points) are especially critical because:
        
        - They must capture **all** approaching flow, as there is no outlet for water except through the inlet
        - Ponding will occur at sag points if the inlet capacity is inadequate
        - Clogging in sag inlets can lead to significant flooding
        
        ### 🔄 Operational Differences:
        
        Sag inlets operate differently than inlets on grade:
        
        - **Weir Flow**: At shallow depths, water flows over the perimeter of the grate
        - **Orifice Flow**: At greater depths, water flows through the grate openings
        - **Transition Flow**: Between weir and orifice conditions, both mechanisms may be active
        
        ### 🚧 Design Considerations:
        
        - Designers typically use the most conservative flow estimate (lowest capacity)
        - Combination inlets or curb-opening inlets are often preferred over grate-only inlets in sags
        - "Flanking inlets" are often placed on either side of sag points as backup
        """)
    
    with st.expander("ℹ️ About the Equations"):
        st.markdown(r"""
        ### 📘 Weir Flow Equation for Sag Inlets:
        
        $$Q_i = C_w \sqrt{2g} P d^{1.5}$$
        
        Where:
        - $Q_i$ = Intercepted flow (ft³/s or m³/s)
        - $C_w$ = Weir coefficient (typically 0.37)
        - $P$ = Perimeter of the grate excluding the side against the curb (ft or m)
        - $d$ = Average depth across the grate (ft or m)
        - $g$ = Gravitational acceleration (32.2 ft/s² or 9.81 m/s²)
        
        ### Orifice Flow Equation for Sag Inlets:
        
        $$Q_i = C_o A_g \sqrt{2gd}$$
        
        Where:
        - $Q_i$ = Intercepted flow (ft³/s or m³/s)
        - $C_o$ = Orifice coefficient (typically 0.67)
        - $A_g$ = Clear opening area of the grate (ft² or m²)
        - $d$ = Average depth across the grate (ft or m)
        - $g$ = Gravitational acceleration (32.2 ft/s² or 9.81 m/s²)
        
        ### Average Depth Calculation:
        
        $$d_{avg} = d_{curb} - \frac{W}{2}S_w$$
        
        Where:
        - $d_{avg}$ = Average depth across the grate (ft or m)
        - $d_{curb}$ = Depth at curb (ft or m)
        - $W$ = Width of grate (ft or m)
        - $S_w$ = Slope of gutter depression (ft/ft or m/m)
        """)
        
# Add footer
st.markdown("---")
st.markdown("""
**References:**
- FHWA Hydraulic Engineering Circular No. 22 (HEC-22), 4th Edition
- Created using Streamlit by [Your Name]
""")
