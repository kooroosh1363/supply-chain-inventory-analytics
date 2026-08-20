from __future__ import annotations

import re

import numpy as np
import pandas as pd


REQUIRED_SOURCE_COLUMNS = {
    "total_outbound",
    "outbound_number",
    "expire_date",
    "pal_grossweight",
    "pal_height",
    "units_per_pal",
}


def _norm(name: str) -> str:
    return re.sub(r"[^0-9a-zA-Z]+", "_", str(name).strip().lower()).strip("_")


def clean_sku_data(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize the real UCI headers and expose stable analytical names."""
    out = df.copy()
    out.columns = [_norm(c) for c in out.columns]

    # Exact headers observed in UCI's sku_data.xlsx, plus documented aliases.
    aliases = {
        "total_outbound": "outbound_pallets",
        "outbound_number": "outbound_orders",
        "expire_date": "shelf_life_days",
        "pal_grossweight": "pallet_gross_weight_kg",
        "pal_height": "pallet_height_cm",
        "units_per_pal": "units_per_pallet",
        "unitprice": "unit_price_eur",
        # Defensive aliases for human-readable/export variants.
        "total_outbound_pallets": "outbound_pallets",
        "number_of_outbound_orders": "outbound_orders",
        "shelf_life": "shelf_life_days",
        "pallet_gross_weight": "pallet_gross_weight_kg",
        "pallet_height": "pallet_height_cm",
    }
    for source, target in aliases.items():
        if source in out.columns and target not in out.columns:
            out[target] = out[source]

    required = {
        "outbound_pallets",
        "outbound_orders",
        "shelf_life_days",
        "pallet_gross_weight_kg",
        "pallet_height_cm",
        "units_per_pallet",
    }
    missing = sorted(required.difference(out.columns))
    if missing:
        raise ValueError(
            f"UCI SKU schema missing required normalized columns: {missing}; "
            f"available={sorted(out.columns.tolist())}"
        )
    return out


def prepare_metrics(df: pd.DataFrame) -> pd.DataFrame:
    x = clean_sku_data(df)
    x["demand_pallets"] = pd.to_numeric(x["outbound_pallets"], errors="coerce").fillna(0)
    x["order_frequency"] = pd.to_numeric(x["outbound_orders"], errors="coerce").fillna(0)
    x["avg_pallets_per_order"] = np.where(
        x["order_frequency"] > 0,
        x["demand_pallets"] / x["order_frequency"],
        np.nan,
    )
    return x


def abc_classification(df: pd.DataFrame) -> pd.DataFrame:
    """Pareto-style demand classes, including the threshold-crossing SKU in its class."""
    x = prepare_metrics(df).sort_values("demand_pallets", ascending=False).copy()
    total = x["demand_pallets"].sum()
    x["demand_share_pct"] = np.where(total > 0, 100 * x["demand_pallets"] / total, 0.0)
    x["cumulative_demand_share_pct"] = x["demand_share_pct"].cumsum()
    previous_cumulative = x["cumulative_demand_share_pct"] - x["demand_share_pct"]
    x["abc_class"] = np.select(
        [previous_cumulative < 80, previous_cumulative < 95],
        ["A", "B"],
        default="C",
    )
    return x


def velocity_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Frequency segmentation using percentile rank; robust to duplicate quantile cut points."""
    x = prepare_metrics(df)
    pct_rank = x["order_frequency"].rank(method="average", pct=True)
    x["velocity_segment"] = np.select(
        [pct_rank <= 1 / 3, pct_rank <= 2 / 3],
        ["slow", "medium"],
        default="fast",
    )
    return x


def shelf_life_risk(df: pd.DataFrame) -> pd.DataFrame:
    x = prepare_metrics(df)
    days = pd.to_numeric(x["shelf_life_days"], errors="coerce")
    x["shelf_life_days"] = days
    x["shelf_life_band"] = pd.cut(
        days,
        bins=[-np.inf, 30, 90, 180, 365, np.inf],
        labels=["<=30d", "31-90d", "91-180d", "181-365d", "365d+"],
    )
    return x.groupby("shelf_life_band", observed=True).agg(
        skus=("demand_pallets", "size"),
        demand_pallets=("demand_pallets", "sum"),
        outbound_orders=("order_frequency", "sum"),
    ).reset_index()


def handling_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Describe physical throughput; this is not labor cost or warehouse effort."""
    x = prepare_metrics(df)
    x["pallet_gross_weight_kg"] = pd.to_numeric(x["pallet_gross_weight_kg"], errors="coerce")
    x["pallet_height_cm"] = pd.to_numeric(x["pallet_height_cm"], errors="coerce")
    x["units_per_pallet"] = pd.to_numeric(x["units_per_pallet"], errors="coerce")
    x["gross_weight_throughput_kg"] = x["demand_pallets"] * x["pallet_gross_weight_kg"]
    return x.sort_values("gross_weight_throughput_kg", ascending=False)


def executive_summary(df: pd.DataFrame) -> pd.DataFrame:
    abc = abc_classification(df)
    a = abc["abc_class"].eq("A")
    return pd.DataFrame([{
        "skus": len(abc),
        "total_outbound_pallets": round(float(abc["demand_pallets"].sum()), 2),
        "total_outbound_orders": round(float(abc["order_frequency"].sum()), 2),
        "a_class_skus": int(a.sum()),
        "a_class_demand_share_pct": round(float(abc.loc[a, "demand_share_pct"].sum()), 2),
        "median_pallets_per_order": round(float(abc["avg_pallets_per_order"].median()), 2),
    }])
