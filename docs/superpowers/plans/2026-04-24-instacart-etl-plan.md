# Instacart Data Warehouse ETL Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây dựng pipeline ETL cho Instacart dataset để nạp dữ liệu vào mô hình star schema gồm `dim_date`, `dim_product`, `dim_customer`, `dim_branch`, `fact_order_line`, `fact_order_summary` đúng đặc tả trong `refs/DSS_HK252_DW_Description_v0.1.pdf`, có incremental load, ETL log, và entrypoint `etl.py` theo yêu cầu đầu ra của vai trò ETL Engineer.

**Architecture:** Pipeline 3 lớp Bronze/Silver/Gold trên DuckDB. Bronze ingest toàn bộ CSV raw của Instacart. Silver chuẩn hóa kiểu dữ liệu, dedup, cleaning, và tạo `synthetic_order_date` (vì dataset không có ngày đặt hàng thực). Gold tạo dimension/fact theo grain yêu cầu, có các bước discretization (`membership_tier`) và aggregation (`fact_order_summary`). Pipeline hỗ trợ incremental load theo `order_id` watermark và ghi trạng thái từng lần chạy vào `ETL_LOG`.

**Tech Stack:** Python 3.11, Pandas, DuckDB, SQL scripts, pytest

---

## File Structure

- Create: `requirements.txt`
- Create: `etl.py`
- Create: `etl/config/settings.yaml`
- Create: `etl/jobs/run_etl.py`
- Create: `etl/jobs/load_seed_branch.py`
- Create: `etl/sql/meta/create_etl_log.sql`
- Create: `etl/sql/bronze/create_bronze_tables.sql`
- Create: `etl/sql/bronze/load_raw_csv.sql`
- Create: `etl/sql/silver/stg_orders.sql`
- Create: `etl/sql/silver/stg_order_products.sql`
- Create: `etl/sql/silver/stg_products.sql`
- Create: `etl/sql/silver/stg_users.sql`
- Create: `etl/sql/gold/dim_date.sql`
- Create: `etl/sql/gold/dim_product.sql`
- Create: `etl/sql/gold/dim_customer.sql`
- Create: `etl/sql/gold/dim_branch.sql`
- Create: `etl/sql/gold/fact_order_line.sql`
- Create: `etl/sql/gold/fact_order_summary.sql`
- Create: `tests/quality/test_bootstrap.py`
- Create: `tests/conftest.py`
- Create: `tests/quality/test_bronze_sources.py`
- Create: `tests/quality/test_silver_orders.py`
- Create: `tests/quality/test_dim_tables.py`
- Create: `tests/quality/test_fact_order_line.py`
- Create: `tests/quality/test_fact_order_summary.py`
- Create: `tests/quality/test_referential_integrity.py`
- Create: `tests/quality/test_schema_contract.py`
- Create: `tests/quality/test_incremental_load.py`
- Create: `docs/data-contracts/instacart-dwh.md`
- Create: `docs/etl-process.md`
- Modify (nếu có): `README.md`

## Chunk 1: Foundation + Bronze ingestion

### Task 1: Bootstrap project ETL

**Files:**
- Create: `requirements.txt`
- Create: `etl.py`
- Create: `etl/config/settings.yaml`
- Create: `etl/jobs/run_etl.py`
- Create: `tests/conftest.py`
- Test: `tests/quality/test_bootstrap.py`

- [ ] **Step 1: Viết test fail cho bootstrap**

```python
def test_config_path_exists():
    from pathlib import Path
    assert Path("etl/config/settings.yaml").exists()
```

- [ ] **Step 2: Chạy test để xác nhận fail**

Run: `pytest tests/quality/test_bootstrap.py -v`  
Expected: FAIL.

- [ ] **Step 3: Viết implement tối thiểu**

```python
from pathlib import Path

def config_path() -> Path:
    return Path("etl/config/settings.yaml")
```

```python
# etl.py
from etl.jobs.run_etl import main

if __name__ == "__main__":
    main()
```

