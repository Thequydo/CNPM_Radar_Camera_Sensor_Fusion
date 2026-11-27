# -*- coding: utf-8 -*-
"""
Module Nhận diện Đối tượng Giao thông bằng YOLOv8-nano (ONNX Runtime)
- Chạy độc lập trên QThread, tự động bỏ qua khung hình cũ khi GPU/CPU đang bận
- Tiền xử lý Letterbox 640x640 chuẩn xác, giữ nguyên tỉ lệ khung hình
- Lọc 5 lớp giao thông chính: Người (0), Xe đạp (1), Ô tô (2), Xe máy (3), Xe buýt (5), Xe tải (7)
- Áp dụng NMS (Non-Maximum Suppression) với IoU 0.45, độ tin cậy >= 0.50
- Khôi phục tọa độ chính xác về kích thước khung hình gốc
"""

import os
import sys
import time
import math
import threading
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
import cv2
import numpy as np
try:
    import onnxruntime as ort
except ImportError:
    ort = None
from PyQt6.QtCore import QThread, pyqtSignal

# Từ điển các lớp COCO được quan tâm
TARGET_CLASSES = {
    0: "Người",
    1: "Xe đạp",
    2: "Ô tô",
    3: "Xe máy",
    5: "Xe buýt",
    7: "Xe tải"
}


@dataclass
class Detection:
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_id: int
    class_name: str
    track_id: int = -1

    @property
    def cx(self) -> float:
        return (self.x1 + self.x2) / 2.0

    @property
    def cy(self) -> float:
        return (self.y1 + self.y2) / 2.0

    @property
    def width(self) -> float:
        return max(0.0, self.x2 - self.x1)

    @property
    def height(self) -> float:
        return max(0.0, self.y2 - self.y1)

    def as_xyxy(self) -> Tuple[int, int, int, int]:
        return int(round(self.x1)), int(round(self.y1)), int(round(self.x2)), int(round(self.y2))


def letterbox_image(image: np.ndarray, target_size: int = 640) -> Tuple[np.ndarray, float, Tuple[int, int]]:
    """
    Biến đổi hình ảnh sang kích thước 640x640 với padding màu xám (114, 114, 114)
    Trả về: (ảnh_letterbox, tỉ_lệ_scale, (pad_x, pad_y))
    """
    h, w = image.shape[:2]
    scale = min(target_size / h, target_size / w)
    nw, nh = int(round(w * scale)), int(round(h * scale))

    resized = cv2.resize(image, (nw, nh), interpolation=cv2.INTER_LINEAR)
    pad_x = (target_size - nw) // 2
    pad_y = (target_size - nh) // 2

    canvas = np.full((target_size, target_size, 3), 114, dtype=np.uint8)
    canvas[pad_y:pad_y + nh, pad_x:pad_x + nw] = resized
    return canvas, scale, (pad_x, pad_y)


