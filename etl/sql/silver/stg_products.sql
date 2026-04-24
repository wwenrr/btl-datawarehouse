create or replace table stg_products as
select
  cast(product_id as bigint) as product_id,
  trim(product_name) as product_name,
  cast(aisle_id as int) as aisle_id,
  cast(department_id as int) as department_id
from bronze_products
where product_id is not null;
