import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats

# ── Page config ──
st.set_page_config(
    page_title="Shipping Fuel LCA Calculator",
    page_icon="🚢",
    layout="wide"
)

st.title("🚢 Shipping Fuel LCA Calculator")
st.markdown("**LNG vs Green Ammonia | Maritime Shipping | IPCC 2021 GWP100**")
st.divider()

# ════════════════════════════════════════════════════════
# HELPER FUNCTION — Slider + Number Input combo
# ════════════════════════════════════════════════════════

def slider_with_input(label, min_val, max_val, default, step, key, help_text=None):
    """Creates a slider with a synchronized number input below it."""
    
    # Initialize session state
    if key not in st.session_state:
        st.session_state[key] = default
    
    # Slider
    slider_val = st.sidebar.slider(
        label,
        min_value=float(min_val),
        max_value=float(max_val),
        value=float(st.session_state[key]),
        step=float(step),
        key=f"{key}_slider",
        help=help_text
    )
    
    # Number input below
    number_val = st.sidebar.number_input(
        f"Or type {label}",
        min_value=float(min_val),
        max_value=float(max_val),
        value=float(slider_val),
        step=float(step),
        key=f"{key}_input",
        label_visibility="collapsed"
    )
    
    # Update session state
    st.session_state[key] = number_val
    return number_val

# ════════════════════════════════════════════════════════
# SIDEBAR — ALL INPUT SLIDERS WITH NUMBER INPUTS
# ════════════════════════════════════════════════════════

st.sidebar.header("⚙️ Parameters")
st.sidebar.caption("Drag slider OR type exact value below each slider")

# ── Route ──
st.sidebar.subheader("🚢 Route")
distance_nm = slider_with_input(
    "Round-trip distance (NM)", 50, 500, 136, 0.1, "distance"
)
speed_knots = slider_with_input(
    "Average speed (knots)", 5, 25, 10, 0.1, "speed"
)
maneuver_hours = slider_with_input(
    "Maneuvering duration (hours)", 0, 12, 4, 0.1, "maneuver_h"
)

cruising_hours = distance_nm / speed_knots
total_hours = cruising_hours + maneuver_hours

st.sidebar.caption(f"Cruising time (calculated): {cruising_hours:.2f} h")
st.sidebar.caption(f"Total time: {total_hours:.2f} h")

# ── Engine ──
st.sidebar.subheader("⚙️ Engine")
engine_power = slider_with_input(
    "Power per engine (kW)", 500, 5000, 2010, 1, "engine_power"
)
n_engines = slider_with_input(
    "Number of main engines", 1, 6, 4, 1, "n_engines"
)
cruise_load = slider_with_input(
    "Cruising load (%)", 30, 100, 75, 0.1, "cruise_load"
)
maneuver_load = slider_with_input(
    "Maneuvering load (%)", 10, 60, 25, 0.1, "maneuver_load"
)
aux_power = slider_with_input(
    "Auxiliary power (kW)", 50, 1000, 300, 1, "aux_power"
)

total_power = engine_power * n_engines
st.sidebar.caption(f"Total installed power: {total_power:,.0f} kW")

# ── Fuel ──
st.sidebar.subheader("⛽ Fuel")
pilot_fraction = slider_with_input(
    "Pilot fuel fraction (%)", 0, 20, 5, 0.1, "pilot_frac"
)
lhv_lng = slider_with_input(
    "LNG LHV (MJ/kg)", 40, 55, 50.0, 0.01, "lhv_lng"
)
lhv_nh3 = slider_with_input(
    "Ammonia LHV (MJ/kg)", 15, 22, 18.6, 0.01, "lhv_nh3"
)
lhv_mgo = slider_with_input(
    "MGO LHV (MJ/kg)", 38, 46, 42.7, 0.01, "lhv_mgo"
)

