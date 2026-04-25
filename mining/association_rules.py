import argparse
from pathlib import Path

import duckdb
import pandas as pd
import yaml
from mlxtend.frequent_patterns import apriori
from mlxtend.frequent_patterns import association_rules as build_association_rules
from mlxtend.preprocessing import TransactionEncoder

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "outputs/data_mining/association_rules.csv"
DEFAULT_SUMMARY_OUTPUT = ROOT / "outputs/data_mining/basket_summary.csv"
DEFAULT_BUNDLE_OUTPUT = ROOT / "outputs/data_mining/bundle_recommendations.csv"
DEFAULT_THRESHOLD_OUTPUT = ROOT / "outputs/data_mining/threshold_comparison.csv"
RULE_COLUMNS = [
    "antecedents",
    "consequents",
    "rule_text",
    "business_meaning",
    "support",
    "confidence",
    "lift",
    "antecedent_support",
    "consequent_support",
]


def load_config() -> dict:
    with (ROOT / "etl/config/settings.yaml").open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_db_path(db_path: str | None = None) -> Path:
    if db_path:
        path = Path(db_path)
    else:
        path = Path(load_config()["database_path"])
    return path if path.is_absolute() else ROOT / path


def load_order_items(db_path: Path) -> pd.DataFrame:
    if not db_path.exists():
        raise FileNotFoundError(f"DuckDB file not found: {db_path}")

    query = """
        select
          fol.order_id_nk,
          dp.product_name,
          dp.aisle_name,
          dp.department_name,
          fol.reordered
        from fact_order_line fol
        join dim_product dp on dp.product_key = fol.product_key
        where dp.product_name is not null
    """
    try:
        with duckdb.connect(str(db_path), read_only=True) as conn:
            return conn.execute(query).fetchdf()
    except duckdb.CatalogException as exc:
        raise RuntimeError(
            "Gold tables are missing. Run ETL through the gold stage before data mining."
        ) from exc


