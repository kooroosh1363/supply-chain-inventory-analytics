from pathlib import Path

import pandas as pd

from src.analytics import (
    abc_classification,
    executive_summary,
    handling_profile,
    shelf_life_risk,
    velocity_segments,
)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "sku_inventory.csv"
OUT = ROOT / "outputs"


def main() -> None:
    if not RAW.exists():
        raise FileNotFoundError("Raw data missing. Run: python -m src.download_data")
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(RAW)

    executive_summary(df).to_csv(OUT / "executive_summary.csv", index=False)
    abc_classification(df).to_csv(OUT / "abc_sku_prioritization.csv", index=False)
    velocity_segments(df).to_csv(OUT / "velocity_segments.csv", index=False)
    shelf_life_risk(df).to_csv(OUT / "shelf_life_risk.csv", index=False)
    handling_profile(df).to_csv(OUT / "handling_profile.csv", index=False)

    print("DA-09 analytics completed successfully.")


if __name__ == "__main__":
    main()
