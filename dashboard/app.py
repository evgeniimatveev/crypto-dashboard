import os
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DB_PATH = Path("data/crypto.duckdb")

st.set_page_config(
    page_title="Crypto On-Chain Dashboard",
    page_icon="₿",
    layout="wide",
)

# ── cold-start DB download ──────────────────────────────────────────────────
def _ensure_db() -> None:
    if DB_PATH.exists():
        return
    from huggingface_hub import hf_hub_download
    DB_PATH.parent.mkdir(exist_ok=True)
    hf_hub_download(
        repo_id=os.environ.get("HF_DATASET_REPO", "evgeniimatveevusa/crypto-db"),
        repo_type="dataset",
        filename="crypto.duckdb",
        local_dir="data",
        token=os.environ.get("HF_TOKEN"),
    )


@st.cache_resource
def get_con():
    _ensure_db()
    return duckdb.connect(str(DB_PATH), read_only=True)


# ── helpers ──────────────────────────────────────────────────────────────────
def fmt_large(n: float) -> str:
    if n >= 1e12:
        return f"${n/1e12:.2f}T"
    if n >= 1e9:
        return f"${n/1e9:.2f}B"
    if n >= 1e6:
        return f"${n/1e6:.2f}M"
    return f"${n:,.0f}"


def color_pct(val: float) -> str:
    return "🟢" if val > 0 else ("🔴" if val < 0 else "⚪")


FG_COLORS = {
    "Extreme Fear": "#d73027",
    "Fear":         "#fc8d59",
    "Neutral":      "#fee090",
    "Greed":        "#91cf60",
    "Extreme Greed":"#1a9850",
}

# ── load data ────────────────────────────────────────────────────────────────
con = get_con()

try:
    latest_run = con.execute(
        "SELECT MAX(fetched_at) FROM crypto_prices"
    ).fetchone()[0]

    df_coins = con.execute("""
        SELECT * FROM crypto_prices
        WHERE fetched_at = (SELECT MAX(fetched_at) FROM crypto_prices)
        ORDER BY market_cap_rank
    """).df()

    df_global = con.execute("""
        SELECT * FROM market_summary
        WHERE fetched_at = (SELECT MAX(fetched_at) FROM market_summary)
        LIMIT 1
    """).df()

    df_fg_today = con.execute("""
        SELECT * FROM fear_greed
        ORDER BY timestamp DESC
        LIMIT 1
    """).df()

    df_fg_30d = con.execute("""
        SELECT DATE_TRUNC('day', timestamp) AS day,
               AVG(value)::INTEGER AS value,
               LAST(value_classification ORDER BY timestamp) AS classification
        FROM fear_greed
        WHERE timestamp >= NOW() - INTERVAL '30 days'
        GROUP BY 1
        ORDER BY 1
    """).df()

    df_quality = con.execute("""
        SELECT checked_at, status, total_rows, null_count, issues_count, details
        FROM data_quality_log ORDER BY checked_at DESC LIMIT 10
    """).df()

    df_runs = con.execute("""
        SELECT run_id, started_at, duration_sec, coins_fetched, rows_inserted, status
        FROM pipeline_runs ORDER BY started_at DESC LIMIT 10
    """).df()

    data_ok = True
except Exception as e:
    data_ok = False
    st.error(f"Could not load data: {e}")
    st.stop()

# ── sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("₿ Crypto Dashboard")
    st.caption("CoinGecko + Fear & Greed · Daily refresh")
    if latest_run:
        st.info(f"Last update\n{str(latest_run)[:16]} UTC")

    top_n = st.slider("Show top N coins", 5, 20, 20)
    st.markdown("---")
    st.markdown("**Sources**")
    st.markdown("- [CoinGecko API](https://www.coingecko.com/en/api)")
    st.markdown("- [Fear & Greed Index](https://alternative.me/crypto/fear-and-greed-index/)")

