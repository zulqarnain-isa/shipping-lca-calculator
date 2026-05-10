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
# SIDEBAR — SLIDERS ONLY
# ════════════════════════════════════════════════════════

st.sidebar.header("⚙️ Parameters")
st.sidebar.caption("Adjust sliders to explore parameter effects")

# ── Route ──
st.sidebar.subheader("🚢 Route")
distance_nm = st.sidebar.slider("Round-trip distance (NM)", 50.0, 500.0, 136.0, 0.1)
speed_knots = st.sidebar.slider("Average speed (knots)", 5.0, 25.0, 10.0, 0.1)
maneuver_hours = st.sidebar.slider("Maneuvering duration (hours)", 0.0, 12.0, 4.0, 0.1)

cruising_hours = distance_nm / speed_knots
total_hours = cruising_hours + maneuver_hours

st.sidebar.caption(f"Cruising time (calculated): {cruising_hours:.2f} h")
st.sidebar.caption(f"Total time: {total_hours:.2f} h")

# ── Engine ──
st.sidebar.subheader("⚙️ Engine")
engine_power = st.sidebar.slider("Power per engine (kW)", 500, 5000, 2010, 1)
n_engines = st.sidebar.slider("Number of main engines", 1, 6, 4, 1)
cruise_load = st.sidebar.slider("Cruising load (%)", 30.0, 100.0, 75.0, 0.1)
maneuver_load = st.sidebar.slider("Maneuvering load (%)", 10.0, 60.0, 25.0, 0.1)
aux_power = st.sidebar.slider("Auxiliary power (kW)", 50, 1000, 300, 1)

total_power = engine_power * n_engines
st.sidebar.caption(f"Total installed power: {total_power:,} kW")

# ── Fuel ──
st.sidebar.subheader("⛽ Fuel")
pilot_fraction = st.sidebar.slider("Pilot fuel fraction (%)", 0.0, 20.0, 5.0, 0.1)
lhv_lng = st.sidebar.slider("LNG LHV (MJ/kg)", 40.0, 55.0, 50.0, 0.01)
lhv_nh3 = st.sidebar.slider("Ammonia LHV (MJ/kg)", 15.0, 22.0, 18.6, 0.01)
lhv_mgo = st.sidebar.slider("MGO LHV (MJ/kg)", 38.0, 46.0, 42.7, 0.01)

# ── Emission Factors ──
st.sidebar.subheader("🌫️ Emission Factors (g/MJ)")
ef_lng_co2 = st.sidebar.slider("LNG CO2", 50.0, 65.0, 57.3, 0.001)
ef_lng_ch4 = st.sidebar.slider("LNG CH4", 0.0, 1.0, 0.41, 0.001)
ef_lng_n2o_x1000 = st.sidebar.slider("LNG N2O (×10⁻³)", 0.0, 10.0, 2.92, 0.001)
ef_lng_n2o = ef_lng_n2o_x1000 / 1000

ef_nh3_n2o = st.sidebar.slider("Ammonia N2O", 0.0, 1.0, 0.27, 0.001)
ef_nh3_slip = st.sidebar.slider("Ammonia NH3 slip", 0.0, 5.0, 1.39, 0.001)

ef_mgo_co2 = st.sidebar.slider("MGO CO2", 65.0, 85.0, 75.1, 0.001)
ef_mgo_ch4_x1000 = st.sidebar.slider("MGO CH4 (×10⁻³)", 0.0, 5.0, 1.41, 0.001)
ef_mgo_ch4 = ef_mgo_ch4_x1000 / 1000

ef_mgo_n2o_x1000 = st.sidebar.slider("MGO N2O (×10⁻³)", 0.0, 10.0, 4.22, 0.001)
ef_mgo_n2o = ef_mgo_n2o_x1000 / 1000

# ── WTT Emissions (NEW) ──
st.sidebar.subheader("🌍 Upstream Emissions (WTT, g CO2-eq/MJ)")
st.sidebar.caption("Source values from literature for each fuel")

include_wtt = st.sidebar.checkbox(
    "Include upstream emissions (WTW analysis)",
    value=False
)

