import argparse
import subprocess
import uuid
from pathlib import Path

import duckdb
import yaml

from etl.jobs.load_seed_branch import ensure_branch_seed_exists
from etl.jobs.prepare_sources import validate_sources

ROOT = Path(__file__).resolve().parents[2]


def load_config() -> dict:
    with (ROOT / "etl/config/settings.yaml").open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def connect_db(db_path: str) -> duckdb.DuckDBPyConnection:
    full = ROOT / db_path
    full.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(full))


def run_sql_file(conn: duckdb.DuckDBPyConnection, rel_path: str) -> None:
    sql = (ROOT / rel_path).read_text(encoding="utf-8")
    conn.execute(sql)


def max_success_watermark(conn: duckdb.DuckDBPyConnection) -> int:
    result = conn.execute(
        """
        select coalesce(max(watermark_order_id), 0)
        from etl_log
        where status = 'SUCCESS'
        """
    ).fetchone()[0]
    return int(result or 0)


def write_etl_log(
    conn: duckdb.DuckDBPyConnection,
    run_id: str,
    stage: str,
    status: str,
    rows_loaded: int,
    watermark_order_id: int,
    message: str,
) -> None:
    conn.execute(
        """
        insert into etl_log (
          run_id, stage, started_at, finished_at, status,
          rows_loaded, watermark_order_id, message
        )
        values (?, ?, now(), now(), ?, ?, ?, ?)
        """,
        [run_id, stage, status, rows_loaded, watermark_order_id, message],
    )


def run_bronze(
    conn: duckdb.DuckDBPyConnection, config: dict, sample_rows: int | None = None
) -> tuple[int, int]:
    validate_sources()
    raw_dir = ROOT / config["raw_data_dir"]
    run_sql_file(conn, "etl/sql/meta/create_etl_log.sql")
    effective_sample_rows = sample_rows if sample_rows is not None else config.get("bronze_sample_rows")

    if effective_sample_rows is not None and int(effective_sample_rows) <= 0:
        raise ValueError("sample_rows must be > 0")
    if effective_sample_rows is not None:
        effective_sample_rows = int(effective_sample_rows)

    if effective_sample_rows is None:
        conn.execute(
            "create or replace temp table _orders_src as select * from read_csv_auto(?, header=true)",
            [str(raw_dir / "orders.csv")],
        )
    else:
        conn.execute(
            "create or replace temp table _orders_src as select * from read_csv_auto(?, header=true) limit ?",
            [str(raw_dir / "orders.csv"), effective_sample_rows],
        )
    conn.execute("create table if not exists bronze_orders as select * from _orders_src where 1=0")

    watermark = max_success_watermark(conn)
    conn.execute(
        """
        insert into bronze_orders
        select s.*
        from _orders_src s
        where cast(s.order_id as bigint) > ?
          and not exists (
            select 1
            from bronze_orders b
            where cast(b.order_id as bigint) = cast(s.order_id as bigint)
          )
        """,
        [watermark],
    )

    if effective_sample_rows is None:
        conn.execute(
            "create or replace table bronze_order_products_prior as select * from read_csv_auto(?, header=true)",
            [str(raw_dir / "order_products__prior.csv")],
        )
        conn.execute(
            "create or replace table bronze_order_products_train as select * from read_csv_auto(?, header=true)",
            [str(raw_dir / "order_products__train.csv")],
        )
        conn.execute(
            "create or replace table bronze_products as select * from read_csv_auto(?, header=true)",
            [str(raw_dir / "products.csv")],
        )
        conn.execute(
            "create or replace table bronze_aisles as select * from read_csv_auto(?, header=true)",
            [str(raw_dir / "aisles.csv")],
        )
        conn.execute(
            "create or replace table bronze_departments as select * from read_csv_auto(?, header=true)",
            [str(raw_dir / "departments.csv")],
        )
    else:
        conn.execute(
            "create or replace table bronze_order_products_prior as select * from read_csv_auto(?, header=true) limit ?",
            [str(raw_dir / "order_products__prior.csv"), effective_sample_rows],
        )
        conn.execute(
            "create or replace table bronze_order_products_train as select * from read_csv_auto(?, header=true) limit ?",
            [str(raw_dir / "order_products__train.csv"), effective_sample_rows],
        )
        conn.execute(
            "create or replace table bronze_products as select * from read_csv_auto(?, header=true) limit ?",
            [str(raw_dir / "products.csv"), effective_sample_rows],
        )
        conn.execute(
            "create or replace table bronze_aisles as select * from read_csv_auto(?, header=true) limit ?",
            [str(raw_dir / "aisles.csv"), effective_sample_rows],
        )
        conn.execute(
            "create or replace table bronze_departments as select * from read_csv_auto(?, header=true) limit ?",
            [str(raw_dir / "departments.csv"), effective_sample_rows],
        )

    rows_loaded = int(
        conn.execute(
            "select count(*) from bronze_orders where cast(order_id as bigint) > ?",
            [watermark],
        ).fetchone()[0]
    )
    new_watermark = int(
        conn.execute("select coalesce(max(cast(order_id as bigint)), 0) from bronze_orders").fetchone()[0]
    )
    return rows_loaded, new_watermark


