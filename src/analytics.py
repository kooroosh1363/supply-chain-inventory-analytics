from __future__ import annotations

import re
import numpy as np
import pandas as pd


def _norm(name: str) -> str:
    return re.sub(r"[^0-9a-zA-Z]+", "_", str(name).strip().lower()).strip("_")


def clean_sku_data(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [_norm(c) for c in out.columns]
    aliases = {
        "unit_weight_kg": "unit_weight",
        "pallet_width_m": "pallet_width",
        "pallet_length_m": "pallet_length",
        "pallet_height_m": "pallet_height",
        "shelf_life_days": "shelf_life",
        "total_outbound_pallets": "outbound_pallets",
        "number_of_outbound_orders": "outbound_orders",
    }
    for source, target in aliases.items():
        if source in out.columns and target not in out.columns:
            out[target] = out[source]
    return out


def _first_existing(df: pd.DataFrame, candidates: list[str]) -> str:
    for c in candidates:
        if c in df.columns:
            return c
    raise ValueError(f"None of the required columns found: {candidates}; available={list(df.columns)}")


def prepare_metrics(df: pd.DataFrame) -> pd.DataFrame:
    x = clean_sku_data(df)
    pallets = _first_existing(x, ["outbound_pallets", "total_outbound_pallets", "total_pallets"])
    orders = _first_existing(x, ["outbound_orders", "number_of_outbound_orders", "orders"])
    x["demand_pallets"] = pd.to_numeric(x[pallets], errors="coerce").fillna(0)
    x["order_frequency"] = pd.to_numeric(x[orders], errors="coerce").fillna(0)
    x["avg_pallets_per_order"] = np.where(
        x["order_frequency"] > 0,
        x["demand_pallets"] / x["order_frequency"],
        np.nan,
    )
    return x


def abc_classification(df: pd.DataFrame) -> pd.DataFrame:
    x = prepare_metrics(df).sort_values("demand_pallets", ascending=False).copy()
    total = x["demand_pallets"].sum()
    x["demand_share_pct"] = np.where(total > 0, 100 * x["demand_pallets"] / total, 0)
    x["cumulative_demand_share_pct"] = x["demand_share_pct"].cumsum()
    x["abc_class"] = np.select(
        [x["cumulative_demand_share_pct"] <= 80, x["cumulative_demand_share_pct"] <= 95],
        ["A", "B"], default="C"
    )
    return x


def velocity_segments(df: pd.DataFrame) -> pd.DataFrame:
    x = prepare_metrics(df)
    q1 = x["order_frequency"].quantile(0.33)
    q2 = x["order_frequency"].quantile(0.67)
    x["velocity_segment"] = pd.cut(
        x["order_frequency"],
        bins=[-np.inf, q1, q2, np.inf],
        labels=["slow", "medium", "fast"],
        include_lowest=True,
    )
    return x


def shelf_life_risk(df: pd.DataFrame) -> pd.DataFrame:
    x = prepare_metrics(df)
    shelf = _first_existing(x, ["shelf_life", "shelf_life_days"])
    days = pd.to_numeric(x[shelf], errors="coerce")
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
    x = prepare_metrics(df)
    height = _first_existing(x, ["pallet_height", "pallet_height_m"])
    units = _first_existing(x, ["units_per_pallet", "quantity_per_pallet"])
    x["pallet_height_value"] = pd.to_numeric(x[height], errors="coerce")
    x["units_per_pallet_value"] = pd.to_numeric(x[units], errors="coerce")
    x["handling_intensity"] = x["demand_pallets"] * x["pallet_height_value"]
    return x.sort_values("handling_intensity", ascending=False)


def executive_summary(df: pd.DataFrame) -> pd.DataFrame:
    abc = abc_classification(df)
    return pd.DataFrame([{
        "skus": len(abc),
        "total_outbound_pallets": round(float(abc["demand_pallets"].sum()), 2),
        "total_outbound_orders": round(float(abc["order_frequency"].sum()), 2),
        "a_class_skus": int((abc["abc_class"] == "A").sum()),
        "a_class_demand_share_pct": round(float(abc.loc[abc["abc_class"] == "A", "demand_share_pct"].sum()), 2),
        "median_pallets_per_order": round(float(abc["avg_pallets_per_order"].median()), 2),
    }])
