create or replace table stg_orders as
with typed as (
  select
    cast(order_id as bigint) as order_id,
    cast(user_id as bigint) as user_id,
    cast(order_number as int) as order_number,
    cast(order_dow as int) as order_dow,
    cast(order_hour_of_day as int) as order_hour_of_day,
    coalesce(cast(days_since_prior_order as int), 0) as days_since_prior_order
  from bronze_orders
  where order_id is not null and user_id is not null
),
dated as (
  select
    *,
    date '2024-01-01' + cast(
      sum(days_since_prior_order) over (
        partition by user_id
        order by order_number
      ) as integer
    ) as synthetic_order_date
  from typed
)
select * from dated;