# ── page header ──────────────────────────────────────────────────────────────
st.markdown("# ₿ Crypto On-Chain Dashboard")
st.markdown("Real-time market data · Top 20 coins · Fear & Greed sentiment · Daily pipeline")
st.divider()

# ── KPI row ──────────────────────────────────────────────────────────────────
if not df_coins.empty and not df_global.empty:
    btc = df_coins[df_coins["symbol"] == "BTC"].iloc[0] if "BTC" in df_coins["symbol"].values else None
    eth = df_coins[df_coins["symbol"] == "ETH"].iloc[0] if "ETH" in df_coins["symbol"].values else None
    g   = df_global.iloc[0]
    fg  = df_fg_today.iloc[0] if not df_fg_today.empty else None

    c1, c2, c3, c4, c5 = st.columns(5)
    if btc is not None:
        c1.metric(
            "Bitcoin (BTC)",
            f"${btc['current_price']:,.0f}",
            f"{btc['price_change_pct_24h']:+.2f}% 24h",
        )
    if eth is not None:
        c2.metric(
            "Ethereum (ETH)",
            f"${eth['current_price']:,.0f}",
            f"{eth['price_change_pct_24h']:+.2f}% 24h",
        )
    c3.metric("Total Market Cap", fmt_large(g["total_market_cap_usd"]),
              f"{g['market_cap_change_pct_24h']:+.2f}% 24h")
    c4.metric("BTC Dominance", f"{g['btc_dominance_pct']:.1f}%")
    if fg is not None:
        c5.metric(
            "Fear & Greed",
            f"{fg['value']} — {fg['value_classification']}",
        )

st.divider()

# ── Fear & Greed ──────────────────────────────────────────────────────────────
col_fg, col_trend = st.columns([1, 2])

with col_fg:
    st.subheader("😨 Fear & Greed Index")
    if fg is not None:
        val = int(fg["value"])
        cls = fg["value_classification"]
        color = FG_COLORS.get(cls, "#888888")
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=val,
            title={"text": cls, "font": {"size": 18}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar":  {"color": color},
                "steps": [
                    {"range": [0,  25], "color": "#d73027"},
                    {"range": [25, 45], "color": "#fc8d59"},
                    {"range": [45, 55], "color": "#fee090"},
                    {"range": [55, 75], "color": "#91cf60"},
                    {"range": [75, 100],"color": "#1a9850"},
                ],
            },
        ))
        fig_gauge.update_layout(height=250, margin=dict(t=30, b=0, l=20, r=20))
        st.plotly_chart(fig_gauge, use_container_width=True)

with col_trend:
    st.subheader("📈 30-Day Sentiment History")
    if not df_fg_30d.empty:
        fig_fg = px.bar(
            df_fg_30d, x="day", y="value",
            color="value",
            color_continuous_scale=["#d73027", "#fc8d59", "#fee090", "#91cf60", "#1a9850"],
            range_color=[0, 100],
            labels={"value": "F&G Index", "day": ""},
        )
        fig_fg.update_layout(
            height=250, coloraxis_showscale=False,
            margin=dict(t=10, b=0, l=0, r=0),
        )
        fig_fg.add_hline(y=50, line_dash="dash", line_color="gray", opacity=0.5)
        st.plotly_chart(fig_fg, use_container_width=True)

st.divider()

# ── Coins table ───────────────────────────────────────────────────────────────
st.subheader("🪙 Top Coins — Live Prices")

df_display = df_coins.head(top_n).copy()
df_display["24h"] = df_display["price_change_pct_24h"].apply(lambda x: f"{color_pct(x)} {x:+.2f}%")
df_display["7d"]  = df_display["price_change_pct_7d"].apply(lambda x: f"{color_pct(x)} {x:+.2f}%")
df_display["30d"] = df_display["price_change_pct_30d"].apply(lambda x: f"{color_pct(x)} {x:+.2f}%")
df_display["Price"]      = df_display["current_price"].apply(lambda x: f"${x:,.2f}" if x < 1000 else f"${x:,.0f}")
df_display["Market Cap"] = df_display["market_cap"].apply(fmt_large)
df_display["Volume"]     = df_display["total_volume"].apply(fmt_large)
df_display["Vol/MCap"]   = df_display["volume_to_mcap_ratio"].apply(lambda x: f"{x:.3f}")

