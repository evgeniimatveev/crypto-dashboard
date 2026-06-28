import os
import sys
import time
from pathlib import Path
from huggingface_hub import hf_hub_download

DB_PATH  = Path("data/crypto.duckdb")
REPO_ID  = os.environ.get("HF_DATASET_REPO", "evgeniimatveevusa/crypto-db")
HF_TOKEN = os.environ.get("HF_TOKEN")

DELAYS = [30, 60, 120, 180]


def download() -> None:
    DB_PATH.parent.mkdir(exist_ok=True)
    for attempt, delay in enumerate(DELAYS + [None], start=1):
        try:
            hf_hub_download(
                repo_id=REPO_ID,
                repo_type="dataset",
                filename="crypto.duckdb",
                local_dir="data",
                token=HF_TOKEN,
            )
            size_mb = DB_PATH.stat().st_size / 1_048_576
            print(f"✅ downloaded {size_mb:.2f} MB from {REPO_ID}")
            return
        except Exception as e:
            if "429" in str(e) and delay is not None:
                print(f"  429 rate limit — waiting {delay}s (attempt {attempt})")
                time.sleep(delay)
            elif "404" in str(e) or "does not exist" in str(e).lower():
                print("DB not found on HF — will be created fresh by pipeline")
                return
            else:
                if delay is not None:
                    print(f"  download failed: {e} — retrying in {delay}s")
                    time.sleep(delay)
                else:
                    print(f"ERROR: {e}", file=sys.stderr)
                    sys.exit(1)


if __name__ == "__main__":
    download()
