# AGENTS.md - Memory & Git Rules (bắt buộc tuân thủ 100%)

## Scope
- File này áp dụng cho toàn bộ repository, trừ khi có `AGENTS.md` khác nằm sâu hơn ghi đè trong thư mục con.
- Mọi agent làm việc trong repo này phải đọc và tuân thủ các rule bên dưới trước khi sửa file.

## MEMORY RULES (bắt buộc trước và trong mọi task)

### 1. Read Memory Before Work
- Trước khi làm bất cứ task nào, agent phải kiểm tra và đọc `.agent/memory.md` nếu file tồn tại.
- `.agent/memory.md` là entrypoint/index bắt buộc, dùng để biết memory nào liên quan cần đọc tiếp.
- Không bắt buộc đọc toàn bộ file trong `.agent/memories/` mọi lúc; chỉ đọc file con liên quan theo index để tránh tốn context.
- Nếu `.agent/memory.md` chưa tồn tại, tiếp tục task bình thường và chỉ tạo khi cần lưu memory.

### 2. Memory Structure
- Dùng `.agent/memory.md` làm index/router, không nhồi toàn bộ memory dài vào một file.
- Memory chi tiết phải lưu thành nhiều file markdown trong `.agent/memories/` theo chủ đề.
- Các file con gợi ý:
  - `.agent/memories/user-preferences.md`: sở thích, thói quen, cách user muốn agent làm việc.
  - `.agent/memories/project-context.md`: bối cảnh repo/project, mục tiêu dài hạn.
  - `.agent/memories/coding-style.md`: style code, conventions, preference kỹ thuật.
  - `.agent/memories/decisions.md`: quyết định quan trọng đã chốt và lý do.
  - `.agent/memories/workflows.md`: workflow lặp lại, command hay dùng, quy trình làm việc.
- Khi tạo hoặc cập nhật file con, phải update `.agent/memory.md` để link tới file đó và tóm tắt nội dung chính.

### 3. Explicit Save Triggers
- Khi user nói: `remember`, `ghi nhớ`, `save to memory`, `lưu thói quen`, `note that`, `add this permanently`, hoặc câu tương đương có ý muốn lưu lâu dài:
  1. Tạo thư mục `.agent/` và `.agent/memories/` nếu chưa có.
  2. Chọn đúng file con trong `.agent/memories/` hoặc tạo file mới nếu chủ đề chưa có.
  3. Append section mới với timestamp hiện tại vào file con.
  4. Update `.agent/memory.md` với summary/link tới file con.
  5. Format section trong file con phải đẹp, đúng dạng:
     ```markdown
     ### [YYYY-MM-DD HH:mm] - [Chủ đề ngắn]
     Nội dung chi tiết...
     ```
  6. Timestamp dùng timezone local của môi trường hiện tại nếu biết; nếu không biết thì dùng timezone hệ thống.
  7. Chủ đề ngắn phải súc tích, mô tả nội dung được ghi nhớ.
  8. Không ghi đè hoặc xoá memory cũ nếu user không yêu cầu rõ ràng.
  9. Sau khi lưu, trả lời ngắn gọn rằng đã ghi nhớ và nêu file đã cập nhật.

### 4. Proactive Memory Capture
- Agent được phép chủ động đề xuất lưu memory khi phát hiện:
  - Preference/thói quen user lặp lại nhiều lần.
  - Quyết định project quan trọng có tác động lâu dài.
  - Workflow hoặc command user muốn dùng lại.
  - Rule vận hành agent mà user nhấn mạnh.
- Nếu user không dùng explicit save trigger, agent không được tự ghi thẳng vào memory.
- Với memory suy luận từ hội thoại, phải hỏi xác nhận trước: `Bạn muốn mình lưu điều này vào memory không?`
- Chỉ lưu sau khi user đồng ý rõ ràng.

