# btl-datawarehouse

ETL pipeline cho Instacart dataset theo mô hình star schema cho môn DSS.

## Setup

```bash
python -m pip install -r requirements.txt
```

## Run ETL

```bash
python etl.py --stage bronze
python etl.py --stage silver
python etl.py --stage gold
python etl.py --stage all
# chạy nhẹ máy: chỉ nạp N dòng mỗi bảng bronze
python etl.py --stage all --sample-rows 100
```

## Test

```bash
pytest tests/quality -v
```
