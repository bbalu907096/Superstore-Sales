import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from plotly.subplots import make_subplots


# Streamlit page setup
st.set_page_config(page_title="📊 Superstore Sales Dashboard", layout="wide")

# -------------------------------
# LOAD DATA
# -------------------------------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("/content/Superstore.csv", encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv("/content/Superstore.csv", encoding='latin-1')

    df.columns = [c.strip() for c in df.columns]

    # Convert dates and create derived columns
    if 'Order Date' in df.columns:
        df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce')
    if 'Ship Date' in df.columns:
        df['Ship Date'] = pd.to_datetime(df['Ship Date'], errors='coerce')
    if 'Profit' in df.columns and 'Sales' in df.columns:
        df['ProfitMargin'] = df['Profit'] / df['Sales']

    return df

df = load_data()

# -------------------------------
# SIDEBAR FILTERS
# -------------------------------
st.sidebar.header("🔍 Filters")

regions = df['Region'].dropna().unique().tolist() if 'Region' in df.columns else []
categories = df['Category'].dropna().unique().tolist() if 'Category' in df.columns else []
sub_categories = df['Sub-Category'].dropna().unique().tolist() if 'Sub-Category' in df.columns else []

selected_region = st.sidebar.multiselect("Select Region(s)", regions, default=regions)
selected_category = st.sidebar.multiselect("Select Category(s)", categories, default=categories)
selected_sub_category = st.sidebar.multiselect("Select Sub-Category(s)", sub_categories, default=sub_categories)

if 'Order Date' in df.columns:
    min_date, max_date = df['Order Date'].min(), df['Order Date'].max()
    date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date])

# -------------------------------
# FILTER DATA
# -------------------------------
filtered_df = df.copy()

if 'Region' in filtered_df.columns and selected_region:
    filtered_df = filtered_df[filtered_df['Region'].isin(selected_region)]
if 'Category' in filtered_df.columns and selected_category:
    filtered_df = filtered_df[filtered_df['Category'].isin(selected_category)]
if 'Sub-Category' in filtered_df.columns and selected_sub_category:
    filtered_df = filtered_df[filtered_df['Sub-Category'].isin(selected_sub_category)]

if 'Order Date' in filtered_df.columns and len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df['Order Date'] >= pd.to_datetime(start_date)) &
        (filtered_df['Order Date'] <= pd.to_datetime(end_date))
    ]

# -------------------------------
# DASHBOARD HEADER
# -------------------------------
st.title("📈 Superstore Sales Dashboard")

total_sales = filtered_df['Sales'].sum() if 'Sales' in filtered_df.columns else 0
total_profit = filtered_df['Profit'].sum() if 'Profit' in filtered_df.columns else 0
avg_margin = filtered_df['ProfitMargin'].mean() * 100 if 'ProfitMargin' in filtered_df.columns else 0

col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Sales", f"${total_sales:,.0f}")
col2.metric("📊 Total Profit", f"${total_profit:,.0f}")
col3.metric("📈 Avg Profit Margin", f"{avg_margin:.2f}%")

st.markdown("---")

# -------------------------------
# CHARTS
# -------------------------------

# Combined interactive dashboard (summary)
fig = make_subplots(rows=2, cols=2,
                    subplot_titles=("Monthly Sales","Sales by Region","Top Products (Sales)","Discount vs Profit"),
                    vertical_spacing=0.12)

# Monthly Sales
if 'Order Date' in filtered_df.columns:
    monthly = filtered_df.set_index('Order Date').resample('M')['Sales'].sum().reset_index()
    fig.add_trace(go.Scatter(x=monthly['Order Date'], y=monthly['Sales'], name='Monthly Sales'), row=1, col=1)

# Sales by Region
if 'Region' in filtered_df.columns:
    region_df = filtered_df.groupby('Region', as_index=False)['Sales'].sum().sort_values('Sales', ascending=False)
    fig.add_trace(go.Bar(x=region_df['Region'], y=region_df['Sales'], name='Sales by Region'), row=1, col=2)

# Top Products
if 'Product Name' in filtered_df.columns and 'Sales' in filtered_df.columns:
    top10 = filtered_df.groupby('Product Name')['Sales'].sum().sort_values(ascending=False).head(8).reset_index()
    fig.add_trace(go.Bar(x=top10['Sales'][::-1], y=top10['Product Name'][::-1], orientation='h', name='Top Products'), row=2, col=1)

# Discount vs Profit
if set(['Discount','Profit']).issubset(filtered_df.columns):
    fig.add_trace(go.Scatter(x=filtered_df['Discount'], y=filtered_df['Profit'], mode='markers', name='Discount vs Profit', marker=dict(size=6, opacity=0.6)), row=2, col=2)

fig.update_layout(height=800, showlegend=False, title_text="Superstore — Summary Dashboard")
st.plotly_chart(fig, use_container_width=True)


# Sales over time
st.subheader("📅 Sales Over Time")
if 'Order Date' in filtered_df.columns:
    trend = filtered_df.groupby('Order Date')[['Sales']].sum().reset_index()
    fig1 = px.line(trend, x='Order Date', y='Sales', markers=True, title="Sales Trend")
    st.plotly_chart(fig1, use_container_width=True)

# Sales by Region
st.subheader("🏙️ Sales by Region")
if 'Region' in filtered_df.columns:
    region_sales = filtered_df.groupby('Region')['Sales'].sum().reset_index()
    fig2 = px.bar(region_sales, x='Region', y='Sales', color='Region', title="Sales by Region")
    st.plotly_chart(fig2, use_container_width=True)

# Top 10 Products
st.subheader("🛍️ Top 10 Products by Sales")
if 'Product Name' in filtered_df.columns:
    top_products = filtered_df.groupby('Product Name')['Sales'].sum().nlargest(10).reset_index()
    fig3 = px.bar(top_products, x='Sales', y='Product Name', orientation='h',
                  title="Top 10 Products", color='Sales')
    st.plotly_chart(fig3, use_container_width=True)

# Profit treemap
st.subheader("💸 Profit by Category and Sub-Category")
if 'Category' in filtered_df.columns and 'Sub-Category' in filtered_df.columns:
    cat_profit = filtered_df.groupby(['Category', 'Sub-Category'])['Profit'].sum().reset_index()
    fig4 = px.treemap(cat_profit, path=['Category', 'Sub-Category'], values='Profit', title="Profit Distribution")
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# -------------------------------
# DATA VIEWER + DOWNLOADS
# -------------------------------
with st.expander("🔎 View Filtered Data"):
    st.dataframe(filtered_df, use_container_width=True)

    # CSV
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download CSV",
        data=csv,
        file_name="Filtered_Superstore_Data.csv",
        mime="text/csv"
    )

    # Excel
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        filtered_df.to_excel(writer, index=False, sheet_name='Filtered Data')
    st.download_button(
        label="⬇️ Download Excel",
        data=buffer.getvalue(),
        file_name="Filtered_Superstore_Data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.caption("📊 Built with Streamlit | Data: Superstore Dataset | Interactive Dashboard")