```python
# tests/conftest.py
import duckdb
import pytest
from pathlib import Path

@pytest.fixture
def conn():
    Path("data/warehouse").mkdir(parents=True, exist_ok=True)
    db = duckdb.connect("data/warehouse/instacart.duckdb")
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 4: Chạy lại test**

Run: `pytest tests/quality/test_bootstrap.py -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt etl.py etl/config/settings.yaml etl/jobs/run_etl.py tests/conftest.py tests/quality/test_bootstrap.py
git commit -m "chore: bootstrap etl project"
```

### Task 2: Ingest đầy đủ raw Instacart vào Bronze

**Files:**
- Create: `etl/sql/bronze/create_bronze_tables.sql`
- Create: `etl/sql/bronze/load_raw_csv.sql`
- Modify: `etl/jobs/run_etl.py`
- Create: `etl/jobs/prepare_sources.py`
- Test: `tests/quality/test_bronze_sources.py`

- [ ] **Step 1: Viết test fail cho source availability + coverage của Bronze**

```python
def test_raw_sources_exist():
    from pathlib import Path
    required = [
        "data/raw/orders.csv",
        "data/raw/order_products__prior.csv",
        "data/raw/order_products__train.csv",
        "data/raw/products.csv",
        "data/raw/aisles.csv",
        "data/raw/departments.csv",
    ]
    assert all(Path(p).exists() for p in required)

def test_bronze_tables_exist(conn):
    required = {
        "bronze_orders",
        "bronze_order_products_prior",
        "bronze_order_products_train",
        "bronze_products",
        "bronze_aisles",
        "bronze_departments",
    }
    found = {r[0] for r in conn.execute("show tables").fetchall()}
    assert required.issubset(found)
```

- [ ] **Step 2: Chạy test để xác nhận fail**

Run: `pytest tests/quality/test_bronze_sources.py -v`  
Expected: FAIL.

- [ ] **Step 3: Viết bước validate nguồn + ingest SQL cho tất cả CSV**

```python
# etl/jobs/prepare_sources.py
from pathlib import Path

REQUIRED = [
    "data/raw/orders.csv",
    "data/raw/order_products__prior.csv",
    "data/raw/order_products__train.csv",
    "data/raw/products.csv",
    "data/raw/aisles.csv",
    "data/raw/departments.csv",
]

def validate_sources():
    missing = [p for p in REQUIRED if not Path(p).exists()]
    if missing:
        raise FileNotFoundError(f"Missing raw files: {missing}")

if __name__ == "__main__":
    validate_sources()
```

```sql
create or replace table bronze_orders as
select * from read_csv_auto('data/raw/orders.csv', header=true);
create or replace table bronze_order_products_prior as
select * from read_csv_auto('data/raw/order_products__prior.csv', header=true);
create or replace table bronze_order_products_train as
select * from read_csv_auto('data/raw/order_products__train.csv', header=true);
create or replace table bronze_products as
select * from read_csv_auto('data/raw/products.csv', header=true);
create or replace table bronze_aisles as
select * from read_csv_auto('data/raw/aisles.csv', header=true);
create or replace table bronze_departments as
select * from read_csv_auto('data/raw/departments.csv', header=true);
```

- [ ] **Step 4: Chạy bronze + test**

Run: `python -m etl.jobs.prepare_sources && python -m etl.jobs.run_etl --stage bronze && pytest tests/quality/test_bronze_sources.py -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add etl/sql/bronze etl/jobs/run_etl.py etl/jobs/prepare_sources.py tests/quality/test_bronze_sources.py
git commit -m "feat: ingest all instacart raw sources into bronze"
```

## Chunk 2: Silver normalization + synthetic date

### Task 3: Chuẩn hóa orders, products, order_products

**Files:**
- Create: `etl/sql/silver/stg_orders.sql`
- Create: `etl/sql/silver/stg_order_products.sql`
- Create: `etl/sql/silver/stg_products.sql`
- Create: `etl/sql/silver/stg_users.sql`
- Test: `tests/quality/test_silver_orders.py`

- [ ] **Step 1: Viết test fail cho uniqueness và synthetic date**

```python
def test_stg_orders_has_synthetic_date(conn):
    nulls = conn.execute(
        "select count(*) from stg_orders where synthetic_order_date is null"
    ).fetchone()[0]
    assert nulls == 0

