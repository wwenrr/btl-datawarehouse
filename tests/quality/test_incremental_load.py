from etl.jobs.run_etl import run_stage


def test_etl_log_has_success_run(conn):
    n = conn.execute(
        """
        select count(*)
        from etl_log
        where status = 'SUCCESS'
        """
    ).fetchone()[0]
    assert n >= 1


def test_incremental_rerun_not_duplicate_fact(conn):
    first = conn.execute("select count(*) from fact_order_line").fetchone()[0]
    run_stage("bronze", with_quality=False)
    run_stage("silver", with_quality=False)
    run_stage("gold", with_quality=False)
    second = conn.execute("select count(*) from fact_order_line").fetchone()[0]
    assert second == first
