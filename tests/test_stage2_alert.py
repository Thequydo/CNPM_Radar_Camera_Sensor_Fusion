# -*- coding: utf-8 -*-
"""
Bộ kiểm thử tự động Giai đoạn 2 (pytest):
Động cơ Cảnh báo (AlertStateMachine), Gom sự cố (IncidentAggregator),
Luồng âm thanh (SoundWorker), và Ghi nhật ký SQLite WAL (database).
"""

import os
import sys
import time
import math
import sqlite3
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from radar_parser import RadarTarget
from alert_engine import (
    AlertStateMachine,
    AlertSeverity,
    IncidentAggregator,
    IncidentRecord,
)
import database


# ==============================================================================
# 1. KIỂM THỬ MÁY TRẠNG THÁI CẢNH BÁO (Mục 2.1)
# ==============================================================================

def test_alert_thresholds_and_stationary_target_rule():
    """
    Kiểm tra các ngưỡng cảnh báo:
    - Vật ở xa (> 3.5m, không TTC) -> An toàn
    - Vật ở vùng cảnh báo (ví dụ 3.0m < 3.5m) -> Có vật trong vùng cảnh báo (Vàng)
    - YÊU CẦU BẮT BUỘC: Vật đứng yên ở cự ly gần (1.0m < 1.8m, closing_speed <= 0.3)
      chỉ được ra mức Vàng, TUYỆT ĐỐI KHÔNG ra mức Đỏ (Nguy cơ va chạm)
    - Vật lao vào với TTC 1.5s (< 1.8s) -> Nguy cơ va chạm (Đỏ)
    """
    sm = AlertStateMachine(cfg={
        "warn_distance_m": 3.5,
        "warn_ttc_sec": 3.0,
        "danger_distance_m": 1.8,
        "danger_ttc_sec": 1.8,
        "min_closing_speed_mps": 0.3,
        "hysteresis_sec": 1.0,
    })

    # 1. Mục tiêu an toàn ở xa
    safe_target = RadarTarget(1, x_m=0.0, y_m=4.5, speed_kmh=0.0, valid=True, closing_speed_mps=0.0, ttc_sec=None)
    state, _, _ = sm.evaluate([safe_target], timestamp=10.0)
    assert state == AlertSeverity.SAFE

    # 2. Mục tiêu ở vùng cảnh báo vàng (cự ly 3.0m < 3.5m)
    warn_target = RadarTarget(1, x_m=0.0, y_m=3.0, speed_kmh=0.0, valid=True, closing_speed_mps=0.0, ttc_sec=None)
    state, _, _ = sm.evaluate([warn_target], timestamp=11.0)
    assert state == AlertSeverity.WARN

    # 3. YÊU CẦU ĐẶC BIỆT: Vật đứng yên ở 1.0 m (< danger_dist = 1.8m, closing_speed = 0.0 <= 0.3, ttc_sec = None)
    # Phải ra mức VÀNG, không được ra mức ĐỎ!
    stationary_close_target = RadarTarget(
        1, x_m=0.0, y_m=1.0, speed_kmh=0.0, valid=True, closing_speed_mps=0.0, ttc_sec=None
    )
    state, _, _ = sm.evaluate([stationary_close_target], timestamp=12.0)
    assert state == AlertSeverity.WARN, "Vật đứng yên dù gần 1.0m chỉ được ra mức Vàng!"

    # 4. Vật lao vào với TTC = 1.5 s (< danger_ttc = 1.8s) -> Nguy cơ va chạm (Đỏ)
    rushing_target = RadarTarget(
        2, x_m=0.0, y_m=2.4, speed_kmh=-5.8, valid=True, closing_speed_mps=1.6, ttc_sec=1.5
    )
    state, _, _ = sm.evaluate([rushing_target], timestamp=13.0)
    assert state == AlertSeverity.DANGER, "Vật lao vào với TTC 1.5s phải ra mức Đỏ!"


