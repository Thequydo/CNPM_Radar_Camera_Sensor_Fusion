# -*- coding: utf-8 -*-
"""
Kiểm thử Tự động Giai đoạn 2A - Bước F: Sửa lỗi & Chẩn đoán RadarPipeline
Bao gồm đúng 7 ca kiểm thử theo đặc tả:
1. Mục tiêu giả đứng yên ở (-0.42, 0.42), 300 khung, sau hiệu chuẩn nền: không lọt mục tiêu nào.
2. Hai người A (-1.0, 1.5) và B (+1.0, 2.5), 100 khung: giữ đúng 2 track ổn định.
3. Hai người đi ngang nhau (đường đi cắt nhau): ID không bị hoán đổi.
4. Vật đứng yên ở 1.0 m: chỉ mức vàng, không bao giờ đỏ.
5. Vật tiến từ 3.0 m xuống 0.3 m (1.0 m/s): lên đỏ trước 0.5 m & giữ đỏ ở vùng mù; vật đứng yên ở 0.3 m: không đỏ.
6. Một lần đi lại gần kéo dài 60 khung: đúng 1 dòng nhật ký, 1 ảnh.
7. Hiển thị vận tốc: -2.0 km/h -> 'Tiến lại gần 2.0 km/h'; +1.2 -> 'Ra xa 1.2 km/h'; |v| nhỏ -> 'Đứng yên'.
"""

import os
import sys
import math
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from radar_parser import (
    RadarTarget,
    RadarPipeline,
    RadarTracker,
    BackgroundModel,
    RadarDebugLogger,
    RADAR_DEBUG_LOG_PATH,
    parse_ld2450_ack_frames,
    configure_ld2450_multitarget,
)
from alert_engine import (
    AlertStateMachine,
    AlertSeverity,
    IncidentAggregator,
)
from config import format_speed_status


def test_step_f1_stationary_ghost_calibrated_out(tmp_path):
    """1. Mục tiêu giả đứng yên ở (x=-0.42, y=0.42), 300 khung, sau hiệu chuẩn nền: không còn mục tiêu nào qua bộ lọc."""
    bg_file = str(tmp_path / "bg_test.json")
    cfg = {
        "min_range_m": 0.5,
        "max_range_m": 6.0,
        "max_angle_deg": 60.0,
        "background_grid_m": 0.10,
        "background_occupancy_ratio": 0.70,
        "background_tolerance_m": 0.15,
        "confirm_frames": 3,
    }
    bg_model = BackgroundModel(storage_path=bg_file, grid_size_m=0.10, occupancy_ratio=0.70, tolerance_m=0.15)
    pipeline = RadarPipeline(cfg=cfg, background_model=bg_model)

    # Giả lập thu thập 300 khung mục tiêu đứng yên ở (-0.42, 0.42) -> cự ly = 0.594m > 0.5m
    calib_frames = [[RadarTarget(1, -0.42, 0.42, speed_kmh=0.0, valid=True)] for _ in range(300)]
    bg_model.calibrate(frames=calib_frames)
    assert bg_model.get_points_count() == 1

    # Chạy 300 khung tiếp theo qua toàn bộ RadarPipeline
    passed_targets = []
    for i in range(300):
        t_step = 1.0 + i * 0.1
        # Thêm nhiễu dao động nhẹ +/- 0.02m
        res = pipeline.process_raw_targets(
            [RadarTarget(1, -0.42 + (i % 3 - 1) * 0.01, 0.42 + (i % 2) * 0.01, speed_kmh=0.0, valid=True)],
            timestamp=t_step,
        )
        passed_targets.extend(res)

    assert len(passed_targets) == 0


