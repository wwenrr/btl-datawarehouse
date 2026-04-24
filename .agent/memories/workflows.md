# Workflows

### [2026-04-24 20:00] - Memory Read Workflow
Trước mỗi task, agent đọc `.agent/memory.md` nếu tồn tại; sau đó chỉ đọc các file con liên quan theo index.

### [2026-04-24 20:47] - Dùng sub-agent khi update rule
Khi user yêu cầu update/bổ sung rule hoặc memory vận hành tương tự, ưu tiên dùng sub-agent để xử lý phần cập nhật file nếu môi trường cho phép, giúp main agent tiết kiệm thời gian cho công việc chính. Main agent vẫn chịu trách nhiệm kiểm tra kết quả và tổng hợp lại.

### [2026-04-24 20:50] - Rút kinh nghiệm khi agent làm sai
Khi agent làm sai và user kêu sửa: nếu lỗi chỉ là one-off thì sửa trực tiếp, không lưu memory. Nếu lỗi xuất phát từ preference/rule/workflow có khả năng lặp lại, agent phải hỏi xác nhận trước khi lưu. Nếu user nói rõ “rút kinh nghiệm”, “nhớ lần sau”, “đừng làm vậy nữa” hoặc câu tương đương, agent ghi thẳng bài học vào memory phù hợp. Main agent vẫn chịu trách nhiệm kiểm tra file đã lưu và tổng hợp kết quả.

### [2026-04-24 21:00] - Model sub-agent khi update agent rule/memory
Khi update agent rule/memory bằng sub-agent, ưu tiên dùng `gpt-5.4-mini` nếu môi trường hỗ trợ. Nếu môi trường không hỗ trợ/expose model này, nói rõ limitation và dùng model/sub-agent khả dụng gần nhất; main agent kiểm tra kết quả trước khi báo user.
