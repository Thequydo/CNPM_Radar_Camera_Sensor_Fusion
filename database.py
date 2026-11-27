# -*- coding: utf-8 -*-
"""
Module Quản trị Cơ sở dữ liệu SQLite & Xác thực Người dùng (RBAC)
Tuân thủ chuẩn đặc tả SRS: US-01..03, FR-01, FR-02, FR-08, FR-10, NFR-05, NFR-06
Bao gồm:
- Băm mật khẩu bằng PBKDF2-HMAC-SHA256 với Salt ngẫu nhiên riêng từng tài khoản
- Khóa tài khoản 5 phút khi sai 5 lần liên tiếp, ghi nhật ký login_log
- Quản lý người dùng: tạo, sửa quyền, khóa, xóa (bảo vệ Admin cuối, không tự khóa mình)
- Cơ chế khởi tạo lần đầu: bắt buộc tạo Admin nếu hệ thống chưa có tài khoản
- Kiểm tra quyền ở tầng logic backend (RBAC)
- Nhật ký sự cố gom cụm và xuất báo cáo CSV UTF-8 BOM / Excel .xlsx
"""

import os
import csv
import time
import secrets
import hashlib
import hmac
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict
from config import DB_PATH, get_config

try:
    import pymysql
except ImportError:
    pymysql = None

_active_backend = "sqlite"
_mysql_last_error = ""
_last_mysql_check_time = 0.0
_mysql_check_interval = 10.0  # Thử lại kết nối MySQL tối đa 10s một lần khi offline để tránh giật lag
_is_mysql_server_available = False


class DBProxyCursor:
    """Cursor trung gian hỗ trợ cả SQLite (?) và MySQL (%s) với cú pháp thống nhất"""
    def __init__(self, raw_cursor, is_mysql: bool = False):
        self.raw = raw_cursor
        self.is_mysql = is_mysql

    def execute(self, sql: str, params=None):
        if self.is_mysql:
            sql = sql.replace('?', '%s')
            # Chuyển đổi cú pháp ON CONFLICT của SQLite sang ON DUPLICATE KEY UPDATE của MySQL
            if 'ON CONFLICT(key) DO UPDATE' in sql:
                sql = """
                    INSERT INTO system_settings (`key`, `value`) VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE `value` = VALUES(`value`)
                """
        if params is None:
            return self.raw.execute(sql)
        return self.raw.execute(sql, params)

    def executemany(self, sql: str, seq_of_params):
        if self.is_mysql:
            sql = sql.replace('?', '%s')
        return self.raw.executemany(sql, seq_of_params)

    @property
    def lastrowid(self):
        return self.raw.lastrowid

    def fetchone(self):
        return self.raw.fetchone()

    def fetchall(self):
        return self.raw.fetchall()

    def fetchmany(self, size=None):
        return self.raw.fetchmany(size) if size else self.raw.fetchmany()

    def __getattr__(self, name):
        return getattr(self.raw, name)


class DBProxyConnection:
    """Connection proxy hỗ trợ ngữ cảnh 'with get_connection() as conn:' cho cả 2 backend"""
    def __init__(self, raw_conn, is_mysql: bool = False):
        self.raw = raw_conn
        self.is_mysql = is_mysql

    def cursor(self):
        return DBProxyCursor(self.raw.cursor(), is_mysql=self.is_mysql)

    def commit(self):
        return self.raw.commit()

    def rollback(self):
        try:
            return self.raw.rollback()
        except Exception:
            pass

    def close(self):
        try:
            return self.raw.close()
        except Exception:
            pass

    def execute(self, sql: str, params=None):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()


def get_mysql_raw_connection(create_db_if_missing: bool = True):
    """Kết nối tới MySQL server (XAMPP / MariaDB) theo cấu hình hệ thống"""
    global _mysql_last_error, _last_mysql_check_time, _is_mysql_server_available
    if pymysql is None:
        _mysql_last_error = "Thư viện pymysql chưa được cài đặt."
        return None

    now = time.time()
    # Nếu trước đó thử kết nối MySQL thất bại và chưa qua 10 giây -> trả về None ngay, không block
    if not _is_mysql_server_available and (now - _last_mysql_check_time < _mysql_check_interval):
        return None

    _last_mysql_check_time = now

    cfg = get_config()
    host = cfg.get("mysql_host", "127.0.0.1")
    port = int(cfg.get("mysql_port", 3306))
    user = cfg.get("mysql_user", "root")
    password = cfg.get("mysql_password", "")
    db_name = cfg.get("mysql_database", "traffic_radar_db")

    try:
        if create_db_if_missing:
            # Kết nối trước tới máy chủ MySQL để tạo Database nếu chưa có
            init_conn = pymysql.connect(
                host=host, port=port, user=user, password=password,
                connect_timeout=0.6, autocommit=True
            )
            with init_conn.cursor() as cur:
                cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            init_conn.close()

        conn = pymysql.connect(
            host=host, port=port, user=user, password=password,
            database=db_name, connect_timeout=0.6, autocommit=True,
            charset="utf8mb4"
        )
        _mysql_last_error = ""
        _is_mysql_server_available = True
        return conn
    except Exception as e:
        _mysql_last_error = str(e)
        _is_mysql_server_available = False
        return None


