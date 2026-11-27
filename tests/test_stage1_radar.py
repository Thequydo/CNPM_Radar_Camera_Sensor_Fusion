# -*- coding: utf-8 -*-
"""
Bộ kiểm thử tự động Giai đoạn 1 (pytest):
Kiểm tra toàn diện Tầng dữ liệu Radar (Giải mã, Lọc, Theo dõi, Hiệu chuẩn nền, Cấu hình config.json).
"""

import os
import sys
import json
import math
import sqlite3
import pytest

# Đảm bảo import được các module ở thư mục gốc dự án C:\CNPM_Project dù chạy pytest từ bất kỳ thư mục nào
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import ConfigManager, DEFAULT_CONFIG
from radar_parser import (
    RadarTarget,
    RadarStreamDecoder,
    BackgroundModel,
    RadarTracker,
    RadarPipeline,
    decode_signed_16bit,
    encode_signed_16bit,
    build_ld2450_frame,
    parse_ld2450_frame,
    filter_targets_by_range,
)


# ==============================================================================
# 1. KIỂM THỬ GIẢI MÃ KHUNG DỮ LIỆU LD2450 & TÁI ĐỒNG BỘ LUỒNG BYTE (Mục 1.1 & 3.1.1-3.1.3)
# ==============================================================================

def test_decode_signed_16bit_sign_magnitude():
    """Kiểm tra giải mã số nguyên 16-bit sign-magnitude chuẩn HLK-LD2450."""
    # Số 0
    assert decode_signed_16bit(0x0000) == 0
    assert decode_signed_16bit(0x8000) == 0

    # Số dương (bit 15 = 1)
    assert decode_signed_16bit(0x8000 | 420) == 420
    assert decode_signed_16bit(0x8000 | 1500) == 1500

    # Số âm (bit 15 = 0)
    assert decode_signed_16bit(420) == -420
    assert decode_signed_16bit(1500) == -1500

    # Khứ hồi encode -> decode
    for val in [-3500, -420, -25, 0, 25, 420, 4000]:
        raw = encode_signed_16bit(val)
        assert decode_signed_16bit(raw) == val


def test_parse_valid_30byte_frame_and_units():
    """
    Kiểm tra giải mã khung 30 byte hợp lệ:
    - Tọa độ x, y từ mm sang m
    - Vận tốc từ cm/s sang km/h
    - Đọc trường resolution (2 byte cuối mỗi slot)
    - Bỏ qua slot rỗng (8 byte đều là 0x00)
    """
    frame = build_ld2450_frame([
        (-420, 420, 25, 320),     # Slot 1: X=-0.42m, Y=0.42m, V=+25cm/s (+0.9km/h), res=320mm
        None,                     # Slot 2: Rỗng (8 byte 0x00)
        (1000, 2000, -100, 350),  # Slot 3: X=+1.00m, Y=2.00m, V=-100cm/s (-3.6km/h), res=350mm
    ])
    assert len(frame) == 30

    targets = parse_ld2450_frame(frame)
    assert targets is not None
    assert len(targets) == 2

    t1, t2 = targets[0], targets[1]
    assert t1.target_id == 1
    assert math.isclose(t1.x_m, -0.42, abs_tol=1e-4)
    assert math.isclose(t1.y_m, 0.42, abs_tol=1e-4)
    assert math.isclose(t1.distance_m, math.hypot(-0.42, 0.42), abs_tol=1e-4)
    assert math.isclose(t1.angle_deg, -45.0, abs_tol=1e-2)
    assert math.isclose(t1.speed_mps, 0.25, abs_tol=1e-4)
    assert math.isclose(t1.speed_kmh, 0.9, abs_tol=1e-4)
    assert t1.resolution_mm == 320

    assert t2.target_id == 3
    assert math.isclose(t2.x_m, 1.0, abs_tol=1e-4)
    assert math.isclose(t2.y_m, 2.0, abs_tol=1e-4)
    assert math.isclose(t2.speed_kmh, -3.6, abs_tol=1e-4)
    assert t2.resolution_mm == 350


