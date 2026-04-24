# Decisions

### [2026-04-24 20:00] - Memory Index Architecture
Dùng `.agent/memory.md` làm index/router và lưu memory chi tiết trong `.agent/memories/*.md` theo chủ đề để tránh một file memory quá dài.

### [2026-04-24 23:19] - Copilot Instructions là tài liệu vận hành chuẩn cho agent
Chốt dùng `.github/copilot-instructions.md` làm nguồn hướng dẫn chính cho các phiên Copilot sau: command, kiến trúc tổng quan, và conventions ETL đặc thù của repo.

### [2026-04-24 23:19] - Cách cập nhật copilot-instructions khi đã có file
Nếu file đã tồn tại thì ưu tiên cập nhật/mở rộng theo nội dung hiện có thay vì thay toàn bộ, để tránh mất context đã chắt lọc từ các phiên trước.
