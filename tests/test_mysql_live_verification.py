"""
Test script for live MySQL verification and per-user data isolation test.
"""
import sys
import os

# Add project root to sys.path
sys.path.insert(0, r"C:\DAIHOC\CNPM_Project")

import database

def test_live_mysql():
    print("=== BẮT ĐẦU TEST TOÀN DIỆN CSDL MYSQL ===")
    
    # 1. Initialize DB
    print("[1] Khởi tạo CSDL qua database.init_db()...")
    database.init_db()
    
    # 2. Check active engine
    db_info = database.get_active_db_info()
    backend = db_info.get("backend")
    print(f"    -> Động cơ CSDL đang kết nối: {backend.upper()}")
    print(f"    -> Host: {db_info.get('mysql_host')}:{db_info.get('mysql_port')}")
    print(f"    -> Database: {db_info.get('mysql_database')}")
    assert backend == "mysql", f"Kỳ vọng 'mysql' nhưng nhận được '{backend}'!"
    
    # 3. Check tables
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("SHOW TABLES")
    raw_tables = cur.fetchall()
    tables = [t[0] if isinstance(t, (tuple, list)) else list(t.values())[0] for t in raw_tables]
    print(f"[2] Danh sách các bảng trong MySQL: {tables}")
    required_tables = ["users", "incidents", "alert_logs", "login_log"]
    for rt in required_tables:
        assert rt in tables, f"Thiếu bảng '{rt}' trong MySQL!"
    print("    -> Đầy đủ tất cả các bảng nghiệp vụ!")
    
    # 4. Check users seed
    cur.execute("SELECT id, username, role, full_name FROM users ORDER BY id ASC")
    users = cur.fetchall()
    print(f"[3] Danh sách tài khoản người dùng ({len(users)} tài khoản):")
    for u in users:
        print(f"    - ID: {u[0]} | User: {u[1]} | Quyền: {u[2]} | Tên: {u[3]}")
    user_names = [u[1] for u in users]
    assert "admin" in user_names, "Thiếu tài khoản admin!"
    assert "phong123" in user_names, "Thiếu tài khoản phong123!"
    assert "ngoquangthe123" in user_names, "Thiếu tài khoản ngoquangthe123!"
    
    # 5. Test multi-user isolation
    print("[4] Kiểm tra phân quyền và cô lập dữ liệu theo tài khoản...")
    
    # Clean previous test records
    cur.execute("DELETE FROM alert_logs WHERE object_type LIKE '%TEST_ISOLATION%'")
    cur.execute("DELETE FROM incidents WHERE notes LIKE '%TEST_ISOLATION%'")
    conn.commit()
    
    # Check or create phong123
    cur.execute("SELECT id FROM users WHERE username = 'phong123'")
    u_phong = cur.fetchone()
    if not u_phong:
        u_phong_id = database.create_user("phong123", "123456", "Phòng Vận Hành", "operator")
    else:
        u_phong_id = u_phong[0]
        
    # Check or create ngoquangthe123
    cur.execute("SELECT id FROM users WHERE username = 'ngoquangthe123'")
    u_the = cur.fetchone()
    if not u_the:
        u_the_id = database.create_user("ngoquangthe123", "123456", "Ngô Quang Thế", "operator")
    else:
        u_the_id = u_the[0]
        
    print(f"    - Tài khoản phong123 (ID: {u_phong_id})")
    print(f"    - Tài khoản ngoquangthe123 (ID: {u_the_id})")
    
    # phong123 records an incident
    inc_id_phong = database.insert_incident(
        start_time="2026-11-27 16:00:00",
        end_time="2026-11-27 16:00:05",
        max_severity="danger",
        object_type="car",
        min_distance_m=1.2,
        min_ttc_sec=1.1,
        max_speed_kmh=45.0,
        image_path="",
        notes="TEST_ISOLATION_PHONG",
        user_id=u_phong_id,
        username="phong123"
    )
    
    # ngoquangthe123 records an incident
    inc_id_the = database.insert_incident(
        start_time="2026-11-27 16:05:00",
        end_time="2026-11-27 16:05:05",
        max_severity="warning",
        object_type="motorbike",
        min_distance_m=2.8,
        min_ttc_sec=2.5,
        max_speed_kmh=30.0,
        image_path="",
        notes="TEST_ISOLATION_THE",
        user_id=u_the_id,
        username="ngoquangthe123"
    )
    
    # Test query as phong123 (Operator: passed user_id)
    incidents_phong = database.get_filtered_incidents(user_id=u_phong_id)
    notes_phong = [inc[9] for inc in incidents_phong]
    assert "TEST_ISOLATION_PHONG" in notes_phong, "phong123 không nhìn thấy sự cố của mình!"
    assert "TEST_ISOLATION_THE" not in notes_phong, "LỖI BẢO MẬT: phong123 nhìn thấy sự cố của ngoquangthe123!"
    print("    -> XÁC NHẬN: phong123 chỉ thấy dữ liệu của phong123 (Bảo mật ĐẠT)")
    
    # Test query as ngoquangthe123 (Operator: passed user_id)
    incidents_the = database.get_filtered_incidents(user_id=u_the_id)
    notes_the = [inc[9] for inc in incidents_the]
    assert "TEST_ISOLATION_THE" in notes_the, "ngoquangthe123 không nhìn thấy sự cố của mình!"
    assert "TEST_ISOLATION_PHONG" not in notes_the, "LỖI BẢO MẬT: ngoquangthe123 nhìn thấy sự cố của phong123!"
    print("    -> XÁC NHẬN: ngoquangthe123 chỉ thấy dữ liệu của ngoquangthe123 (Bảo mật ĐẠT)")
    
    # Test query as admin (Admin: user_id=None -> all)
    incidents_admin_all = database.get_filtered_incidents(user_id=None)
    notes_admin_all = [inc[9] for inc in incidents_admin_all]
    assert "TEST_ISOLATION_PHONG" in notes_admin_all, "admin phải thấy được toàn bộ sự cố (thiếu phong)!"
    assert "TEST_ISOLATION_THE" in notes_admin_all, "admin phải thấy được toàn bộ sự cố (thiếu the)!"
    print("    -> XÁC NHẬN: admin có quyền xem toàn bộ dữ liệu sự cố của mọi tài khoản (ĐẠT)")
    
    # Test admin filter by username
    incidents_admin_phong = database.get_filtered_incidents(username="phong123")
    notes_admin_phong = [inc[9] for inc in incidents_admin_phong]
    assert "TEST_ISOLATION_PHONG" in notes_admin_phong
    assert "TEST_ISOLATION_THE" not in notes_admin_phong
    print("    -> XÁC NHẬN: admin có thể lọc sự cố theo từng tài khoản riêng biệt (ĐẠT)")
    
    # Clean up test rows
    cur.execute("DELETE FROM incidents WHERE notes LIKE '%TEST_ISOLATION%'")
    conn.commit()
    conn.close()
    
    print("=== TẤT CẢ CÁC BƯỚC TEST MYSQL VÀ PHÂN QUYỀN THÀNH CÔNG 100% ===")

if __name__ == "__main__":
    test_live_mysql()
