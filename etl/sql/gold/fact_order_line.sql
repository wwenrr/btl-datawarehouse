create or replace table fact_order_line as
select
  abs(hash(
    concat_ws(
      '|',
      cast(op.order_id as varchar),
      cast(op.product_id as varchar),
      cast(op.add_to_cart_order as varchar)
    )
  )) as order_line_key,
  cast(op.order_id as varchar) as order_id_nk,
  dd.date_key,
  dp.product_key,
  dc.customer_key,
  db.branch_key,
  cast(op.add_to_cart_order as int) as add_to_cart_order,
  cast(op.reordered as boolean) as reordered,
  1 as quantity
from stg_order_products op
join stg_orders o on o.order_id = op.order_id
join dim_date dd on dd.full_date = o.synthetic_order_date
join dim_product dp on dp.product_id_nk = cast(op.product_id as varchar)
join dim_customer dc on dc.user_id_nk = cast(o.user_id as varchar)
join dim_branch db on db.branch_id_nk = 'DEFAULT_BRANCH';
