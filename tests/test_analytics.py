import pandas as pd

from src.analytics import (
    abc_classification,
    executive_summary,
    handling_profile,
    prepare_metrics,
    shelf_life_risk,
    velocity_segments,
)


def fixture() -> pd.DataFrame:
    # Exact normalized source-style headers from UCI sku_data.xlsx.
    return pd.DataFrame({
        "id": [1, 2, 3, 4],
        "unitprice": [10.0, 20.0, 30.0, 40.0],
        "expire_date": [20, 120, 400, 60],
        "outbound_number": [40, 10, 5, 0],
        "total_outbound": [80, 15, 5, 0],
        "pal_grossweight": [500, 600, 700, 450],
        "pal_height": [100, 120, 150, 80],
        "units_per_pal": [100, 80, 50, 120],
    })


def test_prepare_metrics_preserves_population_and_totals():
    out = prepare_metrics(fixture())
    assert len(out) == 4
    assert out["demand_pallets"].sum() == 100
    assert out["order_frequency"].sum() == 55
    assert out.loc[0, "avg_pallets_per_order"] == 2


def test_abc_reconciles_demand_and_includes_threshold_crossing_sku():
    out = abc_classification(fixture())
    assert round(out["demand_share_pct"].sum(), 8) == 100
    assert set(out["abc_class"]).issubset({"A", "B", "C"})
    assert len(out) == 4
    # First SKU reaches exactly 80% and belongs to A.
    assert out.iloc[0]["abc_class"] == "A"


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
    assert len(handling) == 4
    assert handling.iloc[0]["gross_weight_throughput_kg"] == 40000


def test_executive_summary_reconciles_source():
    out = executive_summary(fixture()).iloc[0]
    assert out["skus"] == 4
    assert out["total_outbound_pallets"] == 100
    assert out["total_outbound_orders"] == 55