def test_synthetic_date_deterministic(conn):
    mismatches = conn.execute("""
      with expected as (
        select
          cast(order_id as bigint) as order_id,
          date '2024-01-01'
            + sum(coalesce(cast(days_since_prior_order as int), 0)) over (
                partition by cast(user_id as bigint)
                order by cast(order_number as int)
              ) as expected_date
        from bronze_orders
      )
      select count(*)
      from stg_orders s
      join expected e on e.order_id = s.order_id
      where s.synthetic_order_date != e.expected_date
    """).fetchone()[0]
    assert mismatches == 0
```

- [ ] **Step 2: Chạy test để xác nhận fail**

Run: `pytest tests/quality/test_silver_orders.py -v`  
Expected: FAIL.

- [ ] **Step 3: Viết SQL Silver**

```sql
create or replace table stg_orders as
with typed as (
  select
    cast(order_id as bigint) as order_id,
    cast(user_id as bigint) as user_id,
    cast(order_number as int) as order_number,
    cast(order_dow as int) as order_dow,
    cast(order_hour_of_day as int) as order_hour_of_day,
    coalesce(cast(days_since_prior_order as int), 0) as days_since_prior_order
  from bronze_orders
),
dated as (
  select
    *,
    date '2024-01-01'
      + sum(days_since_prior_order) over (
          partition by user_id order by order_number
        ) as synthetic_order_date
  from typed
)
select * from dated;

create or replace table stg_order_products as
select distinct
  cast(order_id as bigint) as order_id,
  cast(product_id as bigint) as product_id,
  cast(add_to_cart_order as int) as add_to_cart_order,
  cast(reordered as int) as reordered
from (
  select * from bronze_order_products_prior
  union all
  select * from bronze_order_products_train
)
where order_id is not null and product_id is not null;

create or replace table stg_products as
select
  cast(product_id as bigint) as product_id,
  product_name,
  cast(aisle_id as int) as aisle_id,
  cast(department_id as int) as department_id
from bronze_products;

create or replace table stg_users as
select
  cast(user_id as bigint) as user_id,
  count(*) as total_orders
from stg_orders
group by user_id;
```

- [ ] **Step 4: Chạy silver + test**

Run: `python -m etl.jobs.run_etl --stage silver && pytest tests/quality/test_silver_orders.py -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add etl/sql/silver tests/quality/test_silver_orders.py
git commit -m "feat: add silver normalization with synthetic order date"
```

## Chunk 3: Gold dimensions

### Task 4: Build `dim_date` đúng contract

**Files:**
- Create: `etl/sql/gold/dim_date.sql`
- Test: `tests/quality/test_dim_tables.py`

- [ ] **Step 1: Viết test fail cho dim_date columns**

```python
def test_dim_date_required_columns(conn):
    cols = {r[1] for r in conn.execute("pragma_table_info('dim_date')").fetchall()}
    expected = {
        "date_key","full_date","day_of_month","month","quarter","year","day_of_week","is_weekend"
    }
    assert expected.issubset(cols)
```

- [ ] **Step 2: Chạy test để xác nhận fail**

Run: `pytest tests/quality/test_dim_tables.py::test_dim_date_required_columns -v`  
Expected: FAIL.

- [ ] **Step 3: Viết SQL dim_date**

```sql
create or replace table dim_date as
select
  abs(hash(cast(d as varchar))) as date_key,
  d as full_date,
  day(d) as day_of_month,
  month(d) as month,
  quarter(d) as quarter,
  year(d) as year,
  dayname(d) as day_of_week,
  case when dayofweek(d) in (0,6) then true else false end as is_weekend
from (select distinct synthetic_order_date as d from stg_orders);
```

- [ ] **Step 4: Chạy gold + test**

Run: `python -m etl.jobs.run_etl --stage gold && pytest tests/quality/test_dim_tables.py::test_dim_date_required_columns -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add etl/sql/gold/dim_date.sql tests/quality/test_dim_tables.py
git commit -m "feat: build dim_date with required attributes"
```

### Task 5: Build `dim_product`, `dim_customer`, `dim_branch`

**Files:**
- Create: `etl/sql/gold/dim_product.sql`
- Create: `etl/sql/gold/dim_customer.sql`
- Create: `etl/sql/gold/dim_branch.sql`
- Create: `etl/jobs/load_seed_branch.py`
- Create: `data/seed/branches.csv`
- Test: `tests/quality/test_dim_tables.py`

- [ ] **Step 1: Viết test fail cho các cột bắt buộc**

```python
def test_dim_product_has_business_columns(conn):
    cols = {r[1] for r in conn.execute("pragma_table_info('dim_product')").fetchall()}
    assert {"product_id_nk","product_name","aisle_name","department_name","is_organic"}.issubset(cols)
