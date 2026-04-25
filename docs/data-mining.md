# Data Mining: Association Rule Mining

## Overview

This project uses the Gold star schema as the input for market basket analysis. The mining step reads order-line facts, converts each order into a product basket, and applies Apriori association rule mining to discover products that are frequently purchased together.

The current implementation is code-only and lives in:

- `mining/association_rules.py`
- `tests/quality/test_association_rules.py`

The mining output can be used for cross-sell recommendations, product bundling, shelf placement ideas, and the Data Mining section of the DSS report.

## Input Data

The mining pipeline reads from the DuckDB warehouse configured in `etl/config/settings.yaml`.

Required Gold tables:

- `fact_order_line`
- `dim_product`

The source query joins facts to products:

```sql
select
  fol.order_id_nk,
  dp.product_name,
  dp.aisle_name,
  dp.department_name,
  fol.reordered
from fact_order_line fol
join dim_product dp on dp.product_key = fol.product_key
where dp.product_name is not null;
```

Each `order_id_nk` is treated as one basket. Each `product_name` is treated as one item in that basket.

## Environment Setup

Install dependencies inside the project virtual environment only.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The mining implementation uses `mlxtend` for Apriori and association rule generation.

## Running the Pipeline

Build or refresh the warehouse first:

```powershell
.\.venv\Scripts\python.exe etl.py --stage all --sample-rows 5000 --skip-quality
```

Run data mining:

```powershell
.\.venv\Scripts\python.exe -m mining.association_rules --top-n 10
```

Run data mining and persist the rule table back into DuckDB:

```powershell
.\.venv\Scripts\python.exe -m mining.association_rules --top-n 10 --write-db
```

Useful parameters:

| Parameter | Default | Purpose |
|---|---:|---|
| `--min-support` | `0.005` | Minimum frequency threshold for itemsets. |
| `--min-confidence` | `0.1` | Minimum conditional probability for generated rules. |
| `--min-lift` | `1.0` | Minimum lift threshold. Values above `1.0` indicate positive association. |
| `--max-len` | none | Maximum itemset length considered by Apriori. |
| `--top-n` | `50` | Number of highest-ranked rules exported to the main rules file. |
| `--threshold-supports` | `0.005,0.01,0.02` | Support values used for threshold comparison. |
| `--write-db` | off | Writes rules to `dm_association_rules` in DuckDB. |

## Output Files

The default output directory is `outputs/data_mining/`.

| File | Purpose |
|---|---|
| `association_rules.csv` | Main Apriori rule output with metrics and readable interpretation. |
| `basket_summary.csv` | Basket-level profiling: basket count, unique products, basket size, reorder rate, top products, top departments, top aisles. |
| `bundle_recommendations.csv` | Cross-sell friendly rules where the consequent is a single recommended product. |
| `threshold_comparison.csv` | Rule counts and lift summary under multiple `min_support` values. |

When `--write-db` is enabled, the main rules are also written to:

```sql
dm_association_rules
```

## Output Columns

### `association_rules.csv`

| Column | Meaning |
|---|---|
| `antecedents` | Product or product set already present in the basket. |
| `consequents` | Product or product set recommended by the rule. |
| `rule_text` | Human-readable rule in the form `A => B`. |
| `business_meaning` | Short English interpretation for report usage. |
| `support` | Fraction of baskets containing both antecedent and consequent. |
| `confidence` | Probability of the consequent given the antecedent. |
| `lift` | Strength of association compared with random co-occurrence. |
| `antecedent_support` | Fraction of baskets containing the antecedent. |
| `consequent_support` | Fraction of baskets containing the consequent. |

### `bundle_recommendations.csv`

| Column | Meaning |
|---|---|
| `bundle_products` | Existing basket item or itemset. |
| `recommended_product` | Product to recommend or bundle with the antecedent. |
| `support` | Frequency of the complete bundle in all baskets. |
| `confidence` | Probability that the recommendation appears when the bundle products appear. |
| `lift` | Association strength. |
| `recommendation` | Simple cross-sell sentence. |

## Metric Interpretation

For a rule:

```text
Limes, Organic Hass Avocado => Organic Cilantro
```

The metrics mean:

- `support`: how often all products in the rule appear together across all baskets.
- `confidence`: among baskets containing `Limes` and `Organic Hass Avocado`, how many also contain `Organic Cilantro`.
- `lift`: how much stronger this co-purchase pattern is compared with random chance.

A lift above `1.0` indicates a positive association. Higher lift values are usually more interesting, but very low support can mean the pattern is rare. For reporting, use support, confidence, and lift together rather than selecting by only one metric.

## Current Sample Result

With the current local sample run:

- `order_product_rows`: `10000`
- `basket_count`: `978`
- `unique_products`: `4622`
- `avg_basket_size`: `10.2249`
- `reordered_rate`: `0.6014`

Threshold comparison:

| min_support | min_confidence | min_lift | rule_count | max_lift | avg_lift |
|---:|---:|---:|---:|---:|---:|
| `0.005` | `0.1` | `1.0` | `281` | `21.689815` | `4.442453` |
| `0.01` | `0.1` | `1.0` | `36` | `4.156048` | `2.571423` |
| `0.02` | `0.1` | `1.0` | `6` | `2.906328` | `2.166354` |

This shows the expected tradeoff: increasing `min_support` produces fewer, more common rules.

## Quality Checks

Run the test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/quality -q
```

The mining tests cover:

- basket matrix construction;
- basket summary generation;
- association rule metrics and sorting;
- bundle recommendation filtering;
- threshold comparison output.

## Limitations

- The current Instacart source does not contain real price or revenue fields, so the mining output focuses on co-purchase behavior rather than revenue impact.
- `product_name` is used as the item label for readability. If product names are duplicated in a larger dataset, using `product_id_nk` plus `product_name` would be safer.
- The default thresholds are tuned for a small local sample. For a larger dataset, consider stricter values such as `--min-support 0.02 --min-confidence 0.3`.
