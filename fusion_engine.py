# -*- coding: utf-8 -*-
"""
Module Kết hợp Dữ liệu Radar & Camera (Sensor Fusion Engine)
- Ánh xạ tọa độ không gian 2D của Radar (X, Y mét) lên mặt phẳng ảnh Camera (pixel)
  bằng mô hình quang học Pin-hole với góc mở ngang camera_hfov_deg.
- Ghép cặp 1-1 (Greedy / Gating) giữa vật cản nhận diện YOLO và mục tiêu bám vết Radar.
- Mục tiêu ghép cặp thành công: hiển thị Bounding Box kèm tên loại xe/người, khoảng cách,
  tốc độ, TTC và màu cảnh báo (Xanh / Vàng / Đỏ).
- Mục tiêu Radar không ghép được: chỉ hiển thị trên Radar Canvas, không vẽ hộp ảo lên Camera.
- Mục tiêu Camera không ghép được: vẽ viền xám mờ "Chưa có số đo khoảng cách".
"""

import math
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np

try:
    from PIL import Image, ImageDraw, ImageFont
    font_paths = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/tahoma.ttf",
    ]
    _TTF_FONT = None
    for fp in font_paths:
        if os.path.exists(fp):
            _TTF_FONT = ImageFont.truetype(fp, 22)
            break
except Exception:
    _TTF_FONT = None

from detector_worker import Detection
from radar_parser import TrackedTarget


@dataclass
class FusedObject:
    """Đối tượng sau khi kết hợp dữ liệu giữa Camera và Radar"""
    id: int                                # ID từ radar (nếu có) hoặc -1
    detection: Optional[Detection]         # Nhận diện hình ảnh YOLO
    radar_target: Optional[TrackedTarget]  # Dữ liệu mục tiêu Radar đã lọc & bám vết
    projected_px: Optional[float]          # Tọa độ X chiếu trên ảnh (pixel)
    is_associated: bool                    # Đã ghép cặp thành công giữa 2 cảm biến
    threat_level: str = "SAFE"             # SAFE | WARN | DANGER
    threat_color_bgr: Tuple[int, int, int] = (60, 200, 60) # Mặc định xanh lá
    display_label: str = ""                # Nhãn hiển thị


def project_radar_to_camera_x(
    x_m: float,
    y_m: float,
    frame_width: int,
    hfov_deg: float = 65.0,
    offset_x_m: float = 0.0,
    offset_y_m: float = 0.0,
    invert_radar_x: bool = True
) -> Optional[float]:
    """
    Chiếu tọa độ Radar (x_m, y_m) sang hoành độ pixel (px) trên ảnh Camera theo mô hình Pin-hole.
    - x_m > 0: bên phải tâm radar, x_m < 0: bên trái tâm radar.
    - y_m > 0: khoảng cách thẳng phía trước.
    - invert_radar_x: đảo dấu X nếu góc nhìn ngược chiều.
    """
    # Điều chỉnh góc lắp đặt và offset
    adj_x = -x_m if invert_radar_x else x_m
    cam_x = adj_x - offset_x_m
    cam_y = y_m - offset_y_m

    # Nếu vật cản ở sau hoặc quá sát ống kính (<= 10cm) -> không chiếu được
    if cam_y <= 0.10:
        return None

    # Tiêu cự tính theo hoành độ f_x = (w / 2) / tan(hfov / 2)
    half_fov_rad = math.radians(hfov_deg / 2.0)
    fx = (frame_width / 2.0) / math.tan(half_fov_rad)

    # Chiếu hoành độ pixel
    px = (frame_width / 2.0) + (cam_x / cam_y) * fx
    return px


def _hungarian_assign_fusion(cost_matrix: np.ndarray, max_valid_cost: float = 1e5) -> List[Tuple[int, int]]:
    """Thuật toán Hungarian tối ưu ghép cặp 1-1 toàn cục cho Sensor Fusion."""
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
            if float(cost[r_idx, c_idx]) < max_valid_cost:
                if transposed:
                    pairs.append((c_idx, r_idx))
                else:
                    pairs.append((r_idx, c_idx))
    return pairs