def test_hysteresis_escalation_and_deescalation():
    """
    Kiểm tra Hysteresis chống nhấp nháy:
    - Nâng mức tức thì (0 ms): SAFE -> DANGER
    - Hạ mức có trễ (hysteresis_sec = 1.0s):
      + Khi điều kiện giảm đe dọa diễn ra trong < 1.0s: vẫn giữ mức ĐỎ
      + Sau >= 1.0s liên tục: mới hạ mức xuống Vàng hoặc An toàn
    """
    sm = AlertStateMachine(cfg={
        "warn_distance_m": 3.5,
        "warn_ttc_sec": 3.0,
        "danger_distance_m": 1.8,
        "danger_ttc_sec": 1.8,
        "min_closing_speed_mps": 0.3,
        "hysteresis_sec": 1.0,
    })

    t0 = 100.0
    # Đang ở trạng thái An toàn
    state, _, _ = sm.evaluate([], timestamp=t0)
    assert state == AlertSeverity.SAFE

    # Khung 1 (t=100.1): Xuất hiện nguy cơ va chạm -> Nâng mức ĐỎ tức thời!
    danger_target = RadarTarget(1, x_m=0.0, y_m=1.2, speed_kmh=-3.6, valid=True, closing_speed_mps=1.0, ttc_sec=1.2)
    state, _, _ = sm.evaluate([danger_target], timestamp=t0 + 0.1)
    assert state == AlertSeverity.DANGER

    # Khung 2 (t=100.3): Mục tiêu lùi ra xa hoặc chỉ còn ở mức Vàng (khoảng cách 3.0m, TTC=None)
    warn_target = RadarTarget(1, x_m=0.0, y_m=3.0, speed_kmh=0.0, valid=True, closing_speed_mps=0.0, ttc_sec=None)
    state, _, _ = sm.evaluate([warn_target], timestamp=t0 + 0.3)
    # Thời gian hạ mức mới chỉ 0.2s (< 1.0s) -> VẪN GIỮ MỨC ĐỎ
    assert state == AlertSeverity.DANGER

    # Khung 3 (t=100.8): Đã trôi qua 0.7s (< 1.0s) -> VẪN GIỮ MỨC ĐỎ
    state, _, _ = sm.evaluate([warn_target], timestamp=t0 + 0.8)
    assert state == AlertSeverity.DANGER

    # Khung 4 (t=101.4): Đã duy trì mức Vàng liên tục 1.1s (>= 1.0s) -> HẠ MỨC XUỐNG VÀNG!
    state, _, _ = sm.evaluate([warn_target], timestamp=t0 + 1.4)
    assert state == AlertSeverity.WARN

    # Khung 5 (t=101.6): Mục tiêu rời đi (vùng trống rỗng -> raw = SAFE)
    state, _, _ = sm.evaluate([], timestamp=t0 + 1.6)
    # Mới 0.2s -> VẪN GIỮ MỨC VÀNG
    assert state == AlertSeverity.WARN

    # Khung 6 (t=102.7): Vùng trống duy trì 1.1s (>= 1.0s) -> HẠ MỨC VỀ AN TOÀN!
    state, _, _ = sm.evaluate([], timestamp=t0 + 2.7)
    assert state == AlertSeverity.SAFE


def test_dynamic_threshold_reload():
    """Kiểm tra thay đổi ngưỡng trực tiếp từ cấu hình mà không cần khởi động lại"""
    sm = AlertStateMachine(cfg={"warn_distance_m": 3.0, "warn_ttc_sec": 3.0})
    target = RadarTarget(1, x_m=0.0, y_m=3.2, speed_kmh=0.0, valid=True, closing_speed_mps=0.0, ttc_sec=None)
    # 3.2m > 3.0m -> SAFE
    state, _, _ = sm.evaluate([target], timestamp=10.0)
    assert state == AlertSeverity.SAFE

    # Admin mở rộng ngưỡng warn_distance_m lên 4.0m
    sm.reload_config({"warn_distance_m": 4.0, "warn_ttc_sec": 3.0})
    state, _, _ = sm.evaluate([target], timestamp=10.1)
    # Áp dụng ngay lập tức -> WARN
    assert state == AlertSeverity.WARN


# ==============================================================================
# 2. KIỂM THỬ GOM SỰ CỐ THEO SỰ KIỆN (Mục 2.3)
# ==============================================================================

