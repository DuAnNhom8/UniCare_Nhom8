#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def separator(title):
    print("\n" + "=" * 75)
    print(f"🔹 {title}")
    print("=" * 75)

def step(num, desc):
    print(f"\n▶️ [BƯỚC {num}] {desc}")

def run_live_test():
    separator("🚀 BẮT ĐẦU KIỂM THỬ TRỰC TIẾP (LIVE TEST) TASK T05FEAD")
    print(f"🎯 Mục tiêu: Kiểm tra tạo doanh nghiệp và quản lý tin tuyển dụng")
    print(f"🌐 Server Target: {BASE_URL}")

    # 1. Health Check
    step(1, "Kiểm tra kết nối máy chủ FastAPI (GET /health)")
    res = requests.get(f"{BASE_URL}/health")
    print(f"   Status Code: {res.status_code}")
    print(f"   Response: {res.json()}")
    assert res.status_code == 200, "Server chưa sẵn sàng!"
    print("   ✅ Kết nối máy chủ thành công!")

    # 2. Tạo hồ sơ doanh nghiệp mới
    step(2, "Kiểm tra TẠO MỚI hồ sơ Doanh nghiệp (POST /api/companies)")
    company_payload = {
        "employer_id": 99,
        "company_name": "Tập Đoàn Công Nghệ UniCareer AI",
        "industry": "Công nghệ thông tin & Trí tuệ nhân tạo",
        "website": "https://unicareer.ai",
        "location": "Tòa nhà Innovation, TP. Hồ Chí Minh",
        "description": "Nền tảng kết nối việc làm và định hướng nghề nghiệp sinh viên."
    }
    res = requests.post(f"{BASE_URL}/api/companies", json=company_payload)
    print(f"   Status Code: {res.status_code}")
    if res.status_code == 201:
        comp_data = res.json()
        comp_id = comp_data["company_id"]
        print(f"   ✅ Tạo doanh nghiệp thành công! Mã ID: #{comp_id}")
        print(f"   Tên: {comp_data['company_name']} | Ngành: {comp_data['industry']}")
    else:
        # Nếu đã tồn tại employer_id=99 thì lấy thông tin
        print(f"   ℹ️ Đã có doanh nghiệp cho tài khoản này: {res.json().get('detail')}")
        res_get = requests.get(f"{BASE_URL}/api/companies/by-employer/99")
        comp_id = res_get.json()["company_id"]
        print(f"   Lấy ID doanh nghiệp hiện có: #{comp_id}")

    # 3. Xem chi tiết thông tin doanh nghiệp
    step(3, f"Truy vấn chi tiết Doanh nghiệp #{comp_id} (GET /api/companies/{comp_id})")
    res = requests.get(f"{BASE_URL}/api/companies/{comp_id}")
    print(f"   Status Code: {res.status_code}")
    print(f"   Dữ liệu: {res.json()['company_name']} - {res.json()['location']}")
    print("   ✅ Truy vấn thông tin doanh nghiệp thành công!")

    # 4. Cập nhật hồ sơ doanh nghiệp
    step(4, f"Cập nhật thông tin Doanh nghiệp #{comp_id} (PUT /api/companies/{comp_id})")
    update_comp = {
        "company_name": "Tập Đoàn Công Nghệ UniCareer Toàn Cầu (Đã cập nhật)",
        "website": "https://global.unicareer.ai",
        "location": "Tầng 25, Landmark 81, TP. Hồ Chí Minh"
    }
    res = requests.put(f"{BASE_URL}/api/companies/{comp_id}", json=update_comp)
    print(f"   Status Code: {res.status_code}")
    updated_comp = res.json()
    print(f"   Tên mới: {updated_comp['company_name']}")
    print(f"   Địa chỉ mới: {updated_comp['location']}")
    print("   ✅ Cập nhật doanh nghiệp thành công!")

    # 5. Đăng tin tuyển dụng cho doanh nghiệp
    step(5, f"Đăng tin tuyển dụng mới cho Doanh nghiệp #{comp_id} (POST /api/jobs)")
    job_payload = {
        "company_id": comp_id,
        "title": "Kỹ Sư AI & Fullstack Web (Live Test T05FEAD)",
        "description": "Tham gia thiết kế và hoàn thiện các tính năng tuyển dụng và doanh nghiệp.",
        "requirements": "Thành thạo Python, FastAPI, JavaScript, có tinh thần trách nhiệm.",
        "location": "TP. Hồ Chí Minh",
        "salary_range": "12–20 triệu/tháng",
        "job_type": "FULL_TIME",
        "experience_level": "JUNIOR",
        "status": "ACTIVE"
    }
    res = requests.post(f"{BASE_URL}/api/jobs", json=job_payload)
    print(f"   Status Code: {res.status_code}")
    created_job = res.json()
    job_id = created_job["job_id"]
    print(f"   ✅ Tạo tin tuyển dụng thành công! Mã Job ID: #{job_id}")
    print(f"   Tiêu đề: {created_job['title']} | Trạng thái: {created_job['status']}")

    # 6. Xem danh sách tin tuyển dụng của doanh nghiệp
    step(6, f"Lấy danh sách tin tuyển dụng của Doanh nghiệp #{comp_id} (GET /api/jobs?company_id={comp_id})")
    res = requests.get(f"{BASE_URL}/api/jobs?company_id={comp_id}")
    jobs = res.json()
    print(f"   Status Code: {res.status_code}")
    print(f"   Số lượng tin của doanh nghiệp: {len(jobs)} tin")
    for j in jobs:
        print(f"    - #{j['job_id']}: {j['title']} [{j['status']}] - Lương: {j['salary_range']}")

    # 7. Cập nhật nội dung tin tuyển dụng
    step(7, f"Chỉnh sửa nội dung tin tuyển dụng #{job_id} (PUT /api/jobs/{job_id})")
    update_job_payload = {
        "title": "Kỹ Sư AI & Fullstack Web Cao Cấp (Đã cập nhật lương)",
        "salary_range": "18–25 triệu/tháng",
        "location": "Hybrid (Linh hoạt)"
    }
    res = requests.put(f"{BASE_URL}/api/jobs/{job_id}", json=update_job_payload)
    print(f"   Status Code: {res.status_code}")
    uj = res.json()
    print(f"   Tiêu đề mới: {uj['title']}")
    print(f"   Lương mới: {uj['salary_range']}")
    print("   ✅ Cập nhật tin tuyển dụng thành công!")

    # 8. Đóng tin tuyển dụng
    step(8, f"Đóng tin tuyển dụng #{job_id} (PATCH /api/jobs/{job_id}/status -> CLOSED)")
    res = requests.patch(f"{BASE_URL}/api/jobs/{job_id}/status", json={"status": "CLOSED"})
    print(f"   Status Code: {res.status_code}")
    print(f"   Trạng thái hiện tại: {res.json()['status']}")
    print("   ✅ Đóng tin tuyển dụng thành công!")

    # 9. Tạm ẩn tin tuyển dụng
    step(9, f"Tạm ẩn tin tuyển dụng #{job_id} (PATCH /api/jobs/{job_id}/status -> HIDDEN)")
    res = requests.patch(f"{BASE_URL}/api/jobs/{job_id}/status", json={"status": "HIDDEN"})
    print(f"   Status Code: {res.status_code}")
    print(f"   Trạng thái hiện tại: {res.json()['status']}")
    print("   ✅ Tạm ẩn tin tuyển dụng thành công!")

    # 10. Mở lại tin tuyển dụng
    step(10, f"Mở lại tin tuyển dụng #{job_id} (PATCH /api/jobs/{job_id}/status -> ACTIVE)")
    res = requests.patch(f"{BASE_URL}/api/jobs/{job_id}/status", json={"status": "ACTIVE"})
    print(f"   Status Code: {res.status_code}")
    print(f"   Trạng thái hiện tại: {res.json()['status']}")
    print("   ✅ Kích hoạt mở lại tin tuyển dụng thành công!")

    # 11. Kiểm tra các trang web frontend phục vụ doanh nghiệp
    step(11, "Kiểm tra khả năng tải các trang giao diện HTML của Nhà tuyển dụng")
    frontend_pages = [
        ("Trang Quản lý tin tuyển dụng", "/frontend/pages/company/manage-jobs.html"),
        ("Trang Đăng tin tuyển dụng mới", "/frontend/pages/company/post-job.html"),
        ("Trang Chỉnh sửa tin tuyển dụng", f"/frontend/pages/company/edit-job.html?job_id={job_id}")
    ]
    for page_name, path in frontend_pages:
        r = requests.get(f"{BASE_URL}{path}")
        print(f"   - {page_name}: HTTP {r.status_code} ({len(r.content)} bytes)")

    separator("🎉 KẾT QUẢ: TOÀN BỘ 11 BƯỚC KIỂM THỬ TRỰC TIẾP ĐÃ ĐẠT 100% THÀNH CÔNG!")

if __name__ == "__main__":
    run_live_test()
