# -*- coding: utf-8 -*-
"""
Kiểm thử Giai đoạn 3: Nhận diện đối tượng Camera với YOLOv8n ONNX
- Kiểm tra tiền xử lý Letterbox (kích thước, padding, tỉ lệ)
- Kiểm tra giải mã tensor và lọc Non-Maximum Suppression (NMS)
- Kiểm tra tích hợp mô hình ONNX với dữ liệu ảnh thực
"""

import os
import pytest
import numpy as np
import cv2

from detector_worker import (
    letterbox_image,
    postprocess_yolov8,
    YOLOv8Detector,
    Detection,
    TARGET_CLASSES
)


def test_letterbox_preserves_aspect_ratio_and_pads():
    """Kiểm tra letterbox đưa ảnh 1280x720 về 640x640 với padding xám 114 đối xứng"""
    orig = np.zeros((720, 1280, 3), dtype=np.uint8)
    canvas, scale, (pad_x, pad_y) = letterbox_image(orig, target_size=640)

    assert canvas.shape == (640, 640, 3)
    # Tỉ lệ scale = 640 / 1280 = 0.5
    assert pytest.approx(scale, 0.001) == 0.5
    # new_w = 640, new_h = 360 -> pad_x = 0, pad_y = (640 - 360)//2 = 140
    assert pad_x == 0
    assert pad_y == 140
    # Phần đệm trên và dưới phải có giá trị pixel 114
    assert np.all(canvas[0:10, :, :] == 114)
    assert np.all(canvas[630:640, :, :] == 114)


def test_postprocess_yolov8_filters_classes_and_threshold():
    """Kiểm tra giải mã tensor giả lập: lọc đúng lớp giao thông, loại bỏ lớp khác và dưới ngưỡng"""
    # Tensor output shape (1, 84, 8400)
    tensor = np.zeros((1, 84, 8400), dtype=np.float32)

    # Mục tiêu 1: Ô tô (class 2) tại box cx=320, cy=320, w=100, h=80, conf=0.88
    tensor[0, 0, 10] = 320.0
    tensor[0, 1, 10] = 320.0
    tensor[0, 2, 10] = 100.0
    tensor[0, 3, 10] = 80.0
    tensor[0, 4 + 2, 10] = 0.88  # class 2 = Ô tô

    # Mục tiêu 2: Chó mèo (class 16) tại conf=0.95 -> phải bị bỏ qua vì không phải lớp giao thông
    tensor[0, 0, 20] = 100.0
    tensor[0, 1, 20] = 100.0
    tensor[0, 2, 20] = 50.0
    tensor[0, 3, 20] = 50.0
    tensor[0, 4 + 16, 20] = 0.95

    # Mục tiêu 3: Người (class 0) nhưng conf=0.30 (< ngưỡng 0.50) -> phải bị loại
    tensor[0, 0, 30] = 200.0
    tensor[0, 1, 30] = 200.0
    tensor[0, 2, 30] = 60.0
    tensor[0, 3, 30] = 120.0
    tensor[0, 4 + 0, 30] = 0.30

    scale = 0.5
    pad = (0, 140)
    orig_shape = (720, 1280)

    detections = postprocess_yolov8(
        tensor,
        orig_shape=orig_shape,
        scale=scale,
        pad=pad,
        conf_thresh=0.50,
        iou_thresh=0.45
    )

    assert len(detections) == 1
    det = detections[0]
    assert det.class_id == 2
    assert det.class_name == "Ô tô"
    assert pytest.approx(det.confidence, 0.01) == 0.88

    # Kiểm tra tọa độ đã được khôi phục về ảnh 1280x720:
    # box 640x640: cx=320, cy=320, w=100, h=80 -> x1=270, y1=280, x2=370, y2=360
    # Map back: x1 = (270 - 0)/0.5 = 540, x2 = (370 - 0)/0.5 = 740
    # y1 = (280 - 140)/0.5 = 280, y2 = (360 - 140)/0.5 = 440
    assert pytest.approx(det.x1, 1.0) == 540.0
    assert pytest.approx(det.x2, 1.0) == 740.0
    assert pytest.approx(det.y1, 1.0) == 280.0
    assert pytest.approx(det.y2, 1.0) == 440.0


