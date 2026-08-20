from pathlib import Path

from ucimlrepo import fetch_ucirepo

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    dataset = fetch_ucirepo(id=585)
    features = dataset.data.features.copy()
    targets = dataset.data.targets
    frame = features.copy()
    if targets is not None and not targets.empty:
        for col in targets.columns:
            if col not in frame.columns:
                frame[col] = targets[col]
    out = RAW / "sku_inventory.csv"
    frame.to_csv(out, index=False)
    print(f"Saved {len(frame):,} SKU rows to {out}")


if __name__ == "__main__":
    main()