def test_step_f2_two_people_stable_tracks():
    """2. Hai người: A từ (-1.0, 1.5) và B từ (+1.0, 2.5), cùng đi chậm tại chỗ trong 100 khung: giữ ĐÚNG 2 track ổn định."""
    tracker = RadarTracker(association_gate_m=0.5, confirm_frames=3, max_missed_frames=5)

    id_a = None
    id_b = None

    for f in range(100):
        ts = f * 0.1
        # Đi chậm loanh quanh tại chỗ (+/- 0.05m)
        ax = -1.0 + 0.05 * math.sin(f * 0.2)
        ay = 1.5 + 0.05 * math.cos(f * 0.2)
        bx = 1.0 + 0.05 * math.cos(f * 0.2)
        by = 2.5 + 0.05 * math.sin(f * 0.2)

        dets = [
            RadarTarget(1, ax, ay, speed_kmh=-0.5, valid=True),
            RadarTarget(2, bx, by, speed_kmh=-0.3, valid=True),
        ]
        confirmed = tracker.update(dets, timestamp=ts)

        if f >= 2:  # Sau 3 khung xác nhận
            assert len(confirmed) == 2
            # Phân biệt A (x < 0) và B (x > 0)
            a_trk = next(t for t in confirmed if t.x_m < 0)
            b_trk = next(t for t in confirmed if t.x_m > 0)
            if id_a is None:
                id_a = a_trk.target_id
                id_b = b_trk.target_id
                assert id_a != id_b
            else:
                assert a_trk.target_id == id_a
                assert b_trk.target_id == id_b


def test_step_f3_two_people_crossing_paths_no_id_swap():
    """3. Hai người đi ngang nhau (đường đi cắt nhau): ID không bị hoán đổi nhờ dự đoán động học."""
    tracker = RadarTracker(association_gate_m=0.8, confirm_frames=3, max_missed_frames=5, smoothing_alpha=0.8)

    id_left_to_right = None
    id_right_to_left = None

    # A đi từ (-2.0, 2.0) sang (+2.0, 2.0) với tốc độ +1.0 m/s theo X
    # B đi từ (+2.0, 2.05) sang (-2.0, 2.05) với tốc độ -1.0 m/s theo X
    dt = 0.1
    for f in range(41):
        t = f * dt
        ax = -2.0 + 1.0 * t
        ay = 2.0
        bx = 2.0 - 1.0 * t
        by = 2.05

        dets = [
            RadarTarget(1, ax, ay, speed_kmh=0.0, valid=True),
            RadarTarget(2, bx, by, speed_kmh=0.0, valid=True),
        ]
        confirmed = tracker.update(dets, timestamp=t)

        if f == 5:
            assert len(confirmed) == 2
            t_a = min(confirmed, key=lambda x: abs(x.x_m - ax))
            t_b = min(confirmed, key=lambda x: abs(x.x_m - bx))
            id_left_to_right = t_a.target_id
            id_right_to_left = t_b.target_id
            assert id_left_to_right != id_right_to_left

        # Sau khi đã đi qua điểm cắt (t > 2.5s, khi A ở bên phải và B ở bên trái)
        if f == 35:
            assert len(confirmed) == 2
            t_right = max(confirmed, key=lambda x: x.x_m)  # Người A lúc này đang ở bên phải (+1.5m)
            t_left = min(confirmed, key=lambda x: x.x_m)   # Người B lúc này đang ở bên trái (-1.5m)
            assert t_right.target_id == id_left_to_right
            assert t_left.target_id == id_right_to_left


def test_step_f4_stationary_object_at_1m_only_warn():
    """4. Vật đứng yên ở 1.0 m: trạng thái chỉ vàng ('Có vật trong vùng cảnh báo'), không đỏ."""
    cfg = {
        "warn_distance_m": 3.5,
        "warn_ttc_sec": 3.0,
        "danger_distance_m": 1.8,
        "danger_ttc_sec": 1.8,
        "min_closing_speed_mps": 0.3,
        "hysteresis_sec": 1.0,
    }
    asm = AlertStateMachine(cfg=cfg)
    t = RadarTarget(1, 0.0, 1.0, speed_kmh=0.0, closing_speed_mps=0.0, ttc_sec=None, valid=True)
    for i in range(10):
        state, primary, _ = asm.evaluate([t], timestamp=i * 0.1)
        assert state == AlertSeverity.WARN
        assert state != AlertSeverity.DANGER


