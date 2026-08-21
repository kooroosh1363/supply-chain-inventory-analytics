from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.analytics import (
    abc_classification,
    data_quality_summary,
    executive_summary,
    handling_profile,
    shelf_life_risk,
    velocity_segments,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "raw" / "sku_inventory.csv"
DEFAULT_OUTPUT = ROOT / "outputs"


def run(input_path: Path, output_dir: Path) -> list[Path]:
    """Validate one CSV and write the complete analytical output set."""
    if not input_path.is_file():
        raise FileNotFoundError(f"Input data not found: {input_path}")

    frame = pd.read_csv(input_path)
    outputs = {
        "data_quality_summary.csv": data_quality_summary(frame),
        "executive_summary.csv": executive_summary(frame),
        "abc_sku_prioritization.csv": abc_classification(frame),
        "velocity_segments.csv": velocity_segments(frame),
        "shelf_life_risk.csv": shelf_life_risk(frame),
        "handling_profile.csv": handling_profile(frame),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for filename, result in outputs.items():
        target = output_dir / filename
        result.to_csv(target, index=False)
        written.append(target)
    return written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run defensible SKU prioritization analytics.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Source CSV path")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT, help="Output directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    written = run(args.input, args.output_dir)
    print(f"Analytics completed: {len(written)} files written to {args.output_dir}")


if __name__ == "__main__":
    main()