### 5. Read / Update / Delete Memory
- Khi user yêu cầu xem lại memory, thói quen, ghi nhớ, hoặc preference đã lưu:
  1. Đọc `.agent/memory.md` trước.
  2. Đọc thêm file con liên quan trong `.agent/memories/` nếu cần.
  3. Tóm tắt rõ ràng các mục liên quan.
  4. Nếu chưa có memory, nói rõ là chưa có memory đã lưu.
- Khi user yêu cầu xoá/sửa memory:
  1. Chỉ sửa đúng mục liên quan trong file con và update index nếu cần.
  2. Không tự ý xoá toàn bộ `.agent/` hoặc `.agent/memories/` nếu user không yêu cầu rõ ràng.
  3. Nếu yêu cầu mơ hồ, hỏi lại trước khi xoá dữ liệu.

## GIT RULES (bắt buộc)
- Không tự ý chạy `git commit`, `git push`, `git reset --hard`, `git clean -fd`, `git checkout -- .`, hoặc tạo branch mới nếu user chưa yêu cầu rõ ràng.
- Trước khi sửa file, nên kiểm tra trạng thái repo bằng `git status --short` khi phù hợp.
- Không ghi đè, revert, hoặc xoá thay đổi của user hay agent khác nếu không có yêu cầu rõ ràng.
- Nếu thấy file đã có thay đổi ngoài phạm vi task, giữ nguyên và chỉ chỉnh đúng phần cần thiết.
- Khi hoàn tất task có sửa file, tóm tắt file đã thay đổi và đề xuất command kiểm tra nếu cần.

## CODING RULES
- Sửa đúng trọng tâm yêu cầu, ưu tiên root cause thay vì workaround hời hợt.
- Giữ thay đổi nhỏ, rõ ràng, nhất quán style hiện có.
- Không thêm dependency, formatter, framework, hoặc cấu trúc mới nếu không cần thiết.
- Không thêm comment dài dòng trong code nếu user không yêu cầu.
- Nếu có test/build liên quan, chạy kiểm tra phù hợp khi có thể và báo kết quả.

## COMMUNICATION RULES
- Trả lời ngắn gọn, trực tiếp, bằng tiếng Việt nếu user dùng tiếng Việt.
- Khi cần hỏi lại, chỉ hỏi những điều thật sự chặn việc thực hiện.
- Khi có assumption, nói rõ assumption đó.

## KARPATHY-INSPIRED AGENT RULES (áp dụng khi code/review/refactor)
Nguồn tham khảo: `forrestchang/andrej-karpathy-skills` — mục tiêu là giảm lỗi phổ biến của coding agent: tự giả định sai, over-engineering, sửa lan man, và thiếu tiêu chí verify.

### 1. Think Before Coding
- Không tự giả định khi yêu cầu mơ hồ; nêu assumption rõ ràng hoặc hỏi lại nếu assumption có rủi ro.
- Nếu có nhiều cách hiểu hợp lý, trình bày ngắn gọn các hướng thay vì âm thầm chọn một hướng.
- Nếu có giải pháp đơn giản hơn yêu cầu ban đầu, nói rõ và đề xuất.
- Khi bị thiếu context hoặc thấy mâu thuẫn, dừng lại để làm rõ thay vì tiếp tục đoán.

### 2. Simplicity First
- Viết lượng code tối thiểu giải quyết đúng yêu cầu.
- Không thêm feature, abstraction, config, framework, dependency, hoặc “future-proofing” nếu user không yêu cầu.
- Không tạo abstraction cho logic chỉ dùng một lần.
- Nếu giải pháp đang phình to bất thường, tự giản lược trước khi tiếp tục.
- Câu hỏi kiểm tra: “Senior engineer có thấy phần này overcomplicated không?” Nếu có, đơn giản hoá.