# ── Emission Factors ──
st.sidebar.subheader("🌫️ Emission Factors (g/MJ)")
ef_lng_co2 = slider_with_input(
    "LNG CO2", 50, 65, 57.3, 0.001, "ef_lng_co2"
)
ef_lng_ch4 = slider_with_input(
    "LNG CH4", 0.0, 1.0, 0.41, 0.001, "ef_lng_ch4"
)
ef_lng_n2o_x1000 = slider_with_input(
    "LNG N2O (×10⁻³)", 0.0, 10.0, 2.92, 0.001, "ef_lng_n2o"
)
ef_lng_n2o = ef_lng_n2o_x1000 / 1000

ef_nh3_n2o = slider_with_input(
    "Ammonia N2O", 0.0, 1.0, 0.27, 0.001, "ef_nh3_n2o"
)
ef_nh3_slip = slider_with_input(
    "Ammonia NH3 slip", 0.0, 5.0, 1.39, 0.001, "ef_nh3_slip"
)

ef_mgo_co2 = slider_with_input(
    "MGO CO2", 65, 85, 75.1, 0.001, "ef_mgo_co2"
)
ef_mgo_ch4_x1000 = slider_with_input(
    "MGO CH4 (×10⁻³)", 0.0, 5.0, 1.41, 0.001, "ef_mgo_ch4"
)
ef_mgo_ch4 = ef_mgo_ch4_x1000 / 1000

ef_mgo_n2o_x1000 = slider_with_input(
    "MGO N2O (×10⁻³)", 0.0, 10.0, 4.22, 0.001, "ef_mgo_n2o"
)
ef_mgo_n2o = ef_mgo_n2o_x1000 / 1000

# ── SCR ──
st.sidebar.subheader("🔧 SCR (Ammonia only)")
scr_efficiency = slider_with_input(
    "SCR efficiency (%)", 0, 100, 20, 0.1, "scr_eff"
)

# ── Characterization Factors ──
CF_CO2 = 1.0
CF_CH4 = 27.2
CF_N2O = 273.0
CF_NH3 = 0.0

st.sidebar.divider()
st.sidebar.markdown("**LCIA Method:** IPCC 2021 GWP100")
st.sidebar.caption(f"CO2: {CF_CO2} | CH4: {CF_CH4} | N2O: {CF_N2O} | NH3: {CF_NH3}")

# ════════════════════════════════════════════════════════
# CALCULATIONS
# ════════════════════════════════════════════════════════

e_cruising = total_power * (cruise_load/100) * cruising_hours
e_maneuver = total_power * (maneuver_load/100) * maneuver_hours
e_aux = aux_power * total_hours
e_total_kwh = e_cruising + e_maneuver + e_aux
e_total_mj = e_total_kwh * 3.6

e_pilot = e_total_mj * (pilot_fraction/100)
e_main = e_total_mj * (1 - pilot_fraction/100)

mass_pilot = e_pilot / lhv_mgo
mass_lng = e_main / lhv_lng
mass_nh3 = e_main / lhv_nh3

lng_co2 = e_main * ef_lng_co2 / 1000
lng_ch4 = e_main * ef_lng_ch4 / 1000
lng_n2o = e_main * ef_lng_n2o / 1000

mgo_co2 = e_pilot * ef_mgo_co2 / 1000
mgo_ch4 = e_pilot * ef_mgo_ch4 / 1000
mgo_n2o = e_pilot * ef_mgo_n2o / 1000

lng_gwp = (lng_co2*CF_CO2 + lng_ch4*CF_CH4 + lng_n2o*CF_N2O +
           mgo_co2*CF_CO2 + mgo_ch4*CF_CH4 + mgo_n2o*CF_N2O)

nh3_n2o_raw = e_main * ef_nh3_n2o / 1000
nh3_n2o = nh3_n2o_raw * (1 - scr_efficiency/100)
nh3_slip = e_main * ef_nh3_slip / 1000

amm_gwp = (nh3_n2o*CF_N2O + nh3_slip*CF_NH3 +
           mgo_co2*CF_CO2 + mgo_ch4*CF_CH4 + mgo_n2o*CF_N2O)

