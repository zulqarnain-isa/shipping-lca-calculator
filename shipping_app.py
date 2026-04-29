import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# ── Page config ──
st.set_page_config(
    page_title="Shipping Fuel LCA Calculator",
    page_icon="🚢",
    layout="wide"
)

# ── Title ──
st.title("🚢 Shipping Fuel LCA Calculator")
st.markdown("**LNG vs Green Ammonia | Maritime Shipping | IPCC 2021 GWP100**")
st.divider()

# ── Characterization factors ──
CF_CO2 = 1.0
CF_CH4 = 27.2
CF_N2O = 273.0

# ── Fixed emission values (kg per round trip) ──
LNG_CO2  = 18681.0468
LNG_CH4  = 133.668922
LNG_N2O  = 0.951983539
MGO_CO2  = 1289.12154
MGO_CH4  = 0.024203214
MGO_N2O  = 0.072437988
AMM_N2O  = 88.0258752
AMM_NH3  = 453.170246

# ── Sidebar controls ──
st.sidebar.header("⚙️ Parameters")
st.sidebar.markdown("Adjust SCR efficiency to see how it affects results")

scr_efficiency = st.sidebar.slider(
    "SCR Efficiency (%)",
    min_value=0,
    max_value=100,
    value=20,
    step=1,
    help="SCR reduces N2O emissions from ammonia combustion"
)

st.sidebar.divider()
st.sidebar.markdown("**Functional Unit**")
st.sidebar.markdown("One complete round trip")
st.sidebar.divider()
st.sidebar.markdown("**LCIA Method**")
st.sidebar.markdown("IPCC 2021 GWP100")
st.sidebar.markdown("CH4 = 27.2 kg CO2-eq/kg")
st.sidebar.markdown("N2O = 273 kg CO2-eq/kg")

# ── Calculations ──
# LNG
lng_gwp = (LNG_CO2 * CF_CO2 +
           LNG_CH4 * CF_CH4 +
           LNG_N2O * CF_N2O +
           MGO_CO2 * CF_CO2 +
           MGO_CH4 * CF_CH4 +
           MGO_N2O * CF_N2O)

# Ammonia no SCR
amm_gwp = (AMM_N2O * CF_N2O +
           MGO_CO2 * CF_CO2 +
           MGO_CH4 * CF_CH4 +
           MGO_N2O * CF_N2O)

# Ammonia with selected SCR
n2o_after_scr = AMM_N2O * (1 - scr_efficiency / 100)
amm_scr_gwp = (n2o_after_scr * CF_N2O +
               MGO_CO2 * CF_CO2 +
               MGO_CH4 * CF_CH4 +
               MGO_N2O * CF_N2O)

# ── Results section ──
st.subheader("📊 GWP100 Results — One Round Trip")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="🔵 LNG + MGO",
        value=f"{lng_gwp:,.0f} kg CO2-eq",
        help="Reference scenario"
    )

with col2:
    pct2 = (amm_gwp - lng_gwp) / lng_gwp * 100
    st.metric(
        label="🔴 Ammonia (no SCR)",
        value=f"{amm_gwp:,.0f} kg CO2-eq",
        delta=f"{abs(pct2):.1f}% more GWP than LNG",
        delta_color="inverse"
    )

with col3:
    diff  = amm_scr_gwp - lng_gwp
    pct   = diff / lng_gwp * 100
    label = f"{abs(pct):.1f}% {'more' if pct > 0 else 'less'} GWP than LNG"
    color = "inverse" if pct > 0 else "normal"
    st.metric(
        label=f"🟢 Ammonia SCR {scr_efficiency}%",
        value=f"{amm_scr_gwp:,.0f} kg CO2-eq",
        delta=label,
        delta_color=color
    )

st.divider()

