import pandas as pd
import pytest

from src.analytics import (
    abc_classification,
    data_quality_summary,
    executive_summary,
    handling_profile,
    prepare_metrics,
    shelf_life_risk,
    validate_sku_data,
    velocity_segments,
)


def fixture() -> pd.DataFrame:
    return pd.read_csv("tests/fixtures/sku_sample.csv")


def test_prepare_metrics_preserves_population_and_totals():
    out = prepare_metrics(fixture())
    assert len(out) == 4
    assert out["demand_pallets"].sum() == 100
    assert out["order_frequency"].sum() == 55
    assert out.loc[0, "avg_pallets_per_order"] == 2


def test_abc_reconciles_demand_and_includes_threshold_crossing_sku():
    out = abc_classification(fixture())
    assert out["demand_share_pct"].sum() == pytest.approx(100)
    assert set(out["abc_class"]).issubset({"A", "B", "C"})
    assert out.iloc[0]["abc_class"] == "A"


def test_zero_total_demand_is_rejected_for_abc():
    data = fixture()
    data["total_outbound"] = 0
    with pytest.raises(ValueError, match="positive total outbound demand"):
        abc_classification(data)


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("total_outbound", -1, "negative"),
        ("outbound_number", "unknown", "missing/non-numeric"),
    ],
)
def test_invalid_operational_values_are_rejected(column, value, message):
    data = fixture()
    if isinstance(value, str):
        data[column] = data[column].astype("object")
    data.loc[0, column] = value
    with pytest.raises(ValueError, match=message):
        validate_sku_data(data)


def test_duplicate_sku_ids_are_rejected():
    data = fixture()
    data.loc[1, "id"] = data.loc[0, "id"]
    with pytest.raises(ValueError, match="duplicate"):
        validate_sku_data(data)


def test_missing_required_column_is_actionable():
    with pytest.raises(ValueError, match="units_per_pallet"):
        validate_sku_data(fixture().drop(columns="units_per_pal"))


def test_velocity_segments_preserve_all_skus():
    out = velocity_segments(fixture())
    assert len(out) == 4
    assert out["velocity_segment"].notna().all()
    assert set(out["velocity_segment"]).issubset({"slow", "medium", "fast"})


def test_shelf_life_and_handling_outputs_reconcile():
    shelf = shelf_life_risk(fixture())
    handling = handling_profile(fixture())
    assert shelf["skus"].sum() == 4
    assert shelf["demand_pallets"].sum() == 100
    assert handling.iloc[0]["gross_weight_throughput_kg"] == 40000


def test_summaries_reconcile_source():
    executive = executive_summary(fixture()).iloc[0]
    quality = data_quality_summary(fixture()).iloc[0]
    assert executive["skus"] == 4
    assert executive["total_outbound_pallets"] == 100
    assert executive["total_outbound_orders"] == 55
    assert quality["missing_required_values"] == 0
    assert quality["negative_required_values"] == 0
