import streamlit as st
import pandas as pd
import matplotlib as mpl
import plotly.express as px

# Run server on Localhost: python3 -m streamlit run app.py

# Mac環境での日本語文字化け対策
mpl.rcParams['font.family'] = 'AppleGothic'

st.set_page_config(page_title="Hotel Restaurant Demand Analytics", layout="wide")

analytics_url = "http://localhost:8501"  # Localhost preview link for the Streamlit dashboard

st.title("🍽️ Hotel Restaurant Analytics")
st.markdown(
    """
    A clean, interactive view of restaurant demand, guest behavior, and popular menu trends.
    Use the filters in the sidebar to explore the latest insights for your hotel restaurant.
    """
)

st.markdown("---")

@st.cache_data
def load_data():
    from sqlalchemy import create_engine
    engine = create_engine("postgresql://user:password@127.0.0.1:5433/hotel_db")
    df = pd.read_sql("SELECT * FROM restaurant_demand", engine)
    df["date"] = pd.to_datetime(df["date"])
    return df

raw_df = load_data()
raw_df["weekday"] = raw_df["date"].dt.day_name()
raw_df["orders_per_visitor"] = raw_df["orders"] / raw_df["visitor_count"]

with st.sidebar:
    st.header("Filters")
    date_range = st.date_input(
        "Date range",
        [raw_df["date"].min(), raw_df["date"].max()],
        min_value=raw_df["date"].min(),
        max_value=raw_df["date"].max(),
    )
    categories = st.multiselect(
        "Category",
        options=sorted(raw_df["category"].unique()),
        default=sorted(raw_df["category"].unique()),
    )
    weather = st.multiselect(
        "Weather",
        options=sorted(raw_df["weather"].unique()),
        default=sorted(raw_df["weather"].unique()),
    )

filtered_df = raw_df[
    (raw_df["date"] >= pd.to_datetime(date_range[0]))
    & (raw_df["date"] <= pd.to_datetime(date_range[1]))
    & (raw_df["category"].isin(categories))
    & (raw_df["weather"].isin(weather))
]

if filtered_df.empty:
    st.warning("No data available for the selected filters. Adjust the date range, category, or weather.")
else:
    total_orders = int(filtered_df["orders"].sum())
    total_visitors = int(filtered_df["visitor_count"].sum())
    avg_order_rate = filtered_df["orders_per_visitor"].mean() * 100
    top_item_df = (
        filtered_df.groupby("menu_item")["orders"].sum().reset_index().sort_values("orders", ascending=False)
    )
    top_item = top_item_df.iloc[0]
    top_item_category = (
        filtered_df[filtered_df["menu_item"] == top_item["menu_item"]]["category"].mode().iloc[0]
    )

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Total Orders", f"{total_orders:,}")
    metric_col2.metric("Total Visitors", f"{total_visitors:,}")
    metric_col3.metric("Avg Order Rate", f"{avg_order_rate:.1f}%")

    st.markdown("---")
    st.subheader("📊 Demand Overview")

    menu_ranking = (
        filtered_df.groupby("menu_item")["orders"].sum().reset_index().sort_values("orders", ascending=True)
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        fig = px.bar(
            menu_ranking,
            x="orders",
            y="menu_item",
            orientation="h",
            color="orders",
            color_continuous_scale=["#f8e9d2", "#f4a261", "#c1440e"],
            text="orders",
            labels={"orders": "Orders", "menu_item": "Menu Item"},
        )
        fig.update_layout(
            title="Top Selling Menu Items",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Total Orders",
            yaxis_title="",
            margin=dict(l=0, r=0, t=40, b=0),
            coloraxis_showscale=False,
            template="plotly_white",
        )
        # set dynamic x-axis so bars always have headroom beyond the max value
        max_orders = menu_ranking["orders"].max() if not menu_ranking.empty else 0
        fig.update_xaxes(range=[0, max_orders * 1.1 if max_orders > 0 else 10])
        fig.update_traces(textposition="outside", hovertemplate="%{y}: %{x} orders")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("👑 Today's Top Pick")
        top_orders = int(top_item['orders'])
        share_pct = (top_orders / total_orders * 100) if total_orders else 0

        st.markdown(
            f"""
            <div style="border:1px solid #eee; padding:12px; border-radius:8px; background:linear-gradient(180deg,#fffaf0,#fff); white-space:normal;">
                <h3 style="margin:0 0 6px 0;">{top_item['menu_item']}</h3>
                <div style="font-size:14px; color:#333; margin-bottom:6px;">{top_item_category} · <strong style="font-size:18px;">{top_orders:,}</strong> orders</div>
                <div style="font-size:13px; color:#666;">Share of total orders: <strong>{share_pct:.1f}%</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption("This seasonal top pick is especially popular with families and dessert lovers.")

    st.markdown("---")
    st.subheader("📈 Demand & Visitor Trends")

    trend_df = filtered_df.groupby("date")[["orders", "visitor_count"]].sum().reset_index()
    trend_df["orders_per_visitor"] = trend_df["orders"] / trend_df["visitor_count"]

    fig_trend = px.line(
        trend_df,
        x="date",
        y=["orders", "visitor_count", "orders_per_visitor"],
        labels={"value": "Count", "date": "Date", "variable": "Metric"},
        template="plotly_white",
    )
    fig_trend.update_layout(
        title="Daily Demand and Visitor Patterns",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("---")
    st.subheader("📌 Category Share")

    category_share = (
        filtered_df.groupby("category")["orders"].sum().reset_index().sort_values("orders", ascending=False)
    )
    fig_cat = px.pie(
        category_share,
        names="category",
        values="orders",
        hole=0.45,
        title="Order Share by Category",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig_cat.update_traces(textposition="inside", textinfo="percent+label")
    fig_cat.update_layout(margin=dict(l=0, r=0, t=40, b=0), template="plotly_white")
    st.plotly_chart(fig_cat, use_container_width=True)