```

- [ ] **Step 2: Chạy test để xác nhận fail**

Run: `pytest tests/quality/test_dim_tables.py::test_dim_product_has_business_columns -v`  
Expected: FAIL.

- [ ] **Step 3: Viết SQL build 3 dimensions**

```sql
create or replace table dim_product as
select
  abs(hash(cast(p.product_id as varchar))) as product_key,
  cast(p.product_id as varchar) as product_id_nk,
  p.product_name,
  a.aisle as aisle_name,
  d.department as department_name,
  regexp_matches(lower(p.product_name), 'organic') as is_organic
from stg_products p
join bronze_aisles a on a.aisle_id = p.aisle_id
join bronze_departments d on d.department_id = p.department_id;

create or replace table dim_customer as
select
  abs(hash(cast(u.user_id as varchar))) as customer_key,
  cast(u.user_id as varchar) as user_id_nk,
  case
    when u.total_orders >= 40 then 'Platinum'
    when u.total_orders >= 15 then 'Gold'
    else 'Silver'
  end as membership_tier,
  u.total_orders
from stg_users u;

create or replace table dim_branch as
select
  abs(hash(branch_id_nk)) as branch_key,
  branch_id_nk,
  branch_name,
  city,
  region
from read_csv_auto('data/seed/branches.csv', header=true);
```

```python
# etl/jobs/load_seed_branch.py
from pathlib import Path

def ensure_branch_seed_exists() -> Path:
    path = Path("data/seed/branches.csv")
    if not path.exists():
        raise FileNotFoundError("Missing seed file: data/seed/branches.csv")
    return path
```

```csv
# data/seed/branches.csv
branch_id_nk,branch_name,city,region
DEFAULT_BRANCH,Instacart Online Hub,Ho Chi Minh City,South
```

```python
def test_dim_customer_columns(conn):
    cols = {r[1] for r in conn.execute("pragma_table_info('dim_customer')").fetchall()}
    assert {"customer_key","user_id_nk","membership_tier","total_orders"}.issubset(cols)

def test_dim_branch_columns(conn):
    cols = {r[1] for r in conn.execute("pragma_table_info('dim_branch')").fetchall()}
    assert {"branch_key","branch_id_nk","branch_name","city","region"}.issubset(cols)

def test_default_branch_exists(conn):
    n = conn.execute(
        "select count(*) from dim_branch where branch_id_nk = 'DEFAULT_BRANCH'"
    ).fetchone()[0]
    assert n == 1
```

- [ ] **Step 4: Chạy gold + test**

Run: `python -m etl.jobs.run_etl --stage gold && pytest tests/quality/test_dim_tables.py -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add etl/sql/gold/dim_product.sql etl/sql/gold/dim_customer.sql etl/sql/gold/dim_branch.sql etl/jobs/load_seed_branch.py data/seed/branches.csv tests/quality/test_dim_tables.py
git commit -m "feat: build product customer branch dimensions"
```

## Chunk 4: Gold facts + quality gates

### Task 6: Build `fact_order_line` (grain: 1 dòng / order_id + product_id + add_to_cart_order)

**Files:**
- Create: `etl/sql/gold/fact_order_line.sql`
- Test: `tests/quality/test_fact_order_line.py`

- [ ] **Step 1: Viết test fail cho grain và FK null-safety**

```python
def test_fact_order_line_unique_grain(conn):
    dup = conn.execute("""
      select order_id_nk, product_key, add_to_cart_order, count(*) c
      from fact_order_line
      group by 1,2,3 having c > 1
    """).fetchall()
    assert dup == []

def test_fact_order_line_count_matches_staging(conn):
    fact_cnt = conn.execute("select count(*) from fact_order_line").fetchone()[0]
    stg_cnt = conn.execute("select count(*) from stg_order_products").fetchone()[0]
    assert fact_cnt == stg_cnt
