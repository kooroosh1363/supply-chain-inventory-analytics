from __future__ import annotations

from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile

import pandas as pd

from src.analytics import validate_sku_data

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
UCI_ARCHIVE = "https://archive.ics.uci.edu/static/public/585/stock%2Bkeeping%2Bunits.zip"
ARCHIVE_MEMBER = "sku_data.xlsx"
MAX_DOWNLOAD_BYTES = 25 * 1024 * 1024


def download() -> Path:
    """Download, constrain, parse, and validate the official UCI archive."""
    request = Request(UCI_ARCHIVE, headers={"User-Agent": "sku-prioritization-analytics/2.0"})
    with urlopen(request, timeout=60) as response:
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_DOWNLOAD_BYTES:
            raise ValueError("UCI archive exceeds the 25 MiB safety limit")
        archive_bytes = response.read(MAX_DOWNLOAD_BYTES + 1)
    if len(archive_bytes) > MAX_DOWNLOAD_BYTES:
        raise ValueError("UCI archive exceeds the 25 MiB safety limit")

    try:
        with ZipFile(BytesIO(archive_bytes)) as archive:
            if ARCHIVE_MEMBER not in archive.namelist():
                raise ValueError(f"Expected {ARCHIVE_MEMBER!r} in UCI archive")
            with archive.open(ARCHIVE_MEMBER) as source:
                frame = pd.read_excel(source)
    except BadZipFile as exc:
        raise ValueError("Downloaded UCI payload is not a valid ZIP archive") from exc

    validate_sku_data(frame)
    RAW.mkdir(parents=True, exist_ok=True)
    target = RAW / "sku_inventory.csv"
    frame.to_csv(target, index=False)
    return target


def main() -> None:
    target = download()
    print(f"Validated source data saved to {target}")


if __name__ == "__main__":
    main()

