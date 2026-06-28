import pandas as pd
from datetime import datetime, timezone


def transform_coins(raw: list[dict], fetched_at: datetime) -> pd.DataFrame:
    if not raw:
        return pd.DataFrame()
    rows = []
    for c in raw:
        mcap = c.get("market_cap") or 0
        vol  = c.get("total_volume") or 0
        rows.append({
            "id":                    c.get("id", ""),
            "symbol":                (c.get("symbol") or "").upper(),
            "name":                  c.get("name", ""),
            "current_price":         c.get("current_price") or 0.0,
            "market_cap":            mcap,
            "market_cap_rank":       c.get("market_cap_rank") or 0,
            "total_volume":          vol,
            "price_change_24h":      c.get("price_change_24h") or 0.0,
            "price_change_pct_24h":  c.get("price_change_percentage_24h") or 0.0,
            "price_change_pct_7d":   c.get("price_change_percentage_7d_in_currency") or 0.0,
            "price_change_pct_30d":  c.get("price_change_percentage_30d_in_currency") or 0.0,
            "high_24h":              c.get("high_24h") or 0.0,
            "low_24h":               c.get("low_24h") or 0.0,
            "circulating_supply":    c.get("circulating_supply") or 0.0,
            "total_supply":          c.get("total_supply") or 0.0,
            "ath":                   c.get("ath") or 0.0,
            "ath_change_pct":        c.get("ath_change_percentage") or 0.0,
            "volume_to_mcap_ratio":  round(vol / mcap, 6) if mcap > 0 else 0.0,
            "fetched_at":            fetched_at,
        })
    return pd.DataFrame(rows)


def transform_global(raw: dict, fetched_at: datetime) -> pd.DataFrame:
    if not raw:
        return pd.DataFrame()
    mcap = raw.get("total_market_cap", {}).get("usd") or 0
    vol  = raw.get("total_volume", {}).get("usd") or 0
    dom  = raw.get("market_cap_percentage", {})
    return pd.DataFrame([{
        "total_market_cap_usd":    mcap,
        "total_volume_24h_usd":    vol,
        "btc_dominance_pct":       round(dom.get("btc") or 0.0, 2),
        "eth_dominance_pct":       round(dom.get("eth") or 0.0, 2),
        "active_coins":            raw.get("active_cryptocurrencies") or 0,
        "market_cap_change_pct_24h": raw.get("market_cap_change_percentage_24h_usd") or 0.0,
        "fetched_at":              fetched_at,
    }])


def transform_fear_greed(raw: list[dict], fetched_at: datetime) -> pd.DataFrame:
    if not raw:
        return pd.DataFrame()
    rows = []
    for item in raw:
        rows.append({
            "value":                int(item.get("value", 0)),
            "value_classification": item.get("value_classification", ""),
            "timestamp":            datetime.fromtimestamp(int(item["timestamp"]), tz=timezone.utc),
            "fetched_at":           fetched_at,
        })
    return pd.DataFrame(rows)