# ── Two columns for charts ──
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Scenario Comparison")

    scenarios = ['LNG + MGO', 'Ammonia\n(no SCR)', f'Ammonia\nSCR {scr_efficiency}%']
    values    = [lng_gwp, amm_gwp, amm_scr_gwp]
    colors    = ['#2196F3', '#F44336', '#4CAF50']

    fig1, ax1 = plt.subplots(figsize=(7, 5))
    bars = ax1.bar(scenarios, values, color=colors, edgecolor='white', linewidth=0.5)
    ax1.axhline(y=lng_gwp, color='blue', linestyle='--', linewidth=1.5, alpha=0.5)

    for bar, val in zip(bars, values):
        ax1.text(bar.get_x() + bar.get_width()/2,
                 bar.get_height() + 200,
                 f'{val:,.0f}',
                 ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax1.set_ylabel('GWP100 (kg CO2-eq per round trip)')
    ax1.set_title('Scenario Comparison')
    ax1.grid(True, alpha=0.3, axis='y')
    st.pyplot(fig1)

with col_right:
    st.subheader("📈 SCR Sensitivity Analysis")

    scr_range     = np.arange(0, 101, 1)
    ammonia_scores = []
    for scr in scr_range:
        n2o = AMM_N2O * (1 - scr/100)
        gwp = (n2o * CF_N2O +
               MGO_CO2 * CF_CO2 +
               MGO_CH4 * CF_CH4 +
               MGO_N2O * CF_N2O)
        ammonia_scores.append(gwp)

    # Find breakeven
    breakeven = next((s for s, score in zip(scr_range, ammonia_scores)
                      if score <= lng_gwp), None)

    fig2, ax2 = plt.subplots(figsize=(7, 5))
    ax2.plot(scr_range, ammonia_scores,
             color='green', linewidth=2.5, label='Green Ammonia + MGO')
    ax2.axhline(y=lng_gwp, color='blue', linewidth=2,
                linestyle='--', label=f'LNG reference ({lng_gwp:,.0f})')

    if breakeven:
        ax2.axvline(x=breakeven, color='red', linewidth=1.5,
                    linestyle=':', label=f'Breakeven: {breakeven}% SCR')

    # Mark current SCR
    ax2.scatter([scr_efficiency], [amm_scr_gwp],
                color='green', s=100, zorder=5,
                label=f'Current: SCR {scr_efficiency}%')

    ax2.set_xlabel('SCR Efficiency (%)')
    ax2.set_ylabel('GWP100 (kg CO2-eq per round trip)')
    ax2.set_title('SCR Sensitivity Analysis')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)
    st.pyplot(fig2)

st.divider()

# ── Contribution analysis ──
st.subheader("🔍 Contribution Analysis")

contrib_data = {
    'CO2': [
        (LNG_CO2 + MGO_CO2) * CF_CO2,
        MGO_CO2 * CF_CO2,
        MGO_CO2 * CF_CO2
    ],
    'CH4': [
        (LNG_CH4 + MGO_CH4) * CF_CH4,
        MGO_CH4 * CF_CH4,
        MGO_CH4 * CF_CH4
    ],
    'N2O': [
        (LNG_N2O + MGO_N2O) * CF_N2O,
        (AMM_N2O + MGO_N2O) * CF_N2O,
        (n2o_after_scr + MGO_N2O) * CF_N2O
    ],
}

df_contrib = pd.DataFrame(
    contrib_data,
    index=['LNG + MGO', 'Ammonia (no SCR)', f'Ammonia SCR {scr_efficiency}%']
)

fig3, ax3 = plt.subplots(figsize=(10, 5))
colors_contrib = ['#2196F3', '#FF9800', '#F44336']
bottom = np.zeros(3)

for i, (pollutant, color) in enumerate(zip(['CO2', 'CH4', 'N2O'], colors_contrib)):
    values = df_contrib[pollutant].values
    ax3.bar(df_contrib.index, values, bottom=bottom,
            color=color, label=pollutant,
            edgecolor='white', linewidth=0.5)
    for j, (val, bot) in enumerate(zip(values, bottom)):
        if val > 300:
            ax3.text(j, bot + val/2, f'{val:,.0f}',
                     ha='center', va='center',
                     fontsize=9, color='white', fontweight='bold')
    bottom += values

ax3.set_ylabel('GWP100 (kg CO2-eq per round trip)')
ax3.set_title('Contribution Analysis by Pollutant')
ax3.legend()
ax3.grid(True, alpha=0.3, axis='y')
st.pyplot(fig3)

st.divider()

# ── Monte Carlo ──
st.subheader("🎲 Monte Carlo Uncertainty Analysis")
st.markdown("±20% uncertainty on all emission factors | 1,000 simulation runs")

n_runs = 1000
np.random.seed(42)

def sample(value):
    std = value * 0.20 / 2
    return np.clip(np.random.normal(value, std, n_runs), 0, None)

s_lng_co2 = sample(LNG_CO2)
s_lng_ch4 = sample(LNG_CH4)
s_lng_n2o = sample(LNG_N2O)
s_mgo_co2 = sample(MGO_CO2)
s_mgo_ch4 = sample(MGO_CH4)
s_mgo_n2o = sample(MGO_N2O)
s_amm_n2o = sample(AMM_N2O)

lng_runs   = (s_lng_co2*CF_CO2 + s_lng_ch4*CF_CH4 + s_lng_n2o*CF_N2O +
              s_mgo_co2*CF_CO2 + s_mgo_ch4*CF_CH4 + s_mgo_n2o*CF_N2O)