def get_connection():
    """
    Tạo kết nối CSDL hợp nhất (Unified DB Connection):
    - Mặc định ưu tiên MySQL nếu được bật trong cấu hình và MySQL Server đang hoạt động.
    - Tự động fallback sang SQLite cục bộ an toàn nếu MySQL chưa bật (không làm treo/crash app).
    """
    global _active_backend
    cfg = get_config()
    backend_pref = cfg.get("db_backend", "mysql")

    # Nếu đang chạy test tạm thời (DB_PATH bị đổi sang file test fixture), ưu tiên SQLite của test
    from config import DB_PATH as DEFAULT_DB_PATH
    is_testing_fixture = (DB_PATH != DEFAULT_DB_PATH)

    if backend_pref == "mysql" and pymysql is not None and not is_testing_fixture:
        raw_mysql = get_mysql_raw_connection(create_db_if_missing=True)
        if raw_mysql is not None:
            _active_backend = "mysql"
            return DBProxyConnection(raw_mysql, is_mysql=True)

    _active_backend = "sqlite"
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
    except Exception:
        pass
    return DBProxyConnection(conn, is_mysql=False)


def get_active_db_info() -> dict:
    """Trả về trạng thái backend CSDL hiện thời để hiển thị trên giao diện hoặc báo cáo"""
    cfg = get_config()
    return {
        "backend": _active_backend,
        "is_mysql": (_active_backend == "mysql"),
        "mysql_host": cfg.get("mysql_host", "127.0.0.1"),
        "mysql_port": cfg.get("mysql_port", 3306),
        "mysql_database": cfg.get("mysql_database", "traffic_radar_db"),
        "mysql_last_error": _mysql_last_error,
        "sqlite_path": DB_PATH
    }


