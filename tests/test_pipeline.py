from pathlib import Path

import pandas as pd
import pytest

from src.run_analysis import run


EXPECTED_OUTPUTS = {
    "data_quality_summary.csv",
    "executive_summary.csv",
    "abc_sku_prioritization.csv",
    "velocity_segments.csv",
    "shelf_life_risk.csv",
    "handling_profile.csv",
}


def test_pipeline_writes_complete_output_set(tmp_path: Path):
    written = run(Path("tests/fixtures/sku_sample.csv"), tmp_path)
    assert {path.name for path in written} == EXPECTED_OUTPUTS
    assert all(path.stat().st_size > 0 for path in written)
    summary = pd.read_csv(tmp_path / "executive_summary.csv").iloc[0]
    assert summary["total_outbound_pallets"] == 100


def test_pipeline_does_not_create_partial_outputs_for_invalid_data(tmp_path: Path):
    invalid = pd.read_csv("tests/fixtures/sku_sample.csv")
    invalid.loc[0, "total_outbound"] = -1
    input_path = tmp_path / "invalid.csv"
    output_path = tmp_path / "outputs"
    invalid.to_csv(input_path, index=False)

    with pytest.raises(ValueError, match="negative"):
        run(input_path, output_path)
    assert not output_path.exists()

