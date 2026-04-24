from pathlib import Path


def test_raw_sources_exist():
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