def postprocess_yolov8(
    output_tensor: np.ndarray,
    orig_shape: Tuple[int, int],
    scale: float,
    pad: Tuple[int, int],
    conf_thresh: float = 0.50,
    iou_thresh: float = 0.45,
    target_classes: Optional[dict] = None
) -> List[Detection]:
    """
    Giải mã tensor output (1, 84, 8400) của YOLOv8, áp dụng NMS và trả về danh sách Detection.
    """
    if target_classes is None:
        target_classes = TARGET_CLASSES

    # output_tensor có shape (1, 84, 8400) -> chuyển về (8400, 84)
    predictions = np.squeeze(output_tensor)
    if predictions.shape[0] < predictions.shape[1]:
        predictions = predictions.T  # (8400, 84)

    boxes = []
    confidences = []
    class_ids = []

    pad_x, pad_y = pad
    orig_h, orig_w = orig_shape

    # 4 cột đầu: cx, cy, w, h theo tọa độ 640x640
    # 80 cột sau: điểm số cho từng lớp COCO
    scores = predictions[:, 4:]
    max_scores = np.max(scores, axis=1)
    max_classes = np.argmax(scores, axis=1)

    # Lọc sơ bộ theo ngưỡng conf và các lớp cần phát hiện
    mask = max_scores >= conf_thresh
    filtered_indices = np.where(mask)[0]

    for idx in filtered_indices:
        cls_id = int(max_classes[idx])
        if cls_id not in target_classes:
            continue

        conf = float(max_scores[idx])
        cx, cy, w, h = predictions[idx, :4]

        # Đưa về tọa độ góc trên trái (x, y) trên ảnh 640x640
        x = cx - w / 2.0
        y = cy - h / 2.0

        boxes.append([int(round(x)), int(round(y)), int(round(w)), int(round(h))])
        confidences.append(conf)
        class_ids.append(cls_id)

    if not boxes:
        return []

    # Áp dụng Non-Maximum Suppression (NMS)
    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_thresh, iou_thresh)
    if len(indices) == 0:
        return []

    # cv2.dnn.NMSBoxes trả về mảng 1D hoặc 2D tùy phiên bản OpenCV
    if isinstance(indices, np.ndarray):
        indices = indices.flatten()

    results: List[Detection] = []
    for i in indices:
        bx, by, bw, bh = boxes[i]
        # Khôi phục tọa độ về kích thước ảnh gốc
        x1 = (bx - pad_x) / scale
        y1 = (by - pad_y) / scale
        x2 = (bx + bw - pad_x) / scale
        y2 = (by + bh - pad_y) / scale

        # Bounding clamp
        x1 = max(0.0, min(float(orig_w), x1))
        y1 = max(0.0, min(float(orig_h), y1))
        x2 = max(0.0, min(float(orig_w), x2))
        y2 = max(0.0, min(float(orig_h), y2))

        if x2 > x1 and y2 > y1:
            cls_id = class_ids[i]
            results.append(Detection(
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                confidence=confidences[i],
                class_id=cls_id,
                class_name=target_classes[cls_id]
            ))

    return results


def enhance_low_light_frame(image: np.ndarray, clahe: Optional[Any] = None) -> Tuple[np.ndarray, float]:
    """
    Tăng cường độ tương phản và độ sáng cục bộ (Gamma + CLAHE trên kênh L-LAB) cho ảnh thiếu sáng / mưa đêm.
    Chỉ kích hoạt khi độ sáng trung bình nằm trong [2.0, 88.0) để không ảnh hưởng ban ngày hay ảnh đen kiểm thử.
    """
    if image is None or image.size == 0:
        return image, 0.0
    sample = image[::4, ::4]
    mean_luma = float(np.mean(cv2.cvtColor(sample, cv2.COLOR_BGR2GRAY)))
    if mean_luma >= 88.0 or mean_luma < 2.0:
        return image, mean_luma

    gamma = max(0.42, min(0.85, 0.42 + (mean_luma / 88.0) * 0.43))
    lut = np.power(np.arange(256, dtype=np.float32) / 255.0, gamma) * 255.0
    lifted = cv2.LUT(image, np.clip(lut, 0, 255).astype(np.uint8))

    lab = cv2.cvtColor(lifted, cv2.COLOR_BGR2LAB)
    l_ch, a_ch, b_ch = cv2.split(lab)
    if clahe is None:
        clahe = cv2.createCLAHE(clipLimit=1.9, tileGridSize=(8, 8))
    l_eq = clahe.apply(l_ch)
    merged = cv2.cvtColor(cv2.merge([l_eq, a_ch, b_ch]), cv2.COLOR_LAB2BGR)
    return merged, mean_luma