def test_step_f5_approaching_blind_zone_hold_and_stationary_ignore():
    """5. Vật tiến từ 3.0m xuống 0.3m với 1.0 m/s: lên đỏ trước 0.5m và GIỮ đỏ khi mất dấu ở vùng mù; đứng yên ở 0.3m: không đỏ."""
    cfg = {
        "min_range_m": 0.5,
        "warn_distance_m": 3.5,
        "danger_distance_m": 1.8,
        "danger_ttc_sec": 1.8,
        "min_closing_speed_mps": 0.3,
        "hysteresis_sec": 1.0,
        "near_hold_range_m": 1.2,
        "near_hold_sec": 2.0,
        "confirm_frames": 3,
    }
    pipeline = RadarPipeline(cfg=cfg)
    asm = AlertStateMachine(cfg=cfg)

    reached_danger_before_blind = False
    hold_danger_in_blind_zone = False

    # Tiến từ 3.0m xuống 0.3m với v = 1.0 m/s rồi giữ ở 0.3m trong vùng mù
    tracked_dropped_and_held = False
    for step in range(42):
        t_sec = step * 0.1
        y_m = max(0.3, 3.0 - 1.0 * t_sec)
        raw = [RadarTarget(1, 0.0, y_m, speed_kmh=-3.6, valid=True)]
        tracked = pipeline.process_raw_targets(raw, timestamp=t_sec)
        state, _, _ = asm.evaluate(tracked, timestamp=t_sec)

        if y_m >= 0.5 and state == AlertSeverity.DANGER:
            reached_danger_before_blind = True

        # Sau khi mất dấu hoàn toàn khỏi Tracker (len(tracked) == 0) ở vùng < 0.5m, máy trạng thái vẫn phải GIỮ ĐỎ
        if y_m < 0.5 and len(tracked) == 0:
            if state == AlertSeverity.DANGER:
                hold_danger_in_blind_zone = True
                tracked_dropped_and_held = True

    assert reached_danger_before_blind
    assert tracked_dropped_and_held
    assert hold_danger_in_blind_zone
    assert asm.blind_zone_active is True

    # Thử vật đứng yên ở 0.3m -> bị lọc và không kích hoạt đỏ
    pipeline2 = RadarPipeline(cfg=cfg)
    asm2 = AlertStateMachine(cfg=cfg)
    for step in range(20):
        t_sec = step * 0.1
        raw = [RadarTarget(1, 0.0, 0.3, speed_kmh=0.0, valid=True)]
        tracked = pipeline2.process_raw_targets(raw, timestamp=t_sec)
        state, _, _ = asm2.evaluate(tracked, timestamp=t_sec)
        assert len(tracked) == 0
        assert state == AlertSeverity.SAFE


def test_step_f6_60_frames_approach_one_incident_one_snapshot():
    """6. Một lần đi lại gần kéo dài 60 khung: đúng 1 dòng nhật ký, 1 ảnh."""
    agg = IncidentAggregator(cooldown_sec=2.0)
    snapshots = 0
    completed = []

    for f in range(60):
        t_sec = f * 0.1
        dist = 2.0 - 0.02 * f
        tgt = RadarTarget(1, 0.0, dist, speed_kmh=-5.4, closing_speed_mps=1.5, valid=True)
        should_snap, done = agg.update(AlertSeverity.DANGER, [tgt], timestamp=t_sec, object_type="Chưa xác định")
        if should_snap:
            snapshots += 1
        if done:
            completed.append(done)

    # An toàn kéo dài >= 2.0s để chốt sự cố
    for f in range(60, 85):
        t_sec = f * 0.1
        should_snap, done = agg.update(AlertSeverity.SAFE, [], timestamp=t_sec)
        if should_snap:
            snapshots += 1
        if done:
            completed.append(done)

    assert snapshots == 1
    assert len(completed) == 1
    assert completed[0].object_type == "Chưa xác định"


def test_step_f7_speed_display_conventions():
    """7. Hiển thị vận tốc: -2.0 gốc -> 'Tiến lại gần 2.0 km/h'; +1.2 -> 'Ra xa 1.2 km/h'; |v| nhỏ -> 'Đứng yên'."""
    # -2.0 km/h (~ -0.55 m/s) -> Tiến lại gần
    assert format_speed_status(-2.0, 0.55) == "Tiến lại gần 2.0 km/h"
    # +1.2 km/h (~ -0.33 m/s closing) -> Ra xa
    assert format_speed_status(1.2, -0.33) == "Ra xa 1.2 km/h"
    # Đứng yên (|v| < 0.5 km/h hoặc |closing| < 0.3 m/s)
    assert format_speed_status(-0.3, 0.08) == "Đứng yên"
    assert format_speed_status(0.4, -0.1) == "Đứng yên"
    assert format_speed_status(0.0, 0.0) == "Đứng yên"


