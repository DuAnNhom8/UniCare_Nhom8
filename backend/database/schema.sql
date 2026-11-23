CREATE DATABASE IF NOT EXISTS unicareer CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE unicareer;

CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('CANDIDATE', 'EMPLOYER', 'ADMIN') NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_users_role_active (role, is_active)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS candidates (
    candidate_id INT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NULL,
    university VARCHAR(150) NULL,
    major VARCHAR(100) NULL,
    skills TEXT NULL,
    bio TEXT NULL,
    cv_url VARCHAR(255) NULL,
    CONSTRAINT fk_candidates_user FOREIGN KEY (candidate_id)
        REFERENCES users (user_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS companies (
    company_id INT AUTO_INCREMENT PRIMARY KEY,
    employer_id INT NOT NULL UNIQUE,
    company_name VARCHAR(150) NOT NULL,
    description TEXT NULL,
    website VARCHAR(255) NULL,
    CONSTRAINT fk_companies_employer FOREIGN KEY (employer_id)
        REFERENCES users (user_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS job_posts (
    job_id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    requirements TEXT NOT NULL,
    location VARCHAR(100) NULL,
    salary_range VARCHAR(100) NULL,
    deadline DATE NOT NULL,
    status ENUM('ACTIVE', 'CLOSED', 'HIDDEN') NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_jobs_company FOREIGN KEY (company_id)
        REFERENCES companies (company_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_job_status_deadline (status, deadline),
    INDEX idx_job_company (company_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS applications (
    application_id INT AUTO_INCREMENT PRIMARY KEY,
    job_id INT NOT NULL,
    candidate_id INT NOT NULL,
    status ENUM('RECEIVED', 'REVIEWING', 'MATCHED', 'REJECTED') NOT NULL DEFAULT 'RECEIVED',
    ai_match_score INT NULL,
    ai_feedback TEXT NULL,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_application_candidate_job UNIQUE (job_id, candidate_id),
    CONSTRAINT chk_ai_score CHECK (ai_match_score IS NULL OR ai_match_score BETWEEN 0 AND 100),
    CONSTRAINT fk_app_job FOREIGN KEY (job_id)
        REFERENCES job_posts (job_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_app_candidate FOREIGN KEY (candidate_id)
        REFERENCES candidates (candidate_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_app_candidate (candidate_id, applied_at),
    INDEX idx_app_job_status (job_id, status)
) ENGINE=InnoDB;