def test_yolov8_onnx_inference():
    """Kiểm tra khởi tạo và chạy suy luận mô hình ONNX thực tế trên ảnh kiểm thử"""
    model_path = os.path.join(os.path.dirname(__file__), "..", "models", "yolov8n.onnx")
    if not os.path.exists(model_path):
        pytest.skip("Chưa tìm thấy models/yolov8n.onnx để chạy kiểm thử tích hợp")

    detector = YOLOv8Detector(model_path, conf_thresh=0.40)
    assert detector.is_ready is True

    # Tạo ảnh thử nghiệm 1280x720
    test_img = np.zeros((720, 1280, 3), dtype=np.uint8)
    # Vẽ một hình chữ nhật giả lập xe
    cv2.rectangle(test_img, (400, 300), (800, 600), (120, 120, 120), -1)

    dets, latency = detector.detect(test_img)
    assert isinstance(dets, list)
    assert latency > 0.0


def test_detection_tracker_holds_missed_frames_and_smooths_jitter():
    """Kiểm tra DetectionTracker giữ ổn định Bounding Box khi YOLO rớt 2-3 khung và giảm rung tọa độ"""
    from detector_worker import DetectionTracker

    tracker = DetectionTracker(iou_thresh=0.20, pos_alpha=0.42, size_alpha=0.35, max_missed=5)
    deviations = []
    for i in range(10):
        jitter = 12.0 if i % 2 == 0 else -12.0
        # Khung 4 & 5 mất detection tạm thời ([])
        raw = [] if i in (4, 5) else [
            Detection(500.0 + jitter, 300.0, 700.0 + jitter, 500.0, 0.78, 2, "Ô tô")
        ]
        out = tracker.update(raw, (720, 1280))
        assert len(out) == 1, f"Mất khung hình tại bước {i}"
        if i >= 2:
            deviations.append(abs(out[0].cx - 600.0))

    assert max(deviations) < 9.5, f"Dao động tọa độ còn cao: {max(deviations):.2f}px"


def test_detection_tracker_hungarian_crossing_and_bytetrack_rescue():
    """Kiểm tra Hungarian Assignment chống tráo ID khi 2 xe cắt ngang + ByteTrack giữ track bằng conf thấp"""
    from detector_worker import DetectionTracker

    tracker = DetectionTracker(iou_thresh=0.20, pos_alpha=0.42, size_alpha=0.35, max_missed=7)
    # 2 xe khởi tạo ở 2 phía trái/phải đi về phía nhau ở vùng trung tâm
    id_a = None
    id_b = None
    for step in range(18):
        ax1 = 100.0 + step * 35.0
        bx1 = 750.0 - step * 35.0
        # Tại step 10 cho xe A giảm conf tạm thời xuống 0.38 (ByteTrack Stage 2 rescue)
        conf_a = 0.38 if step == 10 else 0.85
        dets = [
            Detection(ax1, 300.0, ax1 + 140.0, 420.0, conf_a, 2, "Ô tô"),
            Detection(bx1, 330.0, bx1 + 140.0, 450.0, 0.85, 2, "Ô tô"),
        ]
        out = tracker.update(dets, (720, 1280))
        assert len(out) == 2
        if step == 2:
            left = min(out, key=lambda d: d.cx)
            right = max(out, key=lambda d: d.cx)
            id_a = left.track_id
            id_b = right.track_id
            assert id_a != id_b

    # Sau khi 2 xe đi xuyên qua nhau (A ở bên phải, B ở bên trái) -> không được tráo ID
    final_right = max(out, key=lambda d: d.cx)
    final_left = min(out, key=lambda d: d.cx)
    assert final_right.track_id == id_a
    assert final_left.track_id == id_b


