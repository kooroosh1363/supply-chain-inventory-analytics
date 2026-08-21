# Data source and provenance

## Source

This project uses the **Stock keeping units** dataset from the UCI Machine Learning Repository.

- Dataset ID: `585`
- DOI: [`10.24432/C5G03C`](https://doi.org/10.24432/C5G03C)
- Dataset license: CC BY 4.0
- Provider: Trialto Latvia LTD, a third-party logistics operator
- Published instances: 2,279 SKUs

Each row represents an SKU. Documented fields cover shelf life, pallet weight and height, units per pallet, outbound pallets, and outbound order counts.

## Reproducible acquisition

```bash
python -m src.download_data
```

The downloader retrieves UCI's published ZIP archive directly over HTTPS, limits the response to 25 MiB, requires the expected `sku_data.xlsx` member, validates its schema and values, and writes `data/raw/sku_inventory.csv`. Raw source data is ignored by Git.

The normal CI pipeline uses `tests/fixtures/sku_sample.csv` so pull-request checks are deterministic and do not depend on a third-party network. A separate weekly/manual workflow downloads and validates the live UCI source to detect upstream drift.

## Claim boundaries

The dataset does **not** provide live on-hand inventory, reorder points, supplier IDs, lead times, purchase orders, shipment delays, or stockout events. The repository therefore does not claim stockout prediction, fill-rate analysis, supplier scorecards, or lead-time performance.

Supported analyses are limited to:

- SKU demand magnitude and order frequency
- ABC/Pareto-style prioritization
- velocity/frequency segmentation
- physical-throughput proxies
- shelf-life handling context

## Citation

*Stock keeping units* [Dataset]. (2019). UCI Machine Learning Repository. https://doi.org/10.24432/C5G03C