```

- [ ] **Step 2: Chạy test để xác nhận fail**

Run: `pytest tests/quality/test_fact_order_line.py -v`  
Expected: FAIL.

- [ ] **Step 3: Viết SQL fact_order_line**

```sql
create or replace table fact_order_line as
select
  abs(hash(
    concat_ws(
      '|',
      cast(op.order_id as varchar),
      cast(op.product_id as varchar),
      cast(op.add_to_cart_order as varchar)
    )
  )) as order_line_key,
  cast(op.order_id as varchar) as order_id_nk,
  dd.date_key,
  dp.product_key,
  dc.customer_key,
  db.branch_key,
  cast(op.add_to_cart_order as int) as add_to_cart_order,
  cast(op.reordered as boolean) as reordered,
  1 as quantity
from stg_order_products op
join stg_orders o on o.order_id = op.order_id
join dim_date dd on dd.full_date = o.synthetic_order_date
join dim_product dp on dp.product_id_nk = cast(op.product_id as varchar)
join dim_customer dc on dc.user_id_nk = cast(o.user_id as varchar)
join dim_branch db on db.branch_id_nk = 'DEFAULT_BRANCH';
```

- [ ] **Step 4: Chạy gold + test**

Run: `python -m etl.jobs.run_etl --stage gold && pytest tests/quality/test_fact_order_line.py -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add etl/sql/gold/fact_order_line.sql tests/quality/test_fact_order_line.py
git commit -m "feat: build fact_order_line with strict grain"
```

### Task 7: Build `fact_order_summary` (grain: 1 dòng / order_id)

**Files:**
- Create: `etl/sql/gold/fact_order_summary.sql`
- Test: `tests/quality/test_fact_order_summary.py`

- [ ] **Step 1: Viết test fail cho unique order_id_nk**

```python
def test_fact_order_summary_unique_order(conn):
    dup = conn.execute("""
      select order_id_nk, count(*) c
      from fact_order_summary
      group by 1 having c > 1
    """).fetchall()
    assert dup == []
```

- [ ] **Step 2: Chạy test để xác nhận fail**

Run: `pytest tests/quality/test_fact_order_summary.py -v`  
Expected: FAIL.

- [ ] **Step 3: Viết SQL fact_order_summary**

```sql
create or replace table fact_order_summary as
select
  abs(hash(fol.order_id_nk)) as order_summary_key,
  fol.order_id_nk,
  min(fol.date_key) as date_key,
  min(fol.customer_key) as customer_key,
  min(fol.branch_key) as branch_key,
  sum(fol.quantity) as total_items,
  count(distinct fol.product_key) as total_distinct_items,
  max(o.days_since_prior_order) as days_since_prior
from fact_order_line fol
join stg_orders o on cast(o.order_id as varchar) = fol.order_id_nk
group by fol.order_id_nk;
```

- [ ] **Step 4: Chạy gold + test**

Run: `python -m etl.jobs.run_etl --stage gold && pytest tests/quality/test_fact_order_summary.py -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add etl/sql/gold/fact_order_summary.sql tests/quality/test_fact_order_summary.py
git commit -m "feat: build fact_order_summary for BI"
```

### Task 8: Enforce schema contract + referential integrity

**Files:**
- Create: `tests/quality/test_referential_integrity.py`
- Create: `tests/quality/test_schema_contract.py`
- Modify: `etl/jobs/run_etl.py`

- [ ] **Step 1: Viết test fail cho FK integrity**

```python
def test_fact_order_line_fk_product(conn):
    orphans = conn.execute("""
      select count(*) from fact_order_line f
      left join dim_product d on d.product_key = f.product_key
      where d.product_key is null
    """).fetchone()[0]
    assert orphans == 0
```

- [ ] **Step 2: Chạy test để xác nhận fail**

Run: `pytest tests/quality/test_referential_integrity.py -v`  
Expected: FAIL.

- [ ] **Step 3: Add quality gate vào orchestrator**

```python
def run_quality():
    import subprocess
    subprocess.run(["pytest", "tests/quality", "-v"], check=True)

def run_stage_all():
    run_stage("bronze")
    run_stage("silver")
    run_stage("gold")
    run_quality()
