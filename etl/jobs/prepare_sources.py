from pathlib import Path

REQUIRED = [
    "data/raw/orders.csv",
    "data/raw/order_products__prior.csv",
    "data/raw/order_products__train.csv",
    "data/raw/products.csv",
    "data/raw/aisles.csv",
    "data/raw/departments.csv",
]


def validate_sources() -> None:
    missing = [p for p in REQUIRED if not Path(p).exists()]
    if missing:
        raise FileNotFoundError(f"Missing raw files: {missing}")


if __name__ == "__main__":
    validate_sources()