def test_reject_negative_or_zero_y_without_abs():
    """
    Mục 3.1.3: Không dùng abs(y_val). Nếu y_mm <= 0 (dữ liệu hỏng), phải loại bỏ mục tiêu đó.
    """
    frame = build_ld2450_frame([
        (500, -1200, 0, 300),  # Y âm (-1.2m) -> phải bị loại bỏ, KHÔNG được biến thành +1.2m
        (0, 0, 50, 0),         # Y = 0 -> phải bị loại bỏ
        (300, 1500, 0, 300),   # Y dương (+1.5m) -> hợp lệ
    ])
    targets = parse_ld2450_frame(frame)
    assert targets is not None
    assert len(targets) == 1
    assert math.isclose(targets[0].y_m, 1.5, abs_tol=1e-4)


def test_stream_resynchronization_with_garbage_and_chunk_splits():
    """
    Mục 1.1 & 3.1.1: Kiểm tra tái đồng bộ khi có byte rác xen giữa, header giả (corrupted frame),
    và khung 30 byte bị cắt làm nhiều lần đọc (kể cả cắt ngay giữa 4 byte header AA FF 03 00).
    """
    decoder = RadarStreamDecoder()

    valid_frame_1 = build_ld2450_frame([(-420, 420, 25, 300), None, None])
    valid_frame_2 = build_ld2450_frame([(200, 2500, -50, 300), None, None])

    # Khung hỏng: có header AA FF 03 00 nhưng không có tail 55 CC ở byte 28..30
    corrupted_frame = b"\xAA\xFF\x03\x00" + b"\x11" * 24 + b"\x99\x99"

    stream = (
        b"\x00\xFF\x12\x34\x56"  # Byte rác đầu luồng
        + valid_frame_1[:2]      # Cắt ngay giữa header (\xAA\xFF)
    )
    # Lần đọc 1: chỉ mới có 2 byte của header -> chưa có frame nào, buffer phải giữ lại đuôi
    out1 = decoder.feed(stream)
    assert len(out1) == 0

    # Lần đọc 2: gửi nốt phần còn lại của frame 1 + khung hỏng + nửa đầu frame 2
    out2 = decoder.feed(valid_frame_1[2:] + b"\x77\x88" + corrupted_frame + valid_frame_2[:13])
    assert len(out2) == 1
    assert len(out2[0]) == 1
    assert math.isclose(out2[0][0].x_m, -0.42, abs_tol=1e-4)

    # Lần đọc 3: gửi nốt phần còn lại của frame 2
    out3 = decoder.feed(valid_frame_2[13:])
    assert len(out3) == 1
    assert len(out3[0]) == 1
    assert math.isclose(out3[0][0].y_m, 2.5, abs_tol=1e-4)


# ==============================================================================
# 2. KIỂM THỬ LỌC VÙNG HỢP LỆ (Mục 1.2)
# ==============================================================================

def test_filter_targets_by_range_and_angle():
    """
    Kiểm tra lọc theo min_range_m (0.2m), max_range_m (6.0m), max_angle_deg (60 độ).
    """
    raw_frame = build_ld2450_frame([
        (0, 150, 0, 300),       # distance = 0.15m (< 0.2m) -> Loại (nhiễu sát ăng-ten)
        (0, 6500, 0, 300),      # distance = 6.50m (> 6.0m) -> Loại (ngoài tầm)
        (2000, 1000, 0, 300),   # angle = atan2(2, 1) = 63.43° (> 60°) -> Loại (ngoài góc mở)
    ])
    parsed = parse_ld2450_frame(raw_frame)
    filtered = filter_targets_by_range(parsed, min_range_m=0.2, max_range_m=6.0, max_angle_deg=60.0)
    assert len(filtered) == 0

    # Mục tiêu hợp lệ trong vùng cực gần và trong tầm [0.2m, 6.0m] và góc [-60°, +60°]
    valid_raw = parse_ld2450_frame(build_ld2450_frame([(0, 350, 0, 300), None, None]))
    filtered_valid = filter_targets_by_range(valid_raw, min_range_m=0.2, max_range_m=6.0, max_angle_deg=60.0)
    assert len(filtered_valid) == 1


