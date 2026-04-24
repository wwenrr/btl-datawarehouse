def test_fact_order_line_fk_product(conn):
    orphans = conn.execute(
        """
        select count(*)
        from fact_order_line f
        left join dim_product d on d.product_key = f.product_key
        where d.product_key is null
        """
    ).fetchone()[0]
    assert orphans == 0


def test_fact_order_line_fk_customer(conn):
    orphans = conn.execute(
        """
        select count(*)
        from fact_order_line f
        left join dim_customer d on d.customer_key = f.customer_key
        where d.customer_key is null
        """
    ).fetchone()[0]
    assert orphans == 0
