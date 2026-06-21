import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="HydrogenOrg Infrastructure Simulator",
    page_icon="⚡",
    layout="wide"
)

st.title("HydrogenOrg Infrastructure Simulator")
st.caption("Development model - Layer 1: Hydrogen Production")

st.sidebar.header("Layer 1 Inputs")

h2_target_kg_day = st.sidebar.number_input("Hydrogen target (kg/day)", min_value=1.0, max_value=100000.0, value=100.0, step=10.0)
electricity_price = st.sidebar.number_input("Electricity price (CHF/kWh)", min_value=0.01, max_value=2.00, value=0.18, step=0.01)
electrolyzer_efficiency = st.sidebar.slider("Electrolyzer efficiency (%)", min_value=40, max_value=85, value=65, step=1)
operating_hours = st.sidebar.slider("Operating hours per day", min_value=1, max_value=24, value=18, step=1)
renewable_share = st.sidebar.slider("Renewable electricity share (%)", min_value=0, max_value=100, value=80, step=5)
transport_distance = st.sidebar.number_input("Transport distance (km)", min_value=0.0, max_value=1000.0, value=50.0, step=10.0)
storage_capacity = st.sidebar.number_input("Storage capacity (kg H2)", min_value=0.0, max_value=100000.0, value=500.0, step=50.0)
daily_demand = st.sidebar.number_input("Daily hydrogen demand (kg/day)", min_value=0.0, max_value=100000.0, value=80.0, step=10.0)

st.sidebar.markdown("---")
st.sidebar.caption("Conceptual research simulator. Not an engineering-certified model.")

LHV_H2_KWH_KG = 33.33
WATER_KG_PER_KG_H2 = 9.0
COMPRESSION_KWH_PER_KG = 2.5
TRUCK_COST_CHF_PER_KG_PER_100KM = 0.35
GREY_H2_CO2_KG_PER_KG_H2 = 10.0

eff = electrolyzer_efficiency / 100
renewable = renewable_share / 100

required_kwh_per_kg = LHV_H2_KWH_KG / eff
production_power_kw = (h2_target_kg_day * required_kwh_per_kg) / operating_hours
daily_energy_kwh = h2_target_kg_day * required_kwh_per_kg
compression_energy_kwh = h2_target_kg_day * COMPRESSION_KWH_PER_KG
total_energy_kwh = daily_energy_kwh + compression_energy_kwh

electricity_cost = total_energy_kwh * electricity_price
transport_cost = h2_target_kg_day * (transport_distance / 100) * TRUCK_COST_CHF_PER_KG_PER_100KM
daily_opex = electricity_cost + transport_cost
cost_per_kg = daily_opex / h2_target_kg_day if h2_target_kg_day else 0

water_required_l = h2_target_kg_day * WATER_KG_PER_KG_H2
net_storage_change = h2_target_kg_day - daily_demand
co2_avoided = h2_target_kg_day * GREY_H2_CO2_KG_PER_KG_H2 * renewable

c1, c2, c3, c4 = st.columns(4)
c1.metric("Required energy", f"{required_kwh_per_kg:.1f} kWh/kg")
c2.metric("Power required", f"{production_power_kw:.1f} kW")
c3.metric("Estimated cost", f"{cost_per_kg:.2f} CHF/kg")
c4.metric("CO₂ avoided", f"{co2_avoided:.0f} kg/day")

st.subheader("Layer 1 - Hydrogen Production Summary")

summary = pd.DataFrame({
    "Parameter": [
        "Hydrogen target",
        "Operating hours",
        "Electrolyzer efficiency",
        "Electricity price",
        "Daily electricity demand",
        "Compression energy",
        "Total daily energy",
        "Water requirement",
        "Transport cost",
        "Estimated daily OPEX",
        "Estimated cost per kg H2",
        "Storage net change",
    ],
    "Value": [
        f"{h2_target_kg_day:.1f} kg/day",
        f"{operating_hours} h/day",
        f"{electrolyzer_efficiency} %",
        f"{electricity_price:.2f} CHF/kWh",
        f"{daily_energy_kwh:.1f} kWh/day",
        f"{compression_energy_kwh:.1f} kWh/day",
        f"{total_energy_kwh:.1f} kWh/day",
        f"{water_required_l:.1f} liters/day",
        f"{transport_cost:.2f} CHF/day",
        f"{daily_opex:.2f} CHF/day",
        f"{cost_per_kg:.2f} CHF/kg",
        f"{net_storage_change:.1f} kg/day",
    ]
})

st.dataframe(summary, use_container_width=True)

st.subheader("Storage Balance Scenario")

days = np.arange(1, 31)
storage = np.clip(storage_capacity / 2 + days * net_storage_change, 0, storage_capacity)
storage_df = pd.DataFrame({"Day": days, "Storage kg": storage}).set_index("Day")
st.line_chart(storage_df)

if net_storage_change > 0:
    days_to_full = storage_capacity / net_storage_change if net_storage_change else 0
    st.success(f"Production exceeds demand by {net_storage_change:.1f} kg/day. Storage would fill in about {days_to_full:.1f} days from empty.")
elif net_storage_change < 0:
    days_to_empty = storage_capacity / abs(net_storage_change)
    st.warning(f"Demand exceeds production by {abs(net_storage_change):.1f} kg/day. Storage would empty in about {days_to_empty:.1f} days from full.")
else:
    st.info("Production and demand are balanced.")

st.subheader("Scenario Interpretation")

if cost_per_kg < 5:
    st.success("Cost scenario appears competitive for an early conceptual model.")
elif cost_per_kg < 10:
    st.info("Cost scenario is moderate. Optimization should focus on electricity price, efficiency and utilization.")
else:
    st.warning("Cost scenario is high. Consider lower electricity cost, higher efficiency or higher operating hours.")

if renewable_share < 50:
    st.warning("Renewable share is low. CO₂ benefit is limited compared with a fully renewable scenario.")
else:
    st.success("Renewable share is strong. This improves the estimated CO₂ avoidance value.")

st.markdown("---")
st.subheader("Next Development Layers")

layers = pd.DataFrame({
    "Layer": ["Layer 1", "Layer 2", "Layer 3", "Layer 4", "Layer 5"],
    "Module": ["Hydrogen Production", "Storage Systems", "Distribution Network", "Demand Simulation", "Economic Analysis"],
    "Status": ["Prototype active", "Next development", "Planned", "Planned", "Planned"]
})

st.dataframe(layers, use_container_width=True)

st.download_button(
    "Download scenario CSV",
    summary.to_csv(index=False).encode("utf-8"),
    "hydrogenorg_his_layer1_scenario.csv",
    "text/csv"
)