def test_enhance_low_light_frame_lifts_dark_and_preserves_daylight():
    """Kiểm tra bộ tăng cường ảnh thiếu sáng chỉ kích hoạt khi ảnh tối [2..88) và giữ nguyên ảnh ban ngày"""
    from detector_worker import enhance_low_light_frame

    day_img = np.full((240, 320, 3), 130, dtype=np.uint8)
    out_day, luma_day = enhance_low_light_frame(day_img)
    assert luma_day >= 88.0
    assert out_day is day_img

    dark_img = np.full((240, 320, 3), 20, dtype=np.uint8)
    dark_img[80:160, 100:220] = 35
    out_dark, luma_dark = enhance_low_light_frame(dark_img)
    assert 2.0 <= luma_dark < 88.0
    assert float(np.mean(out_dark)) > float(np.mean(dark_img)) + 20.0


def test_detection_tracker_class_label_hysteresis_blocks_low_conf_flip():
    """Nhãn 'Ô tô' đã xác nhận không bị 1 frame nhiễu 'Xe buýt (22%)' cướp nhãn khi dừng xe"""
    from detector_worker import DetectionTracker

    tracker = DetectionTracker(iou_thresh=0.20, pos_alpha=0.42, size_alpha=0.35, max_missed=10)
    # 5 frame đầu xác nhận ổn định Ô tô (conf=0.82)
    for _ in range(5):
        out = tracker.update(
            [Detection(450.0, 250.0, 780.0, 520.0, 0.82, 2, "Ô tô")],
            (720, 1280),
        )
    assert len(out) == 1
    assert out[0].class_name == "Ô tô"
    tid = out[0].track_id

    # Frame chói đèn phanh: model nhầm sang Xe buýt 22%
    out_glare = tracker.update(
        [Detection(452.0, 252.0, 778.0, 518.0, 0.22, 5, "Xe buýt")],
        (720, 1280),
    )
    assert len(out_glare) == 1
    assert out_glare[0].track_id == tid
    assert out_glare[0].class_name == "Ô tô"


def test_filter_road_glitches_drops_tiny_stripe_and_keeps_real_cars():
    """Loại nhiễu vạch kẻ đường nhỏ sát mũi xe nhưng giữ nguyên xe thật ở xa gần đường chân trời hoặc xe gần to"""
    from detector_worker import YOLOv8Detector

    # 1. Nhiễu vạch kẻ đường độ tin cậy thấp ở dưới (cy=500/720, bottom=528/720, 66x56px, conf=0.47)
    stripe_noise = Detection(526.0, 472.0, 592.0, 528.0, 0.47, 2, "Ô tô")
    # 2. Xe thật ở xa trên dashcam gắn cao/góc chúc (cy=530/720, bottom=550/720, 62x40px, conf=0.74)
    horizon_car = Detection(814.0, 510.0, 876.0, 550.0, 0.74, 2, "Ô tô")
    # 3. Xe tải thật ở gần bên trái (258x356px)
    near_truck = Detection(0.0, 220.0, 258.0, 576.0, 0.68, 7, "Xe tải")

    # 4. Nhiễu vệt đèn pha mặt đường ban đêm (rộng > 68%, dẹt ngang ratio > 3.0, chạm sát mép dưới 96%)
    headlight_slab = Detection(228.0, 402.0, 1156.0, 688.0, 0.55, 2, "Ô tô")

    kept = YOLOv8Detector.filter_road_glitches(
        [stripe_noise, horizon_car, near_truck, headlight_slab], 720, 1280
    )
    assert len(kept) == 2
    assert horizon_car in kept
    assert near_truck in kept
    assert stripe_noise not in kept
    assert headlight_slab not in kept