def sync_sqlite_to_mysql():
    """Đồng bộ dữ liệu người dùng, cấu hình và sự cố từ SQLite sang MySQL nếu MySQL mới khởi tạo"""
    if _active_backend != "mysql" or not os.path.exists(DB_PATH):
        return

    try:
        with sqlite3.connect(DB_PATH) as sq_conn:
            sq_cur = sq_conn.cursor()

            with get_connection() as my_conn:
                my_cur = my_conn.cursor()

                # 1. Đồng bộ người dùng
                my_cur.execute("SELECT COUNT(*) FROM users")
                if my_cur.fetchone()[0] == 0:
                    sq_cur.execute("SELECT username, password_hash, salt, full_name, role, is_locked, failed_attempts, created_at FROM users")
                    users = sq_cur.fetchall()
                    for u in users:
                        my_cur.execute("""
                            INSERT INTO users (username, password_hash, salt, full_name, role, is_locked, failed_attempts, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, u)

                # 2. Đồng bộ cấu hình
                sq_cur.execute("SELECT key, value FROM system_settings")
                settings = sq_cur.fetchall()
                for k, v in settings:
                    my_cur.execute("""
                        INSERT INTO system_settings (`key`, `value`) VALUES (?, ?)
                        ON DUPLICATE KEY UPDATE `value` = VALUES(`value`)
                    """, (k, v))

                # 3. Đồng bộ sự cố
                my_cur.execute("SELECT COUNT(*) FROM incidents")
                if my_cur.fetchone()[0] == 0:
                    sq_cur.execute("PRAGMA table_info(incidents)")
                    cols = [c[1] for c in sq_cur.fetchall()]
                    has_u = ("user_id" in cols)
                    if has_u:
                        sq_cur.execute("""
                            SELECT start_time, end_time, max_severity, object_type, min_distance_m, min_ttc_sec, max_speed_kmh, image_path, notes, created_at, closing_speed_mps, speed_kmh_raw, user_id, username
                            FROM incidents
                        """)
                    else:
                        sq_cur.execute("""
                            SELECT start_time, end_time, max_severity, object_type, min_distance_m, min_ttc_sec, max_speed_kmh, image_path, notes, created_at, closing_speed_mps, speed_kmh_raw
                            FROM incidents
                        """)
                    inc_rows = sq_cur.fetchall()
                    for r in inc_rows:
                        if has_u:
                            my_cur.execute("""
                                INSERT INTO incidents (start_time, end_time, max_severity, object_type, min_distance_m, min_ttc_sec, max_speed_kmh, image_path, notes, created_at, closing_speed_mps, speed_kmh_raw, user_id, username)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, r)
                        else:
                            # Gán mặc định cho user admin đầu tiên
                            row_list = list(r) + [1, "admin"]
                            my_cur.execute("""
                                INSERT INTO incidents (start_time, end_time, max_severity, object_type, min_distance_m, min_ttc_sec, max_speed_kmh, image_path, notes, created_at, closing_speed_mps, speed_kmh_raw, user_id, username)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, tuple(row_list))
    except Exception as e:
        print("[LỖI ĐỒNG BỘ SQLITE SANG MYSQL]:", e)


def hash_password_pbkdf2(password: str, salt: Optional[str] = None, iterations: int = 100000) -> Tuple[str, str]:
    """
    Băm mật khẩu bằng PBKDF2-HMAC-SHA256 chuẩn bảo mật NIST.
    - salt: chuỗi hex ngẫu nhiên (nếu None sẽ sinh ngẫu nhiên 16 bytes = 32 hex chars)
    - iterations: số vòng lặp PBKDF2 lấy từ cấu hình hệ thống
    Trả về: (password_hash_hex, salt_hex)
    """
    if salt is None or not salt:
        salt = secrets.token_hex(16)
    
    salt_bytes = bytes.fromhex(salt)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt_bytes,
        int(iterations)
    )
    return key.hex(), salt


def verify_password_pbkdf2(password: str, stored_hash: str, salt: str, iterations: int = 100000) -> bool:
    """Xác thực mật khẩu đối chiếu với hash và salt lưu trong CSDL"""
    try:
        salt_bytes = bytes.fromhex(salt)
        calc_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt_bytes,
            int(iterations)
        ).hex()
        return hmac.compare_digest(calc_hash, stored_hash)
    except Exception:
        return False


def init_db():
    """Khởi tạo toàn bộ cấu trúc bảng theo đặc tả SRS (Hỗ trợ cả MySQL và SQLite)"""
    with get_connection() as conn:
        cursor = conn.cursor()

        if _active_backend == "mysql":
            # 1. Bảng users
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    salt VARCHAR(255) NOT NULL DEFAULT '',
                    full_name VARCHAR(255) NOT NULL DEFAULT '',
                    role ENUM('admin', 'operator') NOT NULL DEFAULT 'operator',
                    is_locked INT NOT NULL DEFAULT 0,
                    failed_attempts INT NOT NULL DEFAULT 0,
                    locked_until VARCHAR(50),
                    created_at VARCHAR(50) NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 2. Bảng login_log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS login_log (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    timestamp VARCHAR(50) NOT NULL,
                    username VARCHAR(100) NOT NULL,
                    result VARCHAR(100) NOT NULL,
                    ip_address VARCHAR(100) DEFAULT '127.0.0.1'
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 3. Bảng alert_logs (có user_id và username)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alert_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NULL,
                    username VARCHAR(100) NULL,
                    timestamp VARCHAR(50) NOT NULL,
                    object_type VARCHAR(100) NOT NULL,
                    distance_m DOUBLE NOT NULL,
                    velocity_kmh DOUBLE NOT NULL,
                    ttc_sec DOUBLE NULL,
                    severity VARCHAR(100) NOT NULL,
                    image_path TEXT,
                    start_time VARCHAR(50),
                    end_time VARCHAR(50),
                    min_distance_m DOUBLE,
                    min_ttc_sec DOUBLE,
                    max_speed_kmh DOUBLE,
                    max_severity VARCHAR(100),
                    notes TEXT,
                    closing_speed_mps DOUBLE DEFAULT 0.0,
                    speed_kmh_raw DOUBLE DEFAULT 0.0
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 4. Bảng incidents (lưu riêng theo từng tài khoản)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NULL,
                    username VARCHAR(100) NULL,
                    start_time VARCHAR(50) NOT NULL,
                    end_time VARCHAR(50) NOT NULL,
                    max_severity VARCHAR(100) NOT NULL,
                    object_type VARCHAR(100) NOT NULL,
                    min_distance_m DOUBLE NOT NULL,
                    min_ttc_sec DOUBLE NULL,
                    max_speed_kmh DOUBLE NOT NULL,
                    image_path TEXT,
                    notes TEXT,
                    created_at VARCHAR(50) NOT NULL,
                    closing_speed_mps DOUBLE DEFAULT 0.0,
                    speed_kmh_raw DOUBLE DEFAULT 0.0
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 5. Bảng system_settings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_settings (
                    `key` VARCHAR(100) PRIMARY KEY,
                    `value` TEXT NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            conn.commit()

            # Tự động nạp dữ liệu cũ từ SQLite nếu MySQL mới tinh
            sync_sqlite_to_mysql()

        else:
            # Backend SQLite Cục bộ
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL DEFAULT '',
                    full_name TEXT NOT NULL DEFAULT '',
                    role TEXT NOT NULL CHECK(role IN ('admin', 'operator')),
                    is_locked INTEGER NOT NULL DEFAULT 0,
                    failed_attempts INTEGER NOT NULL DEFAULT 0,
                    locked_until TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            cursor.execute("PRAGMA table_info(users)")
            existing_u_cols = {col[1] for col in cursor.fetchall()}
            user_migrations = [
                ("salt", "TEXT NOT NULL DEFAULT ''"),
                ("is_locked", "INTEGER NOT NULL DEFAULT 0"),
                ("failed_attempts", "INTEGER NOT NULL DEFAULT 0"),
                ("locked_until", "TEXT")
            ]
            for col_name, col_def in user_migrations:
                if col_name not in existing_u_cols:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS login_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    username TEXT NOT NULL,
                    result TEXT NOT NULL,
                    ip_address TEXT DEFAULT '127.0.0.1'
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alert_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    timestamp TEXT NOT NULL,
                    object_type TEXT NOT NULL,
                    distance_m REAL NOT NULL,
                    velocity_kmh REAL NOT NULL,
                    ttc_sec REAL,
                    severity TEXT NOT NULL,
                    image_path TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    max_severity TEXT NOT NULL,
                    object_type TEXT NOT NULL,
                    min_distance_m REAL NOT NULL,
                    min_ttc_sec REAL,
                    max_speed_kmh REAL NOT NULL,
                    image_path TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            cursor.execute("PRAGMA table_info(alert_logs)")
            existing_cols = {col[1] for col in cursor.fetchall()}
            migration_cols = [
                ("user_id", "INTEGER"),
                ("username", "TEXT"),
                ("start_time", "TEXT"),
                ("end_time", "TEXT"),
                ("min_distance_m", "REAL"),
                ("min_ttc_sec", "REAL"),
                ("max_speed_kmh", "REAL"),
                ("max_severity", "TEXT"),
                ("notes", "TEXT"),
                ("closing_speed_mps", "REAL"),
                ("speed_kmh_raw", "REAL"),
            ]
            for col_name, col_type in migration_cols:
                if col_name not in existing_cols:
                    cursor.execute(f"ALTER TABLE alert_logs ADD COLUMN {col_name} {col_type}")

            cursor.execute("PRAGMA table_info(incidents)")
            existing_inc_cols = {col[1] for col in cursor.fetchall()}
            inc_migration_cols = [
                ("user_id", "INTEGER"),
                ("username", "TEXT"),
                ("notes", "TEXT"),
                ("closing_speed_mps", "REAL"),
                ("speed_kmh_raw", "REAL"),
            ]
            for col_name, col_type in inc_migration_cols:
                if col_name not in existing_inc_cols:
                    cursor.execute(f"ALTER TABLE incidents ADD COLUMN {col_name} {col_type}")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            conn.commit()


# ================= QUẢN LÝ XÁC THỰC & NGƯỜI DÙNG (GIAI ĐOẠN 7) =================

def has_any_users() -> bool:
    """Kiểm tra hệ thống đã có tài khoản nào hay chưa (xác định lần chạy đầu tiên)"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0] > 0


def create_initial_admin(username: str, password: str, full_name: str = "Quản trị viên") -> Tuple[bool, str]:
    """
    Thiết lập tài khoản Admin đầu tiên khi hệ thống mới cài đặt.
    Không có tài khoản mặc định cố định trong mã nguồn. Mật khẩu phải >= 6 ký tự.
    """
    if has_any_users():
        return False, "Hệ thống đã có tài khoản quản trị. Không thể chạy lại thiết lập ban đầu."

    if len(password) < 6:
        return False, "Mật khẩu quản trị viên phải có độ dài tối thiểu 6 ký tự."

    cfg = get_config()
    iters = int(cfg.get("auth_pbkdf2_iterations", 100000))
    pwd_hash, salt = hash_password_pbkdf2(password, iterations=iters)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password_hash, salt, full_name, role, is_locked, failed_attempts, created_at)
            VALUES (?, ?, ?, ?, 'admin', 0, 0, ?)
        """, (username.strip(), pwd_hash, salt, full_name.strip(), now_str))
        conn.commit()

    record_login_attempt(username.strip(), "INITIAL_ADMIN_CREATED")
    return True, "Khởi tạo tài khoản Quản trị viên thành công."


def record_login_attempt(username: str, result: str, ip_address: str = "127.0.0.1") -> None:
    """Ghi vết đăng nhập vào bảng login_log để phục vụ kiểm toán an ninh"""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO login_log (timestamp, username, result, ip_address)
                VALUES (?, ?, ?, ?)
            """, (now_str, username, result, ip_address))
            conn.commit()
    except Exception:
        pass