class YOLOv8Detector:
    """Bộ nhận diện YOLOv8 hỗ trợ ONNX Runtime hoặc fallback OpenCV DNN + Low-Light/Rain Enhancement"""

    def __init__(self, model_path: str, conf_thresh: float = 0.50, iou_thresh: float = 0.45):
        self.model_path = model_path
        self.conf_thresh = conf_thresh
        self.iou_thresh = iou_thresh
        self.session = None
        self.cv_net = None
        self.input_name = None
        self.output_name = None
        self.is_ready = False
        self._clahe = cv2.createCLAHE(clipLimit=1.9, tileGridSize=(8, 8))
        self._load_model()

    def _load_model(self):
        if not os.path.exists(self.model_path):
            meipass = getattr(sys, "_MEIPASS", None)
            candidates = [
                os.path.join(meipass, self.model_path) if meipass else "",
                os.path.join(os.path.dirname(os.path.abspath(__file__)), self.model_path),
            ]
            for c in candidates:
                if c and os.path.exists(c):
                    self.model_path = c
                    break
        if not os.path.exists(self.model_path):
            print(f"[CẢNH BÁO] Không tìm thấy tệp mô hình ONNX tại: {self.model_path}")
            return

        if ort is not None:
            try:
                opts = ort.SessionOptions()
                opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                opts.intra_op_num_threads = 4
                self.session = ort.InferenceSession(self.model_path, sess_options=opts, providers=['CPUExecutionProvider'])
                self.input_name = self.session.get_inputs()[0].name
                self.output_name = self.session.get_outputs()[0].name
                self.is_ready = True
                return
            except Exception as e:
                print(f"[CẢNH BÁO] ONNX Runtime không khả dụng ({e}), chuyển sang OpenCV DNN.")

        try:
            self.cv_net = cv2.dnn.readNetFromONNX(self.model_path)
            self.is_ready = True
        except Exception as e:
            print(f"[LỖI] Khởi tạo mô hình YOLOv8 ONNX thất bại: {e}")
            self.is_ready = False

    def _infer_single(self, image: np.ndarray, conf_thresh: float) -> List[Detection]:
        orig_shape = image.shape[:2]
        canvas, scale, pad = letterbox_image(image, 640)

        # Chuyển BGR -> RGB, chuẩn hóa [0, 1], HWC -> CHW, thêm batch dimension (1, 3, 640, 640)
        blob = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        blob = np.transpose(blob, (2, 0, 1))
        blob = np.expand_dims(blob, axis=0)

        if self.session is not None:
            outputs = self.session.run([self.output_name], {self.input_name: blob})
            output_tensor = outputs[0]
        else:
            self.cv_net.setInput(blob)
            output_tensor = self.cv_net.forward()

        return postprocess_yolov8(
            output_tensor=output_tensor,
            orig_shape=orig_shape,
            scale=scale,
            pad=pad,
            conf_thresh=conf_thresh,
            iou_thresh=self.iou_thresh,
            target_classes=TARGET_CLASSES
        )

    @staticmethod
    def filter_road_glitches(detections: List[Detection], orig_h: int, orig_w: int) -> List[Detection]:
        """Lọc nhiễu vạch kẻ đường/bóng phản chiếu quá nhỏ nằm sát vùng tiền cảnh mũi xe."""
        if orig_h < 240 or orig_w < 320 or not detections:
            return detections
        sane: List[Detection] = []
        for d in detections:
            if d.class_id in (2, 5, 7):  # Ô tô, Xe buýt, Xe tải
                w_frac = d.width / float(orig_w)
                h_frac = d.height / float(orig_h)
                cy_frac = d.cy / float(orig_h)
                top_frac = d.y1 / float(orig_h)
                bottom_frac = d.y2 / float(orig_h)
                aspect = d.width / max(1.0, d.height)
                if d.confidence < 0.50 and bottom_frac >= 0.72 and cy_frac >= 0.67:
                    if (w_frac < 0.085 and h_frac < 0.11) or (w_frac * h_frac < 0.0085):
                        continue
                if d.confidence < 0.55 and bottom_frac >= 0.86 and h_frac < 0.16 and w_frac < 0.18:
                    continue
                # Lọc hộp dẹt khổng lồ nằm sát mép dưới (vệt đèn pha chiếu mặt đường / phản chiếu taplo ban đêm)
                if top_frac >= 0.48 and bottom_frac >= 0.90:
                    if (w_frac >= 0.55 and aspect >= 2.35) or w_frac >= 0.85:
                        continue
            sane.append(d)
        return sane

    def detect(self, image: np.ndarray, low_light_adapt: bool = True) -> Tuple[List[Detection], float]:
        """
        Nhận diện đối tượng trên một ảnh OpenCV BGR.
        Tự động tăng cường thiếu sáng + Road-ROI Zoom khi trời tối/mưa.
        Trả về (danh_sách_detections, độ_trễ_ms)
        """
        if not self.is_ready or (self.session is None and self.cv_net is None) or image is None:
            return [], 0.0

        t0 = time.time()
        if low_light_adapt:
            proc_img, mean_luma = enhance_low_light_frame(image, clahe=self._clahe)
            is_dark = (2.0 <= mean_luma < 82.0)
            eff_conf = min(self.conf_thresh, max(0.30, self.conf_thresh - 0.12)) if is_dark else self.conf_thresh
        else:
            proc_img = image
            is_dark = False
            eff_conf = self.conf_thresh

        detections = self._infer_single(proc_img, eff_conf)

        # Road-ROI Zoom Fallback: trong đêm tối / mưa nếu quét toàn khung chưa thấy xe ở phía trước,
        # phóng lớn vùng làn đường trung tâm để nhận diện xe ở xa/chìm trong bóng tối.
        if is_dark and not detections:
            h, w = proc_img.shape[:2]
            if h >= 120 and w >= 160:
                x0, y0 = int(w * 0.22), int(h * 0.28)
                x1, y1 = int(w * 0.78), int(h * 0.84)
                roi_dets = self._infer_single(proc_img[y0:y1, x0:x1], eff_conf)
                for rd in roi_dets:
                    detections.append(Detection(
                        x1=rd.x1 + x0,
                        y1=rd.y1 + y0,
                        x2=rd.x2 + x0,
                        y2=rd.y2 + y0,
                        confidence=rd.confidence,
                        class_id=rd.class_id,
                        class_name=rd.class_name,
                        track_id=rd.track_id,
                    ))

        # Lọc hình học phối cảnh: loại bỏ nhiễu mặt đường/vạch kẻ đường quá nhỏ ở vùng tiền cảnh sát mũi xe
        orig_h, orig_w = image.shape[:2]
        detections = self.filter_road_glitches(detections, orig_h, orig_w)

        latency_ms = (time.time() - t0) * 1000.0
        return detections, latency_ms


