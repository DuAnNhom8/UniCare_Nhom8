# UniCareer – Nhóm 8

Ứng dụng tìm việc và định hướng nghề nghiệp cho sinh viên. Mã nguồn gốc được giữ nguyên theo hai thư mục **backend** và **frontend**. Bản cập nhật giữ các chức năng Sprint 2–3 trước đó và **bổ sung 4 task Sprint 3: kiểm tra ứng tuyển trùng, nộp đơn, xem đơn đã nộp, tích hợp frontend/backend với JWT và CV PDF**.

## 1. Công nghệ

- **Backend:** Python, FastAPI, SQLAlchemy (ORM), Pydantic, PyMySQL, PyJWT, python-multipart.
- **CSDL chính:** MySQL (không tự động thay bằng SQLite khi kết nối lỗi).
- **Frontend:** HTML, CSS, JavaScript thuần (Fetch API).
- **Môi trường:** VS Code, MySQL Workbench hoặc MySQL CLI.

## 2. Cài đặt lần đầu trên Windows (PowerShell)

Mở thư mục **UniCare_Nhom8-main** (thư mục gốc chứa `backend/` và `frontend/`) trong VS Code. Mở terminal tại thư mục gốc này.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
```

Nếu PowerShell chặn Activate.ps1, có thể dùng `Set-ExecutionPolicy -Scope Process Bypass` chỉ cho terminal hiện tại, rồi chạy lệnh activate. Hoặc gọi trực tiếp `.\.venv\Scripts\python.exe`.

Sửa **backend/.env** bằng tài khoản MySQL trên máy, ví dụ:

```ini
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=mat_khau_mysql_cua_ban
DB_NAME=unicareer_db
```

Cần thêm **JWT_SECRET_KEY** bằng khóa ngẫu nhiên trước khi dùng API đăng nhập/ứng tuyển. Sinh khóa trong terminal:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Dán kết quả vào `JWT_SECRET_KEY=...` trong `backend/.env` (không để giá trị `CHANGE_ME...`). Không commit `.env` lên GitHub; `.env` đã được `.gitignore` bỏ qua.

### Khởi tạo database

**Cách 1 – MySQL Workbench:** mở file `backend/database/schema_tv2.sql`, chạy toàn bộ script. Sau đó mở và chạy `backend/database/schema_applications.sql`. Script 1 tạo `users`, `companies`, `job_posts`; script 2 bổ sung `cvs`, `applications`. Có thể chạy script nhiều lần, tuy nhiên dữ liệu demo cũ sẽ được giữ nguyên.

**Cách 2 – MySQL CLI** (tại thư mục gốc):

```powershell
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS unicareer_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
Get-Content backend\database\schema_tv2.sql | mysql -u root -p --default-character-set=utf8mb4
Get-Content backend\database\schema_applications.sql | mysql -u root -p --default-character-set=utf8mb4
```

Lưu ý: hai lệnh gọi `mysql` có thể yêu cầu nhập mật khẩu riêng. Bạn cũng có thể chạy script qua chức năng **Run SQL Script** của Workbench. Nếu chỉ cần thử bản mới, tạo database trống và khởi động FastAPI sẽ tự tạo các bảng và 4 tin mẫu; không cần chạy SQL seed thủ công. Trong môi trường production, nên dùng công cụ migration thay cho `create_all`.

## 3. Chạy trên VS Code

Tại **thư mục gốc** dự án (không `cd backend`):

```powershell
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Mở trong trình duyệt:

| Trang | Địa chỉ |
|---|---|
| Website | http://127.0.0.1:8000/frontend/index.html |
| Danh sách việc làm | http://127.0.0.1:8000/frontend/pages/candidate/index.html |
| Swagger / API Docs | http://127.0.0.1:8000/docs |
| Danh sách qua API | http://127.0.0.1:8000/api/jobs/public |
| Trạng thái API | http://127.0.0.1:8000/health |

**Nên dùng trang `/frontend/...` do FastAPI phục vụ** để JavaScript gọi đúng `/api` trên cùng cổng. Nếu dùng extension Live Server (thường :5500) cũng có cấu hình hỗ trợ khi FastAPI vẫn đang chạy ở :8000. Không mở trực tiếp bằng `file://`.

Nếu hiện `Không thể khởi tạo CSDL`, kiểm tra MySQL đã chạy, tài khoản/mật khẩu trong `.env`, tên database, quyền kết nối, cổng `3306` và thư viện đã cài đặt. Ứng dụng **không âm thầm chuyển sang SQLite** nữa.

