#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHƯƠNG TRÌNH CHẠY KIỂM THỬ TỰ ĐỘNG TOÀN DIỆN - UNICAREER (NHÓM 8)
Thực hiện chạy tuần tự từng bộ kiểm thử đảm bảo tính độc lập và toàn vẹn của CSDL
"""

import os
import sys
import subprocess

TEST_FILES = [
    "backend/test_company_api.py",
    "backend/test_jobs_api.py",
    "backend/test_t05fea1_tuyen_dung.py",
    "backend/test_t05fead_kiem_tra_doanh_nghiep.py",
    "backend/test_t05feb0_tich_hop_he_thong.py",
    "backend/test_t05feb5_kiem_thu_tong_the.py"
]

def main():
    print("=" * 70)
    print("🚀 BẮT ĐẦU CHẠY KIỂM THỬ HỆ THỐNG UNICAREER (NHÓM 8)")
    print("=" * 70)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(base_dir)

    all_passed = True
    total_passed = 0

    for test_file in TEST_FILES:
        print(f"\n▶ Đang chạy: {test_file} ...")
        cmd = [sys.executable, "-m", "unittest", test_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"  ✅ THÀNH CÔNG: {test_file}")
            # Đếm số tests
            lines = result.stderr.strip().split("\n")
            for line in lines:
                if "Ran " in line:
                    print(f"     {line}")
                    total_passed += 1
        else:
            print(f"  ❌ THẤT BẠI: {test_file}")
            print(result.stderr)
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print(f"🎉 TẤT CẢ {len(TEST_FILES)} BỘ KIỂM THỬ ĐỀU ĐẠT CHUẨN (100% PASSED)!")
    else:
        print("⚠️ CÓ KIỂM THỬ KHÔNG ĐẠT. VUI LÒNG KIỂM TRA LẠI.")
    print("=" * 70)
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