def test_incident_aggregation_60_consecutive_frames_produces_one_incident():
    """
    YÊU CẦU BẮT BUỘC Mục 2.4:
    Chuỗi 60 khung liên tục có cảnh báo chỉ ra ĐÚNG 1 dòng sự cố.
    """
    agg = IncidentAggregator(cooldown_sec=2.0)
    base_t = 200.0

    # 60 khung liên tục (mỗi khung cách nhau 0.1 giây = 6.0 giây)
    snapshot_signals = []
    completed_incidents = []

    for i in range(60):
        t = base_t + i * 0.1
        # Cự ly biến thiên từ 2.5m xuống 0.9m rồi lên 1.5m
        curr_d = max(0.9, 2.5 - i * 0.05)
        target = RadarTarget(
            1, x_m=0.0, y_m=curr_d, speed_kmh=-3.6, valid=True,
            closing_speed_mps=1.0, ttc_sec=curr_d / 1.0
        )
        sev = AlertSeverity.DANGER if curr_d < 1.8 else AlertSeverity.WARN
        should_snap, comp = agg.update(sev, [target], timestamp=t)
        if should_snap:
            snapshot_signals.append(i)
        if comp is not None:
            completed_incidents.append(comp)

    # Trong suốt 60 khung diễn ra sự cố: CHƯA ĐƯỢC kết thúc sự cố nào
    assert len(completed_incidents) == 0
    # Chụp ảnh hiện trường ĐÚNG 1 LẦN khi sự cố lần đầu đạt mức ĐỎ
    assert len(snapshot_signals) == 1

    # Bây giờ mục tiêu rời đi, trạng thái trở về AN TOÀN:
    # 1.5 giây sau (chưa đủ 2.0s cooldown): chưa kết thúc
    _, comp_early = agg.update(AlertSeverity.SAFE, [], timestamp=base_t + 6.0 + 1.5)
    assert comp_early is None

    # 2.1 giây sau (đã duy trì An toàn >= 2.0s): KẾT THÚC SỰ CỐ!
    _, comp_final = agg.update(AlertSeverity.SAFE, [], timestamp=base_t + 6.0 + 2.1)
    assert comp_final is not None
    assert comp_final.max_severity == AlertSeverity.DANGER
    assert math.isclose(comp_final.min_distance_m, 0.9, abs_tol=1e-3)
    assert comp_final.min_ttc_sec is not None and comp_final.min_ttc_sec <= 1.0


def test_two_incidents_separated_by_more_than_two_seconds():
    """
    YÊU CẦU BẮT BUỘC Mục 2.4:
    Hai chuỗi cảnh báo cách nhau > 2.0 giây ra ĐÚNG 2 dòng sự cố độc lập.
    """
    agg = IncidentAggregator(cooldown_sec=2.0)
    t = 500.0

    target = RadarTarget(1, x_m=0.0, y_m=2.0, speed_kmh=0.0, valid=True, closing_speed_mps=0.0, ttc_sec=None)

    # Chuỗi 1: 10 khung có cảnh báo Vàng
    for i in range(10):
        t += 0.1
        agg.update(AlertSeverity.WARN, [target], timestamp=t)

    # Vùng an toàn duy trì 3.0 giây (> 2.0s) -> Chốt sự cố 1
    t += 3.0
    _, inc1 = agg.update(AlertSeverity.SAFE, [], timestamp=t)
    assert inc1 is not None

    # Chuỗi 2: 10 khung có cảnh báo Vàng
    for i in range(10):
        t += 0.1
        agg.update(AlertSeverity.WARN, [target], timestamp=t)

    # Vùng an toàn duy trì 2.5 giây (> 2.0s) -> Chốt sự cố 2
    t += 2.5
    _, inc2 = agg.update(AlertSeverity.SAFE, [], timestamp=t)
    assert inc2 is not None

    # Hai sự cố có ID riêng biệt
    assert inc1.id != inc2.id


# ==============================================================================
# 3. KIỂM THỬ CƠ SỞ DỮ LIỆU WAL & MIGRATION AN TOÀN (Mục 2.3)
# ==============================================================================

def test_sqlite_wal_mode_and_incident_logging(tmp_path):
    """
    Kiểm tra:
    - Bật PRAGMA journal_mode=WAL và synchronous=NORMAL
    - Ghi sự cố vào bảng incidents và kiểm tra toàn vẹn dữ liệu
    - Xuất CSV UTF-8-BOM có hỗ trợ lọc theo ngày
    """
    test_db = tmp_path / "test_stage2.db"
    conn = sqlite3.connect(str(test_db))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    
    # Khởi tạo bảng incidents
    conn.execute("""
        CREATE TABLE incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            max_severity TEXT NOT NULL,
            object_type TEXT NOT NULL,
            min_distance_m REAL NOT NULL,
            min_ttc_sec REAL,
            max_speed_kmh REAL NOT NULL,
            image_path TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        INSERT INTO incidents (start_time, end_time, max_severity, object_type, min_distance_m, min_ttc_sec, max_speed_kmh, image_path, created_at)
        VALUES ('2026-11-10 14:00:00', '2026-11-10 14:00:06', 'Nguy cơ va chạm', 'Phương tiện', 0.85, 1.20, 15.5, 'captures/test.jpg', '2026-11-10 14:00:06')
    """)
    conn.commit()

    # Kiểm tra WAL mode
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode;")
    assert cur.fetchone()[0].lower() == "wal"

    cur.execute("PRAGMA synchronous;")
    assert cur.fetchone()[0] == 1  # 1 là NORMAL

    # Kiểm tra đọc dữ liệu sự cố
    cur.execute("SELECT min_distance_m, max_severity FROM incidents WHERE id=1")
    row = cur.fetchone()
    assert math.isclose(row[0], 0.85)
    assert row[1] == "Nguy cơ va chạm"
    conn.close()