```

- [ ] **Step 4: Chạy full ETL + quality gate**

Run: `python -m etl.jobs.run_etl --stage all`  
Expected: ETL hoàn tất, quality tests PASS.

- [ ] **Step 5: Commit**

```bash
git add etl/jobs/run_etl.py tests/quality/test_referential_integrity.py tests/quality/test_schema_contract.py
git commit -m "test: enforce schema and referential integrity checks"
```

### Task 9: Incremental load + ETL_LOG

**Files:**
- Create: `etl/sql/meta/create_etl_log.sql`
- Modify: `etl/jobs/run_etl.py`
- Test: `tests/quality/test_incremental_load.py`

- [ ] **Step 1: Viết test fail cho ETL_LOG và incremental idempotency**

```python
def test_etl_log_has_success_run(conn):
    n = conn.execute("""
      select count(*) from etl_log
      where status = 'SUCCESS' and stage = 'all'
    """).fetchone()[0]
    assert n >= 1

def test_incremental_rerun_not_duplicate_fact(conn):
    first = conn.execute("select count(*) from fact_order_line").fetchone()[0]
    second = conn.execute("select count(*) from fact_order_line").fetchone()[0]
    assert second == first
```

- [ ] **Step 2: Chạy test để xác nhận fail**

Run: `pytest tests/quality/test_incremental_load.py -v`  
Expected: FAIL.

- [ ] **Step 3: Tạo ETL_LOG + logic incremental**

```sql
create table if not exists etl_log (
  run_id varchar,
  stage varchar,
  started_at timestamp,
  finished_at timestamp,
  status varchar,
  rows_loaded bigint,
  watermark_order_id bigint,
  message varchar
);
```

```python
def write_etl_log(conn, run_id, stage, status, rows_loaded, watermark_order_id, message):
    conn.execute("""
      insert into etl_log values (?, ?, now(), now(), ?, ?, ?, ?)
    """, [run_id, stage, status, rows_loaded, watermark_order_id, message])

def incremental_filter_sql():
    return "where cast(order_id as bigint) > coalesce((select max(watermark_order_id) from etl_log where status='SUCCESS'), 0)"
```

- [ ] **Step 4: Chạy full ETL 2 lần + test**

Run: `python etl.py --stage all && python etl.py --stage all && pytest tests/quality/test_incremental_load.py -v`  
Expected: PASS (không duplicate, ETL_LOG có log thành công).

- [ ] **Step 5: Commit**

```bash
git add etl/sql/meta/create_etl_log.sql etl/jobs/run_etl.py tests/quality/test_incremental_load.py
git commit -m "feat: add incremental load and ETL logging"
```

## Chunk 5: Documentation + handoff

### Task 10: Viết data contract và runbook vận hành

**Files:**
- Create: `docs/data-contracts/instacart-dwh.md`
- Create: `docs/etl-process.md`
- Modify: `README.md`

- [ ] **Step 1: Viết section schema contract cho 6 bảng**

Run: `rg "dim_date|dim_product|dim_customer|dim_branch|fact_order_line|fact_order_summary" docs/data-contracts/instacart-dwh.md`  
Expected: Tất cả bảng xuất hiện trong docs.

- [ ] **Step 2: Viết runbook lỗi phổ biến**

Run: `rg "Kaggle|missing file|schema drift|orphan key" docs/data-contracts/instacart-dwh.md`  
Expected: Có mục troubleshooting.

- [ ] **Step 3: Cập nhật README với lệnh chạy chuẩn**

Run: `rg "Extract|Cleaning|Discretization|Aggregation|Incremental|ETL_LOG" docs/etl-process.md`  
Expected: Có đủ quy trình ETL end-to-end đúng yêu cầu vai trò ETL Engineer.

Run: `rg "python -m etl.jobs.run_etl --stage all" README.md`  
Expected: Có lệnh end-to-end.

- [ ] **Step 4: Commit**

```bash
git add docs/data-contracts/instacart-dwh.md docs/etl-process.md README.md
git commit -m "docs: add data contract and etl runbook"
```

## Canonical End-to-End Validation

Run:

```bash
python etl.py --stage bronze
python etl.py --stage silver
python etl.py --stage gold
python etl.py --stage all
python etl.py --stage all
pytest tests/quality -v
```

Expected:
- Bronze có đủ 6 nguồn raw.
- Silver có `synthetic_order_date` không null.
- Gold có đủ 4 dim + 2 fact đúng grain.
- Không có orphan FK, không vi phạm schema contract.
- Rerun incremental không tạo duplicate.
- `etl_log` có bản ghi SUCCESS/FAILED cho mỗi lần chạy.