## 4. Chức năng đã thêm

| Task | Backend | Frontend |
|---|---|---|
| CSDL việc làm & ứng tuyển | `models/job.py`, `models/application.py`, `database/schema_applications.sql` | — |
| Danh sách việc làm | `GET /api/jobs/public` | `pages/candidate/index.html`, `assets/js/candidate.js` |
| Tìm kiếm, lọc | `services/job_service.py` (lọc SQL, phân trang) | Thanh tìm kiếm, địa điểm, loại hình, lương, sắp xếp |
| Xem chi tiết | `GET /api/jobs/public/{job_id}` | `pages/candidate/job-detail.html?id=1` |
| Kiểm tra chức năng | `tests/test_public_jobs.py` | Thử qua giao diện và Swagger |

API ứng viên chỉ hiển thị tin **ACTIVE + APPROVED + deadline >= ngày hiện tại**. Tìm kiếm qua `keyword` trong tiêu đề/mô tả/yêu cầu/tên doanh nghiệp; `location` tìm gần đúng; `job_type` nhận `FULL_TIME`, `PART_TIME`, `INTERNSHIP`; `salary` nhận `paid` hoặc `negotiable`; `sort` nhận `latest` hoặc `deadline`. Kết quả gồm `items`, `total`, `skip`, `limit`.

Ví dụ:

- `/api/jobs/public?keyword=Python`
- `/api/jobs/public?location=Hà%20N%E1%BB%99i&job_type=INTERNSHIP`
- `/api/jobs/public?sort=deadline&skip=0&limit=2`
- `/api/jobs/public/1`

Nếu nhập URL chi tiết với ID của tin chưa duyệt, hết hạn hoặc không tồn tại, API trả `404` và giao diện hiển thị thông báo phù hợp.

## 5. Chạy kiểm thử tự động

```powershell
python -m pip install -r backend\requirements-dev.txt
python -m pytest tests -q
```

Bộ kiểm thử dùng SQLite **tạm thời chỉ trong lúc test** (không thay đổi database MySQL). Nội dung: danh sách công khai, ẩn/đóng/chưa duyệt/hết hạn, tìm kiếm và bộ lọc, phân trang/sắp xếp, chi tiết/404, dữ liệu không hợp lệ, tạo bảng `cvs`/`applications`, và tính tương thích API doanh nghiệp hiện có.

### Kiểm tra thủ công (Sprint 3)

1. Chạy server và mở danh sách; đảm bảo xuất hiện tin từ API, không phải thẻ mẫu HTML.
2. Tìm `Backend`: phải chỉ còn tin Backend; tìm chữ không tồn tại: thông báo trống.
3. Lọc `Hà Nội`: chỉ có tin ở Hà Nội; chọn `Thực tập` và `Có hỗ trợ lương`: kết quả phù hợp.
4. Chọn sắp xếp theo hạn nộp gần nhất, kiểm tra thứ tự; thử lọc đồng thời với từ khóa.
5. Bấm **Xem chi tiết** để xem đúng tiêu đề, mô tả, yêu cầu, công ty, địa điểm và hạn nộp từ API.
6. Dùng `/docs` hoặc Postman để đổi trạng thái một tin sang `HIDDEN`, hoặc đổi `approval_status` sang `PENDING`, rồi tải lại danh sách; tin sẽ không còn công khai.
7. Tắt FastAPI để kiểm tra thông báo lỗi kết nối; không hiển thị dữ liệu demo giả thay cho dữ liệu thật.

## 6. Sprint 3 – 4 task chức năng ứng tuyển

### Luồng sử dụng thực tế

1. Mở `/frontend/pages/auth/register.html` để đăng ký **ứng viên** (role `CANDIDATE`).
2. Sau khi tạo tài khoản, trang tự đăng nhập. Mở `/frontend/pages/candidate/cv-manage.html` để tải CV PDF (tối đa 5 MB).
3. Mở danh sách việc làm → chi tiết → **Ứng tuyển**; hệ thống kiểm tra đã nộp hay chưa, chọn CV có sẵn hoặc tải CV mới, thêm thư giới thiệu, bấm **Gửi hồ sơ ứng tuyển**.
4. Nếu đã ứng tuyển, API trả **409 Conflict** và giao diện thông báo không thể nộp trùng. CSDL đã có `UNIQUE(candidate_id, job_id)` chống trường hợp hai yêu cầu đồng thời.
5. Mở `/frontend/pages/candidate/my-applications.html` để xem các đơn của **tài khoản đang đăng nhập** cùng trạng thái.

