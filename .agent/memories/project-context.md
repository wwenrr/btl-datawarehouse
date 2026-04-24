# Project Context

Repo này chứa bộ rule để cấu hình coding agent, tập trung vào memory, git safety, tư duy phản biện, simplicity, surgical changes, và model routing cho sub-agent.

### [2026-04-24 23:18] - Copilot repo instructions đã được chuẩn hoá
Đã tạo `.github/copilot-instructions.md` cho repo ETL Instacart (DuckDB + SQL + pytest quality). File này tổng hợp lệnh run/test thực tế, kiến trúc Bronze/Silver/Gold + `etl_log`, và các convention quan trọng (grain fact, key hash, quality gate).

### [2026-04-24 23:19] - Big-picture ETL được chuẩn hóa trong memory
Luồng chuẩn của repo: `etl.py` -> `etl/jobs/run_etl.py` điều phối stage -> SQL theo lớp Bronze/Silver/Gold -> ghi `etl_log` để theo dõi run và watermark incremental cho Bronze orders.

### [2026-04-24 23:19] - Phạm vi quality chính thức
`tests/quality/` là bộ kiểm định dữ liệu chính thức cho data contract của star schema, bao gồm kiểm tra grain fact, referential integrity, schema columns, và tính deterministic của synthetic date.