def _hungarian_assign(cost_matrix: np.ndarray, max_valid_cost: float = 1e5) -> List[Tuple[int, int]]:
    """
    Thuật toán Hungarian (Jonker-Volgenant / Munkres) tối ưu toàn cục 1-1 cho ma trận chi phí (N x M).
    Không phụ thuộc scipy; xử lý chuẩn cho cả N > M và N <= M.
    """
    cost = np.asarray(cost_matrix, dtype=np.float64)
    if cost.size == 0 or cost.shape[0] == 0 or cost.shape[1] == 0:
        return []

    n_rows, n_cols = cost.shape
    transposed = False
    if n_rows > n_cols:
        cost = cost.T
        n_rows, n_cols = cost.shape
        transposed = True

    u = np.zeros(n_rows + 1, dtype=np.float64)
    v = np.zeros(n_cols + 1, dtype=np.float64)
    p = np.zeros(n_cols + 1, dtype=np.int32)
    way = np.zeros(n_cols + 1, dtype=np.int32)

    for i in range(1, n_rows + 1):
        p[0] = i
        j0 = 0
        minv = np.full(n_cols + 1, np.inf, dtype=np.float64)
        used = np.zeros(n_cols + 1, dtype=bool)
        row_i = cost[i - 1]
        while True:
            used[j0] = True
            i0 = int(p[j0])
            delta = np.inf
            j1 = 0
            cur_row = cost[i0 - 1] if i0 > 0 else row_i
            for j in range(1, n_cols + 1):
                if not used[j]:
                    cur = float(cur_row[j - 1]) - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            for j in range(n_cols + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = int(way[j0])
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    pairs: List[Tuple[int, int]] = []
    for j in range(1, n_cols + 1):
        if p[j] > 0:
            r_idx = int(p[j] - 1)
            c_idx = int(j - 1)
            val = float(cost[r_idx, c_idx])
            if val < max_valid_cost:
                if transposed:
                    pairs.append((c_idx, r_idx))
                else:
                    pairs.append((r_idx, c_idx))
    return pairs


class _VisualTrack:
    """
    Trạng thái bám vết Kalman Filter 4 chiều [cx, cy, vx, vy] cho từng đối tượng trên Camera.
    Hỗ trợ Adaptive Measurement Noise R theo YOLO confidence score.
    """
    _F = np.array([
        [1.0, 0.0, 1.0, 0.0],
        [0.0, 1.0, 0.0, 1.0],
        [0.0, 0.0, 0.96, 0.0],
        [0.0, 0.0, 0.0, 0.96],
    ], dtype=np.float64)
    _H = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
    ], dtype=np.float64)
    _Q = np.diag([4.0, 4.0, 2.2, 2.2]).astype(np.float64)

    def __init__(self, track_id: int, det: Detection):
        self.track_id = track_id
        self.state = np.array([det.cx, det.cy, 0.0, 0.0], dtype=np.float64)
        self.P = np.diag([36.0, 36.0, 22.0, 22.0]).astype(np.float64)
        self.w = max(8.0, det.width)
        self.h = max(8.0, det.height)
        self.confidence = float(det.confidence)
        self.class_id = int(det.class_id)
        self.class_name = str(det.class_name)
        self._class_scores: Dict[int, Tuple[float, str]] = {
            self.class_id: (max(0.50, self.confidence) * 1.5, self.class_name)
        }
        self.hits = 1
        self.missed = 0
        self.pred_state = self.state.copy()
        self.pred_P = self.P.copy()

    @property
    def cx(self) -> float:
        return float(self.state[0])

    @property
    def cy(self) -> float:
        return float(self.state[1])

    @property
    def vx(self) -> float:
        return float(self.state[2])

    @property
    def vy(self) -> float:
        return float(self.state[3])

    def predict(self) -> Tuple[np.ndarray, np.ndarray]:
        self.pred_state = self._F @ self.state
        self.pred_P = self._F @ self.P @ self._F.T + self._Q
        return self.pred_state, self.pred_P

    def innovation_cov(self, base_r: float = 55.0) -> np.ndarray:
        return self._H @ self.pred_P @ self._H.T + np.diag([base_r, base_r])

    def update_kf(self, det: Detection, base_pos_var: float = 55.0, size_alpha: float = 0.35):
        # Adaptive R theo YOLO confidence: high conf -> R nhỏ (bám sát nhanh), low conf -> R lớn (tin prediction)
        conf_c = max(0.20, min(0.98, float(det.confidence)))
        # Tại conf=0.78 -> scale ~1.0; conf=0.92 -> scale ~0.42; conf=0.38 -> scale ~2.9
        r_scale = ((1.14 - conf_c) / 0.36) ** 2
        r_var = max(12.0, min(350.0, base_pos_var * r_scale))

        z = np.array([det.cx, det.cy], dtype=np.float64)
        y = z - (self._H @ self.pred_state)
        # Khi xe đứng yên (vận tốc ~0, lệch nhỏ), giảm rung biên do chói đèn phanh/mở cốp
        if (
            math.hypot(float(y[0]), float(y[1])) < 4.5
            and abs(float(self.state[2])) < 1.5
            and abs(float(self.state[3])) < 1.5
        ):
            r_var = min(350.0, r_var * 1.8)
        R = np.diag([r_var, r_var]).astype(np.float64)
        S = self._H @ self.pred_P @ self._H.T + R
        K = self.pred_P @ self._H.T @ np.linalg.inv(S)

        self.state = self.pred_state + K @ y
        self.state[2] = max(-55.0, min(55.0, self.state[2]))
        self.state[3] = max(-45.0, min(45.0, self.state[3]))
        I4 = np.eye(4, dtype=np.float64)
        self.P = (I4 - K @ self._H) @ self.pred_P

        # Adaptive EMA kích thước khung theo confidence
        eff_sa = max(0.15, min(0.60, size_alpha * max(0.50, min(1.30, conf_c / 0.72))))
        self.w = eff_sa * max(8.0, det.width) + (1.0 - eff_sa) * self.w
        self.h = eff_sa * max(8.0, det.height) + (1.0 - eff_sa) * self.h

        self.confidence = 0.50 * conf_c + 0.50 * self.confidence

        # Class label hysteresis: tích lũy điểm tin cậy để nhãn không bị 1 frame nhiễu (vd: Xe buýt 22%) cướp mất
        for cid in list(self._class_scores.keys()):
            sc, cname = self._class_scores[cid]
            self._class_scores[cid] = (sc * 0.90, cname)
        d_cid = int(det.class_id)
        d_cname = str(det.class_name)
        vote_w = conf_c * (1.2 if d_cid == self.class_id else 1.0)
        prev_sc = self._class_scores.get(d_cid, (0.0, d_cname))[0]
        self._class_scores[d_cid] = (prev_sc + vote_w, d_cname)

        cur_sc = self._class_scores.get(self.class_id, (0.0, self.class_name))[0]
        best_cid, (best_sc, best_cname) = max(self._class_scores.items(), key=lambda kv: kv[1][0])
        if best_cid != self.class_id and ((best_sc > cur_sc and conf_c >= 0.45) or self.hits <= 1):
            self.class_id = best_cid
            self.class_name = best_cname

        self.hits += 1
        self.missed = 0

    def coast(self, orig_w: int, orig_h: int):
        self.missed += 1
        prev_cx, prev_cy = float(self.state[0]), float(self.state[1])
        damp = 0.72 if self.hits >= 5 else 0.45
        nvx = float(self.state[2]) * damp
        nvy = float(self.state[3]) * damp
        self.P = self.pred_P.copy()
        self.state[0] = max(self.w * 0.25, min(float(orig_w) - self.w * 0.25, prev_cx + nvx))
        self.state[1] = max(self.h * 0.25, min(float(orig_h) - self.h * 0.25, prev_cy + nvy))
        self.state[2] = nvx
        self.state[3] = nvy
        self.confidence *= 0.94