st.dataframe(
    df_display[["market_cap_rank", "name", "symbol", "Price", "24h", "7d", "30d",
                "Market Cap", "Volume", "Vol/MCap"]].rename(columns={
        "market_cap_rank": "#", "name": "Coin", "symbol": "Ticker",
    }),
    use_container_width=True,
    hide_index=True,
)

st.divider()

# ── Charts row ────────────────────────────────────────────────────────────────
c_left, c_right = st.columns(2)

with c_left:
    st.subheader("📊 Market Cap Distribution")
    fig_tree = px.treemap(
        df_display, path=["name"], values="market_cap",
        color="price_change_pct_24h",
        color_continuous_scale=["#d73027", "#f7f7f7", "#1a9850"],
        color_continuous_midpoint=0,
        labels={"price_change_pct_24h": "24h %"},
    )
    fig_tree.update_layout(height=380, margin=dict(t=10, b=0, l=0, r=0))
    fig_tree.update_traces(textinfo="label+percent entry")
    st.plotly_chart(fig_tree, use_container_width=True)

with c_right:
    st.subheader("📉 Price Change Heatmap (7d)")
    df_heat = df_display[["symbol", "price_change_pct_7d"]].sort_values(
        "price_change_pct_7d", ascending=False
    )
    fig_bar = px.bar(
        df_heat, x="symbol", y="price_change_pct_7d",
        color="price_change_pct_7d",
        color_continuous_scale=["#d73027", "#f7f7f7", "#1a9850"],
        color_continuous_midpoint=0,
        labels={"price_change_pct_7d": "7d %", "symbol": ""},
    )
    fig_bar.add_hline(y=0, line_color="gray", line_dash="dash", opacity=0.5)
    fig_bar.update_layout(
        height=380, coloraxis_showscale=False,
        margin=dict(t=10, b=0, l=0, r=0),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# ── Volume vs Market Cap ──────────────────────────────────────────────────────
st.subheader("💧 Liquidity — Volume / Market Cap Ratio")
st.caption("Higher ratio = more actively traded relative to size")

fig_liq = px.bar(
    df_display.sort_values("volume_to_mcap_ratio", ascending=True).tail(15),
    x="volume_to_mcap_ratio", y="symbol", orientation="h",
    color="volume_to_mcap_ratio",
    color_continuous_scale="Blues",
    labels={"volume_to_mcap_ratio": "Vol/MCap", "symbol": ""},
)
fig_liq.update_layout(height=350, coloraxis_showscale=False,
                      margin=dict(t=10, b=0, l=0, r=0))
st.plotly_chart(fig_liq, use_container_width=True)

st.divider()

# ── Pipeline audit ────────────────────────────────────────────────────────────
with st.expander("🔍 Data Quality & Pipeline Audit", expanded=False):
    t1, t2 = st.tabs(["Data Quality Log", "Pipeline Runs"])
    with t1:
        if not df_quality.empty:
            def _style_status(val):
                colors = {"pass": "background-color:#1a9850;color:white",
                          "warn": "background-color:#fc8d59",
                          "fail": "background-color:#d73027;color:white"}
                return colors.get(str(val).lower(), "")
            st.dataframe(
                df_quality.style.applymap(_style_status, subset=["status"]),
                use_container_width=True, hide_index=True,
            )
    with t2:
        if not df_runs.empty:
            st.dataframe(df_runs, use_container_width=True, hide_index=True)

# ── footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Data: [CoinGecko](https://www.coingecko.com/en/api) · "
    "[Fear & Greed Index](https://alternative.me/crypto/fear-and-greed-index/) · "
    "Refreshed daily via GitHub Actions · "
    "[Source](https://github.com/evgeniimatveev/crypto-dashboard)"
)
