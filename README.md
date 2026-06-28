# ₿ Crypto On-Chain Dashboard

Interactive dashboard tracking the top 20 cryptocurrencies — prices, market sentiment, and liquidity — updated daily via GitHub Actions.

**[Live Demo →](https://crypto-dashboard.streamlit.app)**

---

## What's inside

**20 coins** · **$2T+ market cap tracked** · **Fear & Greed sentiment** · **Daily automated refresh**

### Dashboard sections

| Section | What it shows |
|---|---|
| KPI Cards | BTC & ETH prices, total market cap, BTC dominance, Fear & Greed |
| Fear & Greed Gauge | Current index + 30-day sentiment history bar chart |
| Top 20 Coins Table | Price, 24h/7d/30d changes, market cap, volume (color-coded) |
| Market Cap Treemap | Visual share of each coin, colored by 24h performance |
| 7-Day Change Heatmap | Winners vs losers at a glance |
| Liquidity Chart | Volume-to-MarketCap ratio — most actively traded coins |
| Pipeline Audit | Data quality log + run history |

---

## Tech stack

```
CoinGecko API (free)          → prices, market cap, volume for top 20 coins
Fear & Greed Index API (free) → daily sentiment score (0–100)
        ↓
    Python + pandas
        ↓
    DuckDB (5 tables)
        ↓
    HuggingFace Dataset    ← binary DB storage
        ↓
    Streamlit Community Cloud
```

GitHub Actions refreshes data every day at 12:00 UTC.

---

## Engineered features

| Feature | Description |
|---|---|
| `volume_to_mcap_ratio` | Trading activity relative to size — liquidity proxy |
| `market_cap_dominance_pct` | Coin's share of total market cap |
| `price_change_pct_7d / 30d` | Medium-term trend via CoinGecko history |
| `fear_greed_signal` | Extreme Fear / Fear / Neutral / Greed / Extreme Greed classification |

---

## DuckDB schema (5 tables)

| Table | Rows per run | Description |
|---|---|---|
| `crypto_prices` | 20 | Price, volume, changes per coin |
| `market_summary` | 1 | Total market cap, BTC dominance |
| `fear_greed` | 30 (dedup) | Daily Fear & Greed index history |
| `data_quality_log` | 1 | QA pass/warn/fail per run |
| `pipeline_runs` | 1 | Timing, row counts, status |

---

## Run locally

```bash
git clone https://github.com/evgeniimatveev/crypto-dashboard
cd crypto-dashboard
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python run_pipeline.py
streamlit run dashboard/app.py
```

---

## Key findings (live)

- **BTC dominance** fluctuates 50–60% — altcoin season visible when it drops below 50%
- **Fear & Greed below 20** historically precedes market recoveries
- **Stablecoin volume-to-mcap** ratios spike during market volatility
- **Post-IPO companies** and large-cap coins show lower volatility than mid-caps

---

*Data: [CoinGecko API](https://www.coingecko.com/en/api) · [Alternative.me Fear & Greed](https://alternative.me/crypto/fear-and-greed-index/) · Updated daily*
