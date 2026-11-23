# UniCareer – Bàn giao Sprint 3

Nguồn phạm vi: tài liệu `SRS.docx` – UniCareer SRS 1.1, ngày 01/11/2026; ảnh bảng task Sprint 3 do nhóm cung cấp.

## 1. Đối chiếu 7 task

| Task trên bảng | API / giao diện đã triển khai | SRS liên quan | Kiểm thử |
| --- | --- | --- | --- |
| Xây dựng chức năng quản lý người dùng | `GET /admin/users`, `PATCH /admin/users/{id}/status`, `GET /admin/overview`, `static/admin.html` | FR-04, FR-20, AC-02, AC-08 | `test_admin_manage_users_and_overview` |
| Xây dựng chức năng kiểm duyệt tin | `GET /admin/jobs`, `PATCH /admin/jobs/{id}/moderate`, bộ lọc và xác nhận trên trang Admin | FR-21, AC-08 | `test_admin_moderation_and_employer_cannot_unhide` |
| Kiểm tra chức năng quản trị | Phân quyền Admin trên backend, chặn tự khóa, tài khoản bị khóa không dùng được token; audit log Admin | FR-20, FR-21, NFR-05/06/10 | `test_admin_manage_users_and_overview`, `test_admin_moderation_and_employer_cannot_unhide`, `test_static_pages_and_unauthorized_api` |
| Xây dựng chức năng xem hồ sơ ứng tuyển | `GET /employer/jobs/{id}/applications`, `GET /employer/applications/{id}`, `GET /employer/applications/{id}/cv`, `static/employer.html` | FR-17, FR-19, AC-06 | `test_employer_candidate_profile_and_isolation`, `test_cv_upload_and_protected_download` |
| Cập nhật trạng thái đơn ứng tuyển | `PATCH /employer/applications/{id}/status`, `GET /applications/me`, chọn trạng thái tại trang Employer và xem lại từ Candidate | FR-18, FR-22, AC-07 | `test_change_application_status_and_candidate_sees_update` |
| Tích hợp phân tích CV bằng AI | `POST /ai/analyze`, chế độ `rules` hoặc OpenAI API, nhập text hoặc PDF, lưu điểm/nhận xét trong `applications` | FR-23, FR-24 (mở rộng) | `test_ai_preview_save_retrieve_and_privacy`, `test_ai_real_provider_consent_and_mocked_inference` |
| Hiển thị kết quả phân tích AI | `static/ai.html` hiển thị điểm, kỹ năng phù hợp/thiếu, gợi ý; xem lại qua `GET /applications/me` tại trang Candidate | FR-24 | `test_ai_preview_save_retrieve_and_privacy` |

## 2. Các nguyên tắc quan trọng

- Giữ nguyên **5 bảng** của phần 10 trong SRS, không thêm bảng phụ.
- Một ứng viên chỉ có tối đa một đơn trên một tin: `UNIQUE(job_id, candidate_id)`.
- Nhà tuyển dụng chỉ xem hồ sơ ứng tuyển thuộc **công ty của chính mình**. Candidate và Admin không dùng được các API Employer.
- Chỉ Candidate đọc được điểm AI của **đơn của mình** qua `GET /applications/me`. Dữ liệu AI không đưa vào API đọc ứng viên phía Employer.
- `RECEIVED`, `REVIEWING`, `MATCHED`, `REJECTED` là trạng thái đơn do Employer cập nhật. AI **không** thay đổi trạng thái hoặc quyết định tuyển dụng.
- Admin có thể ẩn tin `HIDDEN`. Employer không thể tự kích hoạt lại tin bị ẩn. Tin `CLOSED` không được Admin tự mở lại. Phân biệt nguồn ẩn chi tiết cần nâng cấp schema về sau nếu có yêu cầu.
- Với `AI_PROVIDER=rules`, hệ thống chỉ dò kỹ năng theo từ khóa (không phải mô hình học máy). Với `AI_PROVIDER=openai`, backend gửi CV tới OpenAI API **chỉ khi Candidate đồng ý**.
- Không lưu mật khẩu thô, không đặt API key ở frontend. JWT hết hạn theo cấu hình. Đăng xuất client xóa token; bản MVP chưa có thu hồi token server-side.

## 3. Chạy hệ thống trên MySQL

Tại thư mục gốc sau khi giải nén:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Mở `database/schema.sql` trong MySQL Workbench, chạy toàn bộ script. Cấu hình `.env`:

```env
DATABASE_URL=mysql+pymysql://root:YOUR_URL_ENCODED_PASSWORD@127.0.0.1:3306/unicareer?charset=utf8mb4
JWT_SECRET=REPLACE_WITH_A_RANDOM_SECRET_AT_LEAST_32_CHARACTERS
AI_PROVIDER=rules
```

