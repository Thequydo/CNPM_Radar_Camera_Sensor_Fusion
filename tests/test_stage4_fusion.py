# -*- coding: utf-8 -*-
"""
Kiểm thử Giai đoạn 4: Bộ máy Kết hợp Radar & Camera (Sensor Fusion)
- Kiểm tra hình học quang học Pin-hole (chiếu tọa độ X, Y sang pixel hoành độ)
- Kiểm tra thuật toán ghép cặp 1-1 (Greedy Association)
- Kiểm tra phân loại mức độ đe dọa (SAFE / WARN / DANGER)
- Kiểm tra nguyên tắc: vật đứng yên không được ra DANGER, unassociated radar không vẽ hộp ảo
"""

import pytest
from detector_worker import Detection
from radar_parser import TrackedTarget
from fusion_engine import project_radar_to_camera_x, FusionEngine


def test_pinhole_projection_center_and_lateral():
    """Mục tiêu ở chính giữa (X=0) luôn chiếu vào tâm ảnh (px = w/2)"""
    w = 1280
    # X=0, Y=3.0m, offset=0, invert=False
    px_center = project_radar_to_camera_x(
        x_m=0.0, y_m=3.0, frame_width=w, hfov_deg=65.0, offset_x_m=0.0, offset_y_m=0.0, invert_radar_x=False
    )
    assert px_center is not None
    assert pytest.approx(px_center, 0.1) == 640.0

    # Mục tiêu lệch sang phải (X=1.0m, Y=2.0m)
    px_right = project_radar_to_camera_x(
        x_m=1.0, y_m=2.0, frame_width=w, hfov_deg=65.0, offset_x_m=0.0, offset_y_m=0.0, invert_radar_x=False
    )
    assert px_right is not None
    assert px_right > 640.0

    # Mục tiêu ở sau ống kính (Y <= 0.1m) -> trả về None
    assert project_radar_to_camera_x(x_m=0.0, y_m=0.05, frame_width=w) is None
    assert project_radar_to_camera_x(x_m=0.0, y_m=-1.0, frame_width=w) is None


def test_fusion_engine_1to1_association():
    """Kiểm tra ghép cặp 1-1 giữa detection ô tô và radar target thẳng hàng"""
    engine = FusionEngine(hfov_deg=65.0, offset_x_m=0.0, offset_y_m=0.0, invert_radar_x=False)

    # 1. Detection ô tô tại tâm ảnh: x1=540, x2=740 -> cx=640
    car_det = Detection(
        x1=540.0, y1=300.0, x2=740.0, y2=500.0,
        confidence=0.90, class_id=2, class_name="Ô tô"
    )

    # 2. Radar target 1: X=0.0, Y=3.0m -> px=640 -> Phù hợp ghép với car_det
    target_matched = TrackedTarget(
        id=1, x=0.0, y=3.0, speed_kmh=15.0, distance=3.0, angle_deg=0.0,
        closing_speed_mps=1.5, ttc_s=2.0, hits=5, missed=0, confirmed=True
    )

    # 3. Radar target 2: X=-2.5m, Y=4.0m -> xa về phía trái, không có xe nào trên camera
    target_unmatched = TrackedTarget(
        id=2, x=-2.5, y=4.0, speed_kmh=0.0, distance=4.7, angle_deg=-30.0,
        closing_speed_mps=0.0, ttc_s=None, hits=4, missed=0, confirmed=True
    )

    # 4. Detection người đi bộ ở góc phải: x1=1100, x2=1160 -> cx=1130, không có radar
    person_det = Detection(
        x1=1100.0, y1=200.0, x2=1160.0, y2=450.0,
        confidence=0.82, class_id=0, class_name="Người"
    )

    fused = engine.fuse(
        radar_targets=[target_matched, target_unmatched],
        detections=[car_det, person_det],
        frame_shape=(720, 1280)
    )

    assert len(fused) == 3

    # Tìm đối tượng ghép cặp
    matched = [f for f in fused if f.is_associated]
    assert len(matched) == 1
    assert matched[0].id == 1
    assert matched[0].detection.class_name == "Ô tô"
    assert matched[0].radar_target.distance == 3.0

    # Tìm đối tượng radar không ghép được
    radar_only = [f for f in fused if f.radar_target is not None and not f.is_associated]
    assert len(radar_only) == 1
    assert radar_only[0].id == 2
    assert radar_only[0].detection is None

    # Tìm đối tượng camera không ghép được
    cam_only = [f for f in fused if f.detection is not None and not f.is_associated]
    assert len(cam_only) == 1
    assert cam_only[0].detection.class_name == "Người"
    assert cam_only[0].radar_target is None


