def test_fact_order_line_unique_grain(conn):
    dup = conn.execute(
        """
        select order_id_nk, product_key, add_to_cart_order, count(*) c
        from fact_order_line
        group by 1,2,3
        having c > 1
        """
    ).fetchall()
    assert dup == []


def test_fact_order_line_count_matches_staging(conn):
    fact_cnt = conn.execute("select count(*) from fact_order_line").fetchone()[0]
    stg_cnt = conn.execute("select count(*) from stg_order_products").fetchone()[0]
    assert fact_cnt == stg_cnt