def authenticate_user(username: str, password: str) -> Tuple[bool, Optional[dict], str]:
    """
    Xác thực người dùng (FR-01, FR-02).
    - Kiểm tra khóa tài khoản do sai 5 lần liên tiếp (khóa 5 phút).
    - Kiểm tra băm PBKDF2-HMAC-SHA256 với Salt riêng.
    - Ghi nhận nhật ký bảng login_log.
    Trả về: (thành_công: bool, thông_tin_user: Optional[dict], thông_báo: str)
    """
    username = username.strip()
    cfg = get_config()
    iters = int(cfg.get("auth_pbkdf2_iterations", 100000))
    max_failed = int(cfg.get("max_failed_logins", 5))
    lock_duration_sec = int(cfg.get("lockout_duration_sec", 300))

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, password_hash, salt, full_name, role, is_locked, failed_attempts, locked_until
            FROM users WHERE username = ?
        """, (username,))
        row = cursor.fetchone()

        if not row:
            record_login_attempt(username, "FAILED_USER_NOT_FOUND")
            return False, None, "Tên đăng nhập hoặc mật khẩu không chính xác."

        uid, uname, stored_hash, salt, fname, role, is_locked, failed_attempts, locked_until = row

        now = datetime.now()

        # Kiểm tra trạng thái khóa tài khoản
        if is_locked:
            if locked_until:
                try:
                    lock_time = datetime.strptime(locked_until, "%Y-%m-%d %H:%M:%S")
                    if now >= lock_time:
                        # Hết thời gian khóa 5 phút -> Tự động mở khóa
                        cursor.execute("UPDATE users SET is_locked = 0, failed_attempts = 0, locked_until = NULL WHERE id = ?", (uid,))
                        conn.commit()
                        is_locked = 0
                        failed_attempts = 0
                    else:
                        remaining_sec = int((lock_time - now).total_seconds())
                        mins = max(1, (remaining_sec + 59) // 60)
                        record_login_attempt(username, "FAILED_ACCOUNT_LOCKED")
                        return False, None, f"Tài khoản đang bị tạm khóa. Vui lòng thử lại sau {mins} phút."
                except Exception:
                    record_login_attempt(username, "FAILED_ACCOUNT_LOCKED")
                    return False, None, "Tài khoản hiện đang bị tạm khóa an ninh."
            else:
                record_login_attempt(username, "FAILED_ACCOUNT_LOCKED")
                return False, None, "Tài khoản đã bị Quản trị viên vô hiệu hóa."

        # Kiểm tra mật khẩu
        pwd_match = False
        if salt:
            pwd_match = verify_password_pbkdf2(password, stored_hash, salt, iterations=iters)
        else:
            # Fallback tương thích dữ liệu cũ: nếu tài khoản cũ chưa có salt, kiểm tra SHA256 cũ rồi tự nâng cấp
            old_hash = hashlib.sha256(f"DUT_23KTMT1_RADAR_CAMERA_FUSION_2026:{password}:DUT_23KTMT1_RADAR_CAMERA_FUSION_2026".encode('utf-8')).hexdigest()
            if old_hash == stored_hash:
                pwd_match = True
                # Tự động nâng cấp sang PBKDF2 với salt mới
                new_hash, new_salt = hash_password_pbkdf2(password, iterations=iters)
                cursor.execute("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?", (new_hash, new_salt, uid))
                conn.commit()

        if pwd_match:
            # Đăng nhập thành công -> Reset đếm lần thử sai
            cursor.execute("UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = ?", (uid,))
            conn.commit()
            record_login_attempt(username, "SUCCESS")
            user_data = {
                "id": uid,
                "username": uname,
                "full_name": fname,
                "role": role
            }
            return True, user_data, "Đăng nhập thành công."
        else:
            # Sai mật khẩu -> Tăng số lần thử
            new_failed = failed_attempts + 1
            if new_failed >= max_failed:
                lock_until_dt = now + timedelta(seconds=lock_duration_sec)
                lock_until_str = lock_until_dt.strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    UPDATE users SET is_locked = 1, failed_attempts = ?, locked_until = ? WHERE id = ?
                """, (new_failed, lock_until_str, uid))
                conn.commit()
                record_login_attempt(username, "FAILED_ACCOUNT_LOCKED")
                return False, None, f"Đăng nhập sai 5 lần liên tiếp. Tài khoản đã bị tạm khóa {lock_duration_sec // 60} phút."
            else:
                cursor.execute("UPDATE users SET failed_attempts = ? WHERE id = ?", (new_failed, uid))
                conn.commit()
                remain = max_failed - new_failed
                record_login_attempt(username, "FAILED_WRONG_PASSWORD")
                return False, None, f"Mật khẩu không chính xác. Bạn còn {remain} lần thử trước khi bị khóa."