class FusionEngine:
    """Bộ máy kết hợp đa cảm biến Radar + Camera (Mahalanobis Gating + Hungarian 1-1 + Khử phản xạ kép)"""

    VEHICLE_CLASSES = {2, 3, 5, 7}  # Ô tô, Xe máy, Xe buýt, Xe tải

    def __init__(
        self,
        hfov_deg: float = 65.0,
        offset_x_m: float = 0.0,
        offset_y_m: float = 0.0,
        invert_radar_x: bool = True
    ):
        self.hfov_deg = hfov_deg
        self.offset_x_m = offset_x_m
        self.offset_y_m = offset_y_m
        self.invert_radar_x = invert_radar_x
        self._threat_hold: Dict[int, Tuple[str, float]] = {}

    def update_calibration(self, hfov_deg: float, offset_x_m: float, offset_y_m: float, invert_radar_x: bool):
        self.hfov_deg = float(hfov_deg)
        self.offset_x_m = float(offset_x_m)
        self.offset_y_m = float(offset_y_m)
        self.invert_radar_x = bool(invert_radar_x)

    def fuse(
        self,
        radar_targets: List[TrackedTarget],
        detections: List[Detection],
        frame_shape: Tuple[int, int],  # (h, w)
        warn_dist_m: float = 3.5,
        warn_ttc_s: float = 3.0,
        danger_dist_m: float = 1.8,
        danger_ttc_s: float = 1.8
    ) -> List[FusedObject]:
        """
        Thực hiện ghép cặp tối ưu toàn cục 1-1 bằng Mahalanobis + Hungarian Assignment,
        đồng thời khử phản xạ radar trùng lặp trên cùng một thân xe.
        """
        frame_h, frame_w = frame_shape[:2]
        fused_list: List[FusedObject] = []

        # Tiêu cự quy đổi pixel để tính độ bất định góc của radar
        half_fov_rad = math.radians(max(10.0, self.hfov_deg) / 2.0)
        fx = (frame_w / 2.0) / math.tan(half_fov_rad)
        tan_sigma_theta = math.tan(math.radians(3.5))  # ~3.5 độ sai số góc HLK-LD2450

        # Bước 1: Tính toán tọa độ chiếu px cho từng mục tiêu radar
        projected_radar = []
        for r in radar_targets:
            px = project_radar_to_camera_x(
                x_m=r.x,
                y_m=r.y,
                frame_width=frame_w,
                hfov_deg=self.hfov_deg,
                offset_x_m=self.offset_x_m,
                offset_y_m=self.offset_y_m,
                invert_radar_x=self.invert_radar_x
            )
            projected_radar.append((r, px))

        # Bước 2: Xây ma trận chi phí Mahalanobis chuẩn hóa và giải Hungarian 1-1
        INF_COST = 1e6
        n_r = len(projected_radar)
        n_d = len(detections)
        cost_mat = np.full((n_r, n_d), INF_COST, dtype=np.float64)

        for r_idx, (r, px) in enumerate(projected_radar):
            if px is None or not (-50 <= px <= frame_w + 50):
                continue

            cam_y = max(0.3, float(r.y) - self.offset_y_m)
            cam_x = (-float(r.x) if self.invert_radar_x else float(r.x)) - self.offset_x_m
            # Độ bất định ngang radar khi chiếu sang pixel
            sigma_rad = max(22.0, fx * (1.0 + (cam_x / cam_y) ** 2) * tan_sigma_theta)

            for d_idx, det in enumerate(detections):
                cx = det.cx
                w_box = det.width
                sigma_cam = max(32.0, 0.38 * w_box)
                var_tot = sigma_rad * sigma_rad + sigma_cam * sigma_cam

                diff = abs(px - cx)
                maha_sq = (diff * diff) / var_tot
                gate_px = max(0.6 * w_box, 80.0)

                if (det.x1 - 45 <= px <= det.x2 + 45) and (maha_sq <= 4.5 or diff <= gate_px):
                    # Ưu tiên khoảng cách Mahalanobis nhỏ, cộng thêm sai lệch pixel nhẹ để phá thế cân bằng
                    cost_mat[r_idx, d_idx] = maha_sq + 0.002 * diff

        matched_radar = set()
        matched_det = set()
        associated_objects: List[FusedObject] = []

        if n_r > 0 and n_d > 0:
            for r_idx, d_idx in _hungarian_assign_fusion(cost_mat, max_valid_cost=1e5):
                matched_radar.add(r_idx)
                matched_det.add(d_idx)

                r, px = projected_radar[r_idx]
                det = detections[d_idx]

                # Đánh giá mức độ cảnh báo của đối tượng
                threat, color = self._evaluate_threat(r, warn_dist_m, warn_ttc_s, danger_dist_m, danger_ttc_s)

                # Chuẩn hiển thị Người vận hành: chỉ "Người 0.9 m" khi có số đo cự ly
                label = f"{det.class_name} {r.distance:.1f} m"

                fobj = FusedObject(
                    id=r.id,
                    detection=det,
                    radar_target=r,
                    projected_px=px,
                    is_associated=True,
                    threat_level=threat,
                    threat_color_bgr=color,
                    display_label=label
                )
                fused_list.append(fobj)
                associated_objects.append(fobj)

        # Bước 3: Thêm các mục tiêu Radar CHƯA ghép được (lọc bỏ phản xạ kép trên cùng 1 thân xe)
        for r_idx, (r, px) in enumerate(projected_radar):
            if r_idx in matched_radar:
                continue

            # Kiểm tra xem mục tiêu radar dư này có phải phản xạ đa đường từ chính chiếc xe đã ghép không
            is_multipath_dup = False
            if px is not None:
                for assoc in associated_objects:
                    adet = assoc.detection
                    arad = assoc.radar_target
                    if adet is None or arad is None:
                        continue
                    if adet.class_id not in self.VEHICLE_CLASSES:
                        continue
                    if adet.x1 <= px <= adet.x2:
                        dx_m = abs(float(r.x) - float(arad.x))
                        dy_m = abs(float(r.y) - float(arad.y))
                        dv_kmh = abs(float(r.speed_kmh) - float(arad.speed_kmh))
                        if dx_m <= 0.65 and dy_m <= 0.90 and dv_kmh <= 4.5:
                            is_multipath_dup = True
                            break
            if is_multipath_dup:
                continue

            threat, color = self._evaluate_threat(r, warn_dist_m, warn_ttc_s, danger_dist_m, danger_ttc_s)
            from config import format_speed_status
            speed_txt = format_speed_status(r.speed_kmh, getattr(r, 'closing_speed_mps', 0.0))
            parts = [f"Vật cản #{r.id}", f"{r.distance:.1f}m"]
            if speed_txt != "Đứng yên":
                parts.append(speed_txt)
            label = " | ".join(parts)
            fused_list.append(FusedObject(
                id=r.id,
                detection=None,
                radar_target=r,
                projected_px=px,
                is_associated=False,
                threat_level=threat,
                threat_color_bgr=color,
                display_label=label
            ))

        # Bước 4: Thêm các nhận diện Camera CHƯA ghép được số đo Radar (hiển thị loại vật thể kèm Chờ radar)
        for d_idx, det in enumerate(detections):
            if d_idx not in matched_det:
                label = f"{det.class_name} (Chờ radar)"
                fused_list.append(FusedObject(
                    id=-1,
                    detection=det,
                    radar_target=None,
                    projected_px=None,
                    is_associated=False,
                    threat_level="SAFE",
                    threat_color_bgr=(140, 140, 140), # Xám trung tính
                    display_label=label
                ))

        return fused_list

    def deduplicate_radar_by_detections(
        self,
        radar_targets: List[TrackedTarget],
        detections: List[Detection],
        frame_shape: Tuple[int, int],
    ) -> List[TrackedTarget]:
        """
        Loại bỏ các phản xạ đa đường (2 chấm radar trên cùng 1 thân xe) khi Camera xác nhận
        chỉ có 1 phương tiện nằm tại vùng đó, giúp đồng bộ đếm giữa Camera và Radar Canvas.
        """
        if len(radar_targets) <= 1 or not detections:
            return list(radar_targets)

        frame_h, frame_w = frame_shape[:2]
        half_fov_rad = math.radians(max(10.0, self.hfov_deg) / 2.0)
        fx = (frame_w / 2.0) / math.tan(half_fov_rad)
        tan_sigma_theta = math.tan(math.radians(3.5))

        proj = [
            project_radar_to_camera_x(
                x_m=r.x, y_m=r.y, frame_width=frame_w,
                hfov_deg=self.hfov_deg, offset_x_m=self.offset_x_m,
                offset_y_m=self.offset_y_m, invert_radar_x=self.invert_radar_x,
            )
            for r in radar_targets
        ]

        INF_COST = 1e6
        cost_mat = np.full((len(radar_targets), len(detections)), INF_COST, dtype=np.float64)
        for r_idx, (r, px) in enumerate(zip(radar_targets, proj)):
            if px is None or not (-50 <= px <= frame_w + 50):
                continue
            cam_y = max(0.3, float(r.y) - self.offset_y_m)
            cam_x = (-float(r.x) if self.invert_radar_x else float(r.x)) - self.offset_x_m
            sigma_rad = max(22.0, fx * (1.0 + (cam_x / cam_y) ** 2) * tan_sigma_theta)
            for d_idx, det in enumerate(detections):
                sigma_cam = max(32.0, 0.38 * det.width)
                diff = abs(px - det.cx)
                maha_sq = (diff * diff) / (sigma_rad * sigma_rad + sigma_cam * sigma_cam)
                if (det.x1 - 45 <= px <= det.x2 + 45) and (maha_sq <= 4.5 or diff <= max(0.6 * det.width, 80.0)):
                    cost_mat[r_idx, d_idx] = maha_sq + 0.002 * diff

        matched = _hungarian_assign_fusion(cost_mat, max_valid_cost=1e5)
        matched_r_map = {r_idx: d_idx for r_idx, d_idx in matched}
        suppressed = set()

        for r_idx, (r, px) in enumerate(zip(radar_targets, proj)):
            if r_idx in matched_r_map or px is None:
                continue
            for mr_idx, md_idx in matched_r_map.items():
                adet = detections[md_idx]
                if adet.class_id not in self.VEHICLE_CLASSES:
                    continue
                if adet.x1 <= px <= adet.x2:
                    arad = radar_targets[mr_idx]
                    if (
                        abs(float(r.x) - float(arad.x)) <= 0.65
                        and abs(float(r.y) - float(arad.y)) <= 0.90
                        and abs(float(r.speed_kmh) - float(arad.speed_kmh)) <= 4.5
                    ):
                        suppressed.add(r_idx)
                        break

        return [r for i, r in enumerate(radar_targets) if i not in suppressed]

    def _evaluate_threat(
        self,
        r: TrackedTarget,
        warn_dist_m: float,
        warn_ttc_s: float,
        danger_dist_m: float,
        danger_ttc_s: float
    ) -> Tuple[str, Tuple[int, int, int]]:
        """Xác định màu và cấp cảnh báo cho từng mục tiêu đơn lẻ (có hysteresis chống nháy Đỏ/Vàng)"""
        # Vật đứng yên (closing_speed_mps <= 0.3): không được ra DANGER, tối đa WARN nếu < 1.8m
        is_closing = r.closing_speed_mps is not None and r.closing_speed_mps > 0.3

        raw_threat = "SAFE"
        raw_color: Tuple[int, int, int] = (60, 200, 60)

        # DANGER (Đỏ): tiến lại gần và (khoảng cách <= danger_dist hoặc TTC <= danger_ttc)
        if is_closing and (r.distance <= danger_dist_m or (r.ttc_s is not None and r.ttc_s <= danger_ttc_s)):
            raw_threat = "DANGER"
            raw_color = (40, 40, 230)
        elif r.distance <= warn_dist_m:
            if is_closing or r.distance <= danger_dist_m:
                raw_threat = "WARN"
                raw_color = (30, 200, 240)

        now = time.monotonic()
        # Dọn dẹp trạng thái cũ quá 4s
        if len(self._threat_hold) > 16:
            stale = [k for k, (_, ts) in self._threat_hold.items() if now - ts > 4.0]
            for k in stale:
                del self._threat_hold[k]

        if raw_threat == "DANGER":
            self._threat_hold[r.id] = ("DANGER", now)
            return raw_threat, raw_color

        prev = self._threat_hold.get(r.id)
        if prev is not None:
            prev_lvl, prev_ts = prev
            if prev_lvl == "DANGER" and (now - prev_ts) < 0.8 and r.distance <= warn_dist_m:
                return "DANGER", (40, 40, 230)

        self._threat_hold[r.id] = (raw_threat, now)
        return raw_threat, raw_color