def test_fusion_stationary_target_never_triggers_danger():
    """Quy tắc: Vật đứng yên (closing_speed <= 0.3) dù ở cự ly gần (<1.8m) chỉ ra WARN, không ra DANGER"""
    engine = FusionEngine()
    stationary_close = TrackedTarget(
        id=5, x=0.0, y=1.2, speed_kmh=0.0, distance=1.2, angle_deg=0.0,
        closing_speed_mps=0.0, ttc_s=None, hits=6, missed=0, confirmed=True
    )
    det = Detection(x1=500, y1=200, x2=780, y2=500, confidence=0.88, class_id=2, class_name="Ô tô")

    fused = engine.fuse([stationary_close], [det], (720, 1280))
    assert len(fused) >= 1
    obj = fused[0]
    assert obj.threat_level == "WARN"  # Không được là DANGER


def test_fusion_suppresses_multipath_double_reflection_on_single_car():
    """Kiểm tra khử phản xạ kép: 1 ô tô chỉ ghép 1 mục tiêu radar chính, không hiện thêm Vật cản ảo"""
    engine = FusionEngine(hfov_deg=65.0, offset_x_m=0.0, offset_y_m=0.0, invert_radar_x=False)
    car_det = Detection(
        x1=500.0, y1=300.0, x2=780.0, y2=520.0,
        confidence=0.90, class_id=2, class_name="Ô tô"
    )
    r_main = TrackedTarget(id=1, x=0.0, y=3.0, speed_kmh=-12.0, distance=3.0, closing_speed_mps=3.3, ttc_s=0.9, hits=6, confirmed=True)
    r_echo = TrackedTarget(id=2, x=0.15, y=3.4, speed_kmh=-11.5, distance=3.4, closing_speed_mps=3.2, ttc_s=1.06, hits=5, confirmed=True)

    fused = engine.fuse([r_main, r_echo], [car_det], (720, 1280))
    assert len(fused) == 1
    assert fused[0].is_associated is True
    assert fused[0].id == 1

    dedup = engine.deduplicate_radar_by_detections([r_main, r_echo], [car_det], (720, 1280))
    assert len(dedup) == 1
    assert dedup[0].id == 1


def test_fusion_threat_hysteresis_prevents_instant_danger_flicker():
    """Hysteresis giữ DANGER ngắn hạn (~0.8s) chống nháy Đỏ <-> Vàng khi xe vừa dừng lại"""
    engine = FusionEngine(hfov_deg=65.0, offset_x_m=0.0, offset_y_m=0.0, invert_radar_x=False)
    car_det = Detection(x1=500.0, y1=300.0, x2=780.0, y2=520.0, confidence=0.90, class_id=2, class_name="Ô tô")

    # Bước 1: xe lao tới ở 1.2m -> DANGER
    r_moving = TrackedTarget(
        id=9, x=0.0, y=1.2, speed_kmh=-10.0, distance=1.2,
        closing_speed_mps=2.8, ttc_s=0.43, hits=6, confirmed=True,
    )
    f1 = engine.fuse([r_moving], [car_det], (720, 1280))
    assert f1[0].threat_level == "DANGER"

    # Bước 2 (tức thì ngay sau đó < 0.8s): tốc độ rớt xuống 0.0 -> giữ DANGER ổn định, không nháy ngay về WARN
    r_stopped = TrackedTarget(
        id=9, x=0.0, y=1.2, speed_kmh=0.0, distance=1.2,
        closing_speed_mps=0.0, ttc_s=None, hits=7, confirmed=True,
    )
    f2 = engine.fuse([r_stopped], [car_det], (720, 1280))
    assert f2[0].threat_level == "DANGER"
