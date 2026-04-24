create or replace table dim_date as
select
  abs(hash(cast(d as varchar))) as date_key,
  d as full_date,
  day(d) as day_of_month,
  month(d) as month,
  quarter(d) as quarter,
  year(d) as year,
  dayname(d) as day_of_week,
  case when dayofweek(d) in (0, 6) then true else false end as is_weekend
from (
  select distinct synthetic_order_date as d
  from stg_orders
);
