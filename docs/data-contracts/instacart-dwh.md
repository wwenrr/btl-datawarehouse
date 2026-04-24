# Instacart DWH Data Contract

## Star schema tables

1. `dim_date(date_key, full_date, day_of_month, month, quarter, year, day_of_week, is_weekend)`
2. `dim_product(product_key, product_id_nk, product_name, aisle_name, department_name, is_organic)`
3. `dim_customer(customer_key, user_id_nk, membership_tier, total_orders)`
4. `dim_branch(branch_key, branch_id_nk, branch_name, city, region)`
5. `fact_order_line(order_line_key, order_id_nk, date_key, product_key, customer_key, branch_key, add_to_cart_order, reordered, quantity)`
6. `fact_order_summary(order_summary_key, order_id_nk, date_key, customer_key, branch_key, total_items, total_distinct_items, days_since_prior)`

## Grain

- `fact_order_line`: 1 row per `(order_id_nk, product_key, add_to_cart_order)`.
- `fact_order_summary`: 1 row per `order_id_nk`.

## Quality rules

- No orphan foreign keys from facts to dimensions.
- No duplicate grain rows in both facts.
- `synthetic_order_date` must always be deterministically reproducible from raw orders.

## Troubleshooting

- **missing file**: verify all CSV files exist under `data/raw/`.
- **schema drift**: compare incoming CSV headers with expected raw schema before running.
- **orphan key**: rerun `bronze -> silver -> gold` and inspect failed joins in fact build SQL.
