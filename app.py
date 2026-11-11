import os
from datetime import datetime
import requests
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="SmartAgri", page_icon="🌾", layout="wide")

DATA_FILE = "data/market_prices.csv"
SAMPLE_FILE = "data/sample_market_prices.csv"
os.makedirs("data", exist_ok=True)

st.title("🌾 SmartAgri")
st.caption("Agricultural Market Price Analysis & Farmer Decision Support")
st.info("Academic prototype. Market prices are indicative; verify prices, quality, fees and availability with the market before selling.")

@st.cache_data(ttl=3600)
def load_csv(path):
    return pd.read_csv(path)

def normalize_columns(df):
    """Map common AGMARKNET/data.gov.in column names to a consistent schema."""
    mapping = {}
    for c in df.columns:
        key = c.strip().lower().replace(" ", "").replace("_", "")
        if key in ["state", "statename"]: mapping[c] = "state"
        elif key in ["district", "districtname"]: mapping[c] = "district"
        elif key in ["market", "marketname"]: mapping[c] = "market"
        elif key in ["commodity", "commodityname", "crop"]: mapping[c] = "commodity"
        elif key in ["variety"]: mapping[c] = "variety"
        elif key in ["arrivaldate", "date", "pricedate"]: mapping[c] = "date"
        elif key in ["minprice", "minimumprice"]: mapping[c] = "min_price"
        elif key in ["maxprice", "maximumprice"]: mapping[c] = "max_price"
        elif key in ["modalprice", "modelprice"]: mapping[c] = "modal_price"
    df = df.rename(columns=mapping)
    required = ["state","district","market","commodity","date","min_price","max_price","modal_price"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError("The downloaded file is missing required fields: " + ", ".join(missing))
    df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)
    for c in ["min_price","max_price","modal_price"]:
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(",", ""), errors="coerce")
    df = df.dropna(subset=["date","modal_price"])
    if "variety" not in df.columns: df["variety"] = "Not specified"
    return df

def fetch_datagov(api_key, resource_id, limit=5000):
    url = f"https://api.data.gov.in/resource/{resource_id}"
    params = {"api-key": api_key, "format": "json", "limit": limit}
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    records = payload.get("records", [])
    if not records:
        raise ValueError("The API returned no records. Check the resource ID and API key.")
    return normalize_columns(pd.DataFrame(records))

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# Load locally stored data, otherwise use clearly identified sample data.
data_source = "Sample data (illustrative)"
if os.path.exists(DATA_FILE):
    try:
        data = normalize_columns(pd.read_csv(DATA_FILE))
        data_source = "Previously fetched data (local CSV)"
    except Exception:
        data = load_csv(SAMPLE_FILE)
        data = normalize_columns(data)
else:
    data = normalize_columns(load_csv(SAMPLE_FILE))

with st.sidebar:
    st.header("Data settings")
    st.write("Default mode uses the included illustrative sample dataset.")
    st.caption("For official data, obtain a data.gov.in API key and the correct resource ID for an agricultural market-price resource.")
    api_key = st.text_input("data.gov.in API key", type="password")
    resource_id = st.text_input("Resource ID")
    if st.button("Fetch official market data", use_container_width=True):
        if not api_key or not resource_id:
            st.error("Enter both the API key and resource ID.")
        else:
            try:
                with st.spinner("Fetching records..."):
                    fresh = fetch_datagov(api_key, resource_id)
                    save_data(fresh)
                    st.cache_data.clear()
                st.success(f"Fetched and saved {len(fresh):,} records.")
                st.rerun()
            except Exception as e:
                st.error(f"Could not fetch official data: {e}")
    if st.button("Use included sample data", use_container_width=True):
        if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
        st.rerun()

if os.path.exists(DATA_FILE):
    try:
        data = normalize_columns(pd.read_csv(DATA_FILE))
        data_source = "Previously fetched official data (local CSV)"
    except Exception:
        data = normalize_columns(load_csv(SAMPLE_FILE))
        data_source = "Sample data (illustrative)"

st.caption(f"Data source: **{data_source}** · Latest date in loaded data: **{data['date'].max().date()}**")

# Product categories are a small editable reference list; expand as needed.
categories = {
    "Vegetables": ["Tomato","Onion","Potato","Carrot","Beans"],
    "Fruits": ["Mango","Banana","Apple","Grapes"],
    "Cereals & grains": ["Rice","Wheat","Maize"],
    "Pulses": ["Tur","Chana","Moong"],
    "Oilseeds": ["Groundnut","Soybean","Mustard"],
    "Other agricultural products": []
}
shelf_days = {
    "Tomato": 5, "Onion": 30, "Potato": 21, "Carrot": 14, "Beans": 5,
    "Mango": 5, "Banana": 5, "Apple": 30, "Grapes": 5,
    "Rice": 180, "Wheat": 180, "Maize": 120, "Tur": 180, "Chana": 180,
    "Moong": 180, "Groundnut": 120, "Soybean": 120, "Mustard": 120
}

