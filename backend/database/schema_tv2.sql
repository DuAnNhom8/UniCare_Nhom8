-- ========================================================
-- CƠ SỞ DỮ LIỆU UNICAREER - PHÂN HỆ DOANH NGHIỆP & TUYỂN DỤNG (TV2)
-- Tác giả: TV2 (Đỗ Hoàng Sơn)
-- Mã Task: T85FE93 - Xây dựng CSDL doanh nghiệp và tuyển dụng
-- Chuẩn theo tài liệu đặc tả SRS UniCareer mục 10.2.3 & 10.2.4
-- ========================================================

-- Sử dụng Database
CREATE DATABASE IF NOT EXISTS `unicareer_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `unicareer_db`;

-- 1. BẢNG USERS (Tham chiếu tài khoản người dùng)
CREATE TABLE IF NOT EXISTS `users` (
    `user_id` INT AUTO_INCREMENT PRIMARY KEY,
    `email` VARCHAR(100) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `role` ENUM('CANDIDATE', 'EMPLOYER', 'ADMIN') NOT NULL,
    `is_active` BOOLEAN DEFAULT TRUE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. BẢNG COMPANIES (Quản lý thông tin doanh nghiệp - SRS 10.2.3)
CREATE TABLE IF NOT EXISTS `companies` (
    `company_id` INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Mã doanh nghiệp',
    `employer_id` INT NOT NULL UNIQUE COMMENT 'Tài khoản nhà tuyển dụng (1-1 với USERS)',
    `company_name` VARCHAR(150) NOT NULL COMMENT 'Tên doanh nghiệp',
    `description` TEXT NULL COMMENT 'Mô tả doanh nghiệp',
    `website` VARCHAR(255) NULL COMMENT 'Website doanh nghiệp',
    `industry` VARCHAR(100) NULL COMMENT 'Ngành nghề hoạt động',
    `location` VARCHAR(150) NULL COMMENT 'Địa chỉ trụ sở',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_companies_employer` 
        FOREIGN KEY (`employer_id`) REFERENCES `users` (`user_id`) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. BẢNG JOB_POSTS (Quản lý tin tuyển dụng - SRS 10.2.4)
CREATE TABLE IF NOT EXISTS `job_posts` (
    `job_id` INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Mã tin tuyển dụng',
    `company_id` INT NOT NULL COMMENT 'Doanh nghiệp đăng tin',
    `title` VARCHAR(150) NOT NULL COMMENT 'Tên vị trí tuyển dụng',
    `description` TEXT NOT NULL COMMENT 'Mô tả công việc',
    `requirements` TEXT NOT NULL COMMENT 'Yêu cầu ứng viên',
    `location` VARCHAR(100) NULL COMMENT 'Địa điểm làm việc',
    `salary_range` VARCHAR(100) NULL COMMENT 'Khoảng lương',
    `job_type` ENUM('FULL_TIME', 'PART_TIME', 'INTERNSHIP') DEFAULT 'INTERNSHIP' COMMENT 'Loại hình công việc',
    `experience_level` VARCHAR(50) NULL COMMENT 'Yêu cầu kinh nghiệm',
    `deadline` DATE NOT NULL COMMENT 'Hạn cuối ứng tuyển',
    `status` ENUM('ACTIVE', 'CLOSED', 'HIDDEN') DEFAULT 'ACTIVE' COMMENT 'Trạng thái tin',
    `approval_status` ENUM('PENDING', 'APPROVED', 'REJECTED') DEFAULT 'PENDING' COMMENT 'Trạng thái kiểm duyệt',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_job_posts_company` 
        FOREIGN KEY (`company_id`) REFERENCES `companies` (`company_id`) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================================
-- DỮ LIỆU MẪU BAN ĐẦU (SEED DATA THEO CHUẨN FIGMA)
-- ========================================================

-- Tạo tài khoản nhà tuyển dụng mẫu
INSERT IGNORE INTO `users` (`user_id`, `email`, `password_hash`, `role`) 
VALUES (2, 'hr@technova.com', '$2b$12$eXampleHashedPasswordForDemoOnly', 'EMPLOYER');

-- Tạo hồ sơ doanh nghiệp TechNova
INSERT IGNORE INTO `companies` (`company_id`, `employer_id`, `company_name`, `description`, `website`, `industry`, `location`) 
VALUES (1, 2, 'TechNova', 'Phát triển giải pháp phần mềm cho các doanh nghiệp trẻ và tổ chức.', 'technova.example', 'Công nghệ thông tin', 'TP. Hồ Chí Minh');

-- Tạo các tin tuyển dụng mẫu
INSERT IGNORE INTO `job_posts` (`job_id`, `company_id`, `title`, `description`, `requirements`, `location`, `salary_range`, `job_type`, `experience_level`, `deadline`, `status`, `approval_status`) 
VALUES 
(1, 1, 'Backend Developer Intern', 'Phát triển API bằng Python và FastAPI. Thiết kế, truy vấn và làm việc với MySQL.', 'Nắm kiến thức lập trình Python cơ bản. Biết HTTP, REST API và cơ sở dữ liệu.', 'TP. Hồ Chí Minh', '3-5 triệu/tháng', 'INTERNSHIP', 'Không yêu cầu', '2026-11-30', 'ACTIVE', 'APPROVED'),
(2, 1, 'Frontend Developer Intern', 'Xây dựng giao diện Web bằng HTML/CSS/JS thuần và Figma.', 'Thành thạo HTML5, CSS3, JavaScript cơ bản.', 'Hybrid (TP.HCM)', '3-5 triệu/tháng', 'INTERNSHIP', 'Không yêu cầu', '2026-11-25', 'ACTIVE', 'APPROVED'),
(3, 1, 'Data Analyst Intern', 'Phân tích dữ liệu người dùng và tạo báo cáo trực quan hóa.', 'SQL cơ bản, tư duy logic tốt, biết Python/Excel.', 'Hà Nội', '4-6 triệu/tháng', 'INTERNSHIP', 'Dưới 1 năm', '2026-12-20', 'ACTIVE', 'PENDING');