def create_user(
    operator_role: str,
    username: str,
    password: str,
    full_name: str,
    role: str
) -> Tuple[bool, str]:
    """Tạo người dùng mới (chỉ Admin được phép - RBAC backend check)"""
    if operator_role != "admin":
        return False, "Từ chối truy cập: Chỉ Quản trị viên mới có quyền tạo người dùng."

    username = username.strip()
    if not username:
        return False, "Tên đăng nhập không được để trống."

    if len(password) < 6:
        return False, "Mật khẩu phải có độ dài tối thiểu 6 ký tự."

    if role not in ("admin", "operator"):
        return False, "Vai trò không hợp lệ (chỉ chấp nhận 'admin' hoặc 'operator')."

    cfg = get_config()
    iters = int(cfg.get("auth_pbkdf2_iterations", 100000))
    pwd_hash, salt = hash_password_pbkdf2(password, iterations=iters)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, password_hash, salt, full_name, role, is_locked, failed_attempts, created_at)
                VALUES (?, ?, ?, ?, ?, 0, 0, ?)
            """, (username, pwd_hash, salt, full_name.strip(), role, now_str))
            conn.commit()
        return True, f"Tạo tài khoản '{username}' thành công."
    except sqlite3.IntegrityError:
        return False, f"Tên đăng nhập '{username}' đã tồn tại trong hệ thống."


def register_user(
    username: str,
    password: str,
    full_name: str
) -> Tuple[bool, str]:
    """Tự đăng ký tài khoản người dùng mới (vai trò Operator mặc định)"""
    username = username.strip()
    if not username:
        return False, "Tên đăng nhập không được để trống."
    if len(username) < 3:
        return False, "Tên đăng nhập phải có ít nhất 3 ký tự."
    if not full_name.strip():
        return False, "Họ và tên không được để trống."
    if len(password) < 6:
        return False, "Mật khẩu phải có độ dài tối thiểu 6 ký tự."

    cfg = get_config()
    iters = int(cfg.get("auth_pbkdf2_iterations", 100000))
    pwd_hash, salt = hash_password_pbkdf2(password, iterations=iters)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Kiểm tra trùng tên đăng nhập (không phân biệt chữ hoa / thường)
            cursor.execute("SELECT 1 FROM users WHERE LOWER(username) = LOWER(?)", (username,))
            if cursor.fetchone():
                return False, f"Tên đăng nhập '{username}' đã tồn tại, vui lòng chọn tên khác."

            cursor.execute("""
                INSERT INTO users (username, password_hash, salt, full_name, role, is_locked, failed_attempts, created_at)
                VALUES (?, ?, ?, ?, 'operator', 0, 0, ?)
            """, (username, pwd_hash, salt, full_name.strip(), now_str))
            conn.commit()
        return True, f"Tạo tài khoản '{username}' thành công! Bạn có thể đăng nhập ngay."
    except sqlite3.IntegrityError:
        return False, f"Tên đăng nhập '{username}' đã tồn tại, vui lòng chọn tên khác."



def reset_user_password(
    operator_role: str,
    target_user_id: int,
    new_password: str
) -> Tuple[bool, str]:
    """Admin đặt lại mật khẩu cho một tài khoản"""
    if operator_role != "admin":
        return False, "Từ chối truy cập: Chỉ Quản trị viên mới có quyền đặt lại mật khẩu."

    if len(new_password) < 6:
        return False, "Mật khẩu mới phải có tối thiểu 6 ký tự."

    cfg = get_config()
    iters = int(cfg.get("auth_pbkdf2_iterations", 100000))
    pwd_hash, salt = hash_password_pbkdf2(new_password, iterations=iters)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE id = ?", (target_user_id,))
        if not cursor.fetchone():
            return False, "Không tìm thấy người dùng được chỉ định."

        cursor.execute("""
            UPDATE users SET password_hash = ?, salt = ?, failed_attempts = 0, is_locked = 0, locked_until = NULL
            WHERE id = ?
        """, (pwd_hash, salt, target_user_id))
        conn.commit()
    return True, "Đặt lại mật khẩu thành công."


def set_user_lock_status(
    operator_role: str,
    current_user_id: int,
    target_user_id: int,
    lock: bool
) -> Tuple[bool, str]:
    """Khóa hoặc mở khóa tài khoản (Admin only, không cho tự khóa chính mình)"""
    if operator_role != "admin":
        return False, "Từ chối truy cập: Chỉ Quản trị viên mới có quyền khóa/mở khóa tài khoản."

    if current_user_id == target_user_id and lock:
        return False, "Không thể tự khóa tài khoản của chính mình."

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE id = ?", (target_user_id,))
        row = cursor.fetchone()
        if not row:
            return False, "Không tìm thấy người dùng."

        if lock and row[0] == "admin":
            # Kiểm tra xem có phải admin duy nhất đang mở khóa không
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin' AND is_locked = 0")
            if cursor.fetchone()[0] <= 1:
                return False, "Không thể khóa Quản trị viên khả dụng cuối cùng của hệ thống."

        is_locked_val = 1 if lock else 0
        cursor.execute("""
            UPDATE users SET is_locked = ?, failed_attempts = 0, locked_until = NULL WHERE id = ?
        """, (is_locked_val, target_user_id))
        conn.commit()

    action_text = "Khóa" if lock else "Mở khóa"
    return True, f"Đã {action_text.lower()} tài khoản thành công."


def change_user_role(
    operator_role: str,
    current_user_id: int,
    target_user_id: int,
    new_role: str
) -> Tuple[bool, str]:
    """Thay đổi vai trò người dùng (không cho hạ quyền Admin cuối cùng)"""
    if operator_role != "admin":
        return False, "Từ chối truy cập: Chỉ Quản trị viên mới có quyền đổi vai trò người dùng."

    if new_role not in ("admin", "operator"):
        return False, "Vai trò mới không hợp lệ."

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE id = ?", (target_user_id,))
        row = cursor.fetchone()
        if not row:
            return False, "Không tìm thấy người dùng."

        current_target_role = row[0]
        if current_target_role == "admin" and new_role != "admin":
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            admin_count = cursor.fetchone()[0]
            if admin_count <= 1:
                return False, "Không thể hạ quyền Quản trị viên cuối cùng của hệ thống."

        cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, target_user_id))
        conn.commit()

    return True, f"Đã cập nhật vai trò sang '{new_role.upper()}'."


def delete_user(
    operator_role: str,
    current_user_id: int,
    target_user_id: int
) -> Tuple[bool, str]:
    """Xóa người dùng (không cho tự xóa mình, không cho xóa Admin cuối cùng)"""
    if operator_role != "admin":
        return False, "Từ chối truy cập: Chỉ Quản trị viên mới có quyền xóa người dùng."

    if current_user_id == target_user_id:
        return False, "Không thể tự xóa tài khoản của chính mình."

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE id = ?", (target_user_id,))
        row = cursor.fetchone()
        if not row:
            return False, "Không tìm thấy người dùng."

        target_role = row[0]
        if target_role == "admin":
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            admin_count = cursor.fetchone()[0]
            if admin_count <= 1:
                return False, "Không thể xóa Quản trị viên cuối cùng của hệ thống."

        cursor.execute("DELETE FROM users WHERE id = ?", (target_user_id,))
        conn.commit()

    return True, "Đã xóa tài khoản thành công."


def change_user_password(username: str, old_password: str, new_password: str) -> Tuple[bool, str]:
    """Người dùng tự đổi mật khẩu cá nhân (US-03)"""
    if len(new_password) < 6:
        return False, "Mật khẩu mới phải có tối thiểu 6 ký tự."

    username = username.strip()
    auth_ok, _, err_msg = authenticate_user(username, old_password)
    if not auth_ok:
        return False, f"Mật khẩu cũ không chính xác: {err_msg}"

    cfg = get_config()
    iters = int(cfg.get("auth_pbkdf2_iterations", 100000))
    pwd_hash, salt = hash_password_pbkdf2(new_password, iterations=iters)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password_hash = ?, salt = ? WHERE username = ?", (pwd_hash, salt, username))
        conn.commit()

    return True, "Đổi mật khẩu thành công!"


def get_all_users() -> List[tuple]:
    """Lấy danh sách người dùng cho Admin quản lý (US-02)"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, full_name, role, is_locked, failed_attempts, created_at 
            FROM users ORDER BY id ASC
        """)
        return cursor.fetchall()


# ================= CẤU HÌNH HỆ THỐNG & HIỆU CHUẨN =================

def get_setting(key, default=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM system_settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default


def get_all_settings():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM system_settings")
        return dict(cursor.fetchall())


def set_setting(key, value):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO system_settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, str(value)))
        conn.commit()


def save_bulk_settings(settings_dict):
    with get_connection() as conn:
        cursor = conn.cursor()
        for k, v in settings_dict.items():
            cursor.execute("""
                INSERT INTO system_settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (k, str(v)))
        conn.commit()