amm_runs   = (s_amm_n2o*CF_N2O + s_mgo_co2*CF_CO2 +
              s_mgo_ch4*CF_CH4 + s_mgo_n2o*CF_N2O)

amm20_runs = (s_amm_n2o*(1-0.20)*CF_N2O + s_mgo_co2*CF_CO2 +
              s_mgo_ch4*CF_CH4 + s_mgo_n2o*CF_N2O)

amm90_runs = (s_amm_n2o*(1-0.90)*CF_N2O + s_mgo_co2*CF_CO2 +
              s_mgo_ch4*CF_CH4 + s_mgo_n2o*CF_N2O)

# Stats table

amm_scr_runs = (s_amm_n2o*(1-scr_efficiency/100)*CF_N2O + 
                s_mgo_co2*CF_CO2 +
                s_mgo_ch4*CF_CH4 + 
                s_mgo_n2o*CF_N2O)

mc_stats = pd.DataFrame({
    'Scenario': ['LNG + MGO', 'Ammonia (no SCR)',
                 'Ammonia SCR 20%', 'Ammonia SCR 90%',
                 f'Ammonia SCR {scr_efficiency}% (your selection)'],
    'Mean (kg CO2-eq)': [f"{np.mean(r):,.0f}" for r in
                         [lng_runs, amm_runs, amm20_runs, 
                          amm90_runs, amm_scr_runs]],
    '5th Percentile': [f"{np.percentile(r,5):,.0f}" for r in
                       [lng_runs, amm_runs, amm20_runs, 
                        amm90_runs, amm_scr_runs]],
    '95th Percentile': [f"{np.percentile(r,95):,.0f}" for r in
                        [lng_runs, amm_runs, amm20_runs, 
                         amm90_runs, amm_scr_runs]],
})
st.dataframe(mc_stats, use_container_width=True)

# Combined distribution chart
from scipy import stats

fig4, ax4 = plt.subplots(figsize=(12, 6))

# Add dynamic scenario based on slider
amm_scr_runs = (s_amm_n2o*(1-scr_efficiency/100)*CF_N2O + 
                s_mgo_co2*CF_CO2 +
                s_mgo_ch4*CF_CH4 + 
                s_mgo_n2o*CF_N2O)

# Define dynamic scenario FIRST before anything else
amm_scr_runs = (s_amm_n2o*(1-scr_efficiency/100)*CF_N2O + 
                s_mgo_co2*CF_CO2 +
                s_mgo_ch4*CF_CH4 + 
                s_mgo_n2o*CF_N2O)

mc_scenarios = [
    ('LNG + MGO',                    lng_runs,      '#2196F3'),
    ('Ammonia (no SCR)',              amm_runs,      '#F44336'),
    ('Ammonia SCR 20%',              amm20_runs,    '#FF9800'),
    ('Ammonia SCR 90%',              amm90_runs,    '#4CAF50'),
    (f'Ammonia SCR {scr_efficiency}% (your selection)', 
                                     amm_scr_runs,  '#9C27B0'),
]

for name, runs, color in mc_scenarios:
    mu  = np.mean(runs)
    std = np.std(runs)
    x   = np.linspace(mu - 4*std, mu + 4*std, 300)
    ax4.plot(x, stats.norm.pdf(x, mu, std),
             color=color, linewidth=2.5,
             label=f'{name} (mean: {mu:,.0f})')
    ax4.fill_between(x, stats.norm.pdf(x, mu, std),
                     alpha=0.15, color=color)

ax4.set_xlabel('GWP100 (kg CO2-eq per round trip)', fontsize=12)
ax4.set_ylabel('Probability density', fontsize=12)
ax4.set_title('Monte Carlo — All Scenarios | ±20% uncertainty | 1,000 runs',
              fontsize=12)
ax4.legend(fontsize=9)
ax4.grid(True, alpha=0.3)
st.pyplot(fig4)

st.divider()

# ── Key findings ──
st.subheader("🔑 Key Findings")

col_a, col_b = st.columns(2)

with col_a:
    st.info(f"**Breakeven SCR Efficiency: {breakeven}%**\n\n"
            f"Green ammonia only needs {breakeven}% SCR efficiency "
            f"to outperform LNG on GWP100 basis.")

with col_b:
    n2o_contribution = (AMM_N2O * CF_N2O) / amm_gwp * 100
    st.warning(f"**N2O drives {n2o_contribution:.1f}% of ammonia GWP**\n\n"
               f"N2O emission factor is the most critical "
               f"parameter for ammonia's climate performance.")

st.divider()
st.caption("Master's Thesis Analysis | IPCC 2021 GWP100 | CH4 = 27.2 | "
           "Brightway2 + Python | One complete round trip")