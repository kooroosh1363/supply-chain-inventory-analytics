from __future__ import annotations

import re

import numpy as np
import pandas as pd


ALIASES = {
    "id": "sku_id",
    "total_outbound": "outbound_pallets",
    "outbound_number": "outbound_orders",
    "expire_date": "shelf_life_days",
    "pal_grossweight": "pallet_gross_weight_kg",
    "pal_height": "pallet_height_cm",
    "units_per_pal": "units_per_pallet",
    "unitprice": "unit_price_eur",
    "total_outbound_pallets": "outbound_pallets",
    "number_of_outbound_orders": "outbound_orders",
    "shelf_life": "shelf_life_days",
    "pallet_gross_weight": "pallet_gross_weight_kg",
    "pallet_height": "pallet_height_cm",
}
REQUIRED_COLUMNS = (
    "outbound_pallets",
    "outbound_orders",
    "shelf_life_days",
    "pallet_gross_weight_kg",
    "pallet_height_cm",
    "units_per_pallet",
)


def _norm(name: object) -> str:
    return re.sub(r"[^0-9a-zA-Z]+", "_", str(name).strip().lower()).strip("_")


def clean_sku_data(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize source headers and reject ambiguous duplicate columns."""
    if df.empty:
        raise ValueError("SKU dataset is empty")

    out = df.copy()
    out.columns = [_norm(column) for column in out.columns]
    duplicates = sorted(out.columns[out.columns.duplicated()].unique().tolist())
    if duplicates:
        raise ValueError(f"Duplicate columns after normalization: {duplicates}")

    out = out.rename(columns={key: value for key, value in ALIASES.items() if key in out.columns})
    missing = sorted(set(REQUIRED_COLUMNS).difference(out.columns))
    if missing:
        raise ValueError(
            f"UCI SKU schema missing required normalized columns: {missing}; "
            f"available={sorted(out.columns.tolist())}"
        )
    return out


def validate_sku_data(df: pd.DataFrame) -> pd.DataFrame:
    """Return a typed frame or fail with actionable data-quality details."""
    out = clean_sku_data(df)
    failures: list[str] = []

    for column in REQUIRED_COLUMNS:
        converted = pd.to_numeric(out[column], errors="coerce")
        invalid_count = int(converted.isna().sum())
        negative_count = int((converted < 0).sum())
        if invalid_count:
            failures.append(f"{column}: {invalid_count} missing/non-numeric value(s)")
        if negative_count:
            failures.append(f"{column}: {negative_count} negative value(s)")
        out[column] = converted

    if "sku_id" in out.columns:
        missing_ids = int(out["sku_id"].isna().sum())
        duplicate_ids = int(out["sku_id"].duplicated().sum())
        if missing_ids:
            failures.append(f"sku_id: {missing_ids} missing value(s)")
        if duplicate_ids:
            failures.append(f"sku_id: {duplicate_ids} duplicate value(s)")

    if failures:
        raise ValueError("Invalid SKU data: " + "; ".join(failures))
    return out


def prepare_metrics(df: pd.DataFrame) -> pd.DataFrame:
    x = validate_sku_data(df)
    x["demand_pallets"] = x["outbound_pallets"]
    x["order_frequency"] = x["outbound_orders"]
    x["avg_pallets_per_order"] = np.where(
        x["order_frequency"] > 0,
        x["demand_pallets"] / x["order_frequency"],
        np.nan,
    )
    return x


def abc_classification(df: pd.DataFrame) -> pd.DataFrame:
    """Classify SKUs by cumulative outbound demand (80% A, next 15% B)."""
    x = prepare_metrics(df).sort_values("demand_pallets", ascending=False, kind="stable").copy()
    total = float(x["demand_pallets"].sum())
    if total <= 0:
        raise ValueError("ABC classification requires positive total outbound demand")
    x["demand_share_pct"] = 100 * x["demand_pallets"] / total
    x["cumulative_demand_share_pct"] = x["demand_share_pct"].cumsum()
    previous_cumulative = x["cumulative_demand_share_pct"] - x["demand_share_pct"]
    x["abc_class"] = np.select(
        [previous_cumulative < 80, previous_cumulative < 95],
        ["A", "B"],
        default="C",
    )
    return x


def velocity_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Segment order frequency by percentile rank, robust to tied values."""
    x = prepare_metrics(df)
    percentile_rank = x["order_frequency"].rank(method="average", pct=True)
    x["velocity_segment"] = np.select(
        [percentile_rank <= 1 / 3, percentile_rank <= 2 / 3],
        ["slow", "medium"],
        default="fast",
    )
    return x


def shelf_life_risk(df: pd.DataFrame) -> pd.DataFrame:
    x = prepare_metrics(df)
    x["shelf_life_band"] = pd.cut(
        x["shelf_life_days"],
        bins=[-np.inf, 30, 90, 180, 365, np.inf],
        labels=["<=30d", "31-90d", "91-180d", "181-365d", "365d+"],
    )
    return (
        x.groupby("shelf_life_band", observed=True)
        .agg(
            skus=("demand_pallets", "size"),
            demand_pallets=("demand_pallets", "sum"),
            outbound_orders=("order_frequency", "sum"),
        )
        .reset_index()
    )


def handling_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate physical throughput proxies—not labor or warehouse cost."""
    x = prepare_metrics(df)
    x["gross_weight_throughput_kg"] = x["demand_pallets"] * x["pallet_gross_weight_kg"]
    return x.sort_values("gross_weight_throughput_kg", ascending=False, kind="stable")


def data_quality_summary(df: pd.DataFrame) -> pd.DataFrame:
    x = validate_sku_data(df)
    return pd.DataFrame(
        [
            {
                "rows": len(x),
                "columns": len(x.columns),
                "duplicate_sku_ids": int(x["sku_id"].duplicated().sum()) if "sku_id" in x else 0,
                "missing_required_values": int(x[list(REQUIRED_COLUMNS)].isna().sum().sum()),
                "negative_required_values": int((x[list(REQUIRED_COLUMNS)] < 0).sum().sum()),
            }
        ]
    )


def executive_summary(df: pd.DataFrame) -> pd.DataFrame:
    abc = abc_classification(df)
    a_class = abc["abc_class"].eq("A")
    return pd.DataFrame(
        [
            {
                "skus": len(abc),
                "total_outbound_pallets": round(float(abc["demand_pallets"].sum()), 2),
                "total_outbound_orders": round(float(abc["order_frequency"].sum()), 2),
                "a_class_skus": int(a_class.sum()),
                "a_class_demand_share_pct": round(float(abc.loc[a_class, "demand_share_pct"].sum()), 2),
                "median_pallets_per_order": round(float(abc["avg_pallets_per_order"].median()), 2),
            }
        ]
    )