Tạo khóa bí mật ngẫu nhiên:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Tạo Admin, chạy API:

```powershell
python create_admin.py --email admin@example.com
uvicorn app.main:app --reload
```

| Trang | URL |
| --- | --- |
| Trang chủ, đăng ký, đăng nhập và đơn ứng tuyển Candidate | `http://127.0.0.1:8000/` |
| Quản trị | `http://127.0.0.1:8000/static/admin.html` |
| Nhà tuyển dụng | `http://127.0.0.1:8000/static/employer.html` |
| Phân tích CV | `http://127.0.0.1:8000/static/ai.html` |
| Swagger | `http://127.0.0.1:8000/docs` |

## 4. Kịch bản demo 7 task

1. Admin: đăng nhập, mở `admin.html`, xem thống kê, lọc email/role, thử khóa user; user bị khóa không được gọi API. Mở khóa để tiếp tục.
2. Employer A: đăng ký, mở `employer.html`, cập nhật công ty, tạo tin tuyển dụng còn hạn. Employer B đăng ký như một công ty khác.
3. Candidate: đăng ký, cập nhật hồ sơ qua `PATCH /candidates/me` ở Swagger, tải PDF CV trên `ai.html` (hoặc chỉ nhập CV dạng text), ứng tuyển từ trang chủ.
4. Employer A: chọn tin, mở danh sách đơn, xem chi tiết hồ sơ. Nhấn “Xem CV PDF” nếu Candidate đã upload. Employer B không thể truy cập đơn thuộc A (404).
5. Employer A: đổi trạng thái `RECEIVED` → `REVIEWING`, Candidate trở lại trang chủ xem trạng thái mới.
6. Candidate: mở `ai.html`, chọn tin, nhập CV, phân tích và xem điểm/kỹ năng/gợi ý. Để lưu: chọn `Lưu kết quả vào đơn ứng tuyển hiện có`; cần ứng tuyển trước khi lưu.
7. Candidate: nhấn “Xem kết quả đã lưu”, hoặc xem mục “Đơn ứng tuyển của tôi” tại trang chủ. Admin ẩn tin; danh sách công khai không còn hiển thị tin đó, nhưng dữ liệu đơn vẫn còn.

## 5. Cách kiểm thử

```powershell
python -m pytest -q
```

Có **12 bài test**, 10 bài Sprint 3 + 2 bài API gốc. Test chạy trên SQLite cô lập, dùng mật khẩu giả lập **chỉ trong test** để không cần server MySQL thực. Bản chạy production sử dụng `bcrypt` (phải cài requirements đầy đủ). Đây là kiểm thử API tự động, **không phải** kiểm thử browser end-to-end hoặc xác nhận toàn bộ trên MySQL 8.

## 6. OpenAI thật – nếu nhóm có API key

Thêm vào `.env`:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=YOUR_SERVER_SIDE_KEY
OPENAI_MODEL=gpt-5.5
```

Khởi động lại FastAPI. Candidate phải đánh dấu đồng ý trên giao diện, hoặc gửi `consent_to_external_processing=true` qua API. Key không được xuất hiện trong mã JavaScript hay commit Git. Chỉ gửi CV khi có quyền và sự chấp thuận phù hợp, vì CV có thể chứa dữ liệu cá nhân. Phải tự kiểm thử model/key/quyền truy cập thật; bài test mock xác nhận đường đi và yêu cầu consent, không chứng minh API thực đã gọi thành công.

## 7. Phạm vi chưa được xác minh và cải tiến kế tiếp

- Chưa có môi trường MySQL Server và API key OpenAI trong phiên tạo mã nguồn này, nên chưa có smoke test trực tiếp trên MySQL/OpenAI.
- Đã kiểm tra cú pháp JS bằng Node và API với FastAPI TestClient; chưa chạy automation giao diện thực trên các trình duyệt.
- SRS phần 10 không có các cột loại hình việc làm, kinh nghiệm, quyền lợi dạng riêng; các chức năng lọc tương ứng chưa có dữ liệu để triển khai đầy đủ.
- Trạng thái `HIDDEN` chưa phân biệt được ai thực hiện việc ẩn; việc tự khôi phục tin do Employer ẩn hiện yêu cầu Admin.
- Nhật ký quản trị được lưu dạng file `logs/admin_actions.jsonl`; cần backup và kiểm soát quyền truy cập log. Sản phẩm thực cần thêm cơ chế audit bền vững, rate limiting, chống virus upload, quản lý/thu hồi JWT và kiểm thử tải.
- Khi có MySQL và OpenAI thật, chạy lại toàn bộ luồng đăng ký → ứng tuyển → AI → duyệt → Admin trên môi trường staging trước khi nghiệm thu.
