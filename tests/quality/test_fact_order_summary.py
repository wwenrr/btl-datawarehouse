def test_fact_order_summary_unique_order(conn):
    dup = conn.execute(
        """
        select order_id_nk, count(*) c
        from fact_order_summary
        group by 1
        having c > 1
        """
    ).fetchall()
    assert dup == []


def test_fact_order_summary_columns(conn):
    cols = {r[1] for r in conn.execute("pragma table_info('fact_order_summary')").fetchall()}
    assert {
        "order_summary_key",
        "order_id_nk",
        "date_key",
        "customer_key",
        "branch_key",
        "total_items",
        "total_distinct_items",
        "days_since_prior",
    }.issubset(cols)