# ════════════════════════════════════════════════════════
# DISPLAY: ENERGY DEMAND
# ════════════════════════════════════════════════════════

st.subheader("⚡ Energy Demand (calculated)")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Propulsion Energy (Cruising)", f"{e_cruising:,.0f} kWh")
with col2:
    st.metric("Propulsion Energy (DP/Maneuvering)", f"{e_maneuver:,.0f} kWh")
with col3:
    st.metric("Auxiliary Energy Demand", f"{e_aux:,.0f} kWh")
with col4:
    st.metric("**Total Energy Demand**", f"{e_total_mj:,.1f} MJ")

col5, col6 = st.columns(2)
with col5:
    st.info(f"**Pilot fuel energy** ({pilot_fraction:.1f}%): {e_pilot:,.1f} MJ")
with col6:
    st.info(f"**Main fuel energy** ({100-pilot_fraction:.1f}%): {e_main:,.1f} MJ")

st.divider()

# ════════════════════════════════════════════════════════
# DISPLAY: FUEL MASS
# ════════════════════════════════════════════════════════

st.subheader("⛽ Fuel Consumption per Round Trip")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**🔵 LNG Configuration**")
    st.metric("LNG", f"{mass_lng:,.0f} kg")
    st.metric("MGO pilot", f"{mass_pilot:,.0f} kg")
    st.metric("**Total fuel**", f"{mass_lng + mass_pilot:,.0f} kg")

with col2:
    st.markdown("**🟢 Ammonia Configuration**")
    st.metric("Green Ammonia", f"{mass_nh3:,.0f} kg")
    st.metric("MGO pilot", f"{mass_pilot:,.0f} kg")
    st.metric("**Total fuel**", f"{mass_nh3 + mass_pilot:,.0f} kg")

if mass_lng > 0:
    st.caption(f"Note: Ammonia requires {mass_nh3/mass_lng:.1f}× more mass than LNG for the same energy.")

st.divider()

# ════════════════════════════════════════════════════════
# DISPLAY: GWP RESULTS
# ════════════════════════════════════════════════════════

st.subheader("📊 GWP100 Results — One Round Trip")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="🔵 LNG + MGO",
        value=f"{lng_gwp:,.0f} kg CO2-eq",
        help="Reference scenario"
    )

with col2:
    diff = amm_gwp - lng_gwp
    pct = diff / lng_gwp * 100 if lng_gwp > 0 else 0
    label = f"{abs(pct):.1f}% {'more' if pct > 0 else 'less'} GWP than LNG"
    color = "inverse" if pct > 0 else "normal"
    st.metric(
        label=f"🟢 Ammonia + MGO (SCR {scr_efficiency:.1f}%)",
        value=f"{amm_gwp:,.0f} kg CO2-eq",
        delta=label,
        delta_color=color
    )

st.divider()

# ════════════════════════════════════════════════════════
# CHARTS — TWO COLUMNS
# ════════════════════════════════════════════════════════

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Scenario Comparison")
    
    scenarios = ['LNG + MGO', f'Ammonia + MGO\nSCR {scr_efficiency:.1f}%']
    values = [lng_gwp, amm_gwp]
    colors = ['#2196F3', '#4CAF50']
    
    fig1, ax1 = plt.subplots(figsize=(7, 5))
    bars = ax1.bar(scenarios, values, color=colors, edgecolor='white', linewidth=0.5)
    ax1.axhline(y=lng_gwp, color='blue', linestyle='--', linewidth=1.5, alpha=0.5)
    
    for bar, val in zip(bars, values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 200,
                 f'{val:,.0f}', ha='center', va='bottom',
                 fontsize=10, fontweight='bold')
    
    ax1.set_ylabel('GWP100 (kg CO2-eq per round trip)')
    ax1.set_title('Scenario Comparison')
    ax1.grid(True, alpha=0.3, axis='y')
    st.pyplot(fig1)