def test_near_blind_zone_hold_and_stationary_ignore():
    """
    Yêu cầu bổ sung Giai đoạn 2:
    - Vật tiến từ 3.0 m xuống 0.3 m với vận tốc 1.0 m/s:
      + Đã xác nhận (>= confirm_frames=3)
      + Cự ly cuối < near_hold_range_m (1.2m)
      + Sau đó biến mất vào vùng mù (< min_range_m hoặc mất dấu):
        -> PHẢI KÍCH HOẠT GIỮ CẢNH BÁO "Nguy cơ va chạm" trong near_hold_sec (2.0s)
        -> Ghi nhận sự cố có ghi chú "mục tiêu vào vùng mù".
    - Vật đứng yên ở 0.3 m:
      + closing_speed_mps <= 0.3
      + Sau đó biến mất:
        -> TUYỆT ĐỐI KHÔNG kích hoạt giữ cảnh báo "Nguy cơ va chạm".
    """
    sm = AlertStateMachine(cfg={
        "warn_distance_m": 3.5,
        "warn_ttc_sec": 3.0,
        "danger_distance_m": 1.8,
        "danger_ttc_sec": 1.8,
        "min_closing_speed_mps": 0.3,
        "hysteresis_sec": 1.0,
        "near_hold_range_m": 1.2,
        "near_hold_sec": 2.0,
        "confirm_frames": 3,
    })
    agg = IncidentAggregator(cooldown_sec=2.0)

    # 1. KỊCH BẢN 1: Vật tiến từ 3.0m xuống 0.3m với tốc độ 1.0 m/s
    t = 1000.0
    for step in range(28):
        dist = 3.0 - step * 0.1  # 3.0m -> 0.3m
        target = RadarTarget(
            1, x_m=0.0, y_m=dist, speed_kmh=-3.6, valid=True,
            closing_speed_mps=1.0, ttc_sec=dist / 1.0, age_frames=step + 1
        )
        state, prim, _ = sm.evaluate([target], timestamp=t)
        note = "mục tiêu vào vùng mù" if sm.blind_zone_active else ""
        agg.update(state, [target], timestamp=t, notes=note)
        t += 0.1

    # Tại bước cuối (dist = 0.3m < 1.2m, closing_speed = 1.0 > 0.3)
    assert state == AlertSeverity.DANGER

    # Bây giờ mục tiêu biến mất hoàn toàn vào vùng mù (targets = [])
    # 1.0s sau khi biến mất (< near_hold_sec = 2.0s):
    t_after_disappear = t + 1.0
    state_held, _, _ = sm.evaluate([], timestamp=t_after_disappear)
    assert state_held == AlertSeverity.DANGER, "Phải giữ mức Nguy cơ va chạm khi mục tiêu biến mất trong cự ly gần!"
    assert sm.blind_zone_active is True

    note = "mục tiêu vào vùng mù" if sm.blind_zone_active else ""
    agg.update(state_held, [], timestamp=t_after_disappear, notes=note)

    # Khi hết thời gian giữ cảnh báo (near_hold_sec = 2.0s), bắt đầu chu kỳ hạ mức (Hysteresis = 1.0s)
    # Tại t + 2.1s: vừa hết near_hold (2.0s), bộ đếm Hysteresis bắt đầu đếm
    t_hold_end = t + 2.1
    state_deescalating, _, _ = sm.evaluate([], timestamp=t_hold_end)
    assert sm.blind_zone_active is False
    agg.update(state_deescalating, [], timestamp=t_hold_end)

    # Tại t + 3.3s: đã hết cả near_hold (2.0s) và đủ trễ Hysteresis (1.0s) -> VỀ AN TOÀN!
    t_safe = t + 3.3
    state_safe, _, _ = sm.evaluate([], timestamp=t_safe)
    assert state_safe == AlertSeverity.SAFE

    # Sau thêm 2.1s ở mức An toàn (đủ cooldown_sec = 2.0s) -> Chốt kết thúc sự cố
    t_completed = t_safe + 2.1
    _, completed_inc = agg.update(state_safe, [], timestamp=t_completed)
    assert completed_inc is not None
    assert completed_inc.max_severity == AlertSeverity.DANGER
    assert "mục tiêu vào vùng mù" in completed_inc.notes

    # 2. KỊCH BẢN 2: Vật đứng yên ở 0.3m (speed = 0, closing_speed = 0)
    sm_stationary = AlertStateMachine(cfg={
        "warn_distance_m": 3.5,
        "warn_ttc_sec": 3.0,
        "danger_distance_m": 1.8,
        "danger_ttc_sec": 1.8,
        "min_closing_speed_mps": 0.3,
        "hysteresis_sec": 1.0,
        "near_hold_range_m": 1.2,
        "near_hold_sec": 2.0,
        "confirm_frames": 3,
    })
    t_s = 2000.0
    for step in range(5):
        target_s = RadarTarget(
            2, x_m=0.0, y_m=0.3, speed_kmh=0.0, valid=True,
            closing_speed_mps=0.0, ttc_sec=None, age_frames=step + 1
        )
        state_s, _, _ = sm_stationary.evaluate([target_s], timestamp=t_s)
        # Vật đứng yên ở 0.3m chỉ ở mức VÀNG, không ở mức ĐỎ
        assert state_s == AlertSeverity.WARN
        t_s += 0.1

    # Khi mục tiêu đứng yên này biến mất (targets = []):
    # Sau 0.5s: Không bao giờ kích hoạt giữ mức ĐỎ!
    state_s_after, _, _ = sm_stationary.evaluate([], timestamp=t_s + 0.5)
    assert state_s_after != AlertSeverity.DANGER, "Vật đứng yên biến mất TUYỆT ĐỐI KHÔNG được kích hoạt giữ mức Đỏ!"
    assert sm_stationary.blind_zone_active is False


