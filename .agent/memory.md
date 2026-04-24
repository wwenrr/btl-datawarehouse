# Agent Memory Index

File này là entrypoint/index bắt buộc đọc trước mỗi task. Chỉ đọc thêm file con liên quan trong `.agent/memories/` khi task cần context đó.

## Memory Files

- [User Preferences](memories/user-preferences.md): sở thích, thói quen, cách user muốn agent làm việc.
- [Project Context](memories/project-context.md): bối cảnh repo/project, mục tiêu dài hạn.
- [Coding Style](memories/coding-style.md): style code, conventions, preference kỹ thuật; ưu tiên hash map/lookup map thay cho chuỗi `if/else` dài khi phù hợp.
- [Decisions](memories/decisions.md): quyết định quan trọng đã chốt và lý do.
- [Workflows](memories/workflows.md): workflow lặp lại, command hay dùng, quy trình làm việc.

## Current Summary

- User muốn agent đọc memory index trước khi làm task.
- User muốn memory dài được chia thành nhiều file markdown theo chủ đề, còn `.agent/memory.md` đóng vai trò index/router.
- User muốn agent chỉ ghi thẳng vào memory khi có yêu cầu rõ ràng; nếu agent chủ động phát hiện điều đáng lưu thì phải hỏi xác nhận trước.
- Khi update/bổ sung rule hoặc memory vận hành, ưu tiên dùng sub-agent cập nhật file nếu môi trường cho phép; main agent kiểm tra và tổng hợp.
- Khi agent làm sai và user kêu sửa: lỗi one-off thì sửa không lưu; preference/rule/workflow lặp lại thì hỏi xác nhận trước khi lưu; nếu user nói rõ “rút kinh nghiệm/nhớ lần sau/đừng làm vậy nữa” hoặc tương đương thì ghi thẳng vào memory phù hợp.
- Khi update agent rule/memory bằng sub-agent, ưu tiên `gpt-5.4-mini` nếu môi trường hỗ trợ; nếu môi trường không hỗ trợ/expose model này thì nói limitation, dùng model/sub-agent khả dụng gần nhất, và main agent kiểm tra kết quả.
