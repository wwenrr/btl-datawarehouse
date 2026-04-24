def test_dim_date_required_columns(conn):
    cols = {r[1] for r in conn.execute("pragma table_info('dim_date')").fetchall()}
    expected = {
        "date_key",
        "full_date",
        "day_of_month",
        "month",
        "quarter",
        "year",
        "day_of_week",
        "is_weekend",
    }
    assert expected.issubset(cols)


def test_dim_product_has_business_columns(conn):
    cols = {r[1] for r in conn.execute("pragma table_info('dim_product')").fetchall()}
    assert {"product_id_nk", "product_name", "aisle_name", "department_name", "is_organic"}.issubset(cols)


def test_dim_customer_columns(conn):
    cols = {r[1] for r in conn.execute("pragma table_info('dim_customer')").fetchall()}
    assert {"customer_key", "user_id_nk", "membership_tier", "total_orders"}.issubset(cols)


def test_dim_branch_columns(conn):
    cols = {r[1] for r in conn.execute("pragma table_info('dim_branch')").fetchall()}
    assert {"branch_key", "branch_id_nk", "branch_name", "city", "region"}.issubset(cols)


def test_default_branch_exists(conn):
    n = conn.execute(
        "select count(*) from dim_branch where branch_id_nk = 'DEFAULT_BRANCH'"
    ).fetchone()[0]
    assert n == 1
