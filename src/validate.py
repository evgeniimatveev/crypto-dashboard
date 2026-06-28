import pandas as pd

EXPECTED_COINS = 20
WARN_COINS     = 15
FAIL_COINS     = 10


def validate_coins(df: pd.DataFrame) -> dict:
    issues = []
    if df.empty:
        return {"status": "fail", "total_rows": 0, "null_count": 0, "issues_count": 1,
                "details": "coins DataFrame is empty"}

    null_count = int(df[["current_price", "market_cap", "total_volume"]].isnull().sum().sum())
    if null_count > 0:
        issues.append(f"{null_count} null values in price/mcap/volume")

    zero_price = int((df["current_price"] <= 0).sum())
    if zero_price > 0:
        issues.append(f"{zero_price} coins with price <= 0")

    n = len(df)
    if n < FAIL_COINS:
        status = "fail"
        issues.append(f"only {n}/{EXPECTED_COINS} coins fetched")
    elif n < WARN_COINS:
        status = "warn"
        issues.append(f"{n}/{EXPECTED_COINS} coins fetched")
    else:
        status = "pass" if not issues else "warn"

    return {
        "status":       status,
        "total_rows":   n,
        "null_count":   null_count,
        "issues_count": len(issues),
        "details":      "; ".join(issues) if issues else "all checks passed",
    }
