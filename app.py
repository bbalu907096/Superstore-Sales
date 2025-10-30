import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from io import BytesIO

# -------------------------------
# Streamlit Config
# -------------------------------
st.set_page_config(page_title="📊 Superstore Sales Dashboard", layout="wide")

# -------------------------------
# Load Data
# -------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("data/Superstore.csv", encoding="latin1")
    df.columns = [c.strip() for c in df.columns]
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], errors="coerce")
    df["ProfitMargin"] = df["Profit"] / df["Sales"]
    return df

df = load_data()

# -------------------------------
# Sidebar Filters
# -------------------------------
st.sidebar.header("🔍 Filters")
regions = sorted(df["Region"].dropna().unique())
categories = sorted(df["Category"].dropna().unique())

region = st.sidebar.multiselect("Select Region(s)", regions, default=regions)
category = st.sidebar.multiselect("Select Category(s)", categories, default=categories)

filtered_df = df[(df["Region"].isin(region)) & (df["Category"].isin(category))]

# -------------------------------
# KPIs
# -------------------------------
st.title("📈 Superstore Sales Dashboard")

col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Sales", f"${filtered_df['Sales'].sum():,.0f}")
col2.metric("📊 Total Profit", f"${filtered_df['Profit'].sum():,.0f}")
col3.metric("📈 Avg Profit Margin", f"{filtered_df['ProfitMargin'].mean() * 100:.2f}%")

st.markdown("---")

# -------------------------------
# Charts
# -------------------------------
fig = make_subplots(rows=2, cols=2,
                    subplot_titles=("Monthly Sales","Sales by Region","Top Products","Discount vs Profit"))

# Monthly Sales
monthly = filtered_df.set_index("Order Date").resample("M")["Sales"].sum().reset_index()
fig.add_trace(go.Scatter(x=monthly["Order Date"], y=monthly["Sales"], name="Monthly Sales"), row=1, col=1)

# Sales by Region
region_df = filtered_df.groupby("Region", as_index=False)["Sales"].sum()
fig.add_trace(go.Bar(x=region_df["Region"], y=region_df["Sales"], name="Sales by Region"), row=1, col=2)

# Top Products
top10 = filtered_df.groupby("Product Name")["Sales"].sum().nlargest(10).reset_index()
fig.add_trace(go.Bar(x=top10["Sales"], y=top10["Product Name"], orientation="h", name="Top Products"), row=2, col=1)

# Discount vs Profit
fig.add_trace(go.Scatter(x=filtered_df["Discount"], y=filtered_df["Profit"], mode="markers",
                         name="Discount vs Profit", marker=dict(size=6, opacity=0.6)), row=2, col=2)

fig.update_layout(height=800, showlegend=False, title_text="Superstore — Summary Dashboard")
st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# 30-Day Sales Forecast
# -------------------------------
st.subheader("⏱️ 30-Day Sales Forecast (Exponential Smoothing)")

sales_ts = filtered_df.groupby("Order Date")[["Sales"]].sum().reset_index()
if len(sales_ts) > 20:
    model = ExponentialSmoothing(sales_ts["Sales"], trend="add", seasonal=None)
    fit = model.fit()
    forecast = fit.forecast(30)
    forecast_dates = pd.date_range(sales_ts["Order Date"].max(), periods=30, freq="D")

    fig_forecast = go.Figure()
    fig_forecast.add_trace(go.Scatter(x=sales_ts["Order Date"], y=sales_ts["Sales"], name="Actual Sales"))
    fig_forecast.add_trace(go.Scatter(x=forecast_dates, y=forecast, name="Forecast", line=dict(dash="dot")))
    st.plotly_chart(fig_forecast, use_container_width=True)
else:
    st.info("Not enough data for forecast.")

# -------------------------------
# Data Viewer + Downloads
# -------------------------------
with st.expander("🔎 View Data"):
    st.dataframe(filtered_df)
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download CSV", data=csv, file_name="Filtered_Superstore_Data.csv", mime="text/csv")
