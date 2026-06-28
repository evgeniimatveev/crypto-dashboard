import time
import httpx
from datetime import datetime, timezone


COINGECKO_MARKETS = (
    "https://api.coingecko.com/api/v3/coins/markets"
    "?vs_currency=usd&order=market_cap_desc&per_page=20&page=1"
    "&price_change_percentage=7d,30d&sparkline=false"
)
COINGECKO_GLOBAL = "https://api.coingecko.com/api/v3/global"
FEAR_GREED_URL   = "https://api.alternative.me/fng/?limit=30"


def fetch_coins(retries: int = 3) -> list[dict]:
    for attempt in range(retries):
        try:
            r = httpx.get(COINGECKO_MARKETS, timeout=20)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"  ! coins attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(10 * (attempt + 1))
    return []


def fetch_global() -> dict:
    for attempt in range(3):
        try:
            r = httpx.get(COINGECKO_GLOBAL, timeout=20)
            r.raise_for_status()
            return r.json().get("data", {})
        except Exception as e:
            print(f"  ! global attempt {attempt+1} failed: {e}")
            if attempt < 2:
                time.sleep(10)
    return {}


def fetch_fear_greed() -> list[dict]:
    for attempt in range(3):
        try:
            r = httpx.get(FEAR_GREED_URL, timeout=20)
            r.raise_for_status()
            return r.json().get("data", [])
        except Exception as e:
            print(f"  ! fear&greed attempt {attempt+1} failed: {e}")
            if attempt < 2:
                time.sleep(10)
    return []