### API bổ sung

| Phương thức | Endpoint | Mục đích |
|---|---|---|
| POST | `/api/auth/register` | Tạo ứng viên/nhà tuyển dụng; không cho phép tự đăng ký admin |
| POST | `/api/auth/login` | Nhận JWT bearer (hết hạn sau 2 giờ) |
| GET | `/api/auth/me` | Xem thông tin tài khoản theo JWT |
| POST | `/api/candidate/cvs` | Tải CV PDF với Multipart Form (field `file`) |
| GET | `/api/candidate/cvs` | Danh sách CV của chính ứng viên |
| GET | `/api/candidate/cvs/{cv_id}/download` | Tải CV riêng tư, kiểm tra chủ sở hữu |
| GET | `/api/candidate/applications/check/{job_id}` | Kiểm tra ứng tuyển trùng |
| POST | `/api/candidate/applications` | Gửi đơn: `job_id`, `cv_id`, `cover_letter` |
| GET | `/api/candidate/applications` | Danh sách đơn riêng tư, phân trang `skip`, `limit` |

Các API `/api/candidate/*` chỉ dành cho tài khoản **CANDIDATE** đã xác thực. Không sử dụng `candidate_id` do trình duyệt gửi. API chỉ cho nộp khi tin tuyển dụng **ACTIVE / APPROVED / còn hạn** và CV thuộc ứng viên đó.

### CSDL và lưu trữ

- Giữ **nguyên schema hiện có**: bảng `users`, `companies`, `job_posts`, `cvs`, `applications`. Không cần thêm bảng/column mới so với bản Sprint trước.
- Nếu chưa có các bảng, chạy `backend/database/schema_tv2.sql` rồi `schema_applications.sql` trong MySQL Workbench (hoặc dùng `create_all` trên database trống).
- CV lưu dưới `backend/private_uploads/` (đã được `.gitignore` loại trừ, **không** nằm trong thư mục `frontend/`). Có thể đặt biến `CV_STORAGE_DIR` để chọn vị trí riêng tư khác. Chỉ tải về sau khi xác thực chủ sở hữu.
- Mật khẩu đăng ký mới được băm PBKDF2-HMAC-SHA256 có salt, **khác BCrypt**. Dữ liệu demo có mật khẩu giả không dùng để đăng nhập. Khi ghép với phân hệ xác thực của nhóm, cần thống nhất cách băm mật khẩu và JWT trước khi triển khai chung.

### Kiểm thử tự động

```powershell
python -m pip install -r backend\requirements-dev.txt
python -m pytest tests -q
```

Bản này hiện có **11 bài kiểm thử** sử dụng SQLite tạm để test, không động chạm MySQL thật. Kiểm thử các tình huống: đăng ký, đăng nhập, phân quyền, CV riêng tư, tệp PDF giả, tệp quá lớn, gửi đơn thành công, gửi trùng (409), CV khác chủ sở hữu (404), lịch sử riêng tư, trang HTML.

## 7. Phạm vi chưa triển khai / cần kiểm tra trên máy của bạn

- **Cần kiểm tra trực tiếp MySQL trên máy của bạn**: các bài test chạy SQLite tạm và không thay thế kiểm thử MySQL/VS Code. Không có quyền truy cập MySQL cá nhân của bạn trong phiên này.
- Phân hệ **doanh nghiệp xem và duyệt đơn ứng tuyển**, cập nhật trạng thái `REVIEWING/ACCEPTED/REJECTED`, hồ sơ cá nhân đầy đủ, và công cụ AI chưa được tích hợp trong lượt này.
- API doanh nghiệp/tuyển dụng vốn có ở bản gốc (tạo/sửa/xóa tin) **chưa bảo vệ bằng JWT**; chỉ dùng trong môi trường lớp học / máy nội bộ. Không public internet trước khi hoàn thiện xác thực và phân quyền các phân hệ còn lại.
- Chưa có giới hạn tốc độ đăng nhập, email verification, quên mật khẩu thực, quét virus cho CV. Hệ thống kiểm tra phần mở đầu PDF và kích thước 5 MB; cần tăng cường an toàn trước production.
- Chỉ tài khoản mới đăng ký theo cơ chế PBKDF2 trong bản này đăng nhập được; tài khoản mẫu hoặc mật khẩu từ phân hệ khác cần thống nhất thuật toán trước khi ghép nhánh.
