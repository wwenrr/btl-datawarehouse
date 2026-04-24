PLEASE READ AGENTS.md BEFORE WORKING IN THIS REPOSITORY. This file contains important instructions for how to build, test, run, and understand the architecture of the `btl-datawarehouse` project. It also outlines key conventions to follow when contributing to this repository.

# Copilot Instructions for `btl-datawarehouse`

## Build, test, and run commands

```bash
# Install dependencies
python -m pip install -r requirements.txt

# Run ETL
python etl.py --stage bronze
python etl.py --stage silver
python etl.py --stage gold
python etl.py --stage all

# Lightweight local run (limit Bronze source rows)
python etl.py --stage all --sample-rows 100

# Skip quality gate during `--stage all`
python etl.py --stage all --skip-quality
```

```bash
# Quality test suite
pytest tests/quality -q

# Single test file
pytest tests/quality/test_dim_tables.py -v

# Single test case
pytest tests/quality/test_dim_tables.py::test_dim_date_required_columns -v
```

## High-level architecture

- **Entrypoint:** `etl.py` calls `etl.jobs.run_etl.main`.
- **Orchestrator:** `etl/jobs/run_etl.py` controls stages (`bronze|silver|gold|all`), writes ETL run metadata to `etl_log`, and runs quality tests automatically only for `--stage all` unless `--skip-quality` is set.
- **Storage model:** DuckDB file at `data/warehouse/instacart.duckdb` (configured in `etl/config/settings.yaml`).
- **Bronze:** loads raw CSV files from `data/raw`. `bronze_orders` is incremental (watermark + anti-duplicate by `order_id`), while other bronze tables are rebuilt via `create or replace`.
- **Silver:** SQL transformations in `etl/sql/silver/*.sql` normalize/cast types, deduplicate order-product rows, and create deterministic `synthetic_order_date`.
- **Gold:** SQL transformations in `etl/sql/gold/*.sql` build a star schema (`dim_*`, `fact_order_line`, `fact_order_summary`) consistent with `docs/data-contracts/instacart-dwh.md`.
- **Seed dependency:** `dim_branch` depends on `data/seed/branches.csv`; missing seed file raises immediately (`ensure_branch_seed_exists`).
- **Quality harness:** `tests/conftest.py` snapshots and restores tracked `data/raw`, seed, and warehouse files before/after session tests, then preloads bronze→silver→gold for stable test fixtures.

## Key conventions in this repository

- **Authoritative quality scope:** treat `tests/quality/` as the canonical validation layer for ETL outputs and data contracts.
- **Pipeline logging contract:** every stage run writes `etl_log` with `SUCCESS`/`FAILED`, `rows_loaded`, and `watermark_order_id`; incremental behavior relies on successful watermark history.
- **Deterministic surrogate keys:** dimensions/facts use DuckDB `hash(...)`-based keys; business/natural keys are kept as `*_nk` columns.
- **Fact grain expectations:** `fact_order_line` grain is `(order_id_nk, product_key, add_to_cart_order)` and `fact_order_summary` grain is `order_id_nk` (enforced by tests and data contract).
- **Raw source strictness:** required source files are fixed in `etl/jobs/prepare_sources.py`; missing raw files fail fast before Bronze ingestion.
- **Agent workflow rules:** follow repository agent rules in `AGENTS.md`, especially reading `.agent/memory.md` before work and not running destructive git actions or commits without explicit user request.