def build_basket_matrix(order_items: pd.DataFrame) -> pd.DataFrame:
    required = {"order_id_nk", "product_name"}
    missing = required - set(order_items.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    cleaned = order_items.dropna(subset=["order_id_nk", "product_name"]).copy()
    cleaned["product_name"] = cleaned["product_name"].astype(str).str.strip()
    cleaned = cleaned[cleaned["product_name"] != ""]

    baskets = cleaned.groupby("order_id_nk")["product_name"].apply(lambda items: sorted(set(items)))
    baskets = baskets[baskets.map(len) >= 2]
    if baskets.empty:
        raise ValueError("Need at least one basket with two or more products to mine association rules.")

    encoder = TransactionEncoder()
    encoded = encoder.fit_transform(baskets.tolist())
    return pd.DataFrame(encoded, columns=encoder.columns_)


def summarize_baskets(order_items: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    required = {"order_id_nk", "product_name"}
    missing = required - set(order_items.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    cleaned = order_items.dropna(subset=["order_id_nk", "product_name"]).copy()
    cleaned["product_name"] = cleaned["product_name"].astype(str).str.strip()
    cleaned = cleaned[cleaned["product_name"] != ""]
    if cleaned.empty:
        raise ValueError("No order-product rows available for basket summary.")

    basket_sizes = cleaned.groupby("order_id_nk")["product_name"].nunique()
    rows = [
        {"section": "overall", "metric": "order_product_rows", "label": "all", "value": len(cleaned)},
        {"section": "overall", "metric": "basket_count", "label": "all", "value": basket_sizes.size},
        {"section": "overall", "metric": "unique_products", "label": "all", "value": cleaned["product_name"].nunique()},
        {"section": "overall", "metric": "avg_basket_size", "label": "all", "value": round(basket_sizes.mean(), 4)},
        {"section": "overall", "metric": "median_basket_size", "label": "all", "value": round(basket_sizes.median(), 4)},
        {"section": "overall", "metric": "max_basket_size", "label": "all", "value": int(basket_sizes.max())},
    ]

    if "reordered" in cleaned.columns:
        reordered = cleaned["reordered"].astype(bool)
        rows.append(
            {
                "section": "overall",
                "metric": "reordered_rate",
                "label": "all",
                "value": round(float(reordered.mean()), 4),
            }
        )

    rows.extend(top_counts(cleaned, "product_name", "top_product", top_n))
    if "department_name" in cleaned.columns:
        rows.extend(top_counts(cleaned, "department_name", "top_department", top_n))
    if "aisle_name" in cleaned.columns:
        rows.extend(top_counts(cleaned, "aisle_name", "top_aisle", top_n))

    return pd.DataFrame(rows, columns=["section", "metric", "label", "value"])


def top_counts(data: pd.DataFrame, column: str, section: str, top_n: int) -> list[dict]:
    counts = data[column].dropna().astype(str).str.strip()
    counts = counts[counts != ""].value_counts().head(top_n)
    return [
        {"section": section, "metric": "line_count", "label": label, "value": int(value)}
        for label, value in counts.items()
    ]


def mine_rules(
    basket_matrix: pd.DataFrame,
    min_support: float = 0.005,
    min_confidence: float = 0.1,
    min_lift: float = 1.0,
    max_len: int | None = None,
    top_n: int | None = 50,
) -> pd.DataFrame:
    if basket_matrix.empty:
        raise ValueError("Basket matrix is empty.")

    frequent_itemsets = apriori(
        basket_matrix,
        min_support=min_support,
        use_colnames=True,
        max_len=max_len,
    )
    if frequent_itemsets.empty:
        return pd.DataFrame(columns=RULE_COLUMNS)

    rules = build_association_rules(
        frequent_itemsets,
        num_itemsets=len(basket_matrix),
        metric="confidence",
        min_threshold=min_confidence,
    )
    if rules.empty:
        return pd.DataFrame(columns=RULE_COLUMNS)

    rules = rules.rename(
        columns={
            "antecedent support": "antecedent_support",
            "consequent support": "consequent_support",
        }
    )
    rules = rules[rules["lift"] >= min_lift].copy()
    rules = rules.sort_values(["lift", "confidence", "support"], ascending=False)
    if top_n is not None:
        rules = rules.head(top_n)

    result = rules[
        [
            "antecedents",
            "consequents",
            "support",
            "confidence",
            "lift",
            "antecedent_support",
            "consequent_support",
        ]
    ].copy()
    result["antecedents"] = result["antecedents"].map(format_itemset)
    result["consequents"] = result["consequents"].map(format_itemset)
    result["rule_text"] = result["antecedents"] + " => " + result["consequents"]
    result["business_meaning"] = result.apply(describe_rule, axis=1)
    result = result[RULE_COLUMNS]
    return result.reset_index(drop=True)


def format_itemset(itemset: frozenset) -> str:
    return ", ".join(sorted(str(item) for item in itemset))


def describe_rule(rule: pd.Series) -> str:
    return (
        f"Recommend {rule['consequents']} when a basket contains {rule['antecedents']} "
        f"(confidence={rule['confidence']:.2%}, lift={rule['lift']:.2f})."
    )


def build_bundle_recommendations(rules: pd.DataFrame) -> pd.DataFrame:
    if rules.empty:
        return pd.DataFrame(
            columns=[
                "bundle_products",
                "recommended_product",
                "support",
                "confidence",
                "lift",
                "recommendation",
            ]
        )

    bundles = rules[~rules["consequents"].str.contains(",", regex=False)].copy()
    bundles = bundles.rename(
        columns={
            "antecedents": "bundle_products",
            "consequents": "recommended_product",
        }
    )
    bundles["recommendation"] = (
        "Bundle "
        + bundles["bundle_products"]
        + " with "
        + bundles["recommended_product"]
        + " for cross-sell."
    )
    return bundles[
        [
            "bundle_products",
            "recommended_product",
            "support",
            "confidence",
            "lift",
            "recommendation",
        ]
    ].reset_index(drop=True)


def compare_thresholds(
    basket_matrix: pd.DataFrame,
    support_values: list[float],
    min_confidence: float,
    min_lift: float,
    max_len: int | None,
) -> pd.DataFrame:
    rows = []
    for min_support in support_values:
        rules = mine_rules(
            basket_matrix,
            min_support=min_support,
            min_confidence=min_confidence,
            min_lift=min_lift,
            max_len=max_len,
            top_n=None,
        )
        rows.append(
            {
                "min_support": min_support,
                "min_confidence": min_confidence,
                "min_lift": min_lift,
                "rule_count": len(rules),
                "max_lift": round(float(rules["lift"].max()), 6) if not rules.empty else 0.0,
                "avg_lift": round(float(rules["lift"].mean()), 6) if not rules.empty else 0.0,
            }
        )
    return pd.DataFrame(rows)


def write_rules(rules: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rules.to_csv(output_path, index=False)


def write_dataframe(data: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(output_path, index=False)


def write_rules_to_duckdb(db_path: Path, rules: pd.DataFrame) -> None:
    with duckdb.connect(str(db_path)) as conn:
        conn.register("_dm_rules", rules)
        conn.execute("create or replace table dm_association_rules as select * from _dm_rules")
        conn.unregister("_dm_rules")


def parse_support_values(value: str) -> list[float]:
    values = [positive_float(part.strip()) for part in value.split(",") if part.strip()]
    if not values:
        raise argparse.ArgumentTypeError("at least one support value is required")
    return values


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be > 0")
    return parsed


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be > 0")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mine association rules from Gold order-line facts.")
    parser.add_argument("--db-path", default=None, help="DuckDB path. Defaults to etl/config/settings.yaml.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="CSV output path.")
    parser.add_argument("--summary-output", default=str(DEFAULT_SUMMARY_OUTPUT), help="Basket summary CSV output path.")
    parser.add_argument("--bundle-output", default=str(DEFAULT_BUNDLE_OUTPUT), help="Bundle recommendation CSV output path.")
    parser.add_argument(
        "--threshold-output",
        default=str(DEFAULT_THRESHOLD_OUTPUT),
        help="Threshold comparison CSV output path.",
    )
    parser.add_argument("--min-support", type=positive_float, default=0.005)
    parser.add_argument("--min-confidence", type=positive_float, default=0.1)
    parser.add_argument("--min-lift", type=positive_float, default=1.0)
    parser.add_argument("--max-len", type=positive_int, default=None)
    parser.add_argument("--top-n", type=positive_int, default=50)
    parser.add_argument(
        "--threshold-supports",
        type=parse_support_values,
        default=[0.005, 0.01, 0.02],
        help="Comma-separated min_support values for comparison.",
    )
    parser.add_argument("--write-db", action="store_true", help="Write rules to dm_association_rules in DuckDB.")
    return parser.parse_args()


def resolve_output_path(path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else ROOT / path


def main() -> None:
    args = parse_args()
    db_path = resolve_db_path(args.db_path)
    output_path = resolve_output_path(args.output)
    summary_output = resolve_output_path(args.summary_output)
    bundle_output = resolve_output_path(args.bundle_output)
    threshold_output = resolve_output_path(args.threshold_output)

    order_items = load_order_items(db_path)
    summary = summarize_baskets(order_items, top_n=args.top_n)
    basket_matrix = build_basket_matrix(order_items)
    rules = mine_rules(
        basket_matrix,
        min_support=args.min_support,
        min_confidence=args.min_confidence,
        min_lift=args.min_lift,
        max_len=args.max_len,
        top_n=args.top_n,
    )
    bundles = build_bundle_recommendations(rules)
    threshold_comparison = compare_thresholds(
        basket_matrix,
        support_values=args.threshold_supports,
        min_confidence=args.min_confidence,
        min_lift=args.min_lift,
        max_len=args.max_len,
    )

    write_dataframe(summary, summary_output)
    write_rules(rules, output_path)
    write_dataframe(bundles, bundle_output)
    write_dataframe(threshold_comparison, threshold_output)
    if args.write_db:
        write_rules_to_duckdb(db_path, rules)

    print(f"Loaded {len(order_items):,} order-product rows")
    print(f"Built basket matrix: {basket_matrix.shape[0]:,} baskets x {basket_matrix.shape[1]:,} products")
    print(f"Wrote {len(rules):,} rules to {output_path}")
    print(f"Wrote basket summary to {summary_output}")
    print(f"Wrote {len(bundles):,} bundle recommendations to {bundle_output}")
    print(f"Wrote threshold comparison to {threshold_output}")
    if args.write_db:
        print(f"Wrote rules to DuckDB table dm_association_rules in {db_path}")
    if not rules.empty:
        print(rules.to_string(index=False))


if __name__ == "__main__":
    main()
