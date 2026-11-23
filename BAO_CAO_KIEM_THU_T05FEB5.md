# BÁO CÁO KIỂM THỬ TỔNG THỂ HỆ THỐNG UNICAREER
**Dự án:** Hệ thống Hướng nghiệp & Tuyển dụng Sinh viên (UniCareer)  
**Mã Task:** `T05FEB5`  
**Tên Task:** Kiểm thử tổng thể  
**Mô tả:** Chạy thử các luồng chính từ đăng nhập đến ứng tuyển và quản trị  
**Người thực hiện:** Đỗ Hoàng Sơn (TV2 - PTIT-HCM-066)  
**Thời gian thực hiện:** 23/11/2026  
**Trạng thái:** ✅ **HOÀN THÀNH (100% PASSED)**

---

## 1. MỤC TIÊU VÀ PHẠM VI KIỂM THỬ

Mục tiêu của đợt kiểm thử tổng thể (System & End-to-End Testing) nhằm xác thực toàn bộ các phân hệ đã tích hợp của nền tảng UniCareer, đảm bảo các luồng dữ liệu liên kết thông suốt từ đầu đến cuối giữa các nhóm người dùng:
1. **Sinh viên / Ứng viên (Candidate):** Đăng ký, đăng nhập, hoàn thiện hồ sơ, tìm kiếm việc làm, nộp đơn ứng tuyển, kiểm tra trạng thái đơn.
2. **Nhà tuyển dụng / Doanh nghiệp (Employer & Company):** Đăng ký tài khoản, quản lý thông tin doanh nghiệp, đăng và quản trị tin tuyển dụng, tiếp nhận và duyệt đơn ứng viên.
3. **Quản trị viên (Admin):** Giám sát các chỉ số hệ thống trên Dashboard, kiểm duyệt nội dung tin tuyển dụng trước khi công khai, quản lý trạng thái tài khoản người dùng (khóa/mở khóa).

---

## 2. BẢNG TỔNG HỢP KẾT QUẢ KIỂM THỬ THEO LUỒNG NGHIỆP VỤ

### Kịch bản 1: Xác thực & Phân quyền người dùng (Authentication & RBAC)
| Mã TC | Tên ca kiểm thử | Mô tả & Dữ liệu đầu vào | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **TC01** | Đăng ký tài khoản Sinh viên | Email hợp lệ, mật khẩu $\ge$ 6 ký tự, vai trò `CANDIDATE` | HTTP 201, tự động tạo bản ghi trong bảng `users` và `candidates` | Khởi tạo thành công hồ sơ ứng viên | ✅ PASS |
| **TC02** | Đăng ký tài khoản Doanh nghiệp | Email hợp lệ, vai trò `EMPLOYER`, tên công ty | HTTP 201, tự động tạo bản ghi trong bảng `users` và `companies` | Khởi tạo thành công hồ sơ doanh nghiệp | ✅ PASS |
| **TC03** | Đăng nhập cấp Token | Email và mật khẩu chính xác | HTTP 200, cấp Bearer Token và trả về đúng vai trò của người dùng | Nhận token và thông tin phiên | ✅ PASS |
| **TC04** | Bảo mật xác thực | Thử đăng nhập sai mật khẩu / đăng ký trùng email | HTTP 401 khi sai mật khẩu; HTTP 400 khi trùng email | Chặn chính xác các vi phạm xác thực | ✅ PASS |

---

### Kịch bản 2: Hồ sơ sinh viên & Quản lý kỹ năng / CV (Candidate Profile)
| Mã TC | Tên ca kiểm thử | Mô tả & Dữ liệu đầu vào | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **TC05** | Xem & Cập nhật hồ sơ | Chỉnh sửa họ tên, số điện thoại, trường học, chuyên ngành, kỹ năng và CV | HTTP 200, lưu trữ bền vững vào CSDL, phản ánh chính xác khi truy vấn | Cập nhật hồ sơ sinh viên thành công | ✅ PASS |

---