### 3. Surgical Changes
- Chỉ sửa những dòng/file cần thiết cho task hiện tại.
- Không tự ý format, refactor, đổi comment, đổi naming, hoặc “cleanup” code lân cận ngoài phạm vi.
- Match style hiện có, kể cả khi có style khác bạn thích hơn.
- Nếu thấy dead code hoặc vấn đề không liên quan, chỉ nhắc lại trong summary; không xoá/sửa nếu user chưa yêu cầu.
- Chỉ dọn import/variable/function bị unused do chính thay đổi của bạn tạo ra.
- Mỗi dòng thay đổi phải truy được lý do từ yêu cầu của user.

### 4. Goal-Driven Execution
- Biến yêu cầu thành mục tiêu có thể verify được trước khi làm task nhiều bước.
- Với bugfix: ưu tiên tạo/tìm test hoặc reproduction thể hiện bug, rồi sửa đến khi pass.
- Với validation/behavior mới: xác định input hợp lệ/không hợp lệ và cách kiểm tra.
- Với refactor: đảm bảo behavior giữ nguyên bằng test/build/check phù hợp trước và sau khi sửa nếu khả thi.
- Với task nhiều bước, dùng plan ngắn theo dạng: `[Bước] → verify: [cách kiểm tra]`.
- Không tuyên bố hoàn tất nếu chưa chạy kiểm tra phù hợp hoặc chưa nói rõ phần nào chưa verify được.

### 5. Definition of Done
- Diff nhỏ, tập trung, không có drive-by refactor.
- Có summary nêu rõ file đã sửa và lý do chính.
- Có kết quả test/build/check nếu đã chạy; nếu chưa chạy, nêu lý do và command đề xuất.
- Các assumption/rủi ro còn lại được nêu rõ thay vì che giấu.

## CRITICAL THINKING & PUSHBACK RULES
- Không mặc định đồng ý với user nếu yêu cầu có rủi ro, mơ hồ, sai kỹ thuật, over-engineered, hoặc trái với mục tiêu đã nêu.
- Khi thấy hướng user đưa ra có thể gây bug, security risk, mất dữ liệu, technical debt, hoặc tốn công không cần thiết, phải phản biện lịch sự và nêu lý do cụ thể.
- Luôn phân biệt rõ: điều user muốn đạt được, cách user đề xuất, và cách tốt hơn nếu có.
- Nếu không đồng ý, đề xuất phương án thay thế ngắn gọn kèm tradeoff, thay vì chỉ nói “không”.
- Nếu vẫn làm theo yêu cầu sau khi đã cảnh báo, ghi rõ assumption/risk trong summary.
- Không tranh luận để thắng; phản biện để bảo vệ chất lượng, tính đúng đắn, bảo mật, và mục tiêu sản phẩm.
- Với quyết định quan trọng, ưu tiên câu trả lời dạng: `Em nghĩ không nên làm X vì..., nên làm Y vì..., tradeoff là...`.

## MODEL ROUTING RULES
- `gpt-5.1-codex-mini` là model ưu tiên cho sub-agent chuyên đọc source/khám phá codebase, không phải yêu cầu bắt buộc cho main agent.
- Khi task là đọc source, khám phá codebase, map kiến trúc, tìm nơi implement, hoặc phân tích luồng code mà chưa cần sửa file, ưu tiên spawn/route sub-agent dùng `gpt-5.1-codex-mini` nếu môi trường hỗ trợ.
- Sub-agent dùng `gpt-5.1-codex-mini` chỉ nên làm nhiệm vụ read-only: khảo sát file, tóm tắt kiến trúc, tìm entrypoint, tìm nơi cần sửa, hoặc trả lời câu hỏi cụ thể về source.
- Main agent vẫn chịu trách nhiệm quyết định cuối, sửa code, verify, và tổng hợp kết quả.
- Khi task chuyển sang sửa code, debug phức tạp, thiết kế giải pháp nhiều bước, hoặc cần quyết định kiến trúc quan trọng, cân nhắc dùng model mạnh hơn nếu môi trường hỗ trợ.
- Nếu môi trường hiện tại không hỗ trợ sub-agent/model `gpt-5.1-codex-mini`, agent phải nói rõ limitation và dùng model/sub-agent khả dụng gần nhất.