def draw_fused_annotations(
    frame: np.ndarray,
    fused_objects: List[FusedObject],
    selected_target_id: Optional[int] = None
) -> np.ndarray:
    """
    Vẽ khung chữ nhật nhận diện và nhãn thông số lên khung hình camera.
    Không vẽ hộp giả lập cho mục tiêu radar không nhìn thấy trên camera.
    """
    out = frame.copy()

    for obj in fused_objects:
        det = obj.detection
        if det is None:
            # Mục tiêu chỉ có trên radar -> không vẽ lên camera
            continue

        x1, y1, x2, y2 = det.as_xyxy()
        color = obj.threat_color_bgr
        is_selected = (obj.id == selected_target_id) and (obj.id != -1)

        # Viền hộp nhận diện: 2px hoặc 3px nếu đang được chọn
        thickness = 3 if is_selected else 2
        cv2.rectangle(out, (x1, y1), (x2, y2), color, thickness)

        # Dấu hiệu mục tiêu đang được chọn (corner brackets nổi bật)
        if is_selected:
            corner_len = min(20, (x2 - x1) // 4, (y2 - y1) // 4)
            # 4 góc nổi bật màu trắng/cyan
            sel_color = (255, 255, 255)
            cv2.line(out, (x1, y1), (x1 + corner_len, y1), sel_color, 4)
            cv2.line(out, (x1, y1), (x1, y1 + corner_len), sel_color, 4)
            cv2.line(out, (x2, y1), (x2 - corner_len, y1), sel_color, 4)
            cv2.line(out, (x2, y1), (x2, y1 + corner_len), sel_color, 4)
            cv2.line(out, (x1, y2), (x1 + corner_len, y2), sel_color, 4)
            cv2.line(out, (x1, y2), (x1, y2 - corner_len), sel_color, 4)
            cv2.line(out, (x2, y2), (x2 - corner_len, y2), sel_color, 4)
            cv2.line(out, (x2, y2), (x2, y2 - corner_len), sel_color, 4)

        # Thanh tiêu đề nhãn (Pill label) - Chỉ hiển thị khi có nhãn chữ (đã ghép số đo cự ly)
        label = obj.display_label
        if label:
            # Đo kích thước chữ chuẩn xác
            if _TTF_FONT is not None:
                try:
                    bbox = _TTF_FONT.getbbox(label)
                    txt_w = bbox[2] - bbox[0]
                    txt_h = bbox[3] - bbox[1]
                except Exception:
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    (txt_w, txt_h), _ = cv2.getTextSize(label, font, 0.7, 2)
            else:
                font = cv2.FONT_HERSHEY_SIMPLEX
                (txt_w, txt_h), _ = cv2.getTextSize(label, font, 0.7, 2)

            pill_h = txt_h + 10
            pill_w = txt_w + 18

            if y1 - pill_h < 0:
                label_y1 = y1
                label_y2 = y1 + pill_h
            else:
                label_y1 = y1 - pill_h
                label_y2 = y1
            label_x1 = x1
            label_x2 = min(frame.shape[1], x1 + pill_w)

            patch_w = max(10, label_x2 - label_x1)
            patch_h = max(10, label_y2 - label_y1)

            # Chữ nhãn: ưu tiên TrueType Font Bold nếu có để hiển thị sắc nét rõ ràng
            if _TTF_FONT is not None and patch_w > 0 and patch_h > 0:
                try:
                    patch = Image.new('RGB', (patch_w, patch_h), color=(18, 22, 28))
                    draw = ImageDraw.Draw(patch)
                    draw.text((8, 4), label, font=_TTF_FONT, fill=(255, 255, 255))
                    patch_bgr = np.array(patch)[:, :, ::-1]
                    out[label_y1:label_y2, label_x1:label_x2] = patch_bgr
                    cv2.rectangle(out, (label_x1, label_y1), (label_x2, label_y2), color, 2)
                except Exception:
                    cv2.rectangle(out, (label_x1, label_y1), (label_x2, label_y2), (18, 22, 28), -1)
                    cv2.rectangle(out, (label_x1, label_y1), (label_x2, label_y2), color, 2)
                    cv2.putText(out, label, (label_x1 + 6, label_y2 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
            else:
                cv2.rectangle(out, (label_x1, label_y1), (label_x2, label_y2), (18, 22, 28), -1)
                cv2.rectangle(out, (label_x1, label_y1), (label_x2, label_y2), color, 2)
                cv2.putText(out, label, (label_x1 + 6, label_y2 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

        # Nếu có điểm chiếu radar px, vẽ chấm định vị nhỏ ở đáy hộp để kiểm tra trực quan
        if obj.projected_px is not None and obj.is_associated:
            proj_x = int(round(obj.projected_px))
            if 0 <= proj_x < frame.shape[1]:
                cv2.circle(out, (proj_x, y2), 4, color, -1)
                cv2.circle(out, (proj_x, y2), 5, (255, 255, 255), 1)

    return out
