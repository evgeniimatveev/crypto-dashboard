import os
import sys
import time
from pathlib import Path
from huggingface_hub import HfApi
from huggingface_hub.utils import HfHubHTTPError

DB_PATH  = Path("data/crypto.duckdb")
REPO_ID  = os.environ.get("HF_DATASET_REPO", "evgeniimatveevusa/crypto-db")
HF_TOKEN = os.environ.get("HF_TOKEN")

DELAYS = [30, 60, 120, 180]


def upload() -> None:
    if not DB_PATH.exists():
        print(f"ERROR: {DB_PATH} not found", file=sys.stderr)
        sys.exit(1)

    api = HfApi()
    for attempt, delay in enumerate(DELAYS + [None], start=1):
        try:
            api.upload_file(
                path_or_fileobj=str(DB_PATH),
                path_in_repo="crypto.duckdb",
                repo_id=REPO_ID,
                repo_type="dataset",
                token=HF_TOKEN,
            )
            size_mb = DB_PATH.stat().st_size / 1_048_576
            print(f"✅ uploaded {size_mb:.2f} MB → {REPO_ID}")
            return
        except HfHubHTTPError as e:
            if "429" in str(e) and delay is not None:
                print(f"  429 rate limit — waiting {delay}s (attempt {attempt})")
                time.sleep(delay)
            else:
                raise
    print("ERROR: upload failed after all retries", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    upload()