with col_right:
    st.subheader("📈 SCR Sensitivity Analysis")
    
    scr_range = np.arange(0, 101, 1)
    ammonia_scores = []
    for scr in scr_range:
        n2o_scr = (e_main * ef_nh3_n2o / 1000) * (1 - scr/100)
        gwp = (n2o_scr*CF_N2O + nh3_slip*CF_NH3 +
               mgo_co2*CF_CO2 + mgo_ch4*CF_CH4 + mgo_n2o*CF_N2O)
        ammonia_scores.append(gwp)
    
    breakeven = next((s for s, score in zip(scr_range, ammonia_scores)
                      if score <= lng_gwp), None)
    
    fig2, ax2 = plt.subplots(figsize=(7, 5))
    ax2.plot(scr_range, ammonia_scores, color='green',
             linewidth=2.5, label='Green Ammonia + MGO')
    ax2.axhline(y=lng_gwp, color='blue', linewidth=2,
                linestyle='--', label=f'LNG ref ({lng_gwp:,.0f})')
    
    if breakeven is not None:
        ax2.axvline(x=breakeven, color='red', linewidth=1.5,
                    linestyle=':', label=f'Breakeven: {breakeven}% SCR')
    
    ax2.scatter([scr_efficiency], [amm_gwp],
                color='green', s=100, zorder=5,
                label=f'Current: SCR {scr_efficiency:.1f}%')
    
    ax2.set_xlabel('SCR Efficiency (%)')
    ax2.set_ylabel('GWP100 (kg CO2-eq per round trip)')
    ax2.set_title('SCR Sensitivity')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)
    st.pyplot(fig2)

st.divider()

# ════════════════════════════════════════════════════════
# CONTRIBUTION ANALYSIS
# ════════════════════════════════════════════════════════

st.subheader("🔍 Contribution Analysis")

contrib_data = {
    'CO2': [(lng_co2 + mgo_co2)*CF_CO2, mgo_co2*CF_CO2],
    'CH4': [(lng_ch4 + mgo_ch4)*CF_CH4, mgo_ch4*CF_CH4],
    'N2O': [(lng_n2o + mgo_n2o)*CF_N2O, (nh3_n2o + mgo_n2o)*CF_N2O],
}

df_contrib = pd.DataFrame(
    contrib_data,
    index=['LNG + MGO', f'Ammonia + MGO\nSCR {scr_efficiency:.1f}%']
)

fig3, ax3 = plt.subplots(figsize=(10, 5))
colors_contrib = ['#2196F3', '#FF9800', '#F44336']
bottom = np.zeros(2)

for pollutant, color in zip(['CO2', 'CH4', 'N2O'], colors_contrib):
    values = df_contrib[pollutant].values
    ax3.bar(df_contrib.index, values, bottom=bottom,
            color=color, label=pollutant,
            edgecolor='white', linewidth=0.5)
    for j, (val, bot) in enumerate(zip(values, bottom)):
        if val > 300:
            ax3.text(j, bot + val/2, f'{val:,.0f}',
                     ha='center', va='center',
                     fontsize=10, color='white', fontweight='bold')
    bottom += values

ax3.set_ylabel('GWP100 (kg CO2-eq per round trip)')
ax3.set_title('Contribution Analysis by Pollutant')
ax3.legend()
ax3.grid(True, alpha=0.3, axis='y')
st.pyplot(fig3)

st.divider()

# ════════════════════════════════════════════════════════
# MONTE CARLO
# ════════════════════════════════════════════════════════

st.subheader("🎲 Monte Carlo Uncertainty Analysis")
st.markdown("±20% uncertainty on emission factors | 1,000 simulation runs")

n_runs = 1000
np.random.seed(42)

def sample_factor(value):
    std = value * 0.20 / 2
    return np.clip(np.random.normal(value, std, n_runs), 0, None)

s_lng_co2 = sample_factor(ef_lng_co2)
s_lng_ch4 = sample_factor(ef_lng_ch4)
s_lng_n2o = sample_factor(ef_lng_n2o)
s_nh3_n2o = sample_factor(ef_nh3_n2o)
s_mgo_co2 = sample_factor(ef_mgo_co2)
s_mgo_ch4 = sample_factor(ef_mgo_ch4)
s_mgo_n2o = sample_factor(ef_mgo_n2o)

