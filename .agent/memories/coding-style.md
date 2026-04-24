# Coding Style

Chưa có coding style cụ thể ngoài các rule trong `AGENTS.md`.

### [2026-04-24 20:45] - Ưu tiên hash map thay if/else dài
User không thích code có quá nhiều `if/else`; khi phù hợp, ưu tiên dùng hash map / lookup map / dispatch table để code gọn và dễ mở rộng hơn.

### [2026-04-24 23:19] - Convention đặt tên khóa trong DWH
Repo dùng pattern rõ ràng cho khóa: surrogate key dạng `*_key` (thường hash), natural/business key dạng `*_nk`; khi sửa SQL Gold/Fact nên giữ nhất quán naming này.

### [2026-04-24 23:22] - Python style tham chiếu clean-code-python
Khi viết Python trong repo, tham chiếu `zedr/clean-code-python` như guideline ưu tiên readability/refactorability:
- Đặt tên biến/hàm rõ nghĩa, nhất quán vocabulary, tránh magic number.
- Hàm nên làm một việc, hạn chế nhiều tham số; tránh boolean flag điều khiển nhiều nhánh.
- Hạn chế side effect lan tỏa; tách logic thuần và điểm I/O/ghi trạng thái.
- Áp dụng tư duy SOLID/DRY ở mức vừa đủ, tránh over-engineer.
- Dùng type hints để giữ contract rõ và tránh phá tương thích khi override.