# ==============================================================================
# 3. KIỂM THỬ THEO DÕI MỤC TIÊU, XÁC NHẬN N KHUNG & TÍNH CLOSING SPEED / TTC (Mục 1.3 & 3.1.4)
# ==============================================================================

def test_tracker_confirmation_persistence_and_deletion():
    """
    Kiểm tra:
    - Mục tiêu chỉ xuất hiện sau khi tồn tại liên tiếp >= confirm_frames (3 khung).
    - Giữ nguyên ID ổn định khi di chuyển trong ngưỡng association_gate_m (0.5m).
    - Xóa track sau max_missed_frames (5 khung) mất dấu liên tiếp.
    """
    tracker = RadarTracker(
        association_gate_m=0.5,
        confirm_frames=3,
        max_missed_frames=5,
        smoothing_alpha=0.5,
        min_closing_speed_mps=0.3,
    )

    t0 = 100.0
    det = parse_ld2450_frame(build_ld2450_frame([(0, 3000, 0, 300), None, None]))

    # Khung 1 & Khung 2: chưa đủ 3 khung liên tiếp -> danh sách xác nhận phải rỗng
    assert len(tracker.update(det, timestamp=t0)) == 0
    assert len(tracker.update(det, timestamp=t0 + 0.1)) == 0

    # Khung 3: đủ 3 khung liên tiếp -> được xác nhận với ID = 1
    confirmed = tracker.update(det, timestamp=t0 + 0.2)
    assert len(confirmed) == 1
    track_id = confirmed[0].target_id
    assert confirmed[0].hit_count == 3

    # Khung 4: di chuyển nhẹ từ Y=3.0m -> Y=2.8m (khoảng cách dịch chuyển 0.2m <= 0.5m) -> giữ nguyên ID
    det_moved = parse_ld2450_frame(build_ld2450_frame([(0, 2800, 0, 300), None, None]))
    confirmed_4 = tracker.update(det_moved, timestamp=t0 + 0.3)
    assert len(confirmed_4) == 1
    assert confirmed_4[0].target_id == track_id

    # Mất dấu 4 khung liên tiếp (<= max_missed_frames=5): vẫn còn giữ track trong bộ nhớ
    for step in range(1, 5):
        res = tracker.update([], timestamp=t0 + 0.3 + step * 0.1)
        assert len(res) == 1
        assert res[0].target_id == track_id

    # Khung mất dấu thứ 5 (missed_frames == 5 >= max_missed_frames): bị xóa hoàn toàn
    res_deleted = tracker.update([], timestamp=t0 + 0.8)
    assert len(res_deleted) == 0
    assert len(tracker.tracks) == 0


