# UniCareer

UniCareer kết nối sinh viên với các cơ hội việc làm, đồng thời cung cấp quy trình làm việc cho nhà tuyển dụng và quản trị viên.

## Quy trình làm việc tích hợp

- Ứng viên có thể duyệt và lọc các công việc đã được phê duyệt, duy trì thông tin tài khoản riêng biệt với nhiều phiên bản CV có cấu trúc, ứng tuyển một lần cho mỗi công việc và theo dõi trạng thái ứng tuyển.
- Nhà tuyển dụng có thể quản lý hồ sơ công ty và tin tuyển dụng của họ, xem xét đơn ứng tuyển, xem CV ứng tuyển và cập nhật trạng thái đơn ứng tuyển.
- Quản trị viên có thể phê duyệt hoặc từ chối tin tuyển dụng và kích hoạt hoặc vô hiệu hóa tài khoản.
- Danh sách việc làm công khai chỉ bao gồm các công việc đang hoạt động, đã được phê duyệt và chưa hết hạn. Dữ liệu của nhà tuyển dụng và tải xuống CV bị hạn chế theo quyền sở hữu và vai trò.

## Chạy cục bộ (Windows PowerShell)

1. Tạo một cơ sở dữ liệu MySQL có tên `unicareer_db`.
2. Từ thư mục gốc dự án `DuAn_Nhom8-main`, tạo và kích hoạt môi trường ảo, sau đó cài đặt các gói phụ thuộc backend:

   ```powershell
   python -m venv backend\.venv
   .\backend\.venv\Scripts\Activate.ps1
   python -m pip install -r backend\requirements.txt
   Copy-Item backend\.env.example backend\.env
   ```

3. Chỉnh sửa `backend\.env` và đặt `DATABASE_URL` cùng với một `SECRET_KEY` riêng tư có ít nhất 32 ký tự. Tạo một khóa bằng lệnh `python -c "import secrets; print(secrets.token_urlsafe(48))"`. API sẽ từ chối khởi động nếu thiếu cấu hình bắt buộc hoặc khóa bí mật quá ngắn. Giữ `.env` ngoài quyền quản lý mã nguồn. Để bật phân tích CV, hãy thêm khóa Gemini API dưới dạng `GEMINI_API_KEY`; `GEMINI_MODEL` mặc định là `gemini-3.5-flash-lite`. Ứng viên có thể tạo CV bằng trình tạo hoặc tải lên tệp PDF/DOCX tối đa 10 MB. Cả hai loại đều có thể được phân tích sau khi có sự đồng ý rõ ràng.
4. Khởi động API từ thư mục gốc dự án:

   ```powershell
   Set-Location backend
   uvicorn app.main:app --reload
   ```

5. Mở `http://127.0.0.1:8000/frontend/index.html`. Tài liệu API có sẵn tại `http://127.0.0.1:8000/docs`.

Ứng dụng sẽ tạo các bảng còn thiếu và gieo mầm các vai trò candidate, employer và admin khi khởi động. Ứng dụng không tạo tài khoản quản trị viên. Để cấp quyền cho một tài khoản, trước tiên hãy đăng ký một tài khoản đáng tin cậy, sau đó chạy câu lệnh SQL sau trong cơ sở dữ liệu đã cấu hình, thay thế email:

```sql
UPDATE users SET role = 'admin' WHERE email = 'admin@example.com';
DELETE FROM user_roles
WHERE user_id = (SELECT id FROM users WHERE email = 'admin@example.com');
INSERT INTO user_roles (user_id, role_id)
SELECT users.id, roles.id
FROM users
JOIN roles ON roles.name = 'admin'
WHERE users.email = 'admin@example.com';
```

Đăng xuất và đăng nhập lại sau khi cấp quyền để tài khoản nhận vai trò quản trị viên trong phiên làm việc của mình.

Phân tích CV chỉ gửi nội dung CV đã chọn và mô tả công việc đến Google Gemini sau khi ứng viên đồng ý rõ ràng. Ứng viên có thể chọn riêng để cho phép nhà tuyển dụng phân tích CV đính kèm với đơn ứng tuyển. Phân tích mang tính chất tham khảo, không phải là quyết định tuyển dụng và kết quả của nó được lưu trữ trong cơ sở dữ liệu ứng dụng. Không bật tính năng này nếu chưa thông báo cho người dùng về việc xử lý dữ liệu của Google.

## Chạy các bài kiểm thử quy trình backend

Từ thư mục gốc dự án:

```powershell
python -m pip install -r backend\requirements-test.txt
python -m pytest backend\tests
```

Các bài kiểm thử quy trình sử dụng SQLite và giả lập (mock) phản hồi Gemini; chúng không yêu cầu máy chủ MySQL hoặc khóa Gemini API.
