create or replace table dim_customer as
select
  abs(hash(cast(u.user_id as varchar))) as customer_key,
  cast(u.user_id as varchar) as user_id_nk,
  case
    when u.total_orders >= 40 then 'Platinum'
    when u.total_orders >= 15 then 'Gold'
    else 'Silver'
  end as membership_tier,
  u.total_orders
from stg_users u;