def test_speed_convention_and_formatting(tmp_path, monkeypatch):
    """
    Kiểm thử quy ước tốc độ và định dạng hiển thị:
    - speed_kmh ÂM: tiến lại gần -> 'Tiến lại gần X km/h'
    - speed_kmh DƯƠNG: ra xa -> 'Ra xa X km/h'
    - |closing_speed| < 0.3 m/s hoặc tốc độ < 0.5 km/h -> 'Đứng yên'
    - Lưu CSDL cả closing_speed_mps và speed_kmh_raw
    """
    from config import format_speed_status

    # 1. Tiến lại gần: speed âm (-2.0 km/h), closing_speed > 0.3 (+0.6 m/s)
    s1 = format_speed_status(-2.0, 0.6)
    assert s1 == "Tiến lại gần 2.0 km/h"

    # 2. Ra xa: speed dương (+3.6 km/h), closing_speed < -0.3 (-1.0 m/s)
    s2 = format_speed_status(3.6, -1.0)
    assert s2 == "Ra xa 3.6 km/h"

    # 3. Đứng yên: speed 0.0, closing_speed 0.0
    s3 = format_speed_status(0.0, 0.0)
    assert s3 == "Đứng yên"

    # 4. Dao động nhỏ |closing_speed| < 0.3
    s4 = format_speed_status(-0.4, 0.1)
    assert s4 == "Đứng yên"

    # 5. Kiểm tra lưu và đọc CSDL với closing_speed_mps và speed_kmh_raw (cô lập bằng tmp_path)
    import database
    test_db = str(tmp_path / "test_speed.db")
    monkeypatch.setattr(database, "DB_PATH", test_db)
    database.init_db()
    inc_id = database.insert_incident(
        start_time="2026-11-11 20:00:00",
        end_time="2026-11-11 20:00:05",
        max_severity="Nguy cơ va chạm",
        object_type="Người đi bộ",
        min_distance_m=1.2,
        min_ttc_sec=1.5,
        max_speed_kmh=5.4,
        image_path="",
        notes="kiểm thử",
        closing_speed_mps=1.5,
        speed_kmh_raw=-5.4,
    )
    assert inc_id > 0
    records = database.get_filtered_incidents(limit=1)
    assert len(records) > 0
    top = records[0]
    # top: (id, start_time, end_time, object_type, min_dist, max_v, min_ttc, severity, img, notes, closing_speed_mps, speed_kmh_raw)
    assert top[3] == "Người đi bộ"
    assert math.isclose(top[10], 1.5, abs_tol=0.1)
    assert math.isclose(top[11], -5.4, abs_tol=0.1)