def run_silver(conn: duckdb.DuckDBPyConnection) -> int:
    run_sql_file(conn, "etl/sql/silver/stg_orders.sql")
    run_sql_file(conn, "etl/sql/silver/stg_order_products.sql")
    run_sql_file(conn, "etl/sql/silver/stg_products.sql")
    run_sql_file(conn, "etl/sql/silver/stg_users.sql")
    return int(conn.execute("select count(*) from stg_order_products").fetchone()[0])


def run_gold(conn: duckdb.DuckDBPyConnection) -> int:
    ensure_branch_seed_exists()
    run_sql_file(conn, "etl/sql/gold/dim_date.sql")
    run_sql_file(conn, "etl/sql/gold/dim_product.sql")
    run_sql_file(conn, "etl/sql/gold/dim_customer.sql")
    run_sql_file(conn, "etl/sql/gold/dim_branch.sql")
    run_sql_file(conn, "etl/sql/gold/fact_order_line.sql")
    run_sql_file(conn, "etl/sql/gold/fact_order_summary.sql")
    return int(conn.execute("select count(*) from fact_order_line").fetchone()[0])


def run_quality_checks() -> None:
    subprocess.run(["pytest", "tests/quality", "-q"], cwd=ROOT, check=True)


def run_stage(stage: str, with_quality: bool = True, sample_rows: int | None = None) -> None:
    config = load_config()
    conn = connect_db(config["database_path"])
    run_sql_file(conn, "etl/sql/meta/create_etl_log.sql")
    run_id = str(uuid.uuid4())
    watermark = 0
    rows_loaded = 0
    try:
        if stage == "bronze":
            rows_loaded, watermark = run_bronze(conn, config, sample_rows=sample_rows)
        elif stage == "silver":
            rows_loaded = run_silver(conn)
            watermark = max_success_watermark(conn)
        elif stage == "gold":
            rows_loaded = run_gold(conn)
            watermark = max_success_watermark(conn)
        elif stage == "all":
            bronze_rows, watermark = run_bronze(conn, config, sample_rows=sample_rows)
            silver_rows = run_silver(conn)
            gold_rows = run_gold(conn)
            rows_loaded = bronze_rows + silver_rows + gold_rows
            if with_quality:
                run_quality_checks()
        else:
            raise ValueError(f"Unsupported stage: {stage}")

        write_etl_log(
            conn,
            run_id=run_id,
            stage=stage,
            status="SUCCESS",
            rows_loaded=rows_loaded,
            watermark_order_id=watermark,
            message="OK",
        )
    except Exception as exc:
        write_etl_log(
            conn,
            run_id=run_id,
            stage=stage,
            status="FAILED",
            rows_loaded=rows_loaded,
            watermark_order_id=watermark,
            message=str(exc)[:500],
        )
        raise
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["bronze", "silver", "gold", "all"], required=True)
    parser.add_argument("--skip-quality", action="store_true")
    parser.add_argument(
        "--sample-rows",
        type=int,
        default=None,
        help="Limit rows loaded per bronze source table (for lightweight local runs).",
    )
    args = parser.parse_args()
    run_stage(args.stage, with_quality=not args.skip_quality, sample_rows=args.sample_rows)


if __name__ == "__main__":
    main()