def _box_iou_xywh(ax: float, ay: float, aw: float, ah: float, bx: float, by: float, bw: float, bh: float) -> float:
    ax1, ay1, ax2, ay2 = ax - aw * 0.5, ay - ah * 0.5, ax + aw * 0.5, ay + ah * 0.5
    bx1, by1, bx2, by2 = bx - bw * 0.5, by - bh * 0.5, bx + bw * 0.5, by + bh * 0.5
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0.0:
        return 0.0
    union = (aw * ah) + (bw * bh) - inter
    return inter / union if union > 0.0 else 0.0


class DetectionTracker:
    """
    Bộ bám vết nâng cao (Kalman Filter + Hungarian Assignment + ByteTrack 2-tầng + Adaptive R):
    - Dự đoán trạng thái [cx, cy, vx, vy] bằng Kalman Filter giảm rung khung và giữ quỹ đạo mượt.
    - Ghép cặp tối ưu toàn cục 1-1 bằng Hungarian Algorithm (chống tráo ID khi xe cắt ngang).
    - ByteTrack 2-stage: ưu tiên ghép detection độ tin cậy cao trước, dùng detection thấp hơn để cứu track bị che khuất.
    - Adaptive R theo confidence score YOLO.
    """
    VEHICLE_CLASSES = {1, 2, 3, 5, 7}

    def __init__(
        self,
        iou_thresh: float = 0.20,
        pos_alpha: float = 0.42,
        size_alpha: float = 0.35,
        max_missed: int = 7,
        high_conf_thresh: float = 0.48,
    ):
        self.iou_thresh = float(iou_thresh)
        self.pos_alpha = float(pos_alpha)
        self.size_alpha = float(size_alpha)
        self.max_missed = int(max_missed)
        self.high_conf_thresh = float(high_conf_thresh)
        # Quy đổi pos_alpha sang base_pos_var cho Kalman Filter
        pa = max(0.15, min(0.85, self.pos_alpha))
        self.base_pos_var = 55.0 * ((0.42 / pa) ** 1.3)
        self._tracks: Dict[int, _VisualTrack] = {}
        self._next_id = 1
        self._lock = threading.Lock()

    def reset(self):
        with self._lock:
            self._tracks.clear()
            self._next_id = 1

    @staticmethod
    def _classes_compatible(cls_a: int, cls_b: int) -> bool:
        if cls_a == cls_b:
            return True
        return (cls_a in DetectionTracker.VEHICLE_CLASSES) and (cls_b in DetectionTracker.VEHICLE_CLASSES)

    def _build_cost_matrix(
        self,
        tids: List[int],
        det_indices: List[int],
        detections: List[Detection],
        strict_gate: bool = False,
    ) -> np.ndarray:
        INF_COST = 1e6
        n_t = len(tids)
        n_d = len(det_indices)
        cost = np.full((n_t, n_d), INF_COST, dtype=np.float64)
        if n_t == 0 or n_d == 0:
            return cost

        for r, tid in enumerate(tids):
            tr = self._tracks[tid]
            pred_cx = float(tr.pred_state[0])
            pred_cy = float(tr.pred_state[1])
            diag = max(30.0, math.hypot(tr.w, tr.h))
            tr_area = max(1.0, tr.w * tr.h)
            S_inv = np.linalg.inv(tr.innovation_cov(self.base_pos_var))
            max_dist = max(55.0, diag * (0.45 if strict_gate else 0.60))

            for c, d_idx in enumerate(det_indices):
                det = detections[d_idx]
                if not self._classes_compatible(tr.class_id, det.class_id):
                    continue
                det_w = max(8.0, det.width)
                det_h = max(8.0, det.height)
                area_ratio = (det_w * det_h) / tr_area
                if area_ratio < 0.28 or area_ratio > 3.5:
                    continue

                iou = _box_iou_xywh(pred_cx, pred_cy, tr.w, tr.h, det.cx, det.cy, det_w, det_h)
                center_dist = math.hypot(det.cx - pred_cx, det.cy - pred_cy)
                nu = np.array([det.cx - pred_cx, det.cy - pred_cy], dtype=np.float64)
                maha_sq = float(nu.T @ S_inv @ nu)

                iou_ok = iou >= (max(self.iou_thresh, 0.25) if strict_gate else self.iou_thresh)
                dist_ok = center_dist <= max_dist
                maha_ok = (not strict_gate) and (maha_sq <= 12.25) and (center_dist <= max_dist * 1.4)
                if iou_ok or dist_ok or maha_ok:
                    norm_dist = min(2.0, center_dist / max_dist)
                    maha_term = min(3.0, math.sqrt(max(0.0, maha_sq)) * 0.22)
                    cls_bonus = 0.0 if tr.class_id == det.class_id else 0.18
                    # Chi phí tối ưu: IoU thấp phạt nặng, Mahalanobis + khoảng cách chuẩn hóa
                    cost[r, c] = (1.0 - iou) * 2.2 + norm_dist * 0.8 + maha_term + cls_bonus
        return cost

    def update(self, detections: List[Detection], frame_shape: Tuple[int, int]) -> List[Detection]:
        orig_h, orig_w = int(frame_shape[0]), int(frame_shape[1])
        with self._lock:
            track_ids = list(self._tracks.keys())
            for tid in track_ids:
                self._tracks[tid].predict()

            # Tầng 1 (ByteTrack): ghép với detection độ tin cậy cao trước
            high_idx = [i for i, d in enumerate(detections) if d.confidence >= self.high_conf_thresh]
            low_idx = [i for i, d in enumerate(detections) if d.confidence < self.high_conf_thresh]

            matched_tracks = set()
            matched_dets = set()

            if track_ids and high_idx:
                cost1 = self._build_cost_matrix(track_ids, high_idx, detections, strict_gate=False)
                for r_idx, c_idx in _hungarian_assign(cost1):
                    tid = track_ids[r_idx]
                    d_idx = high_idx[c_idx]
                    self._tracks[tid].update_kf(detections[d_idx], self.base_pos_var, self.size_alpha)
                    matched_tracks.add(tid)
                    matched_dets.add(d_idx)

            # Tầng 2 (ByteTrack): cứu các track đã từng ổn định bị che khuất một phần bằng detection độ tin cậy thấp hơn
            rem_tracks = [
                tid for tid in track_ids
                if tid not in matched_tracks and (self._tracks[tid].hits >= 2 or self._tracks[tid].missed == 0)
            ]
            if rem_tracks and low_idx:
                cost2 = self._build_cost_matrix(rem_tracks, low_idx, detections, strict_gate=True)
                for r_idx, c_idx in _hungarian_assign(cost2):
                    tid = rem_tracks[r_idx]
                    d_idx = low_idx[c_idx]
                    self._tracks[tid].update_kf(detections[d_idx], self.base_pos_var, self.size_alpha)
                    matched_tracks.add(tid)
                    matched_dets.add(d_idx)

            # Cập nhật hoặc xóa các track chưa khớp (giữ mượt khi YOLO mất tạm thời)
            to_del: List[int] = []
            for tid in track_ids:
                if tid in matched_tracks:
                    continue
                tr = self._tracks[tid]
                tr.coast(orig_w, orig_h)
                if tr.hits < 2 and tr.confidence < 0.48:
                    to_del.append(tid)
                elif tr.missed > self.max_missed:
                    to_del.append(tid)

            for tid in to_del:
                del self._tracks[tid]

            # Thêm track mới cho detection độ tin cậy cao chưa ghép (hoặc detection chưa ghép nếu chưa có track)
            for d_idx, det in enumerate(detections):
                if d_idx in matched_dets:
                    continue
                tid = self._next_id
                self._next_id += 1
                self._tracks[tid] = _VisualTrack(tid, det)

            # Xuất danh sách Detection đã ổn định
            out: List[Detection] = []
            for tid in sorted(self._tracks.keys()):
                tr = self._tracks[tid]
                if tr.missed > 0 and tr.hits < 2 and tr.confidence < 0.50:
                    continue
                if tr.hits < 2 and tr.confidence < 0.48:
                    continue
                if tr.missed > 2 and tr.hits < 3:
                    continue
                if tr.missed > 0 and tr.confidence < 0.25:
                    continue
                x1 = max(0.0, min(float(orig_w), tr.cx - tr.w * 0.5))
                y1 = max(0.0, min(float(orig_h), tr.cy - tr.h * 0.5))
                x2 = max(0.0, min(float(orig_w), tr.cx + tr.w * 0.5))
                y2 = max(0.0, min(float(orig_h), tr.cy + tr.h * 0.5))
                if x2 - x1 >= 4.0 and y2 - y1 >= 4.0:
                    out.append(Detection(
                        x1=x1,
                        y1=y1,
                        x2=x2,
                        y2=y2,
                        confidence=min(0.99, max(0.01, tr.confidence)),
                        class_id=tr.class_id,
                        class_name=tr.class_name,
                        track_id=tid,
                    ))
            return out


