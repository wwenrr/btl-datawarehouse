create or replace table stg_order_products as
select distinct
  cast(order_id as bigint) as order_id,
  cast(product_id as bigint) as product_id,
  cast(add_to_cart_order as int) as add_to_cart_order,
  cast(reordered as int) as reordered
from (
  select * from bronze_order_products_prior
  union all
  select * from bronze_order_products_train
)
where order_id is not null and product_id is not null;
