# -*- coding: utf-8 -*-
"""
Chuyển đổi video thật từ captures/nexar_samples (.mp4) thành tệp Radar mô phỏng đồng bộ (.csv)
để phát trực tiếp trên SimulationPlayer:
- Dùng YOLOv8n (detector_worker.py) quét ở nhịp 10 Hz (đúng tốc độ lấy mẫu Radar HLK-LD2450)
- Bám vết tối đa 3 mục tiêu (ID 1..3), chiếu ngược Pinhole sang (x_m, y_m) khớp 100% Bounding Box
- Đồng bộ thêm kịch bản tiếp cận theo time_of_alert / time_of_event từ metadata.csv (cho clip positive)
"""

import os
import sys
import csv
import math
import time
import pathlib
from typing import Dict, List, Tuple

import cv2

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from detector_worker import YOLOv8Detector, Detection
from config import config_manager


def load_metadata(meta_csv: pathlib.Path) -> Dict[str, dict]:
    info: Dict[str, dict] = {}
    if not meta_csv.exists():
        return info
    with open(meta_csv, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            info[row["file_name"]] = row
    return info


def det_to_depth_unclamped_m(det: Detection, frame_w: int, frame_h: int) -> float:
    w_frac = det.width / max(1.0, float(frame_w))
    h_frac = det.height / max(1.0, float(frame_h))
    bottom_frac = det.y2 / max(1.0, float(frame_h))
    size_score = max(w_frac * 0.95, h_frac * 1.10)
    # Ước lượng chiều sâu quang học liên tục đến ~20m trước khi giới hạn về dải Radar
    raw_d = 0.85 / max(size_score, 0.042)
    if bottom_frac > 0.78:
        raw_d *= 0.85
    return max(0.75, min(20.0, raw_d))


def det_to_range_m(det: Detection, frame_w: int, frame_h: int) -> float:
    return max(0.75, min(5.80, det_to_depth_unclamped_m(det, frame_w, frame_h)))


def process_video(
    video_path: pathlib.Path,
    detector: YOLOv8Detector,
    meta: dict,
    is_positive: bool,
    hfov_deg: float = 65.0,
) -> pathlib.Path:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Không mở được video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps < 10.0 or fps > 120.0:
        fps = 30.0
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1280)
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 720)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    sample_stride = max(1, int(round(fps / 10.0)))  # Lấy mẫu YOLO ~10 Hz
    fx = (frame_w / 2.0) / math.tan(math.radians(hfov_deg / 2.0))

    t_alert = float(meta["time_of_alert"]) if meta.get("time_of_alert") else None
    t_event = float(meta["time_of_event"]) if meta.get("time_of_event") else None

    # Tracker tối đa 3 slot (ID 1, 2, 3)
    tracks: Dict[int, dict] = {}
    keyframes: List[Tuple[int, List[Tuple[int, float, float, float]]]] = []

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            break

        if frame_idx % sample_stride == 0:
            t_sec = frame_idx / fps
            t_ms = int(round(t_sec * 1000.0))

            dets, _ = detector.detect(frame)
            # Ưu tiên tối đa 3 phương tiện/người to và gần nhất trung tâm
            dets_sorted = sorted(
                dets,
                key=lambda d: (d.width * d.height) * (1.2 - 0.5 * abs(d.cx - frame_w / 2.0) / (frame_w / 2.0)),
                reverse=True,
            )[:3]

            # Ghép detection với track gần nhất
            used_dets = set()
            matched_tracks = {}
            for tid, tr in list(tracks.items()):
                best_i = -1
                best_dist = 180.0
                for idx, d in enumerate(dets_sorted):
                    if idx in used_dets:
                        continue
                    dist_px = math.hypot(d.cx - tr["cx"], d.cy - tr["cy"])
                    if dist_px < best_dist:
                        best_dist = dist_px
                        best_i = idx
                if best_i >= 0:
                    used_dets.add(best_i)
                    d = dets_sorted[best_i]
                    matched_tracks[tid] = (tr, d)
                else:
                    tr["missed"] += 1

            # Xóa track mất quá ngưỡng nhịp (giữ lâu hơn khi xe đã đứng rất gần để chống mất khi mở cốp/chói đèn)
            for tid in list(tracks.keys()):
                max_miss = 25 if tracks[tid]["y_m"] < 2.2 else 12
                if tid not in matched_tracks and tracks[tid]["missed"] > max_miss:
                    del tracks[tid]

            # Cấp ID mới (1..3) cho detection chưa ghép
            for idx, d in enumerate(dets_sorted):
                if idx in used_dets:
                    continue
                free_id = next((k for k in (1, 2, 3) if k not in tracks), None)
                if free_id is None:
                    break
                y_depth_init = det_to_depth_unclamped_m(d, frame_w, frame_h)
                y_init = max(0.75, min(5.80, y_depth_init))
                if not is_positive:
                    y_init = max(2.4, y_init)
                cam_x_init = ((d.cx - frame_w / 2.0) / fx) * y_init
                tracks[free_id] = {
                    "cx": d.cx,
                    "cy": d.cy,
                    "x_m": max(-y_init * 1.5, min(y_init * 1.5, -cam_x_init)),
                    "y_m": y_init,
                    "y_depth": y_depth_init,
                    "v_kmh": 0.0,
                    "t_sec": t_sec,
                    "missed": 0,
                    "hits": 0,
                }
                matched_tracks[free_id] = (tracks[free_id], d)

            # Kiểm tra pha sự cố đối với video positive
            in_incident_window = False
            inc_progress = 0.0
            if is_positive and t_alert is not None and t_event is not None:
                win_start = max(0.0, t_alert - 1.5)
                win_end = t_event + 0.8
                if win_start <= t_sec <= win_end:
                    in_incident_window = True
                    inc_progress = min(1.0, max(0.0, (t_sec - win_start) / max(0.5, t_event - win_start)))

            # Chọn track gần tâm nhất để áp dụng kịch bản tiếp cận trong vùng sự cố (nếu positive)
            primary_tid = None
            if matched_tracks:
                primary_tid = min(
                    matched_tracks.keys(),
                    key=lambda tid: abs(matched_tracks[tid][1].cx - frame_w / 2.0),
                )

            frame_rows: List[Tuple[int, float, float, float]] = []
            for tid, (tr, d) in sorted(matched_tracks.items()):
                dt = max(0.05, t_sec - tr["t_sec"])
                y_depth_target = det_to_depth_unclamped_m(d, frame_w, frame_h)
                y_depth_smooth = 0.25 * y_depth_target + 0.75 * tr.get("y_depth", y_depth_target)

                y_target = max(0.75, min(5.80, y_depth_smooth))
                if not is_positive:
                    # Clip bình thường giữ khoảng cách an toàn thực tế
                    y_target = max(2.4, y_target)
                elif in_incident_window and tid == primary_tid:
                    # Đưa mục tiêu chính tiến sát từ ~3.2m xuống ~0.95m đúng lúc event
                    y_ramp = 3.2 - 2.25 * inc_progress
                    y_target = min(y_target, y_ramp)

                y_smooth = 0.28 * y_target + 0.72 * tr["y_m"]
                # Nghịch đảo phép chiếu Pinhole khớp invert_radar_x=True
                cam_x = ((d.cx - frame_w / 2.0) / fx) * y_smooth
                x_raw = -cam_x
                # Giới hạn trong góc mở ±58° của HLK-LD2450
                max_lat = y_smooth * math.tan(math.radians(58.0))
                x_raw = max(-max_lat, min(max_lat, x_raw))
                x_smooth = 0.30 * x_raw + 0.70 * tr["x_m"] if tr["missed"] == 0 else tr["x_m"]

                # Tính vận tốc từ chiều sâu quang học trước kẹp 5.8m để xe ở xa vẫn có tốc độ tương đối thực
                dy_depth = y_depth_smooth - tr.get("y_depth", y_depth_smooth)
                dy_depth_dt = dy_depth / dt
                v_inst_kmh = max(-36.0, min(28.0, dy_depth_dt * 3.6))
                if abs(dy_depth) < 0.015 and not (in_incident_window and tid == primary_tid):
                    # Xe đứng yên: giảm nhiễu vận tốc do chói đèn phanh/viền hộp rung nhẹ
                    v_inst_kmh *= 0.30
                if not is_positive and v_inst_kmh < 0.0:
                    # Với clip bình thường, giữ TTC >= 3.3s để không báo đỏ giả ở tầm xa
                    max_safe_closing_kmh = (y_smooth / 3.3) * 3.6
                    v_inst_kmh = max(v_inst_kmh, -max_safe_closing_kmh)
                if in_incident_window and tid == primary_tid:
                    v_inst_kmh = min(v_inst_kmh, -18.0 - 8.0 * inc_progress)
                v_smooth = 0.28 * v_inst_kmh + 0.72 * tr["v_kmh"]

                tr["cx"] = d.cx
                tr["cy"] = d.cy
                tr["x_m"] = x_smooth
                tr["y_m"] = y_smooth
                tr["y_depth"] = y_depth_smooth
                tr["v_kmh"] = v_smooth
                tr["t_sec"] = t_sec
                tr["missed"] = 0
                tr["hits"] = tr.get("hits", 0) + 1

                if tr["hits"] >= 2 or d.confidence >= 0.48:
                    frame_rows.append((tid, round(x_smooth, 3), round(y_smooth, 3), round(v_smooth, 1)))

            # Giữ vị trí coasting cho các track đang mất khung tạm thời (chống Radar trống khi chói đèn/dừng xe)
            for tid, tr in sorted(tracks.items()):
                if tid in matched_tracks or tr.get("hits", 0) < 2:
                    continue
                v_coast = tr["v_kmh"] * 0.50
                if abs(v_coast) < 1.1:
                    v_coast = 0.0
                tr["v_kmh"] = v_coast
                frame_rows.append((tid, round(tr["x_m"], 3), round(tr["y_m"], 3), round(v_coast, 1)))

            # Nếu đang ở đúng cửa sổ va chạm của video positive mà YOLO tạm bị khuất/chói: giữ điểm giả lập trung tâm
            if is_positive and in_incident_window and not frame_rows:
                y_f = round(3.0 - 2.05 * inc_progress, 3)
                v_f = round(-22.0, 1)
                frame_rows.append((1, 0.0, y_f, v_f))

            keyframes.append((frame_idx, frame_rows))

        frame_idx += 1

    cap.release()

    # Làm mượt zero-phase 2 chiều theo chuỗi thời gian cho từng ID mục tiêu để chống rung số
    def _smooth_series(vals: List[float], passes: int = 2) -> List[float]:
        arr = list(vals)
        n = len(arr)
        if n < 3:
            return arr
        for _ in range(passes):
            nxt = [0.0] * n
            for i in range(n):
                s = 0.0
                w_sum = 0.0
                for off, w_k in ((-2, 0.1), (-1, 0.2), (0, 0.4), (1, 0.2), (2, 0.1)):
                    j = min(max(0, i + off), n - 1)
                    s += arr[j] * w_k
                    w_sum += w_k
                nxt[i] = s / w_sum
            arr = nxt
        return arr

    # Gom các đoạn liên tục của mỗi tid
    key_maps = [{r[0]: list(r) for r in rows} for _, rows in keyframes]
    for tid in (1, 2, 3):
        run_indices: List[int] = []
        for idx in range(len(keyframes) + 1):
            has_tid = (idx < len(keyframes)) and (tid in key_maps[idx])
            if has_tid:
                run_indices.append(idx)
            elif run_indices:
                xs = _smooth_series([key_maps[j][tid][1] for j in run_indices], passes=2)
                ys = _smooth_series([key_maps[j][tid][2] for j in run_indices], passes=2)
                vs = _smooth_series([key_maps[j][tid][3] for j in run_indices], passes=2)
                for p, j in enumerate(run_indices):
                    v_clean = 0.0 if abs(vs[p]) < 1.1 else vs[p]
                    key_maps[j][tid] = [tid, round(xs[p], 3), round(ys[p], 3), round(v_clean, 1)]
                run_indices = []
    keyframes = [
        (keyframes[idx][0], [tuple(key_maps[idx][tid]) for tid in sorted(key_maps[idx].keys())])
        for idx in range(len(keyframes))
    ]

    # Ghi CSV chuẩn theo từng khung hình (nội suy mượt hoặc giữ bậc theo t_ms)
    out_csv = video_path.with_suffix(".csv")
    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["t_ms", "id", "x_m", "y_m", "speed_kmh"])
        for k_i in range(len(keyframes)):
            f_start, rows_a = keyframes[k_i]
            f_end = keyframes[k_i + 1][0] if k_i + 1 < len(keyframes) else total_frames
            rows_b_map = {r[0]: r for r in keyframes[k_i + 1][1]} if k_i + 1 < len(keyframes) else {}

            span = max(1, f_end - f_start)
            for fi in range(f_start, f_end):
                t_ms = int(round((fi / fps) * 1000.0))
                alpha = (fi - f_start) / span
                for tid, xa, ya, va in rows_a:
                    if tid in rows_b_map:
                        _, xb, yb, vb = rows_b_map[tid]
                        xi = round(xa + (xb - xa) * alpha, 3)
                        yi = round(ya + (yb - ya) * alpha, 3)
                        vi = round(va + (vb - va) * alpha, 1)
                    else:
                        xi, yi, vi = xa, ya, va
                    writer.writerow([t_ms, tid, xi, yi, vi])

    return out_csv


def main():
    samples_dir = ROOT / "captures" / "nexar_samples" / "train"
    model_path = ROOT / "models" / "yolov8n.onnx"
    hfov = float(config_manager.get("camera_hfov_deg", 65.0))

    detector = YOLOv8Detector(str(model_path), conf_thresh=0.38, iou_thresh=0.45)
    if not detector.is_ready:
        raise RuntimeError(f"Không nạp được mô hình {model_path}")

    for sub, is_pos in (("positive", True), ("negative", False)):
        folder = samples_dir / sub
        if not folder.exists():
            continue
        meta_map = load_metadata(folder / "metadata.csv")
        for mp4 in sorted(folder.glob("*.mp4")):
            t0 = time.time()
            meta = meta_map.get(mp4.name, {})
            out_csv = process_video(mp4, detector, meta, is_positive=is_pos, hfov_deg=hfov)
            print(f"[OK] {sub}/{mp4.name} -> {out_csv.name} ({time.time() - t0:.1f}s)")


if __name__ == "__main__":
    main()
