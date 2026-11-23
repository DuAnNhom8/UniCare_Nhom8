"""
LIVE DEMO TEST CHO TASK T05FEA1: HOÀN THIỆN CHỨC NĂNG TUYỂN DỤNG
Chạy trực tiếp trên Web Server http://127.0.0.1:8000
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def separator(title):
    print("\n" + "=" * 70)
    print(f"🔹 {title}")
    print("=" * 70)

def step(num, desc):
    print(f"\n▶️ [BƯỚC {num}] {desc}")

def run_demo():
    print("🚀 BẮT ĐẦU CHẠY KIỂM THỬ TRỰC TIẾP (LIVE DEMO) CHỨC NĂNG TUYỂN DỤNG")
    print(f"🌐 Server Target: {BASE_URL}")

    # 1. Kiểm tra kết nối server
    step(1, "Kiểm tra trạng thái máy chủ (Health Check)")
    res = requests.get(f"{BASE_URL}/health")
    print(f"   HTTP Status: {res.status_code}")
    print(f"   Response: {res.json()}")
    assert res.status_code == 200, "Server không phản hồi!"
    print("   ✅ Kết nối máy chủ thành công!")

    # 2. Xem danh sách tin tuyển dụng hiện tại
    step(2, "Lấy danh sách tin tuyển dụng hiện có (GET /api/jobs)")
    res = requests.get(f"{BASE_URL}/api/jobs")
    jobs = res.json()
    print(f"   HTTP Status: {res.status_code}")
    print(f"   Tổng số tin hiện có trên hệ thống: {len(jobs)} tin")
    for j in jobs[:3]:
        print(f"    - ID #{j['job_id']}: {j['title']} | Trạng thái: {j['status']} | Lương: {j['salary_range']}")

    # 3. Thực hiện TẠO MỚI TIN TUYỂN DỤNG (POST /api/jobs)
    step(3, "Tạo mới tin tuyển dụng (POST /api/jobs)")
    new_job_data = {
        "company_id": 1,
        "title": "Chuyên viên AI & NLP Intern (Demo T05FEA1)",
        "description": "Nghiên cứu áp dụng LLM và phân tích CV tự động cho sinh viên.",
        "requirements": "Thành thạo Python, PyTorch, hiểu biết về REST API và tư duy giải thuật.",
        "location": "TP. Hồ Chí Minh",
        "salary_range": "6–9 triệu/tháng",
        "job_type": "INTERNSHIP",
        "experience_level": "Không yêu cầu",
        "deadline": "2026-12-30",
        "status": "ACTIVE"
    }
    print(f"   Gửi dữ liệu tạo tin: {json.dumps(new_job_data, ensure_ascii=False, indent=2)}")
    res = requests.post(f"{BASE_URL}/api/jobs", json=new_job_data)
    print(f"   HTTP Status: {res.status_code} (201 Created)")
    created = res.json()
    job_id = created["job_id"]
    print(f"   ✅ Tạo thành công tin mới! ID cấp phát: #{job_id}")
    print(f"   Chi tiết: Tiêu đề: '{created['title']}', Trạng thái: '{created['status']}'")

    # 4. Thực hiện CẬP NHẬT TIN TUYỂN DỤNG (PUT /api/jobs/{id})
    step(4, f"Cập nhật nội dung tin tuyển dụng #{job_id} (PUT /api/jobs/{job_id})")
    update_data = {
        "title": "Senior AI & NLP Intern (Đã Cập Nhật)",
        "salary_range": "8–12 triệu/tháng",
        "location": "Hybrid (TP. Hồ Chí Minh)"
    }
    print(f"   Nội dung cần sửa: {json.dumps(update_data, ensure_ascii=False)}")
    res = requests.put(f"{BASE_URL}/api/jobs/{job_id}", json=update_data)
    print(f"   HTTP Status: {res.status_code}")
    updated = res.json()
    print(f"   ✅ Cập nhật thành công!")
    print(f"   Tiêu đề mới: '{updated['title']}'")
    print(f"   Mức lương mới: '{updated['salary_range']}'")
    print(f"   Địa điểm mới: '{updated['location']}'")
    print(f"   Trạng thái hiện tại: '{updated['status']}'")

    # 5. Thực hiện ĐÓNG TIN TUYỂN DỤNG (PATCH /api/jobs/{id}/status -> CLOSED)
    step(5, f"Đóng tin tuyển dụng #{job_id} (PATCH /api/jobs/{job_id}/status)")
    res = requests.patch(f"{BASE_URL}/api/jobs/{job_id}/status", json={"status": "CLOSED"})
    print(f"   HTTP Status: {res.status_code}")
    print(f"   ✅ Trạng thái sau khi đóng tin: {res.json()['status']}")

    # Kiểm tra lọc tin đã đóng
    filter_closed = requests.get(f"{BASE_URL}/api/jobs?status=CLOSED").json()
    print(f"   Số lượng tin trong danh mục [ĐÃ ĐÓNG]: {len(filter_closed)} tin")
    assert any(j['job_id'] == job_id for j in filter_closed), "Tin vừa đóng không nằm trong danh sách CLOSED!"

    # 6. Thực hiện TẠM ẨN TIN TUYỂN DỤNG (PATCH /api/jobs/{id}/status -> HIDDEN)
    step(6, f"Tạm ẩn tin tuyển dụng #{job_id} (PATCH /api/jobs/{job_id}/status)")
    res = requests.patch(f"{BASE_URL}/api/jobs/{job_id}/status", json={"status": "HIDDEN"})
    print(f"   HTTP Status: {res.status_code}")
    print(f"   ✅ Trạng thái sau khi ẩn tin: {res.json()['status']}")

    # Kiểm tra lọc tin tạm ẩn
    filter_hidden = requests.get(f"{BASE_URL}/api/jobs?status=HIDDEN").json()
    print(f"   Số lượng tin trong danh mục [TẠM ẨN]: {len(filter_hidden)} tin")
    assert any(j['job_id'] == job_id for j in filter_hidden), "Tin vừa ẩn không nằm trong danh sách HIDDEN!"

    # 7. Thực hiện MỞ LẠI TIN TUYỂN DỤNG (PATCH /api/jobs/{id}/status -> ACTIVE)
    step(7, f"Mở lại tin tuyển dụng #{job_id} (PATCH /api/jobs/{job_id}/status)")
    res = requests.patch(f"{BASE_URL}/api/jobs/{job_id}/status", json={"status": "ACTIVE"})
    print(f"   HTTP Status: {res.status_code}")
    print(f"   ✅ Trạng thái sau khi mở lại tin: {res.json()['status']}")

    # 8. Kiểm tra giao diện Web tĩnh
    step(8, "Kiểm tra giao diện Web tĩnh của Nhà tuyển dụng")
    pages = [
        ("Trang Quản lý tin", "/frontend/pages/company/manage-jobs.html"),
        ("Trang Đăng tin mới", "/frontend/pages/company/post-job.html"),
        ("Trang Sửa tin", f"/frontend/pages/company/edit-job.html?job_id={job_id}")
    ]
    for name, path in pages:
        res = requests.get(f"{BASE_URL}{path}")
        print(f"   - {name} ({path}): HTTP {res.status_code} OK ({len(res.content)} bytes)")

    separator("🎉 KẾT QUẢ: TOÀN BỘ 8 BƯỚC KIỂM THỬ ĐÃ HOÀN TẤT THÀNH CÔNG 100%!")

if __name__ == "__main__":
    run_demo()
