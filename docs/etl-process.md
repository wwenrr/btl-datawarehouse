# Quy trình ETL

## 1. Extract

- Nguồn dữ liệu: Instacart CSV từ Kaggle.
- Validate đủ file: `orders`, `order_products__prior`, `order_products__train`, `products`, `aisles`, `departments`.

## 2. Cleaning

- Chuẩn hóa kiểu dữ liệu numeric/id.
- Trim `product_name`.
- Dedup dữ liệu order-product line.

## 3. Discretization

- `membership_tier` trong `dim_customer`:
  - `Platinum` nếu `total_orders >= 40`
  - `Gold` nếu `total_orders >= 15`
  - `Silver` còn lại

## 4. Aggregation

- `fact_order_summary` tổng hợp:
  - `total_items`
  - `total_distinct_items`
  - `days_since_prior`

## 5. Incremental load

- Bronze orders load theo watermark `order_id` lấy từ `etl_log`.
- Rerun không duplicate `order_id` đã nạp.

## 6. ETL_LOG

- Bảng `etl_log` ghi trạng thái từng run:
  - `run_id`, `stage`, `status`
  - `rows_loaded`
  - `watermark_order_id`
  - `message`
