# Data Source & Provenance

## Source

DA-09 uses the **Stock keeping units** dataset from the UCI Machine Learning Repository.

- Dataset ID: `585`
- DOI: `10.24432/C5G03C`
- License: **CC BY 4.0**
- Provider: Trialto Latvia LTD, a third-party logistics operator
- Instances: **2,279 SKUs**
- UCI subject area: Business

Each observation represents a distinct item/SKU. UCI documents handling-related attributes such as shelf life, pallet weight, pallet height, and units per pallet, plus turnover-related attributes such as total outbound pallets and number of outbound orders.

## Why this source fits DA-09

This is real operational data from a logistics context and supports defensible inventory-prioritization analysis. It is especially useful for combining **demand magnitude**, **demand frequency**, **handling complexity**, and **shelf-life constraints**.

## Reproducible acquisition

Run:

```bash
python -m src.download_data
```

The script uses the official `ucimlrepo` client and writes the source data into `data/raw/`, which is ignored by Git.

## Important claim boundaries

The dataset does **not** provide live on-hand inventory, reorder points, supplier IDs, supplier lead times, purchase orders, shipment delays, or stockout events. DA-09 therefore does not invent these fields and does not claim stockout prediction, supplier scorecards, fill rate, or lead-time performance.

Instead, the project focuses on what the source really supports:

- SKU demand magnitude and order frequency
- ABC/Pareto-style inventory prioritization
- velocity/frequency segmentation
- handling intensity proxies
- shelf-life / expiry handling risk
- decision-ready SKU prioritization

## Citation

*Stock keeping units* [Dataset]. (2019). UCI Machine Learning Repository. https://doi.org/10.24432/C5G03C