# ================= NHẬT KÝ SỰ CỐ & XUẤT BÁO CÁO (GIAI ĐOẠN 8) =================

def insert_alert(
    object_type: str,
    distance_m: float,
    velocity_kmh: float,
    ttc_sec: Optional[float],
    severity: str,
    image_path: str = "",
    user_id: Optional[int] = None,
    username: str = ""
):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alert_logs (timestamp, object_type, distance_m, velocity_kmh, ttc_sec, severity, image_path, user_id, username)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (now_str, object_type, round(distance_m, 2), round(abs(float(velocity_kmh)), 1), 
              round(ttc_sec, 2) if ttc_sec is not None else None, severity, image_path, user_id, username))
        conn.commit()


def insert_incident(
    start_time: str,
    end_time: str,
    max_severity: str,
    object_type: str = "Phương tiện",
    min_distance_m: float = 0.0,
    min_ttc_sec = None,
    max_speed_kmh: float = 0.0,
    image_path: str = "",
    notes: str = "",
    closing_speed_mps: float = 0.0,
    speed_kmh_raw: float = 0.0,
    user_id: Optional[int] = None,
    username: str = "",
) -> int:
    """Lưu trữ sự cố gom cụm gắn chặt với tài khoản người vận hành (Multi-user Isolation)"""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO incidents (start_time, end_time, max_severity, object_type, min_distance_m, min_ttc_sec, max_speed_kmh, image_path, notes, created_at, closing_speed_mps, speed_kmh_raw, user_id, username)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (start_time, end_time, max_severity, object_type, round(min_distance_m, 2),
              round(min_ttc_sec, 2) if min_ttc_sec is not None else None,
              round(abs(float(max_speed_kmh)), 1), image_path, notes, now_str,
              round(float(closing_speed_mps), 2), round(float(speed_kmh_raw), 1),
              user_id, username))
        inc_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO alert_logs (timestamp, object_type, distance_m, velocity_kmh, ttc_sec, severity, image_path,
                                    start_time, end_time, min_distance_m, min_ttc_sec, max_speed_kmh, max_severity, notes, closing_speed_mps, speed_kmh_raw, user_id, username)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (start_time, object_type, round(min_distance_m, 2), round(float(speed_kmh_raw), 1),
              round(min_ttc_sec, 2) if min_ttc_sec is not None else None, max_severity, image_path,
              start_time, end_time, round(min_distance_m, 2),
              round(min_ttc_sec, 2) if min_ttc_sec is not None else None,
              round(abs(float(max_speed_kmh)), 1), max_severity, notes,
              round(float(closing_speed_mps), 2), round(float(speed_kmh_raw), 1),
              user_id, username))
        conn.commit()
        return inc_id


