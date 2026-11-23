-- Chạy SAU schema_tv2.sql (bảng users, companies, job_posts đã có).
USE `unicareer_db`;

CREATE TABLE IF NOT EXISTS `cvs` (
  `cv_id` INT AUTO_INCREMENT PRIMARY KEY,
  `candidate_id` INT NOT NULL,
  `title` VARCHAR(150) NOT NULL,
  `file_path` VARCHAR(500) NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX `ix_cvs_candidate_id` (`candidate_id`),
  CONSTRAINT `fk_cvs_candidate` FOREIGN KEY (`candidate_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `applications` (
  `application_id` INT AUTO_INCREMENT PRIMARY KEY,
  `candidate_id` INT NOT NULL,
  `job_id` INT NOT NULL,
  `cv_id` INT NULL,
  `cover_letter` TEXT NULL,
  `status` ENUM('PENDING', 'REVIEWING', 'ACCEPTED', 'REJECTED') NOT NULL DEFAULT 'PENDING',
  `applied_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `uq_candidate_job` (`candidate_id`, `job_id`),
  INDEX `ix_applications_candidate_id` (`candidate_id`),
  INDEX `ix_applications_job_id` (`job_id`),
  CONSTRAINT `fk_applications_candidate` FOREIGN KEY (`candidate_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_applications_job` FOREIGN KEY (`job_id`) REFERENCES `job_posts` (`job_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_applications_cv` FOREIGN KEY (`cv_id`) REFERENCES `cvs` (`cv_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