def test_tracker_closing_speed_and_ttc_calculation():
    """
    Mục 1.3 & 3.1.4:
    - closing_speed_mps tính từ đạo hàm khoảng cách theo thời gian (-dD/dt), dương khi tiến lại gần.
    - ttc_sec = distance_m / closing_speed_mps khi closing_speed_mps > 0.3 m/s.
    - Khi mục tiêu đứng yên hoặc đi ra xa (closing_speed_mps <= 0.3 m/s), ttc_sec phải là None.
    """
    tracker = RadarTracker(
        association_gate_m=0.5,
        confirm_frames=3,
        max_missed_frames=5,
        smoothing_alpha=1.0,  # alpha=1.0 để kiểm tra chính xác đạo hàm không bị trễ EMA
        min_closing_speed_mps=0.3,
    )

    # Mục tiêu tiến lại gần với vận tốc 2.0 m/s:
    # t=0.0s: y=4.0m -> t=0.1s: y=3.8m -> t=0.2s: y=3.6m -> t=0.3s: y=3.4m
    timestamps = [0.0, 0.1, 0.2, 0.3]
    y_mm_values = [4000, 3800, 3600, 3400]

    confirmed = []
    for ts, y_mm in zip(timestamps, y_mm_values):
        det = parse_ld2450_frame(build_ld2450_frame([(0, y_mm, -200, 300), None, None]))
        confirmed = tracker.update(det, timestamp=ts)

    assert len(confirmed) == 1
    target = confirmed[0]
    assert math.isclose(target.distance_m, 3.4, abs_tol=1e-3)
    assert math.isclose(target.closing_speed_mps, 2.0, abs_tol=0.05)
    assert target.ttc_sec is not None
    assert math.isclose(target.ttc_sec, 3.4 / target.closing_speed_mps, rel_tol=1e-3)

    # Bây giờ mục tiêu đứng yên ở y=3.4m trong các khung tiếp theo -> closing_speed_mps về 0 -> ttc_sec là None
    for ts in [0.4, 0.5, 0.6, 0.7]:
        det = parse_ld2450_frame(build_ld2450_frame([(0, 3400, 0, 300), None, None]))
        confirmed = tracker.update(det, timestamp=ts)

    assert len(confirmed) == 1
    assert confirmed[0].closing_speed_mps <= 0.3
    assert confirmed[0].ttc_sec is None


# ==============================================================================
# 4. KIỂM THỬ HIỆU CHUẨN NỀN TĨNH & LOẠI MỤC TIÊU MA TRÊN COM5 (Mục 1.4 & 1.5)
# ==============================================================================

