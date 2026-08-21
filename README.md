# Supply Chain Inventory Analytics

[![CI](https://github.com/kooroosh1363/supply-chain-inventory-analytics/actions/workflows/ci.yml/badge.svg)](https://github.com/kooroosh1363/supply-chain-inventory-analytics/actions/workflows/ci.yml)
[![Source validation](https://github.com/kooroosh1363/supply-chain-inventory-analytics/actions/workflows/source-validation.yml/badge.svg)](https://github.com/kooroosh1363/supply-chain-inventory-analytics/actions/workflows/source-validation.yml)

Defensible SKU prioritization using a real public logistics dataset—without inventing inventory or supplier fields that the source does not contain.

## Decision supported

How should an operations team prioritize a large SKU portfolio when it has historical outbound demand, order frequency, handling characteristics, and shelf-life information, but no live stock balance or supplier lead times?

The pipeline produces:

- ABC/Pareto prioritization by outbound pallet demand
- fast, medium, and slow order-frequency segments
- average pallets per outbound order
- shelf-life bands for expiry-sensitive handling context
- gross-weight throughput as a physical-handling proxy
- executive and data-quality summaries with reconciliation checks

## Architecture

```mermaid
flowchart LR
    A[UCI ZIP or local CSV] --> B[Schema and value validation]
    B --> C[Metric preparation]
    C --> D[ABC, velocity, shelf-life, handling]
    D --> E[Six auditable CSV outputs]
```

## Quick start

Requires Python 3.11+.

```bash
python -m pip install -r requirements.txt
python -m pytest --quiet
python -m src.download_data
python -m src.run_analysis
```

For a deterministic offline demonstration:

```bash
python -m src.run_analysis \
  --input tests/fixtures/sku_sample.csv \
  --output-dir outputs
```

## Output contract

| File | Decision value |
|---|---|
| `data_quality_summary.csv` | Row, missing-value, duplicate-ID, and domain checks |
| `executive_summary.csv` | Portfolio-level demand and ABC KPIs |
| `abc_sku_prioritization.csv` | SKU demand contribution and A/B/C class |
| `velocity_segments.csv` | Order-frequency segment for every SKU |
| `shelf_life_risk.csv` | SKU, demand, and order totals by shelf-life band |
| `handling_profile.csv` | SKU-level physical-throughput proxy |

Generated outputs and raw data are intentionally excluded from version control. The pipeline recreates them from the selected input.

## Data integrity and CI

Validation rejects empty inputs, missing required columns, duplicate SKU identifiers, non-numeric required values, negative operational values, and zero-total-demand ABC runs. Tests cover calculations, failure paths, reconciliation, and the end-to-end file contract.

Pull-request CI runs completely offline against an explicitly synthetic four-row fixture. A separate weekly/manual workflow exercises the official live download, so an external outage does not make ordinary code checks flaky.

## Evidence and boundaries

The real source is UCI's **Stock keeping units** dataset (ID 585, CC BY 4.0). See [DATA_SOURCE.md](DATA_SOURCE.md) for acquisition and provenance.

The source has no live inventory, reorder points, stockout events, supplier IDs, lead times, purchase orders, or shipment delays. Consequently, this project makes no claims about stockout prediction, fill rate, supplier performance, or lead-time performance. `gross_weight_throughput_kg` is a transparent proxy—not measured labor, warehouse effort, or cost.

This is a production-oriented analytical portfolio project: reproducible, tested, and explicit about what its evidence can and cannot support.
