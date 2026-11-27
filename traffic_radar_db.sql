-- =============================================================================
-- CƠ SỞ DỮ LIỆU MYSQL - HỆ THỐNG GIÁM SÁT GIAO THÔNG & CẢNH BÁO VA CHẠM AI
-- Đồ án Công nghệ phần mềm (Software Engineering) - DUT
-- Hỗ trợ phân quyền người dùng (RBAC) và Lưu trữ sự cố riêng biệt từng tài khoản
-- =============================================================================

CREATE DATABASE IF NOT EXISTS `traffic_radar_db` 
DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `traffic_radar_db`;

-- -----------------------------------------------------------------------------
-- 1. BẢNG NGƯỜI DÙNG & PHÂN QUYỀN (USERS)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(100) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `salt` VARCHAR(255) NOT NULL DEFAULT '',
    `full_name` VARCHAR(255) NOT NULL DEFAULT '',
    `role` ENUM('admin', 'operator') NOT NULL DEFAULT 'operator',
    `is_locked` TINYINT(1) NOT NULL DEFAULT 0,
    `failed_attempts` INT NOT NULL DEFAULT 0,
    `locked_until` DATETIME NULL,
    `created_at` DATETIME NOT NULL,
    INDEX `idx_username` (`username`),
    INDEX `idx_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 2. BẢNG NHẬT KÝ ĐĂNG NHẬP (LOGIN_LOG - AUDIT LOG AN NINH)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `login_log` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `timestamp` DATETIME NOT NULL,
    `username` VARCHAR(100) NOT NULL,
    `result` VARCHAR(100) NOT NULL,
    `ip_address` VARCHAR(100) DEFAULT '127.0.0.1',
    INDEX `idx_login_user` (`username`),
    INDEX `idx_login_time` (`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 3. BẢNG SỰ CỐ VA CHẠM GOM CỤM (INCIDENTS) - LƯU RIÊNG THEO TỪNG TÀI KHOẢN
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `incidents` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NULL COMMENT 'ID tài khoản người vận hành ghi nhận sự cố',
    `username` VARCHAR(100) NULL COMMENT 'Tên tài khoản người vận hành',
    `start_time` VARCHAR(50) NOT NULL,
    `end_time` VARCHAR(50) NOT NULL,
    `max_severity` VARCHAR(100) NOT NULL,
    `object_type` VARCHAR(100) NOT NULL,
    `min_distance_m` DOUBLE NOT NULL,
    `min_ttc_sec` DOUBLE NULL,
    `max_speed_kmh` DOUBLE NOT NULL,
    `image_path` TEXT NULL,
    `notes` TEXT NULL,
    `created_at` VARCHAR(50) NOT NULL,
    `closing_speed_mps` DOUBLE DEFAULT 0.0,
    `speed_kmh_raw` DOUBLE DEFAULT 0.0,
    INDEX `idx_incident_user` (`user_id`),
    INDEX `idx_incident_username` (`username`),
    INDEX `idx_incident_time` (`start_time`),
    INDEX `idx_incident_severity` (`max_severity`),
    CONSTRAINT `fk_incident_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 4. BẢNG NHẬT KÝ CẢNH BÁO CHI TIẾT (ALERT_LOGS) - LƯU RIÊNG THEO TỪNG TÀI KHOẢN
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `alert_logs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NULL,
    `username` VARCHAR(100) NULL,
    `timestamp` VARCHAR(50) NOT NULL,
    `object_type` VARCHAR(100) NOT NULL,
    `distance_m` DOUBLE NOT NULL,
    `velocity_kmh` DOUBLE NOT NULL,
    `ttc_sec` DOUBLE NULL,
    `severity` VARCHAR(100) NOT NULL,
    `image_path` TEXT NULL,
    `start_time` VARCHAR(50) NULL,
    `end_time` VARCHAR(50) NULL,
    `min_distance_m` DOUBLE NULL,
    `min_ttc_sec` DOUBLE NULL,
    `max_speed_kmh` DOUBLE NULL,
    `max_severity` VARCHAR(100) NULL,
    `notes` TEXT NULL,
    `closing_speed_mps` DOUBLE DEFAULT 0.0,
    `speed_kmh_raw` DOUBLE DEFAULT 0.0,
    INDEX `idx_alert_user` (`user_id`),
    INDEX `idx_alert_time` (`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 5. BẢNG CẤU HÌNH HỆ THỐNG (SYSTEM_SETTINGS)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `system_settings` (
    `key` VARCHAR(100) PRIMARY KEY,
    `value` TEXT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- NẠP DỮ LIỆU TÀI KHOẢN KHỞI TẠO (USERS BAN ĐẦU)
-- -----------------------------------------------------------------------------
INSERT INTO `users` (`id`, `username`, `password_hash`, `salt`, `full_name`, `role`, `is_locked`, `failed_attempts`, `created_at`) VALUES
(1, 'admin', 'b482e891d55ba69de6aba50658c4f16ae8cbbdcb8d7564a5018b358df700b1c1', 'c2065e4f6e6fe2f69093721718583715', 'Quản trị viên Kỹ thuật', 'admin', 0, 0, '2026-11-10 16:34:30'),
(3, 'ngoquangthe123', 'b514ce027acacc090eb2a4e2cb773b32f60e0a9559b734d5febffb2cea8439d7', '4b168b7a23b85371d970766b8f5619fb', 'Ngô Quang Thế', 'operator', 0, 0, '2026-11-20 08:07:46'),
(8, 'phong123', '5224c6d05978e517831b890b15d417972ea04085a43d07f15bdc065e70c4a2bf', '1fd15dd61c64793fd1a8b753e3206300', 'Huỳnh Ngọc Tịnh Phong', 'operator', 0, 0, '2026-11-27 10:15:27')
ON DUPLICATE KEY UPDATE `full_name`=VALUES(`full_name`);
