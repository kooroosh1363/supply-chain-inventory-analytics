from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
UCI_ARCHIVE = "https://archive.ics.uci.edu/static/public/585/stock%2Bkeeping%2Bunits.zip"


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    request = Request(UCI_ARCHIVE, headers={"User-Agent": "DA-09-portfolio-analytics/1.0"})
    with urlopen(request, timeout=60) as response:
        archive_bytes = response.read()
    with ZipFile(BytesIO(archive_bytes)) as zf:
        with zf.open("sku_data.xlsx") as source:
            frame = pd.read_excel(source)
    out = RAW / "sku_inventory.csv"
    frame.to_csv(out, index=False)
    print(f"Saved {len(frame):,} SKU rows to {out}")


if __name__ == "__main__":
    main()
