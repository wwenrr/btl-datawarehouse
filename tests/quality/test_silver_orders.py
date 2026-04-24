def test_stg_orders_has_synthetic_date(conn):
    nulls = conn.execute(
        "select count(*) from stg_orders where synthetic_order_date is null"
    ).fetchone()[0]
    assert nulls == 0


def test_synthetic_date_deterministic(conn):
    mismatches = conn.execute(
        """
        with expected as (
          select
            cast(order_id as bigint) as order_id,
            date '2024-01-01' + cast(
              sum(coalesce(cast(days_since_prior_order as int), 0)) over (
                partition by cast(user_id as bigint)
                order by cast(order_number as int)
              ) as integer
            ) as expected_date
          from bronze_orders
        )
        select count(*)
        from stg_orders s
        join expected e on e.order_id = s.order_id
        where s.synthetic_order_date != e.expected_date
        """
    ).fetchone()[0]
    assert mismatches == 0
