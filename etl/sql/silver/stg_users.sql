create or replace table stg_users as
select
  cast(user_id as bigint) as user_id,
  count(*) as total_orders
from stg_orders
group by user_id;