class DetectorWorker(QThread):
    """
    Luồng chạy nhận diện đối tượng ngầm, nhận khung hình qua push_frame.
    Chỉ xử lý khung hình mới nhất, tự động hủy bỏ khung hình cũ khi quá tải.
    """
    detections_ready = pyqtSignal(list, np.ndarray, float)  # (detections, frame, latency_ms)

    def __init__(self, model_path: str = "models/yolov8n.onnx", conf_thresh: float = 0.50, iou_thresh: float = 0.45):
        super().__init__()
        self.detector = YOLOv8Detector(model_path, conf_thresh, iou_thresh)
        self.tracker = DetectionTracker(iou_thresh=0.20, pos_alpha=0.42, size_alpha=0.35, max_missed=10)
        self.is_running = False
        self._lock = threading.Lock()
        self._latest_frame: Optional[np.ndarray] = None
        self._new_frame_event = threading.Event()

    def set_thresholds(self, conf_thresh: float, iou_thresh: float):
        self.detector.conf_thresh = conf_thresh
        self.detector.iou_thresh = iou_thresh

    def reset_tracker(self):
        self.tracker.reset()

    def push_frame(self, frame: np.ndarray):
        """Đưa khung hình mới vào luồng nhận diện (ghi đè khung hình cũ nếu chưa xử lý xong)"""
        with self._lock:
            self._latest_frame = frame
        self._new_frame_event.set()

    def stop(self):
        self.is_running = False
        self._new_frame_event.set()
        self.wait(1500)
        self.tracker.reset()

    def run(self):
        self.is_running = True
        self.tracker.reset()
        while self.is_running:
            # Chờ tín hiệu có khung hình mới
            has_new = self._new_frame_event.wait(timeout=0.05)
            if not self.is_running:
                break
            if not has_new:
                continue

            self._new_frame_event.clear()
            frame_to_process = None
            with self._lock:
                if self._latest_frame is not None:
                    frame_to_process = self._latest_frame
                    self._latest_frame = None

            if frame_to_process is not None:
                raw_detections, latency_ms = self.detector.detect(frame_to_process)
                tracked = self.tracker.update(raw_detections, frame_to_process.shape[:2])
                self.detections_ready.emit(tracked, frame_to_process, latency_ms)
