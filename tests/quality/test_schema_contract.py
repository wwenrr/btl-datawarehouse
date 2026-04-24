def test_required_tables_exist(conn):
    required = {
        "dim_date",
        "dim_product",
        "dim_customer",
        "dim_branch",
        "fact_order_line",
        "fact_order_summary",
    }
    found = {r[0] for r in conn.execute("show tables").fetchall()}
    assert required.issubset(found)