### Kịch bản 3: Quản lý tin tuyển dụng của Doanh nghiệp (Job Management)
| Mã TC | Tên ca kiểm thử | Mô tả & Dữ liệu đầu vào | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **TC06** | Đăng & Cập nhật tin tuyển dụng | Doanh nghiệp tạo tin tuyển dụng mới với đầy đủ vị trí, mô tả, yêu cầu, hạn nộp | HTTP 201 khi tạo mới, HTTP 200 khi cập nhật mức lương và nội dung | Đăng tin và cập nhật thành công | ✅ PASS |

---

### Kịch bản 4: Tìm kiếm, lọc và xem chi tiết việc làm (Job Search)
| Mã TC | Tên ca kiểm thử | Mô tả & Dữ liệu đầu vào | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **TC07** | Tìm kiếm & Chi tiết công việc | Tìm theo từ khóa `"Backend"`, lọc theo địa điểm `"TP. Hồ Chí Minh"` | HTTP 200, trả về danh sách việc làm phù hợp và xem chi tiết tin | Tìm kiếm và xem chi tiết chính xác | ✅ PASS |

---

### Kịch bản 5: Quy trình ứng tuyển liên kết End-to-End (Application Workflow)
| Mã TC | Tên ca kiểm thử | Mô tả & Dữ liệu đầu vào | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **TC08** | Nộp đơn ứng tuyển & Điểm AI | Sinh viên gửi hồ sơ vào tin tuyển dụng đang mở | HTTP 201, sinh đơn ứng tuyển với trạng thái `RECEIVED`, AI tính điểm độ phù hợp | Nộp đơn thành công, điểm AI: 90% | ✅ PASS |
| **TC09** | Ràng buộc chống nộp trùng | Thử gửi thêm đơn vào cùng một vị trí đã nộp | HTTP 400, thông báo *"Bạn đã nộp hồ sơ ứng tuyển vào vị trí này rồi."* | Ngăn chặn nộp trùng thành công | ✅ PASS |
| **TC10** | Theo dõi đơn ứng tuyển cá nhân | Sinh viên tra cứu lịch sử các đơn đã gửi | HTTP 200, danh sách hiển thị tên việc làm, công ty và trạng thái hiện tại | Hiển thị chính xác đơn ứng tuyển | ✅ PASS |
| **TC11** | Nhà tuyển dụng duyệt đơn | Doanh nghiệp xem ứng viên và cập nhật trạng thái `REVIEWING` $\to$ `ACCEPTED` | HTTP 200, trạng thái được cập nhật; phía sinh viên thấy kết quả đổi tức thì | Duyệt hồ sơ và đồng bộ 2 chiều thành công | ✅ PASS |

---

### Kịch bản 6: Quản trị hệ thống & Kiểm duyệt tin đăng (Admin Management)
| Mã TC | Tên ca kiểm thử | Mô tả & Dữ liệu đầu vào | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **TC12** | Thống kê tổng thể Dashboard | Admin truy vấn thống kê toàn hệ thống qua `/api/admin/stats` | HTTP 200, trả về chính xác số người dùng, việc làm, doanh nghiệp, đơn ứng tuyển | Số liệu thống kê đồng bộ chuẩn xác | ✅ PASS |
| **TC13** | Kiểm duyệt tin tuyển dụng | Admin xem xét tin trong hàng đợi `PENDING` và phê duyệt `APPROVED` | HTTP 200, tin chuyển sang trạng thái đã duyệt và xuất hiện công khai | Kiểm duyệt tin thành công | ✅ PASS |
| **TC14** | Khóa & Mở khóa tài khoản | Admin khóa tài khoản vi phạm và khôi phục khi cần | Khóa tài khoản thành công; chặn đăng nhập với HTTP 403; mở khóa đăng nhập bình thường | Kiểm soát tài khoản người dùng an toàn | ✅ PASS |

---

## 3. KẾT LUẬN

- Toàn bộ các luồng chức năng chính từ **Đăng nhập $\to$ Hồ sơ $\to$ Tìm việc $\to$ Ứng tuyển $\to$ Doanh nghiệp duyệt đơn $\to$ Quản trị hệ thống** đã được kiểm thử toàn diện và hoạt động ổn định, chính xác.
- Đạt tiêu chuẩn nghiệm thu của Task `T05FEB5` và sẵn sàng báo cáo tiến độ Sprint 4.
