import pandas as pd

from src.analytics import (
    abc_classification,
    executive_summary,
    prepare_metrics,
    velocity_segments,
)


def fixture() -> pd.DataFrame:
    return pd.DataFrame({
        "Total outbound pallets": [80, 15, 5, 0],
        "Number of outbound orders": [40, 10, 5, 0],
        "Shelf life days": [20, 120, 400, 60],
        "Pallet height m": [1.0, 1.2, 1.5, 0.8],
        "Units per pallet": [100, 80, 50, 120],
    })


def test_prepare_metrics_preserves_population_and_totals():
    out = prepare_metrics(fixture())
    assert len(out) == 4
    assert out["demand_pallets"].sum() == 100
    assert out["order_frequency"].sum() == 55
    assert out.loc[0, "avg_pallets_per_order"] == 2


def test_abc_reconciles_demand_and_assigns_all_classes():
    out = abc_classification(fixture())
    assert round(out["demand_share_pct"].sum(), 8) == 100
    assert set(out["abc_class"]).issubset({"A", "B", "C"})
    assert len(out) == 4


def test_velocity_segments_preserve_all_skus():
    out = velocity_segments(fixture())
    assert len(out) == 4
    assert out["velocity_segment"].notna().all()


def test_executive_summary_reconciles_source():
    out = executive_summary(fixture()).iloc[0]
    assert out["skus"] == 4
    assert out["total_outbound_pallets"] == 100
    assert out["total_outbound_orders"] == 55