def get_filtered_alerts(severity_filter="TẤT CẢ", search_text="", limit=100, user_id: Optional[int] = None, username: Optional[str] = None):
    query = "SELECT id, timestamp, object_type, distance_m, velocity_kmh, ttc_sec, severity, image_path, user_id, username FROM alert_logs WHERE 1=1"
    params = []
    if user_id is not None:
        if username:
            query += " AND (user_id = ? OR username = ?)"
            params.extend([user_id, username])
        else:
            query += " AND user_id = ?"
            params.append(user_id)
    elif username:
        query += " AND username = ?"
        params.append(username)
    if severity_filter and severity_filter != "TẤT CẢ":
        query += " AND severity LIKE ?"
        params.append(f"%{severity_filter}%")
    if search_text:
        query += " AND (object_type LIKE ? OR timestamp LIKE ? OR id = ? OR username LIKE ?)"
        params.extend([f"%{search_text}%", f"%{search_text}%", search_text if search_text.isdigit() else -1, f"%{search_text}%"])
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def get_filtered_incidents(
    severity_filter="TẤT CẢ",
    date_filter="",
    search_text="",
    limit=100,
    user_id: Optional[int] = None,
    username: Optional[str] = None
):
    """
    Lấy danh sách sự cố có phân quyền theo tài khoản người dùng:
    - Nếu có user_id (Operator): Chỉ lấy sự cố do chính tài khoản đó ghi nhận.
    - Nếu user_id is None (Admin): Lấy tất cả hoặc có thể tìm kiếm theo username.
    """
    query = """
        SELECT id, start_time, end_time, object_type, min_distance_m, max_speed_kmh, min_ttc_sec, max_severity, image_path, notes, closing_speed_mps, speed_kmh_raw, user_id, username 
        FROM incidents WHERE 1=1
    """
    params = []
    if user_id is not None:
        if username:
            query += " AND (user_id = ? OR username = ?)"
            params.extend([user_id, username])
        else:
            query += " AND user_id = ?"
            params.append(user_id)
    elif username:
        query += " AND username = ?"
        params.append(username)
    if severity_filter and severity_filter != "TẤT CẢ":
        query += " AND max_severity LIKE ?"
        params.append(f"%{severity_filter}%")
    if date_filter:
        query += " AND (start_time LIKE ? OR end_time LIKE ?)"
        params.extend([f"{date_filter}%", f"{date_filter}%"])
    if search_text:
        query += " AND (object_type LIKE ? OR start_time LIKE ? OR id = ? OR username LIKE ?)"
        params.extend([f"%{search_text}%", f"%{search_text}%", search_text if search_text.isdigit() else -1, f"%{search_text}%"])
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        if not rows and not date_filter and user_id is None:
            cursor.execute("""
                SELECT id, timestamp, timestamp, object_type, distance_m, velocity_kmh, ttc_sec, severity, image_path, notes, closing_speed_mps, velocity_kmh, user_id, username
                FROM alert_logs ORDER BY id DESC LIMIT ?
            """, (limit,))
            return cursor.fetchall()
        return rows


