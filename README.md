# DA-09 — Supply Chain & Inventory Analytics

Portfolio-grade operations analytics using the real/public **UCI Stock keeping units** dataset from a third-party logistics context.

## Business question

How should an operations team prioritize a large SKU portfolio when it has historical outbound demand, order frequency, handling characteristics, and shelf-life information—but does **not** have live stock balances or supplier lead times?

DA-09 answers that question without inventing unsupported fields.

## What the project analyzes

- total outbound pallet demand and outbound order frequency
- ABC / Pareto-style SKU prioritization by demand contribution
- fast / medium / slow order-frequency segmentation
- average pallets per outbound order
- shelf-life bands for expiry-sensitive handling context
- handling-intensity proxy using outbound pallet demand and pallet height
- executive KPI summary with reconciliation checks

## Data source

UCI Machine Learning Repository — **Stock keeping units**, dataset ID 585, DOI `10.24432/C5G03C`, CC BY 4.0. See [DATA_SOURCE.md](DATA_SOURCE.md) for provenance and claim boundaries.

Raw data is downloaded at runtime and excluded from Git:

```bash
python -m src.download_data
```

## Run locally

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python -m src.download_data
python -m src.run_analysis
```

## Outputs

- `executive_summary.csv`
- `abc_sku_prioritization.csv`
- `velocity_segments.csv`
- `shelf_life_risk.csv`
- `handling_profile.csv`

Generated outputs are intentionally excluded from version control and rebuilt by the pipeline.

## Analytical boundaries

This dataset does **not** contain live on-hand inventory, reorder points, stockout events, supplier identifiers, supplier lead times, purchase orders, or shipment-delay records. Therefore this repository does not claim stockout prediction, fill-rate analysis, supplier scorecards, or lead-time performance.

`handling_intensity` is an interpretable operational **proxy**, not a measured labor-cost or warehouse-effort metric.

## Engineering quality

GitHub Actions installs dependencies, runs unit tests, downloads the official UCI dataset, executes the full pipeline, and validates every expected deliverable. Tests reconcile SKU population, total outbound demand, total order frequency, ABC demand shares, and segmentation coverage.

## Portfolio signal

DA-09 demonstrates the ability to translate imperfect operational data into defensible supply-chain analytics while keeping a strict boundary between observed data, derived metrics, proxies, and unsupported business claims.
