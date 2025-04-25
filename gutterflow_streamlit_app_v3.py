import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

st.title("Composite Gutter Flow Calculator")

with st.expander("ℹ️ About this app"):
    st.markdown("""
    This [Streamlit](https://streamlit.io/) app calculates the width of flow in a composite gutter section for roadside drainage use. This uses Mannings Equation, which is an iterative process, more details below...

    How it works...
   
    ### 📘 The Manning’s Equation for open channel flow is:
      """)

# Display Manning's equation using LaTeX
st.latex(r'''
V = \frac{k}{n} R_h^{2/3} S^{1/2}
''')

# Display with the full equation and variable definitions
st.markdown(r'''
### Manning's Equation

$$V = \frac{k}{n} R_h^{2/3} S^{1/2}$$

Where:
- $V$ = Mean velocity (m/s or ft/s)
- $k$ = Conversion constant (1.0 for SI units, 1.49 for US customary units)
- $n$ = Manning's roughness coefficient
- $R_h$ = Hydraulic radius (m or ft)
- $S$ = Channel slope (m/m or ft/ft)

The discharge equation is:
$$Q = V \times A$$

Where:
- $Q$ = Discharge (m³/s or ft³/s)
- $A$ = Cross-sectional area (m² or ft²)
''')


 st.markdown("""
 ---
    ### 🔁 Why Iteration Is Needed

    If we **know the flow** \( Q \) and want to find **depth** or **top width**:

    - We can't solve the equation algebraically for depth because both **\( A \)** and **\( P \)** depend nonlinearly on the depth or top width.
    - The **hydraulic radius** \( R = A/P \) changes as we change depth.
    - So we must use a **numerical approach** (trial and error or a root finder).

---

    ### 🌀 Iteration Process

    1. **Guess** a depth or top width.
    2. **Compute**:
       - \( A \) = flow area
       - \( P \) = wetted perimeter
       - \( R = A/P \)
    3. **Calculate** flow \( Q_{calc} \) using Manning’s Equation.
    4. **Compare** \( Q_{calc} \) to your known flow \( Q \).
    5. If close, **done**. If not, **adjust** and try again.

    This is why the tool uses a numerical solver (`root_scalar`) — it automates this iterative process to find the correct top width for any given flow.

    ### Why It Matters
    - In simple shapes (rectangualr, triangular), the iteration is pretty fast
    - In complex sections (box culverts, irregular gutters), **iteration is essential** because \( A \) and \( P \) vary nonlinerarly with depth. 
    - No closed-form solution for \( h \) or \( T \) -> **must use numerical methods**.
    
    Created by [Mike Thomas](https://www.linkedin.com/in/mikethomasca/)
    """)



st.sidebar.header("Input Parameters")

W = st.sidebar.slider("Gutter Width W (m)", 0.1, 1.0, 0.3, 0.001, format="%.3f")
Sw = st.sidebar.slider("Gutter Slope Sw (rise/run)", 0.001, 0.1, 0.065, 0.001, format="%.3f")
Nw = st.sidebar.number_input("Manning’s n for Gutter Nw", value=0.012, step=0.001, format="%.3f")
Sx = st.sidebar.slider("Road Cross Slope Sx", 0.001, 0.1, 0.020, 0.001, format="%.3f")
Nx = st.sidebar.number_input("Manning’s n for Road Nx", value=0.018, step=0.001, format="%.3f")
Sl = st.sidebar.slider("Longitudinal Slope Sl", 0.001, 0.12, 0.02, 0.001, format="%.3f")
Q_max = st.sidebar.number_input("Max Flow Q for Plot (m³/s)", value=0.10, step=0.001, format="%.3f")
Q_input = st.sidebar.number_input("Target Flow Q_input (m³/s)", value=0.025, step=0.001, format="%.3f")

def mannings_flow(area, hydraulic_radius, slope, n):
    return (1 / n) * area * (hydraulic_radius ** (2 / 3)) * (slope ** 0.5)

def compute_composite_flow(T, W, Sw, Nw, Sx, Nx, Sl):
    Tw = min(T, W)
    Ts = max(T - W, 0)

    Aw = 0.5 * Tw * (Sw * Tw)
    Pw = Tw * np.sqrt(1 + Sw**2)
    Rw = Aw / Pw if Pw != 0 else 0
    Qw = mannings_flow(Aw, Rw, Sl, Nw)

    As = Ts * (Sw * W + Sx * Ts / 2)
    Ps = Ts + np.sqrt((Sw * W)**2 + Ts**2) + Ts * np.sqrt(1 + Sx**2)
    Rs = As / Ps if Ps != 0 else 0
    Qs = mannings_flow(As, Rs, Sl, Nx)

    return Qw + Qs

def compute_max_depth(T, W, Sw, Sx):
    if T <= W:
        return Sw * T
    else:
        return Sw * W + Sx * (T - W)

T_values = np.linspace(0.01, 10.0, 500)
Q_values = [compute_composite_flow(T, W, Sw, Nw, Sx, Nx, Sl) for T in T_values]
T_filtered = [T for T, Q in zip(T_values, Q_values) if Q <= Q_max]
Q_filtered = [Q for Q in Q_values if Q <= Q_max]

try:
    flow_interp = interp1d(Q_filtered, T_filtered, fill_value="extrapolate")
    T_for_Q_input = float(flow_interp(Q_input))
    depth_for_Q_input = compute_max_depth(T_for_Q_input, W, Sw, Sx)
except:
    T_for_Q_input = None
    depth_for_Q_input = None

fig, ax = plt.subplots()
ax.plot(T_filtered, Q_filtered, label="Flow vs Top Width", color="teal")
if T_for_Q_input and Q_input <= Q_max:
    ax.axhline(y=Q_input, color='red', linestyle='--', label=f"Q_input = {Q_input:.3f} m³/s")
    ax.axvline(x=T_for_Q_input, color='blue', linestyle='--', label=f"T = {T_for_Q_input:.3f} m")
    ax.plot(T_for_Q_input, Q_input, 'ro')
ax.set_xlabel("Top Width T (m)")
ax.set_ylabel("Flow Q (m³/s)")
ax.set_title("Flow vs Top Width in Composite Gutter Section")
ax.grid(True)
ax.legend()
st.pyplot(fig)

if T_for_Q_input and Q_input <= Q_max:
    st.markdown(f"**Computed Top Width for Q_input = {Q_input:.3f} m³/s is T = {T_for_Q_input:.3f} m**")
    st.markdown(f"**Maximum Depth at T = {T_for_Q_input:.3f} m is {depth_for_Q_input:.3f} m**")
    if depth_for_Q_input > 0.150:
        st.warning("⚠️ Maximum depth exceeds 150 mm limit!")

# Display input variables used
st.markdown("---")
st.markdown("### Variables Used in Calculation")
st.markdown(f"- **Gutter Width W** = {W:.3f} m")
st.markdown(f"- **Gutter Slope Sw** = {Sw:.3f}")
st.markdown(f"- **Manning's n for Gutter Nw** = {Nw:.3f}")
st.markdown(f"- **Road Cross Slope Sx** = {Sx:.3f}")
st.markdown(f"- **Manning's n for Road Nx** = {Nx:.3f}")
st.markdown(f"- **Longitudinal Slope Sl** = {Sl:.3f}")
