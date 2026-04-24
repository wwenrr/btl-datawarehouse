create or replace table dim_product as
select
  abs(hash(cast(p.product_id as varchar))) as product_key,
  cast(p.product_id as varchar) as product_id_nk,
  p.product_name,
  a.aisle as aisle_name,
  d.department as department_name,
  regexp_matches(lower(p.product_name), 'organic') as is_organic
from stg_products p
join bronze_aisles a on cast(a.aisle_id as int) = p.aisle_id
join bronze_departments d on cast(d.department_id as int) = p.department_id;