def export_to_csv(export_path: str, severity_filter: str = "TẤT CẢ", date_filter: str = "", user_id: Optional[int] = None, username: Optional[str] = None) -> int:
    """Xuất danh sách sự cố ra file CSV với mã hóa UTF-8 BOM (utf-8-sig) có gắn tài khoản"""
    records = get_filtered_incidents(severity_filter=severity_filter, date_filter=date_filter, search_text="", limit=10000, user_id=user_id, username=username)
    headers = [
        "Mã sự cố (ID)",
        "Thời gian bắt đầu",
        "Thời gian kết thúc",
        "Loại đối tượng",
        "Khoảng cách nhỏ nhất (m)",
        "Vận tốc lớn nhất (km/h)",
        "Thời gian va chạm TTC min (s)",
        "Mức độ cảnh báo cao nhất",
        "Đường dẫn ảnh bằng chứng",
        "Ghi chú",
        "Tốc độ tiếp cận (m/s)",
        "Tốc độ thô (km/h)",
        "User ID",
        "Tài khoản người vận hành"
    ]
    with open(export_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for r in records:
            writer.writerow(r)
    return len(records)


def export_to_excel(export_path: str, severity_filter: str = "TẤT CẢ", date_filter: str = "", user_id: Optional[int] = None, username: Optional[str] = None) -> int:
    """Xuất báo cáo sự cố chuyên nghiệp dạng bảng tính Microsoft Excel (.xlsx) qua openpyxl có gắn tài khoản"""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    records = get_filtered_incidents(severity_filter=severity_filter, date_filter=date_filter, search_text="", limit=10000, user_id=user_id, username=username)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Nhat_Ky_Su_Co"

    headers = [
        "Mã sự cố",
        "Thời gian bắt đầu",
        "Thời gian kết thúc",
        "Loại đối tượng",
        "Khoảng cách min (m)",
        "Vận tốc max (km/h)",
        "TTC min (s)",
        "Mức cảnh báo",
        "Đường dẫn ảnh",
        "Ghi chú",
        "Tốc độ m/s",
        "Tốc độ thô",
        "User ID",
        "Tài khoản người vận hành"
    ]
    ws.append(headers)

    header_fill = PatternFill(start_color="1E2329", end_color="1E2329", fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    thin_border = Border(
        left=Side(style='thin', color='CCCCCC'),
        right=Side(style='thin', color='CCCCCC'),
        top=Side(style='thin', color='CCCCCC'),
        bottom=Side(style='thin', color='CCCCCC')
    )

    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

    for r_idx, r in enumerate(records, start=2):
        row_vals = list(r)
        while len(row_vals) < len(headers):
            row_vals.append("")
        ws.append(row_vals[:len(headers)])

        for c_idx in range(1, len(headers) + 1):
            c = ws.cell(row=r_idx, column=c_idx)
            c.font = Font(name="Segoe UI", size=10)
            c.border = thin_border
            if c_idx in (1, 5, 6, 7, 13):
                c.alignment = Alignment(horizontal="center", vertical="center")

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = col[0].column_letter
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    wb.save(export_path)
    return len(records)


def export_incidents(export_path: str, severity_filter: str = "TẤT CẢ", date_filter: str = "", user_id: Optional[int] = None, username: Optional[str] = None) -> int:
    """Tự động phân nhánh xuất CSV hoặc Excel tùy theo đuôi tệp"""
    if export_path.lower().endswith(".xlsx"):
        return export_to_excel(export_path, severity_filter, date_filter, user_id=user_id, username=username)
    else:
        return export_to_csv(export_path, severity_filter, date_filter, user_id=user_id, username=username)


if __name__ == "__main__":
    init_db()
    print("Database & RBAC initialized successfully at:", DB_PATH)