st.subheader("1. Explore market prices")
c1,c2,c3 = st.columns(3)
states = ["All"] + sorted(data["state"].dropna().astype(str).unique().tolist())
state = c1.selectbox("State", states)
commodities = ["All"] + sorted(data["commodity"].dropna().astype(str).unique().tolist())
commodity = c2.selectbox("Agricultural product", commodities)
districts_data = data if state == "All" else data[data.state.astype(str)==state]
districts = ["All"] + sorted(districts_data["district"].dropna().astype(str).unique().tolist())
district = c3.selectbox("District", districts)

filtered = data.copy()
if state != "All": filtered = filtered[filtered.state.astype(str)==state]
if commodity != "All": filtered = filtered[filtered.commodity.astype(str)==commodity]
if district != "All": filtered = filtered[filtered.district.astype(str)==district]

if filtered.empty:
    st.warning("No records match these filters. Try a broader selection.")
    st.stop()

summary = filtered.groupby(["state","district","market","commodity"], as_index=False).agg(
    min_price=("min_price","mean"), max_price=("max_price","mean"),
    modal_price=("modal_price","mean"), latest_date=("date","max")
)
summary["min_price"] = summary["min_price"].round(2)
summary["max_price"] = summary["max_price"].round(2)
summary["modal_price"] = summary["modal_price"].round(2)

st.dataframe(summary.sort_values("modal_price", ascending=False), use_container_width=True, hide_index=True)
st.download_button("Download filtered market comparison CSV",
                   summary.to_csv(index=False).encode("utf-8"),
                   "smartagri_market_comparison.csv", "text/csv")

st.subheader("2. Price trend")
markets = sorted(filtered["market"].dropna().astype(str).unique().tolist())
chosen_market = st.selectbox("Choose market for trend", markets)
trend = filtered[filtered.market.astype(str)==chosen_market].groupby("date", as_index=False)["modal_price"].mean().sort_values("date")
fig, ax = plt.subplots()
ax.plot(trend["date"], trend["modal_price"], marker="o")
ax.set_title(f"Average modal price trend – {chosen_market}")
ax.set_xlabel("Date"); ax.set_ylabel("Price (₹ per quintal)")
ax.grid(True, alpha=.3)
fig.autofmt_xdate()
st.pyplot(fig)
plt.close(fig)

st.subheader("3. Farmer selling decision support")
st.write("Compare estimated returns using the latest available modal price in each market.")
product_options = sorted(filtered["commodity"].dropna().astype(str).unique().tolist())
selected_product = st.selectbox("Product to sell", product_options, key="farmer_product")
quantity = st.number_input("Harvest quantity (quintals)", min_value=0.1, value=10.0, step=0.5)
quality_note = st.selectbox("Produce condition", ["Fresh / good condition","Needs quick sale","Suitable for storage"])
days_to_sell = st.number_input("Expected days before sale", min_value=0, max_value=365, value=1)
cost_per_market = st.number_input("Estimated transport and selling cost per market (₹)", min_value=0.0, value=300.0, step=50.0)

product_rows = filtered[filtered.commodity.astype(str)==selected_product].sort_values("date")
latest = product_rows.groupby(["state","district","market"], as_index=False).tail(1).copy()
latest["gross_revenue"] = latest["modal_price"] * quantity
latest["net_return"] = latest["gross_revenue"] - cost_per_market

# Transparent heuristic: urgency increases when expected sale delay exceeds reference shelf-life.
shelf = shelf_days.get(selected_product, 14)
if quality_note == "Needs quick sale":
    effective_shelf = max(1, int(shelf * 0.5))
elif quality_note == "Suitable for storage":
    effective_shelf = int(shelf * 1.5)
else:
    effective_shelf = shelf
urgency = days_to_sell >= effective_shelf
latest["estimated_net_return"] = latest["net_return"]
latest = latest.sort_values("estimated_net_return", ascending=False)

if urgency:
    st.warning(f"Your expected selling delay ({days_to_sell} days) is at or beyond the illustrative reference shelf-life ({effective_shelf} days) for {selected_product}. Consider checking storage and selling promptly.")
else:
    st.info(f"Illustrative reference shelf-life for {selected_product}: about {effective_shelf} days. Actual shelf life varies with variety, maturity, handling and storage.")
best = latest.iloc[0]
st.success(f"Highest estimated return in the available records: {best['market']} ({best['district']}, {best['state']}) — ₹{best['estimated_net_return']:,.2f} after the entered cost.")
st.caption("This recommendation ranks markets by the latest recorded modal price minus the same user-entered cost. It does not verify today's availability, buyer demand, quality deductions, commissions or actual spoilage.")
st.dataframe(latest[["state","district","market","date","modal_price","gross_revenue","estimated_net_return"]].rename(columns={
    "date":"Price date","modal_price":"Modal price (₹/quintal)","gross_revenue":"Estimated gross (₹)","estimated_net_return":"Estimated net (₹)"
}), use_container_width=True, hide_index=True)

st.subheader("4. Quick statistics")
m1,m2,m3 = st.columns(3)
m1.metric("Average modal price", f"₹{filtered.modal_price.mean():,.2f}")
m2.metric("Highest modal price", f"₹{filtered.modal_price.max():,.2f}")
m3.metric("Lowest modal price", f"₹{filtered.modal_price.min():,.2f}")
st.caption("Prices are expressed in ₹ per quintal in the included sample. Check the selected official resource's units before using fetched data.")
