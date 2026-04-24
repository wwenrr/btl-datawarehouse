create table if not exists etl_log (
  run_id varchar,
  stage varchar,
  started_at timestamp,
  finished_at timestamp,
  status varchar,
  rows_loaded bigint,
  watermark_order_id bigint,
  message varchar
);