def test_background_calibration_eliminates_ghost_and_keeps_moving_target(tmp_path):
    """
    Kịch bản bắt buộc Mục 1.5:
    - Truyền chuỗi 300 khung có mục tiêu cố định tại x = -0.42 m, y = 0.42 m, speed = 0.9 km/h
      (đúng như kết quả thực tế từ COM5 của người dùng).
    - Sau khi chạy hiệu chuẩn nền, hàm trả về 0 mục tiêu ma.
    - Truyền chuỗi khung có mục tiêu di chuyển từ y = 4.0 m về y = 1.0 m -> được giữ lại,
      gán ID ổn định và tính đúng khoảng cách, tốc độ tiến lại gần.
    """
    cfg_file = tmp_path / "config.json"
    bg_file = tmp_path / "background.json"
    cm = ConfigManager(config_path=str(cfg_file), legacy_db_path=str(tmp_path / "nonexistent.db"))

    bg_model = BackgroundModel(
        storage_path=str(bg_file),
        grid_size_m=0.10,
        occupancy_ratio=0.70,
        tolerance_m=0.15,
    )
    pipeline = RadarPipeline(cfg=cm.data, background_model=bg_model)

    # 1. Hiệu chuẩn nền với 300 khung chứa mục tiêu ma tại X=-0.42m, Y=0.42m, V=+0.9km/h (+25cm/s)
    ghost_frame = build_ld2450_frame([(-420, 420, 25, 300), None, None])
    ghost_raw_frames = [parse_ld2450_frame(ghost_frame) for _ in range(300)]
    pipeline.background.calibrate(duration_s=5.0, frames=ghost_raw_frames)

    # Đảm bảo đã hoàn tất học nền và lưu vào background.json
    assert not pipeline.background.is_calibrating
    assert bg_file.exists()
    assert len(pipeline.background.background_cells) >= 1

    # 2. Truyền thêm 20 khung chỉ có mục tiêu ma (kể cả dao động nhẹ tới X=-0.45m, Y=0.42m như thực tế COM5)
    base_ts = 1000.0
    for i in range(20):
        jitter_x = -420 if i % 2 == 0 else -450
        jitter_frame = build_ld2450_frame([(jitter_x, 420, 25, 300), None, None])
        frames_out = pipeline.process_bytes(jitter_frame, timestamp=base_ts + 6.0 + i * 0.1)
        assert len(frames_out) == 1
        assert len(frames_out[0]) == 0, "Mục tiêu ma cố định phải bị loại bỏ hoàn toàn sau khi học nền!"

    # 3. Truyền chuỗi khung có mục tiêu thật di chuyển từ y = 4.0m về y = 1.0m (kèm mục tiêu ma ở slot 1)
    # Mục tiêu ma ở slot 1 phải bị lọc, còn mục tiêu thật ở slot 2 phải được giữ lại và theo dõi ổn định!
    moving_steps = 30  # 30 khung, mỗi khung 0.1s (3.0 giây), đi từ 4.0m về 1.0m (vận tốc tiến gần = 1.0 m/s)
    confirmed_history = []
    for step in range(moving_steps + 1):
        ts = base_ts + 10.0 + step * 0.1
        y_mm = int(4000 - step * (3000 / moving_steps))  # 4000mm -> 1000mm
        combined_frame = build_ld2450_frame([
            (-420, 420, 25, 300),     # Slot 1: Mục tiêu ma cố định
            (0, y_mm, -100, 300),     # Slot 2: Người đi bộ thật từ 4.0m về 1.0m
            None,
        ])
        frames_out = pipeline.process_bytes(combined_frame, timestamp=ts)
        for confirmed in frames_out:
            if confirmed:
                confirmed_history.append(confirmed)

    # Phải được xác nhận từ khung thứ 3 trở đi
    assert len(confirmed_history) >= moving_steps - 2
    # Trong mọi khung đã xác nhận, chỉ có đúng 1 mục tiêu (mục tiêu thật), không có mục tiêu ma
    first_id = confirmed_history[0][0].target_id
    for frame_targets in confirmed_history:
        assert len(frame_targets) == 1
        assert frame_targets[0].target_id == first_id

    final_target = confirmed_history[-1][0]
    assert math.isclose(final_target.distance_m, 1.0, abs_tol=0.15)
    assert math.isclose(final_target.closing_speed_mps, 1.0, abs_tol=0.15)
    assert final_target.ttc_sec is not None
    assert math.isclose(final_target.ttc_sec, final_target.distance_m / final_target.closing_speed_mps, rel_tol=0.05)

    # 4. Kiểm tra nạp lại từ background.json và xóa nền (clear)
    reloaded_bg = BackgroundModel(storage_path=str(bg_file))
    assert reloaded_bg.is_background(-0.42, 0.42) is True
    reloaded_bg.clear()
    assert reloaded_bg.is_background(-0.42, 0.42) is False


# ==============================================================================
# 5. KIỂM THỬ QUẢN LÝ CẤU HÌNH DUY NHẤT QUA CONFIG.JSON (Câu trả lời #3 của người dùng)
# ==============================================================================