def test_ld2450_multitarget_ack_handshake_and_log_dir(tmp_path):
    """Kiểm tra bắt tay ACK Đa mục tiêu (0x0090 + 0x0091) và đường dẫn LOGS_DIR từ config."""
    import config as cfg_mod
    import radar_parser as rp_mod
    assert rp_mod.LOGS_DIR == cfg_mod.LOGS_DIR

    # Kiểm tra parse_ld2450_ack_frames với byte rác + gói ACK hợp lệ (0x0191 mode = 2)
    ack_mode2 = b"\xAA\xFF\x03\x00" + b"\xFD\xFC\xFB\xFA\x06\x00\x91\x01\x00\x00\x02\x00\x04\x03\x02\x01"
    acks = parse_ld2450_ack_frames(ack_mode2)
    assert len(acks) == 1
    assert acks[0][0] == 0x0191
    assert acks[0][1] == 0
    assert acks[0][2] == b"\x02\x00"

    class _MockSerial:
        def __init__(self):
            self._rx = bytearray()
            self.written = []

        @property
        def in_waiting(self):
            return len(self._rx)

        def reset_input_buffer(self):
            self._rx.clear()

        def write(self, data: bytes):
            self.written.append(data)
            cmd = data[6] | (data[7] << 8)
            if cmd == 0x00FF:
                self._rx.extend(b"\xFD\xFC\xFB\xFA\x08\x00\xFF\x01\x00\x00\x01\x00\x40\x00\x04\x03\x02\x01")
            elif cmd == 0x0090:
                self._rx.extend(b"\xFD\xFC\xFB\xFA\x04\x00\x90\x01\x00\x00\x04\x03\x02\x01")
            elif cmd == 0x0091:
                self._rx.extend(b"\xFD\xFC\xFB\xFA\x06\x00\x91\x01\x00\x00\x02\x00\x04\x03\x02\x01")
            elif cmd == 0x00FE:
                self._rx.extend(b"\xFD\xFC\xFB\xFA\x04\x00\xFE\x01\x00\x00\x04\x03\x02\x01")

        def read(self, n: int) -> bytes:
            out = bytes(self._rx[:n])
            del self._rx[:n]
            return out

    log_file = str(tmp_path / "radar_debug_test.log")
    dbg_logger = RadarDebugLogger(log_path=log_file)
    res = configure_ld2450_multitarget(_MockSerial(), logger=dbg_logger)
    assert res["enable_ack"] is True
    assert res["multi_ack"] is True
    assert res["mode"] == 2
    assert res["end_ack"] is True
    with open(log_file, "r", encoding="utf-8") as f:
        txt = f.read()
    assert "Multi-Target (0x0002)" in txt


def test_intermittent_second_person_confirms_while_single_spike_rejected():
    """Mục tiêu thứ 2 chập chờn 1 khung (hit, hit, miss, hit) vẫn xác nhận, nhưng nhiễu 1-2 khung rỗng bị loại."""
    tracker = RadarTracker(association_gate_m=0.5, confirm_frames=3, max_missed_frames=5)
    p1 = RadarTarget(1, -1.0, 1.8, speed_kmh=0.0, valid=True)
    p2 = RadarTarget(2, 0.5, 2.0, speed_kmh=0.0, valid=True)
    spike = RadarTarget(3, 2.5, 4.0, speed_kmh=0.0, valid=True)

    # Khung 1: p1 + p2 + spike
    assert len(tracker.update([p1, p2, spike], timestamp=0.0)) == 0
    # Khung 2: p1 + p2 (spike mất)
    assert len(tracker.update([p1, p2], timestamp=0.1)) == 0
    # Khung 3: p1 xác nhận; p2 nhấp nháy mất 1 khung; spike mất tiếp (bị xóa hẳn)
    c3 = tracker.update([p1], timestamp=0.2)
    assert len(c3) == 1
    assert c3[0].target_id == 1
    assert 3 not in tracker.tracks  # nhiễu đơn lẻ đã bị xóa sau 2 khung mất
    # Khung 4: p2 quay lại -> đạt 3 hits và xác nhận cùng p1
    c4 = tracker.update([p1, p2], timestamp=0.3)
    assert len(c4) == 2