wtt_lng = st.sidebar.slider("LNG WTT GWP100", 0.0, 30.0, 9.7, 0.1)
wtt_nh3 = st.sidebar.slider("Green Ammonia WTT GWP100", 0.0, 30.0, 9.7, 0.1)
wtt_mgo = st.sidebar.slider("MGO WTT GWP100", 0.0, 30.0, 12.8, 0.1)

# ── SCR ──
st.sidebar.subheader("🔧 SCR (Ammonia only)")
scr_efficiency = st.sidebar.slider("SCR efficiency (%)", 0.0, 100.0, 20.0, 0.1)

# ── Economic Parameters ──
st.sidebar.subheader("💰 Economic Parameters")
st.sidebar.caption("Defaults are illustrative — adjust as needed")

price_lng = st.sidebar.slider("LNG price (€/kg)", 0.1, 3.0, 0.50, 0.01)
price_nh3 = st.sidebar.slider("Green Ammonia price (€/kg)", 0.1, 5.0, 1.20, 0.01)
price_mgo = st.sidebar.slider("MGO price (€/kg)", 0.1, 2.0, 0.80, 0.01)
price_carbon = st.sidebar.slider("EU ETS carbon price (€/ton CO2)", 0, 200, 80, 1)

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

# WTT calculations (kg CO2-eq per round trip)
wtt_lng_kg = e_main * wtt_lng / 1000
wtt_nh3_kg = e_main * wtt_nh3 / 1000
wtt_mgo_kg = e_pilot * wtt_mgo / 1000

# WTW totals
lng_wtw = lng_gwp + wtt_lng_kg + wtt_mgo_kg
amm_wtw = amm_gwp + wtt_nh3_kg + wtt_mgo_kg

# Decide what to display based on toggle
if include_wtt:
    lng_display = lng_wtw
    amm_display = amm_wtw
    analysis_type = "WTW"
else:
    lng_display = lng_gwp
    amm_display = amm_gwp
    analysis_type = "TTW"

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

st.subheader(f"📊 GWP100 Results — One Round Trip ({analysis_type})")

col1, col2 = st.columns(2)

with col1:
    st.metric(label=f"🔵 LNG + MGO ({analysis_type})", 
              value=f"{lng_display:,.0f} kg CO2-eq",
              help="Reference scenario")
    if include_wtt:
        st.caption(f"TTW: {lng_gwp:,.0f} | WTT: {wtt_lng_kg + wtt_mgo_kg:,.0f}")

with col2:
    diff = amm_display - lng_display
    pct = diff / lng_display * 100 if lng_display > 0 else 0
    label = f"{abs(pct):.1f}% {'more' if pct > 0 else 'less'} GWP than LNG"
    color = "inverse" if pct > 0 else "normal"
    st.metric(
        label=f"🟢 Ammonia + MGO (SCR {scr_efficiency:.1f}%) ({analysis_type})",
        value=f"{amm_display:,.0f} kg CO2-eq",
        delta=label, delta_color=color
    )
    if include_wtt:
        st.caption(f"TTW: {amm_gwp:,.0f} | WTT: {wtt_nh3_kg + wtt_mgo_kg:,.0f}")

st.divider()

# ════════════════════════════════════════════════════════
# CHARTS — TWO COLUMNS
# ════════════════════════════════════════════════════════

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Scenario Comparison")
    
    scenarios = ['LNG + MGO', f'Ammonia + MGO\nSCR {scr_efficiency:.1f}%']
    values = [lng_display, amm_display]
    colors = ['#2196F3', '#4CAF50']
    
    fig1, ax1 = plt.subplots(figsize=(7, 5))
    bars = ax1.bar(scenarios, values, color=colors, edgecolor='white', linewidth=0.5)
    ax1.axhline(y=lng_display, color='blue', linestyle='--', linewidth=1.5, alpha=0.5)
    
    for bar, val in zip(bars, values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 200,
                 f'{val:,.0f}', ha='center', va='bottom',
                 fontsize=10, fontweight='bold')
    
    ax1.set_ylabel('GWP100 (kg CO2-eq per round trip)')
    ax1.set_title(f'Scenario Comparison ({analysis_type})')
    ax1.grid(True, alpha=0.3, axis='y')
    st.pyplot(fig1)