def test_config_json_one_time_migration_and_single_source_of_truth(tmp_path):
    """
    Kiểm tra:
    - Khi chưa có config.json, nhập một lần giá trị từ bảng system_settings của SQLite cũ.
    - Sau khi đã tạo config.json, mọi thay đổi trong SQLite cũ KHÔNG ảnh hưởng đến config.json,
      và bảng system_settings cũ vẫn được giữ nguyên không bị xóa.
    """
    db_path = tmp_path / "legacy_test.db"
    cfg_path = tmp_path / "config.json"

    # Tạo bảng system_settings cũ trong SQLite
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE system_settings (key TEXT PRIMARY KEY, value TEXT)")
    conn.execute("INSERT INTO system_settings VALUES ('warn_distance_m', '4.2')")
    conn.execute("INSERT INTO system_settings VALUES ('danger_distance_m', '1.8')")
    conn.commit()
    conn.close()

    # Lần chạy đầu tiên: chưa có config.json -> tự động nhập từ SQLite sang config.json
    cm = ConfigManager(config_path=str(cfg_path), legacy_db_path=str(db_path))
    cfg = cm.load()
    assert cfg_path.exists()
    assert math.isclose(cfg["warn_distance_m"], 4.2)
    assert math.isclose(cfg["danger_distance_m"], 1.8)
    assert math.isclose(cfg["min_range_m"], DEFAULT_CONFIG["min_range_m"])

    # Thay đổi trong SQLite sau lần chạy đầu KHÔNG được ghi đè vào config.json (không đồng bộ 2 chiều)
    conn = sqlite3.connect(str(db_path))
    conn.execute("UPDATE system_settings SET value = '9.9' WHERE key = 'warn_distance_m'")
    conn.commit()
    # Kiểm tra bảng cũ vẫn còn nguyên vẹn
    rows = conn.execute("SELECT COUNT(*) FROM system_settings").fetchone()[0]
    conn.close()
    assert rows == 2

    cm_reload = ConfigManager(config_path=str(cfg_path), legacy_db_path=str(db_path))
    assert math.isclose(cm_reload.get("warn_distance_m"), 4.2)


def test_tracker_smooths_speed_and_reduces_jitter():
    """Kiểm tra RadarTracker làm mượt cả vận tốc speed_kmh và closing_speed_mps để chống nhảy số liên tục"""
    tracker = RadarTracker(
        association_gate_m=0.5,
        confirm_frames=3,
        max_missed_frames=5,
        smoothing_alpha=0.6,
        min_closing_speed_mps=0.3,
    )
    raw_speeds_kmh = [-10.0, -14.5, -8.5, -14.0, -9.0, -13.5, -9.2, -13.8]
    raw_y_mm = [3000, 2970, 2940, 2905, 2875, 2840, 2810, 2775]
    smoothed_speeds = []
    for i, (y_mm, sp_kmh) in enumerate(zip(raw_y_mm, raw_speeds_kmh)):
        det = parse_ld2450_frame(build_ld2450_frame([(0, y_mm, int(sp_kmh / 3.6 * 100), 300), None, None]))
        confirmed = tracker.update(det, timestamp=i * 0.1)
        if confirmed:
            smoothed_speeds.append(confirmed[0].speed_kmh)

    assert len(smoothed_speeds) >= 5
    # Dao động biên độ giữa các khung kề nhau phải giảm đáng kể (< 50% biên độ nhảy thô ~5.5 km/h)
    max_step_raw = max(abs(raw_speeds_kmh[i] - raw_speeds_kmh[i - 1]) for i in range(1, len(raw_speeds_kmh)))
    max_step_smooth = max(abs(smoothed_speeds[i] - smoothed_speeds[i - 1]) for i in range(1, len(smoothed_speeds)))
    assert max_step_smooth < max_step_raw * 0.50


def test_tracker_rolling_regression_prevents_false_stationary_on_noisy_approach():
    """Kiểm tra cửa sổ trượt N=6 khung + Kalman Filter giúp xe tiến gần không bị nhầm thành Đứng yên khi nhiễu vị trí"""
    import random
    rng = random.Random(123)
    tracker = RadarTracker(
        association_gate_m=0.5,
        confirm_frames=3,
        max_missed_frames=5,
        smoothing_alpha=0.6,
        min_closing_speed_mps=0.3,
    )
    closing_samples = []
    for i in range(25):
        noisy_y_mm = int((4500 - i * 110) + rng.uniform(-35, 35))
        det = parse_ld2450_frame(build_ld2450_frame([(0, noisy_y_mm, -110, 300), None, None]))
        confirmed = tracker.update(det, timestamp=i * 0.1)
        if confirmed:
            closing_samples.append(confirmed[0].closing_speed_mps)

    assert len(closing_samples) >= 20
    # Tất cả các mẫu đã xác nhận khi xe tiến 1.1 m/s phải luôn > min_closing_speed (0.3 m/s)
    assert min(closing_samples[2:]) > 0.35
