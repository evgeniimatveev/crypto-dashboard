import os
import sys
import uuid
from datetime import datetime, timezone

from src.extract   import fetch_coins, fetch_global, fetch_fear_greed
from src.transform import transform_coins, transform_global, transform_fear_greed
from src.validate  import validate_coins
from src.load      import (
    init_db, insert_coins, insert_market_summary,
    insert_fear_greed, insert_quality_log, insert_pipeline_run,
)

HEALTH_CHECK = os.getenv("HEALTH_CHECK", "false").lower() == "true"


def write_job_summary(qa: dict, coins_fetched: int, duration: float) -> None:
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    emoji = {"pass": "✅", "warn": "⚠️", "fail": "❌"}.get(qa["status"], "❓")
    lines = [
        "## 📊 Crypto Pipeline — Run Summary\n",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Status | {emoji} **{qa['status'].upper()}** |",
        f"| Coins fetched | {coins_fetched}/20 |",
        f"| Null values | {qa['null_count']} |",
        f"| Issues | {qa['issues_count']} |",
        f"| Details | {qa['details']} |",
        f"| Duration | {duration:.1f}s |",
    ]
    with open(summary_path, "a") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    run_id     = str(uuid.uuid4())[:8]
    started_at = datetime.now(timezone.utc)
    print(f"[{started_at.isoformat()}] run_id={run_id}")

    if HEALTH_CHECK:
        print("HEALTH_CHECK mode — skipping API calls")
        return 0

    print("→ extracting …")
    raw_coins  = fetch_coins()
    raw_global = fetch_global()
    raw_fg     = fetch_fear_greed()

    fetched_at = datetime.now(timezone.utc)

    print("→ transforming …")
    df_coins  = transform_coins(raw_coins, fetched_at)
    df_global = transform_global(raw_global, fetched_at)
    df_fg     = transform_fear_greed(raw_fg, fetched_at)

    print("→ validating …")
    qa = validate_coins(df_coins)
    print(f"   QA: {qa['status']} — {qa['details']}")
    if qa["status"] == "fail":
        print("FAIL: data quality gate not passed", file=sys.stderr)

    print("→ loading …")
    con  = init_db()
    rows = insert_coins(con, df_coins)
    insert_market_summary(con, df_global)
    insert_fear_greed(con, df_fg)
    insert_quality_log(con, run_id, fetched_at, qa)

    finished_at = datetime.now(timezone.utc)
    duration    = (finished_at - started_at).total_seconds()
    status      = qa["status"] if qa["status"] != "fail" else "fail"
    insert_pipeline_run(con, run_id, started_at, finished_at,
                        duration, len(df_coins), rows, status)
    con.close()

    write_job_summary(qa, len(df_coins), duration)
    print(f"✅ done in {duration:.1f}s — {rows} rows inserted")
    return 1 if qa["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