with col_right:
    st.subheader("📈 SCR Sensitivity Analysis")
    
    scr_range = np.arange(0, 101, 1)
    ammonia_scores = []
    for scr in scr_range:
        n2o_scr = (e_main * ef_nh3_n2o / 1000) * (1 - scr/100)
        gwp_ttw = (n2o_scr*CF_N2O + nh3_slip*CF_NH3 +
                   mgo_co2*CF_CO2 + mgo_ch4*CF_CH4 + mgo_n2o*CF_N2O)
        if include_wtt:
            gwp = gwp_ttw + wtt_nh3_kg + wtt_mgo_kg
        else:
            gwp = gwp_ttw
        ammonia_scores.append(gwp)
    
    breakeven = next((s for s, score in zip(scr_range, ammonia_scores)
                      if score <= lng_display), None)
    
    fig2, ax2 = plt.subplots(figsize=(7, 5))
    ax2.plot(scr_range, ammonia_scores, color='green',
             linewidth=2.5, label='Green Ammonia + MGO')
    ax2.axhline(y=lng_display, color='blue', linewidth=2,
                linestyle='--', label=f'LNG ref ({lng_display:,.0f})')
    
    if breakeven is not None:
        ax2.axvline(x=breakeven, color='red', linewidth=1.5,
                    linestyle=':', label=f'Breakeven: {breakeven}% SCR')
    
    ax2.scatter([scr_efficiency], [amm_display],
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
# TORNADO DIAGRAM — Impact on GWP Difference
# ════════════════════════════════════════════════════════

st.subheader("🌪️ Tornado Diagram — Parameter Importance")
st.markdown("Shows which parameters most affect the **GWP difference between Ammonia and LNG**. "
            "Each parameter varied ±20%.")

# Function to calculate both GWPs given modified parameters
def calc_both_gwps(params):
    p = {
        'ef_lng_co2': ef_lng_co2, 'ef_lng_ch4': ef_lng_ch4, 'ef_lng_n2o': ef_lng_n2o,
        'ef_nh3_n2o': ef_nh3_n2o, 'ef_nh3_slip': ef_nh3_slip,
        'ef_mgo_co2': ef_mgo_co2, 'ef_mgo_ch4': ef_mgo_ch4, 'ef_mgo_n2o': ef_mgo_n2o,
        'lhv_lng': lhv_lng, 'lhv_nh3': lhv_nh3, 'lhv_mgo': lhv_mgo,
        'engine_power': engine_power, 'n_engines': n_engines,
        'cruise_load': cruise_load, 'maneuver_load': maneuver_load,
        'aux_power': aux_power, 'cruising_hours': cruising_hours,
        'maneuver_hours': maneuver_hours, 'total_hours': total_hours,
        'pilot_fraction': pilot_fraction, 'scr_efficiency': scr_efficiency,
        'wtt_lng': wtt_lng, 'wtt_nh3': wtt_nh3, 'wtt_mgo': wtt_mgo,
    }
    p.update(params)
    
    tot_power = p['engine_power'] * p['n_engines']
    e_cr = tot_power * (p['cruise_load']/100) * p['cruising_hours']
    e_mn = tot_power * (p['maneuver_load']/100) * p['maneuver_hours']
    e_ax = p['aux_power'] * p['total_hours']
    e_t_mj = (e_cr + e_mn + e_ax) * 3.6
    
    e_p = e_t_mj * (p['pilot_fraction']/100)
    e_m = e_t_mj * (1 - p['pilot_fraction']/100)
    
    # LNG GWP
    l_co2 = e_m * p['ef_lng_co2'] / 1000
    l_ch4 = e_m * p['ef_lng_ch4'] / 1000
    l_n2o = e_m * p['ef_lng_n2o'] / 1000
    m_co2 = e_p * p['ef_mgo_co2'] / 1000
    m_ch4 = e_p * p['ef_mgo_ch4'] / 1000
    m_n2o = e_p * p['ef_mgo_n2o'] / 1000
    
    lng_g = (l_co2*CF_CO2 + l_ch4*CF_CH4 + l_n2o*CF_N2O +
             m_co2*CF_CO2 + m_ch4*CF_CH4 + m_n2o*CF_N2O)
    
    # Ammonia GWP
    n_n2o = (e_m * p['ef_nh3_n2o'] / 1000) * (1 - p['scr_efficiency']/100)
    n_slip = e_m * p['ef_nh3_slip'] / 1000
    
    amm_g = (n_n2o*CF_N2O + n_slip*CF_NH3 +
             m_co2*CF_CO2 + m_ch4*CF_CH4 + m_n2o*CF_N2O)
    
    # Add WTT if WTW mode is on
    if include_wtt:
        wtt_l = e_m * p['wtt_lng'] / 1000 + e_p * p['wtt_mgo'] / 1000
        wtt_a = e_m * p['wtt_nh3'] / 1000 + e_p * p['wtt_mgo'] / 1000
        lng_g += wtt_l
        amm_g += wtt_a
    
    return lng_g, amm_g

# Parameters to test
parameters_to_test = {
    'NH3 N2O EF':      ('ef_nh3_n2o', ef_nh3_n2o),
    'LNG CO2 EF':      ('ef_lng_co2', ef_lng_co2),
    'LNG CH4 EF':      ('ef_lng_ch4', ef_lng_ch4),
    'LNG N2O EF':      ('ef_lng_n2o', ef_lng_n2o),
    'NH3 slip EF':     ('ef_nh3_slip', ef_nh3_slip),
    'NH3 LHV':         ('lhv_nh3', lhv_nh3),
    'LNG LHV':         ('lhv_lng', lhv_lng),
    'MGO LHV':         ('lhv_mgo', lhv_mgo),
    'MGO CO2 EF':      ('ef_mgo_co2', ef_mgo_co2),
    'Cruising load':   ('cruise_load', cruise_load),
    'Engine power':    ('engine_power', engine_power),
    'Auxiliary power': ('aux_power', aux_power),
    'Pilot fraction':  ('pilot_fraction', pilot_fraction),
    'SCR efficiency':  ('scr_efficiency', scr_efficiency),
}

# Add WTT parameters when WTW mode is on
if include_wtt:
    parameters_to_test['LNG WTT'] = ('wtt_lng', wtt_lng)
    parameters_to_test['NH3 WTT'] = ('wtt_nh3', wtt_nh3)
    parameters_to_test['MGO WTT'] = ('wtt_mgo', wtt_mgo)

baseline_diff = amm_gwp - lng_gwp  # Negative if ammonia is better
tornado_data = []

for label, (param_name, base_value) in parameters_to_test.items():
    low_val = base_value * 0.80
    high_val = base_value * 1.20
    
    lng_low, amm_low = calc_both_gwps({param_name: low_val})
    lng_high, amm_high = calc_both_gwps({param_name: high_val})
    
    diff_low = amm_low - lng_low
    diff_high = amm_high - lng_high
    
    tornado_data.append({
        'parameter': label,
        'low_diff': diff_low - baseline_diff,
        'high_diff': diff_high - baseline_diff,
        'range': abs(diff_high - diff_low)
    })

# Sort by impact
tornado_data.sort(key=lambda x: x['range'], reverse=True)

# Plot
fig5, ax5 = plt.subplots(figsize=(11, 7))

y_pos = np.arange(len(tornado_data))
labels = [d['parameter'] for d in tornado_data]
low_bars = [d['low_diff'] for d in tornado_data]
high_bars = [d['high_diff'] for d in tornado_data]

ax5.barh(y_pos, low_bars, color='#2196F3', alpha=0.7, label='-20% parameter value')
ax5.barh(y_pos, high_bars, color='#F44336', alpha=0.7, label='+20% parameter value')

ax5.set_yticks(y_pos)
ax5.set_yticklabels(labels)
ax5.invert_yaxis()
ax5.axvline(x=0, color='black', linewidth=1.5)
ax5.set_xlabel('Change in (Ammonia GWP − LNG GWP) — kg CO2-eq', fontsize=11)
ax5.set_title(f'Tornado Diagram — Baseline GWP Difference: {baseline_diff:,.0f} kg CO2-eq ({analysis_type})\n'
              '(parameters ranked by impact on the comparison)', fontsize=12)

# Add directional labels on the chart
x_min, x_max = ax5.get_xlim()
y_top = -0.7
ax5.text(x_min * 0.5, y_top, '← Ammonia performs BETTER',
         ha='center', va='center', fontsize=11, fontweight='bold',
         color='#2E7D32',
         bbox=dict(boxstyle='round,pad=0.4', facecolor='#E8F5E9', edgecolor='#2E7D32'))
ax5.text(x_max * 0.5, y_top, 'LNG performs BETTER →',
         ha='center', va='center', fontsize=11, fontweight='bold',
         color='#1565C0',
         bbox=dict(boxstyle='round,pad=0.4', facecolor='#E3F2FD', edgecolor='#1565C0'))

ax5.legend(loc='lower right')
ax5.grid(True, alpha=0.3, axis='x')

plt.tight_layout()
st.pyplot(fig5)

st.markdown("""
**📖 How to read this diagram:**

- **Bar length** — Longer bars mean that parameter has a bigger impact on the comparison
- **Bar position** — Bars to the **left** mean Ammonia performs better; bars to the **right** mean LNG performs better
- **Bar color** — 🔵 Blue = parameter decreased by 20%, 🔴 Red = parameter increased by 20%

For example, if the *NH3 N2O EF* blue bar extends far to the left, it means: 
*"If NH3 N2O emissions are 20% lower than expected, ammonia performs significantly better than LNG."*
""")

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

# Add WTT as separate segment if WTW mode is on
if include_wtt:
    contrib_data['WTT (Upstream)'] = [
        wtt_lng_kg + wtt_mgo_kg,
        wtt_nh3_kg + wtt_mgo_kg
    ]

df_contrib = pd.DataFrame(
    contrib_data,
    index=['LNG + MGO', f'Ammonia + MGO\nSCR {scr_efficiency:.1f}%']
)

fig3, ax3 = plt.subplots(figsize=(10, 5))

# Build colors and pollutants list dynamically
if include_wtt:
    pollutants_list = ['CO2', 'CH4', 'N2O', 'WTT (Upstream)']
    colors_contrib = ['#2196F3', '#FF9800', '#F44336', '#4CAF50']
else:
    pollutants_list = ['CO2', 'CH4', 'N2O']
    colors_contrib = ['#2196F3', '#FF9800', '#F44336']

bottom = np.zeros(2)

for pollutant, color in zip(pollutants_list, colors_contrib):
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
ax3.set_title(f'Contribution Analysis by Pollutant ({analysis_type})')
ax3.legend()
ax3.grid(True, alpha=0.3, axis='y')
st.pyplot(fig3)

st.divider()

# ════════════════════════════════════════════════════════
# COST ANALYSIS
# ════════════════════════════════════════════════════════

st.subheader("💰 Operational Cost Analysis")
st.markdown("OPEX comparison including fuel and EU ETS carbon costs (CAPEX excluded)")

fuel_cost_lng = mass_lng * price_lng
fuel_cost_nh3 = mass_nh3 * price_nh3
fuel_cost_mgo = mass_pilot * price_mgo

carbon_cost_lng = (lng_gwp / 1000) * price_carbon
carbon_cost_amm = (amm_gwp / 1000) * price_carbon

total_cost_lng = fuel_cost_lng + fuel_cost_mgo + carbon_cost_lng
total_cost_amm = fuel_cost_nh3 + fuel_cost_mgo + carbon_cost_amm

col1, col2 = st.columns(2)

with col1:
    st.markdown("**🔵 LNG + MGO**")
    cost_data_lng = pd.DataFrame({
        'Cost Component': ['LNG fuel', 'MGO pilot', 'Carbon (EU ETS)', 'TOTAL'],
        'Amount (€)': [
            f"€{fuel_cost_lng:,.0f}", f"€{fuel_cost_mgo:,.0f}",
            f"€{carbon_cost_lng:,.0f}", f"€{total_cost_lng:,.0f}"
        ]
    })
    st.dataframe(cost_data_lng, use_container_width=True, hide_index=True)

with col2:
    st.markdown(f"**🟢 Ammonia + MGO (SCR {scr_efficiency:.1f}%)**")
    cost_data_amm = pd.DataFrame({
        'Cost Component': ['Ammonia fuel', 'MGO pilot', 'Carbon (EU ETS)', 'TOTAL'],
        'Amount (€)': [
            f"€{fuel_cost_nh3:,.0f}", f"€{fuel_cost_mgo:,.0f}",
            f"€{carbon_cost_amm:,.0f}", f"€{total_cost_amm:,.0f}"
        ]
    })
    st.dataframe(cost_data_amm, use_container_width=True, hide_index=True)

st.markdown("### 📐 Cost Comparison Metrics")

cost_diff = total_cost_amm - total_cost_lng
gwp_saved = (lng_gwp - amm_gwp) / 1000

col_a, col_b, col_c = st.columns(3)

with col_a:
    if cost_diff > 0:
        st.metric("Cost Difference (per trip)",
                  f"€{abs(cost_diff):,.0f} more",
                  delta="Ammonia is more expensive", delta_color="inverse")
    else:
        st.metric("Cost Difference (per trip)",
                  f"€{abs(cost_diff):,.0f} less",
                  delta="Ammonia is cheaper", delta_color="normal")

with col_b:
    if gwp_saved > 0:
        st.metric("CO2-eq Saved (per trip)",
                  f"{gwp_saved:,.2f} tons",
                  delta="Ammonia reduces emissions", delta_color="normal")
    else:
        st.metric("CO2-eq Saved (per trip)",
                  f"{abs(gwp_saved):,.2f} tons more",
                  delta="Ammonia increases emissions", delta_color="inverse")

with col_c:
    if gwp_saved > 0 and cost_diff > 0:
        abatement_cost = cost_diff / gwp_saved
        st.metric("Carbon Abatement Cost",
                  f"€{abatement_cost:,.0f}/ton CO2",
                  help="Extra cost per ton of CO2-eq avoided")
    elif gwp_saved > 0 and cost_diff < 0:
        st.metric("Carbon Abatement Cost", "Win-Win!",
                  delta="Cheaper AND greener", delta_color="normal")
    else:
        st.metric("Carbon Abatement Cost", "N/A",
                  help="Ammonia neither saves emissions nor costs less")

st.caption("💡 **Carbon abatement cost reference:** "
           "Renewable electricity ~€100/ton | Carbon capture ~€600/ton | "
           "Direct air capture ~€800/ton | Tree planting ~€20/ton")

st.divider()

# ════════════════════════════════════════════════════════
# MONTE CARLO
# ════════════════════════════════════════════════════════

st.subheader("🎲 Monte Carlo Uncertainty Analysis")
if include_wtt:
    st.markdown("±20% uncertainty on emission factors and WTT values | 1,000 simulation runs (WTW)")
else:
    st.markdown("±20% uncertainty on emission factors | 1,000 simulation runs (TTW)")

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

# Add WTT uncertainty when WTW mode is on
if include_wtt:
    s_wtt_lng = sample_factor(wtt_lng)
    s_wtt_nh3 = sample_factor(wtt_nh3)
    s_wtt_mgo = sample_factor(wtt_mgo)
    
    lng_runs = lng_runs + e_main*s_wtt_lng/1000 + e_pilot*s_wtt_mgo/1000
    amm_runs = amm_runs + e_main*s_wtt_nh3/1000 + e_pilot*s_wtt_mgo/1000

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
ax4.set_title(f'Monte Carlo Distributions ({analysis_type}) | ±20% uncertainty | 1,000 runs',
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
        st.info(f"**Breakeven SCR: {breakeven}%** ({analysis_type})\n\n"
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
           "Brightway2 + Python + Streamlit | One complete round trip | "
           "Costs are illustrative and exclude CAPEX")
