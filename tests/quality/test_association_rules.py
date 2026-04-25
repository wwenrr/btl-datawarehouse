import pandas as pd

from mining.association_rules import (
    build_basket_matrix,
    build_bundle_recommendations,
    compare_thresholds,
    mine_rules,
    summarize_baskets,
)


def test_build_basket_matrix_from_order_items():
    order_items = pd.DataFrame(
        [
            {"order_id_nk": "1", "product_name": "Bread"},
            {"order_id_nk": "1", "product_name": "Milk"},
            {"order_id_nk": "2", "product_name": "Bread"},
            {"order_id_nk": "2", "product_name": "Eggs"},
        ]
    )

    matrix = build_basket_matrix(order_items)

    assert matrix.shape == (2, 3)
    assert set(matrix.columns) == {"Bread", "Eggs", "Milk"}


def test_summarize_baskets_returns_overall_and_top_counts():
    order_items = pd.DataFrame(
        [
            {"order_id_nk": "1", "product_name": "Bread", "department_name": "Bakery", "reordered": True},
            {"order_id_nk": "1", "product_name": "Milk", "department_name": "Dairy", "reordered": False},
            {"order_id_nk": "2", "product_name": "Bread", "department_name": "Bakery", "reordered": True},
        ]
    )

    summary = summarize_baskets(order_items, top_n=2)

    metrics = set(summary["metric"])
    assert {"basket_count", "unique_products", "avg_basket_size", "reordered_rate"}.issubset(metrics)
    assert "top_product" in set(summary["section"])
    assert "top_department" in set(summary["section"])


def test_mine_rules_returns_metrics_sorted_by_lift():
    basket_matrix = pd.DataFrame(
        [
            {"Bread": True, "Milk": True, "Eggs": False},
            {"Bread": True, "Milk": True, "Eggs": False},
            {"Bread": True, "Milk": False, "Eggs": True},
            {"Bread": False, "Milk": True, "Eggs": True},
        ]
    )

    rules = mine_rules(
        basket_matrix,
        min_support=0.25,
        min_confidence=0.5,
        min_lift=0.1,
        top_n=10,
    )

    assert set(
        [
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
    ).issubset(rules.columns)
    assert rules["lift"].is_monotonic_decreasing


def test_build_bundle_recommendations_keeps_single_consequent_rules():
    rules = pd.DataFrame(
        [
            {
                "antecedents": "Bread",
                "consequents": "Milk",
                "support": 0.5,
                "confidence": 0.8,
                "lift": 1.2,
            },
            {
                "antecedents": "Bread",
                "consequents": "Milk, Eggs",
                "support": 0.25,
                "confidence": 0.5,
                "lift": 1.1,
            },
        ]
    )

    bundles = build_bundle_recommendations(rules)

    assert len(bundles) == 1
    assert bundles.iloc[0]["bundle_products"] == "Bread"
    assert bundles.iloc[0]["recommended_product"] == "Milk"


def test_compare_thresholds_returns_rule_counts():
    basket_matrix = pd.DataFrame(
        [
            {"Bread": True, "Milk": True, "Eggs": False},
            {"Bread": True, "Milk": True, "Eggs": False},
            {"Bread": True, "Milk": False, "Eggs": True},
            {"Bread": False, "Milk": True, "Eggs": True},
        ]
    )

    comparison = compare_thresholds(
        basket_matrix,
        support_values=[0.25, 0.5],
        min_confidence=0.5,
        min_lift=0.1,
        max_len=None,
    )

    assert list(comparison["min_support"]) == [0.25, 0.5]
    assert set(["rule_count", "max_lift", "avg_lift"]).issubset(comparison.columns)