lng_runs = (e_main*s_lng_co2/1000*CF_CO2 + e_main*s_lng_ch4/1000*CF_CH4 +
            e_main*s_lng_n2o/1000*CF_N2O + e_pilot*s_mgo_co2/1000*CF_CO2 +
            e_pilot*s_mgo_ch4/1000*CF_CH4 + e_pilot*s_mgo_n2o/1000*CF_N2O)

amm_runs = (e_main*s_nh3_n2o/1000*(1-scr_efficiency/100)*CF_N2O +
            e_pilot*s_mgo_co2/1000*CF_CO2 + e_pilot*s_mgo_ch4/1000*CF_CH4 +
            e_pilot*s_mgo_n2o/1000*CF_N2O)

mc_stats = pd.DataFrame({
    'Scenario': ['LNG + MGO', f'Ammonia + MGO (SCR {scr_efficiency:.1f}%)'],
    'Mean (kg CO2-eq)': [f"{np.mean(r):,.0f}" for r in [lng_runs, amm_runs]],
    '5th Percentile': [f"{np.percentile(r,5):,.0f}" for r in [lng_runs, amm_runs]],
    '95th Percentile': [f"{np.percentile(r,95):,.0f}" for r in [lng_runs, amm_runs]],
})
st.dataframe(mc_stats, use_container_width=True)

fig4, ax4 = plt.subplots(figsize=(12, 6))

mc_scenarios = [
    ('LNG + MGO', lng_runs, '#2196F3'),
    (f'Ammonia + MGO (SCR {scr_efficiency:.1f}%)', amm_runs, '#4CAF50'),
]

for name, runs, color in mc_scenarios:
    mu = np.mean(runs)
    std = np.std(runs)
    x = np.linspace(mu - 4*std, mu + 4*std, 300)
    ax4.plot(x, stats.norm.pdf(x, mu, std), color=color, linewidth=2.5,
             label=f'{name} (mean: {mu:,.0f})')
    ax4.fill_between(x, stats.norm.pdf(x, mu, std), alpha=0.15, color=color)

ax4.set_xlabel('GWP100 (kg CO2-eq per round trip)', fontsize=12)
ax4.set_ylabel('Probability density', fontsize=12)
ax4.set_title('Monte Carlo Distributions | ±20% uncertainty | 1,000 runs',
              fontsize=12)
ax4.legend(fontsize=10)
ax4.grid(True, alpha=0.3)
st.pyplot(fig4)

st.divider()

# ════════════════════════════════════════════════════════
# KEY FINDINGS
# ════════════════════════════════════════════════════════

st.subheader("🔑 Key Findings")

col_a, col_b, col_c = st.columns(3)

with col_a:
    if breakeven is not None:
        st.info(f"**Breakeven SCR: {breakeven}%**\n\n"
                f"Green ammonia needs at least {breakeven}% SCR efficiency "
                f"to outperform LNG under current settings.")
    else:
        st.warning("**No breakeven found**\n\nAmmonia cannot beat LNG even at 100% SCR.")

with col_b:
    if amm_gwp > 0:
        n2o_pct = (nh3_n2o * CF_N2O) / amm_gwp * 100
    else:
        n2o_pct = 0
    st.warning(f"**N2O drives {n2o_pct:.1f}% of ammonia GWP**\n\n"
               f"N2O is the most critical parameter "
               f"for ammonia's climate performance.")

with col_c:
    fuel_ratio = mass_nh3 / mass_lng if mass_lng > 0 else 0
    st.error(f"**Ammonia needs {fuel_ratio:.1f}× more mass**\n\n"
             f"For same energy delivery — important for "
             f"vessel storage tank sizing.")

st.divider()
st.caption("Physics-based simulation | IPCC 2021 GWP100 | "
           "Brightway2 + Python + Streamlit | One complete round trip")
