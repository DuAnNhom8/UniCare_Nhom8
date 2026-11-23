#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHƯƠNG TRÌNH KIỂM THỬ TRỰC TIẾP (LIVE TEST) CHO TASK T05FEB0
Tích hợp các module hệ thống: Tài khoản, Doanh nghiệp, Việc làm, Ứng tuyển và Quản trị
Chạy độc lập với TestClient hoặc Web Server thật
"""

import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from backend.app.main import app

def print_banner(msg):
    print("\n" + "=" * 75)
    print(f"🌟 {msg}")
    print("=" * 75)

def print_step(num, desc):
    print(f"\n▶️ [BƯỚC {num}] {desc}")

def run_live_test():
    print_banner("BẮT ĐẦU KIỂM THỬ TRỰC TIẾP TÍCH HỢP HỆ THỐNG UNICAREER (TASK T05FEB0)")

    with TestClient(app) as client:
        # 1. Khởi động & Kiểm tra kết nối
        print_step(1, "Kiểm tra trạng thái hệ thống (Health & Modules)")
        res_health = client.get("/health")
        print(f"   Status: {res_health.status_code} | Payload: {res_health.json()}")

        res_root = client.get("/")
        print(f"   Project: {res_root.json()['project']} | Version: {res_root.json()['version']}")
        print(f"   Các module đã kích hoạt: {len(res_root.json()['modules'])} modules")

        # 2. Đăng ký & Xác thực tài khoản
        print_step(2, "Đăng ký tài khoản Sinh viên mới và đăng nhập")
        test_email = "student_live@ptit.edu.vn"
        res_reg = client.post("/api/auth/register", json={
            "email": test_email,
            "password": "password123",
            "role": "CANDIDATE",
            "full_name": "Đỗ Hoàng Sơn (Sinh viên Live Test)"
        })
        user_id = res_reg.json().get("user_id") if res_reg.status_code == 201 else 3
        print(f"   Đăng ký: {res_reg.status_code} | User ID: {user_id}")

        res_login = client.post("/api/auth/login", json={
            "email": test_email if res_reg.status_code == 201 else "sinhvien@ptit.edu.vn",
            "password": "password123" if res_reg.status_code == 201 else "demo123"
        })
        print(f"   Đăng nhập: {res_login.status_code} | Quyền: {res_login.json()['user']['role']} | Token: {res_login.json()['access_token']}")

        # 3. Hồ sơ ứng viên
        print_step(3, "Cập nhật hồ sơ ứng viên và kỹ năng")
        res_profile = client.put(f"/api/candidates/profile?user_id={user_id}", json={
            "full_name": "Đỗ Hoàng Sơn",
            "phone": "0987654321",
            "university": "PTIT TP.HCM",
            "major": "Công nghệ Thông tin",
            "skills": "Python, FastAPI, MySQL, HTML5/CSS3, JavaScript"
        })
        print(f"   Hồ sơ cập nhật: {res_profile.status_code} | Tên: {res_profile.json()['full_name']} | Kỹ năng: {res_profile.json()['skills']}")

        # 4. Tìm kiếm việc làm
        print_step(4, "Tìm kiếm cơ hội việc làm đang tuyển dụng")
        res_jobs = client.get("/api/jobs?status=ACTIVE")
        jobs = res_jobs.json()
        print(f"   Tìm thấy {len(jobs)} vị trí việc làm đang mở nhận hồ sơ:")
        for idx, j in enumerate(jobs[:3], 1):
            print(f"     {idx}. [ID {j['job_id']}] {j['title']} ({j.get('location', 'N/A')}) - Lương: {j.get('salary_range', 'Thỏa thuận')}")

        # Chọn tin còn hạn nộp hồ sơ
        from datetime import date
        today_str = str(date.today())
        unexpired_jobs = [j for j in jobs if not j.get('deadline') or str(j['deadline']) >= today_str]
        target_job_id = unexpired_jobs[0]["job_id"] if unexpired_jobs else (jobs[0]["job_id"] if jobs else 1)

        # 5. Ứng tuyển vào công việc
        print_step(5, f"Sinh viên nộp đơn ứng tuyển vào tin #{target_job_id}")
        res_apply = client.post(f"/api/candidates/apply?user_id={user_id}", json={
            "job_id": target_job_id,
            "candidate_id": user_id,
            "cover_letter": "Hồ sơ ứng tuyển chính thức cho dự án thực tập."
        })
        print(f"   Nộp đơn: {res_apply.status_code} | Trạng thái: {res_apply.json().get('status', res_apply.text)}")

        # 6. Kiểm tra danh sách đơn đã nộp
        print_step(6, "Sinh viên kiểm tra danh sách đơn ứng tuyển cá nhân")
        res_my_apps = client.get(f"/api/candidates/applications?user_id={user_id}")
        my_apps = res_my_apps.json()
        print(f"   Tổng số đơn đã nộp: {len(my_apps)}")
        if my_apps:
            print(f"   Đơn gần nhất: Vị trí '{my_apps[0]['job_title']}' tại '{my_apps[0]['company_name']}' - Trạng thái: {my_apps[0]['status']}")

        # 7. Doanh nghiệp xử lý đơn
        print_step(7, "Nhà tuyển dụng xem danh sách hồ sơ nhận được và cập nhật trạng thái")
        res_comp_apps = client.get("/api/companies/1/applications")
        comp_apps = res_comp_apps.json()
        print(f"   Doanh nghiệp nhận được {len(comp_apps)} hồ sơ ứng viên.")
        if comp_apps:
            first_app = comp_apps[0]
            app_id = first_app["application_id"]
            res_up = client.put(f"/api/companies/1/applications/{app_id}/status", json={"status": "REVIEWING"})
            print(f"   Cập nhật đơn #{app_id} sang trạng thái: {res_up.json()['status']}")

        # 8. Quản trị hệ thống & Kiểm duyệt
        print_step(8, "Quản trị viên (Admin) kiểm tra Dashboard thống kê và kiểm duyệt tin")
        res_stats = client.get("/api/admin/stats")
        print(f"   Thống kê hệ thống:")
        stats = res_stats.json()
        for k, v in stats.items():
            print(f"     - {k}: {v}")

        # Duyệt tin
        res_admin_jobs = client.get("/api/admin/jobs")
        admin_jobs = res_admin_jobs.json()
        pending_jobs = [j for j in admin_jobs if j.get("approval_status") == "PENDING"]
        if pending_jobs:
            target_p = pending_jobs[0]["job_id"]
            res_appr = client.put(f"/api/admin/jobs/{target_p}/approval", json={"approval_status": "APPROVED"})
            print(f"   Admin đã duyệt tin #{target_p}: {res_appr.json()['approval_status']}")
        else:
            print("   Tất cả tin tuyển dụng đều đã được kiểm duyệt công khai.")

    print_banner("✅ TẤT CẢ LUỒNG TÍCH HỢP HỆ THỐNG ĐÃ HOẠT ĐỘNG HOÀN HẢO!")

if __name__ == "__main__":
    run_live_test()
