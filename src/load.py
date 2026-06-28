import duckdb
import pandas as pd
from pathlib import Path

DB_PATH = Path("data/crypto.duckdb")

DDL = """
CREATE TABLE IF NOT EXISTS crypto_prices (
    id                      VARCHAR,
    symbol                  VARCHAR,
    name                    VARCHAR,
    current_price           DOUBLE,
    market_cap              DOUBLE,
    market_cap_rank         INTEGER,
    total_volume            DOUBLE,
    price_change_24h        DOUBLE,
    price_change_pct_24h    DOUBLE,
    price_change_pct_7d     DOUBLE,
    price_change_pct_30d    DOUBLE,
    high_24h                DOUBLE,
    low_24h                 DOUBLE,
    circulating_supply      DOUBLE,
    total_supply            DOUBLE,
    ath                     DOUBLE,
    ath_change_pct          DOUBLE,
    volume_to_mcap_ratio    DOUBLE,
    fetched_at              TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS market_summary (
    total_market_cap_usd        DOUBLE,
    total_volume_24h_usd        DOUBLE,
    btc_dominance_pct           DOUBLE,
    eth_dominance_pct           DOUBLE,
    active_coins                INTEGER,
    market_cap_change_pct_24h   DOUBLE,
    fetched_at                  TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS fear_greed (
    value                   INTEGER,
    value_classification    VARCHAR,
    timestamp               TIMESTAMPTZ,
    fetched_at              TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS data_quality_log (
    run_id      VARCHAR,
    checked_at  TIMESTAMPTZ,
    total_rows  INTEGER,
    null_count  INTEGER,
    issues_count INTEGER,
    status      VARCHAR,
    details     VARCHAR
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id          VARCHAR,
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    duration_sec    DOUBLE,
    coins_fetched   INTEGER,
    rows_inserted   INTEGER,
    status          VARCHAR,
    error_message   VARCHAR
);
"""


def init_db() -> duckdb.DuckDBPyConnection:
    DB_PATH.parent.mkdir(exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    con.execute(DDL)
    return con


def insert_coins(con: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    con.execute("INSERT INTO crypto_prices SELECT * FROM df")
    return len(df)


def insert_market_summary(con: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> None:
    if not df.empty:
        con.execute("INSERT INTO market_summary SELECT * FROM df")


def insert_fear_greed(con: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> None:
    if df.empty:
        return
    # deduplicate: only insert dates not already present
    existing = con.execute("SELECT DISTINCT DATE_TRUNC('day', timestamp) FROM fear_greed").fetchdf()
    if not existing.empty:
        existing_dates = set(existing.iloc[:, 0].astype(str))
        df = df[~df["timestamp"].astype(str).str[:10].isin(existing_dates)]
    if not df.empty:
        con.execute("INSERT INTO fear_greed SELECT * FROM df")


def insert_quality_log(con: duckdb.DuckDBPyConnection, run_id: str,
                       checked_at, result: dict) -> None:
    con.execute(
        "INSERT INTO data_quality_log VALUES (?,?,?,?,?,?,?)",
        [run_id, checked_at, result["total_rows"], result["null_count"],
         result["issues_count"], result["status"], result["details"]]
    )


def insert_pipeline_run(con: duckdb.DuckDBPyConnection, run_id: str,
                        started_at, finished_at, duration: float,
                        coins: int, rows: int, status: str, error: str = "") -> None:
    con.execute(
        "INSERT INTO pipeline_runs VALUES (?,?,?,?,?,?,?,?)",
        [run_id, started_at, finished_at, duration, coins, rows, status, error]
    )
