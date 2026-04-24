import csv
import sys
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from etl.jobs.run_etl import run_stage


def _write_csv(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def _snapshot_file(path: Path) -> bytes | None:
    if not path.exists():
        return None
    return path.read_bytes()


def _restore_file(path: Path, content: bytes | None) -> None:
    if content is None:
        if path.exists():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


@pytest.fixture(scope="session", autouse=True)
def setup_sample_data():
    tracked_files = [
        ROOT / "data/raw/orders.csv",
        ROOT / "data/raw/order_products__prior.csv",
        ROOT / "data/raw/order_products__train.csv",
        ROOT / "data/raw/products.csv",
        ROOT / "data/raw/aisles.csv",
        ROOT / "data/raw/departments.csv",
        ROOT / "data/seed/branches.csv",
        ROOT / "data/warehouse/instacart.duckdb",
    ]
    snapshots = {path: _snapshot_file(path) for path in tracked_files}

    _write_csv(
        ROOT / "data/raw/orders.csv",
        [
            ["order_id", "user_id", "eval_set", "order_number", "order_dow", "order_hour_of_day", "days_since_prior_order"],
            ["1", "10", "prior", "1", "1", "10", ""],
            ["2", "10", "train", "2", "2", "11", "5"],
            ["3", "11", "prior", "1", "5", "12", ""],
        ],
    )
    _write_csv(
        ROOT / "data/raw/order_products__prior.csv",
        [
            ["order_id", "product_id", "add_to_cart_order", "reordered"],
            ["1", "101", "1", "0"],
            ["3", "102", "1", "0"],
        ],
    )
    _write_csv(
        ROOT / "data/raw/order_products__train.csv",
        [
            ["order_id", "product_id", "add_to_cart_order", "reordered"],
            ["2", "101", "1", "1"],
            ["2", "103", "2", "0"],
        ],
    )
    _write_csv(
        ROOT / "data/raw/products.csv",
        [
            ["product_id", "product_name", "aisle_id", "department_id"],
            ["101", "Organic Banana", "1", "1"],
            ["102", "Milk 1L", "2", "2"],
            ["103", "Fresh Apple", "1", "1"],
        ],
    )
    _write_csv(ROOT / "data/raw/aisles.csv", [["aisle_id", "aisle"], ["1", "Fresh Fruits"], ["2", "Dairy"]])
    _write_csv(
        ROOT / "data/raw/departments.csv",
        [["department_id", "department"], ["1", "Produce"], ["2", "Dairy Eggs"]],
    )
    _write_csv(
        ROOT / "data/seed/branches.csv",
        [["branch_id_nk", "branch_name", "city", "region"], ["DEFAULT_BRANCH", "Instacart Online Hub", "Ho Chi Minh City", "South"]],
    )

    db = ROOT / "data/warehouse/instacart.duckdb"
    if db.exists():
        db.unlink()

    try:
        run_stage("bronze", with_quality=False)
        run_stage("silver", with_quality=False)
        run_stage("gold", with_quality=False)
        yield
    finally:
        for path, content in snapshots.items():
            _restore_file(path, content)


@pytest.fixture()
def conn(setup_sample_data):
    db = duckdb.connect(str(ROOT / "data/warehouse/instacart.duckdb"))
    try:
        yield db
    finally:
        db.close()
