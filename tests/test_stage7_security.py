# -*- coding: utf-8 -*-
"""
Kiểm thử Giai đoạn 7: Quản lý Người dùng & Bảo mật (SRS US-01..03, FR-01, FR-02)
- Kiểm tra băm mật khẩu PBKDF2-HMAC-SHA256 với salt ngẫu nhiên
- Kiểm tra thiết lập lần đầu và không dùng tài khoản cố định
- Kiểm tra khóa 5 phút sau 5 lần đăng nhập sai liên tiếp
- Kiểm tra phân quyền RBAC: Operator bị chặn ở tầng logic
- Kiểm tra bảo vệ Admin cuối cùng và không cho tự khóa mình
"""

import os
import sqlite3
import pytest
import database


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Fixture tạo CSDL SQLite tạm thời cho từng ca kiểm thử"""
    db_file = str(tmp_path / "test_security.db")
    monkeypatch.setattr(database, "DB_PATH", db_file)
    database.init_db()
    return db_file


def test_pbkdf2_hashing_and_salt_verification():
    """Kiểm tra băm PBKDF2: cùng mật khẩu nhưng khác salt cho ra 2 chuỗi băm khác nhau"""
    pwd = "SecretPassword123!"
    hash1, salt1 = database.hash_password_pbkdf2(pwd, iterations=5000)
    hash2, salt2 = database.hash_password_pbkdf2(pwd, iterations=5000)

    assert salt1 != salt2
    assert hash1 != hash2

    # Xác thực mật khẩu
    assert database.verify_password_pbkdf2(pwd, hash1, salt1, iterations=5000) is True
    assert database.verify_password_pbkdf2(pwd, hash2, salt2, iterations=5000) is True
    assert database.verify_password_pbkdf2("WrongPassword", hash1, salt1, iterations=5000) is False


def test_first_run_initial_admin_setup(temp_db):
    """Kiểm tra quy trình thiết lập lần đầu: bắt buộc tạo Admin, mật khẩu >= 6 ký tự"""
    assert database.has_any_users() is False

    # Thử tạo mật khẩu ngắn (< 6 ký tự) -> phải thất bại
    ok, msg = database.create_initial_admin("superadmin", "12345")
    assert ok is False
    assert database.has_any_users() is False

    # Tạo hợp lệ
    ok, msg = database.create_initial_admin("superadmin", "AdminSecure#2026")
    assert ok is True
    assert database.has_any_users() is True

    # Không cho chạy lại thiết lập lần đầu khi đã có tài khoản
    ok2, _ = database.create_initial_admin("hacker", "123456")
    assert ok2 is False


def test_login_lockout_after_5_failed_attempts(temp_db):
    """Kiểm tra khóa tài khoản 5 phút khi nhập sai 5 lần liên tiếp"""
    database.create_initial_admin("admin_test", "CorrectPassword123")

    # Đăng nhập sai 4 lần -> chưa khóa
    for attempt in range(1, 5):
        ok, user, msg = database.authenticate_user("admin_test", "WrongPassword")
        assert ok is False
        assert user is None
        assert "Bạn còn" in msg

    # Lần thứ 5 sai -> kích hoạt khóa 5 phút
    ok5, user5, msg5 = database.authenticate_user("admin_test", "WrongPassword")
    assert ok5 is False
    assert "tạm khóa" in msg5

    # Thử lại với mật khẩu ĐÚNG trong khi đang bị khóa -> vẫn bị từ chối
    ok_blocked, _, msg_blocked = database.authenticate_user("admin_test", "CorrectPassword123")
    assert ok_blocked is False
    assert "đang bị tạm khóa" in msg_blocked


def test_rbac_operator_blocked_from_admin_functions(temp_db):
    """Kiểm tra phân quyền: Vai trò Operator bị chặn ở tầng logic đối với mọi hàm quản trị"""
    database.create_initial_admin("admin_root", "RootPassword123")

    # Admin tạo tài khoản Operator
    ok, _ = database.create_user("admin", "op_user", "Operator123", "Nhân viên trực", "operator")
    assert ok is True

    # 1. Operator thử tạo tài khoản mới -> Bị chặn
    ok_create, msg = database.create_user("operator", "rogue_user", "Password123", "Rogue", "operator")
    assert ok_create is False
    assert "Từ chối truy cập" in msg

    # 2. Operator thử đặt lại mật khẩu của người khác -> Bị chặn
    ok_reset, msg = database.reset_user_password("operator", 1, "NewPassword123")
    assert ok_reset is False
    assert "Từ chối truy cập" in msg

    # 3. Operator thử thay đổi vai trò -> Bị chặn
    ok_role, msg = database.change_user_role("operator", 2, 2, "admin")
    assert ok_role is False
    assert "Từ chối truy cập" in msg

    # 4. Operator thử khóa tài khoản -> Bị chặn
    ok_lock, msg = database.set_user_lock_status("operator", 2, 1, True)
    assert ok_lock is False
    assert "Từ chối truy cập" in msg


def test_protect_last_admin_and_prevent_self_locking(temp_db):
    """Kiểm tra bảo vệ an toàn: Không cho xóa hoặc hạ quyền Admin cuối, không cho tự khóa mình"""
    database.create_initial_admin("admin_root", "RootPassword123")

    with database.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = 'admin_root'")
        admin_id = cursor.fetchone()[0]

    # 1. Admin không thể tự khóa tài khoản của chính mình
    ok_self_lock, msg = database.set_user_lock_status("admin", admin_id, admin_id, True)
    assert ok_self_lock is False
    assert "tự khóa" in msg

    # 2. Không thể hạ quyền Admin cuối cùng của hệ thống
    ok_demote, msg = database.change_user_role("admin", admin_id, admin_id, "operator")
    assert ok_demote is False
    assert "Admin cuối cùng" in msg or "Quản trị viên cuối cùng" in msg

    # 3. Không thể tự xóa chính mình
    ok_del_self, msg = database.delete_user("admin", admin_id, admin_id)
    assert ok_del_self is False
    assert "tự xóa" in msg

    # 4. Không thể xóa Admin duy nhất
    ok_del_last, msg = database.delete_user("admin", 999, admin_id)
    assert ok_del_last is False
    assert "Quản trị viên cuối cùng" in msg
