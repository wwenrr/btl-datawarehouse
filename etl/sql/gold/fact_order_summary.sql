create or replace table fact_order_summary as
select
  abs(hash(fol.order_id_nk)) as order_summary_key,
  fol.order_id_nk,
  min(fol.date_key) as date_key,
  min(fol.customer_key) as customer_key,
  min(fol.branch_key) as branch_key,
  sum(fol.quantity) as total_items,
  count(distinct fol.product_key) as total_distinct_items,
  max(o.days_since_prior_order) as days_since_prior
from fact_order_line fol
join stg_orders o on cast(o.order_id as varchar) = fol.order_id_nk
group by fol.order_id_nk;
