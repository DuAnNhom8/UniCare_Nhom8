# UniCareer – Báo cáo QA Sprint 3

## Thời điểm kiểm tra

17/11/2026. Phạm vi: mã nguồn gói UniCareer Sprint 3, 7 task trên bảng.

## Kết quả

| Loại kiểm tra | Kết quả | Phạm vi và giới hạn |
| --- | --- | --- |
| Pytest API/logic | **12/12 PASS** | 2 bài gốc + 10 bài Sprint 3, DB SQLite cô lập |
| Python syntax | **PASS** | `python -m compileall -q app create_admin.py` |
| JavaScript syntax | **PASS** | `node --check static/admin.js`, `static/employer.js`, `static/app.js` |
| Serve API nội bộ | **PASS** | `GET /health` trả `{"status":"ok","project":"UniCareer"}` khi chạy uvicorn với SQLite URL |
| MySQL 8 | **CHƯA KIỂM THỬ TRỰC TIẾP** | Môi trường phát triển không có MySQL Server |
| Gọi OpenAI API thực | **CHƯA KIỂM THỬ TRỰC TIẾP** | Không cung cấp API key cho lần kiểm tra này; kiểm tra đường đi OpenAI bằng mock |
| E2E bằng trình duyệt | **CHƯA XÁC MINH** | Môi trường chạy trình duyệt chặn truy cập local/static URL |

## Kịch bản bao phủ tự động

- Chặn Candidate và Employer truy cập API Admin.
- Tìm/lọc user, tổng quan Admin, khóa và mở khóa user; user bị khóa không dùng được JWT.
- Xem hồ sơ ứng viên, kỹ năng, CV PDF của ứng viên đã ứng tuyển.
- Chặn Employer B xem hồ sơ/CV của Employer A; chặn Candidate và Admin dùng API Employer.
- Cập nhật trạng thái đơn, Candidate thấy trạng thái mới trong `GET /applications/me`.
- Phân tích CV không lưu, phân tích lưu sau khi ứng tuyển, Candidate chỉ xem AI của mình.
- Kiểm tra yêu cầu đồng ý khi dùng OpenAI mode; test mock đảm bảo API không gọi nhà cung cấp nếu thiếu đồng ý.
- Kiểm duyệt ẩn và khôi phục tin, chặn Employer tự hiện lại tin bị Admin ẩn.
- Chống ứng tuyển trùng, chặn `ai_match_score` ngoài 0–100.
- Kiểm tra các trang/giao diện tĩnh có thể truy cập và API cần đăng nhập trả HTTP 401.

## Cần làm trước khi nghiệm thu trên môi trường thật

1. Cài dependencies đầy đủ qua `pip install -r requirements.txt`, tạo MySQL theo `database/schema.sql` và thiết lập `.env`.
2. Lặp lại kịch bản demo `docs/SPRINT3_HANDOFF.md` bằng 3 loại tài khoản thực, trên MySQL 8.x.
3. Test trình duyệt Chrome và Edge tại `/static/admin.html`, `/static/employer.html`, `/static/ai.html`.
4. Nếu bật OpenAI, cấu hình key hợp lệ, có đồng ý người dùng và chạy thử với CV không chứa dữ liệu cá nhân thực.
5. Kiểm tra sao lưu phục hồi, quyền truy cập file CV, log quản trị, giới hạn kích thước PDF và cấu hình CORS/HTTPS khi triển khai.
