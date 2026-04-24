create or replace table dim_branch as
select
  abs(hash(branch_id_nk)) as branch_key,
  branch_id_nk,
  branch_name,
  city,
  region
from read_csv_auto('data/seed/branches.csv', header=true);
