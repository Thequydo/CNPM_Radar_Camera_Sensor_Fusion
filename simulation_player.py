# -*- coding: utf-8 -*-
"""
Module Phát lại Mô phỏng Đồng bộ Radar & Camera (SimulationPlayer)
- Đọc video thật (mp4/avi) và tệp dữ liệu Radar CSV theo thời gian thực (lock-step)
- Định dạng CSV chuẩn: t_ms, id, x_m, y_m, speed_kmh
- Hỗ trợ tua điểm bắt đầu (start_sec) và tự động lặp lại khi hết video
- Tương thích ngược hoàn toàn với kịch bản tổng hợp hình hộp mặc định
"""

import os
import time
import csv
from typing import List, Dict
import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

from radar_parser import RadarTarget


class SimulationPlayer(QThread):
    """Luồng phát lại đồng bộ dữ liệu Camera và Radar đã ghi trước"""
    frame_ready = pyqtSignal(np.ndarray)
    targets_ready = pyqtSignal(list)       # Danh sách RadarTarget tại khung thời gian tương ứng
    raw_status_ready = pyqtSignal(list)    # Cập nhật bảng Gỡ lỗi Radar (nếu đang bật)
    status_changed = pyqtSignal(str, bool)

    def __init__(
        self,
        video_path: str = "",
        radar_csv_path: str = "",
        fps: float = 30.0,
        loop: bool = True,
        start_sec: float = 0.0,
    ):
        super().__init__()
        self.video_path = video_path
        self.radar_csv_path = radar_csv_path
        self.fps = fps
        self.loop = loop
        self.start_sec = max(0.0, float(start_sec))
        self.is_running = False
        self.radar_timeline: Dict[int, List[RadarTarget]] = {}
        self.cap = None

    def set_paths(self, video_path: str, radar_csv_path: str = "", start_sec: float = 0.0):
        self.video_path = video_path or ""
        self.radar_csv_path = radar_csv_path or ""
        self.start_sec = max(0.0, float(start_sec))

    def load_radar_csv(self, csv_path: str, fps_override: float = None):
        """Nạp dữ liệu Radar CSV và nhóm theo mốc thời gian làm tròn t_ms"""
        self.radar_timeline.clear()
        if not csv_path or not os.path.exists(csv_path):
            return

        eff_fps = float(fps_override) if (fps_override and fps_override > 5.0) else float(self.fps)
        eff_fps = max(10.0, eff_fps)

        try:
            with open(csv_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    t_ms = int(float(row.get("t_ms", 0)))
                    frame_idx = int(round(t_ms / (1000.0 / eff_fps)))

                    tid = int(row.get("id", 1))
                    xm = float(row.get("x_m", 0.0))
                    ym = float(row.get("y_m", 0.0))
                    speed = float(row.get("speed_kmh", 0.0))

                    # Đánh dấu age_frames=5 để AlertStateMachine xác nhận bám vết ổn định
                    target = RadarTarget(
                        target_id=tid,
                        x_m=xm,
                        y_m=ym,
                        speed_kmh=speed,
                        valid=True,
                        age_frames=5,
                    )

                    if frame_idx not in self.radar_timeline:
                        self.radar_timeline[frame_idx] = []
                    self.radar_timeline[frame_idx].append(target)
        except Exception as e:
            print(f"[CẢNH BÁO] Không thể đọc tệp Radar CSV mô phỏng: {e}")

    def stop(self):
        self.is_running = False
        self.wait(1500)
        if self.cap and self.cap.isOpened():
            try:
                self.cap.release()
            except Exception:
                pass

    def run(self):
        self.is_running = True
        eff_fps = max(10.0, float(self.fps))

        has_video = bool(self.video_path and os.path.exists(self.video_path))
        total_frames = 0
        if has_video:
            self.cap = cv2.VideoCapture(self.video_path)
            if not self.cap.isOpened():
                has_video = False
            else:
                cap_fps = self.cap.get(cv2.CAP_PROP_FPS)
                if cap_fps and 10.0 <= cap_fps <= 120.0:
                    eff_fps = float(cap_fps)
                total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

        self.load_radar_csv(self.radar_csv_path, fps_override=eff_fps)

        start_frame = 0
        if has_video and self.start_sec > 0.0 and total_frames > 0:
            start_frame = min(max(0, int(round(self.start_sec * eff_fps))), max(0, total_frames - 15))
            if start_frame > 0:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        vname = os.path.basename(self.video_path) if has_video else "Kịch bản tổng hợp 2D"
        self.status_changed.emit(f"Mô phỏng: {vname} ({eff_fps:.1f} FPS)", True)

        frame_idx = start_frame
        frame_interval = 1.0 / eff_fps
        last_valid_targets: List[RadarTarget] = []
        last_valid_frame_idx = -1000
        max_timeline_frame = max(self.radar_timeline.keys(), default=-1)

        while self.is_running:
            t_start = time.time()

            frame = None
            if has_video and self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    if self.loop:
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
                        frame_idx = start_frame
                        last_valid_targets = []
                        last_valid_frame_idx = -1000
                        ret, frame = self.cap.read()
                    else:
                        break

            if frame is None:
                if has_video:
                    break
                frame = self._synthesize_simulation_frame(frame_idx)

            targets = self.radar_timeline.get(frame_idx, [])
            if targets:
                last_valid_targets = targets
                last_valid_frame_idx = frame_idx
            elif (
                has_video
                and self.radar_timeline
                and frame_idx <= max_timeline_frame
                and last_valid_targets
                and (frame_idx - last_valid_frame_idx) <= 10
            ):
                targets = [
                    RadarTarget(
                        target_id=t.target_id,
                        x_m=t.x_m,
                        y_m=t.y_m,
                        speed_kmh=0.0,
                        closing_speed_mps=0.0,
                        valid=True,
                        age_frames=t.age_frames,
                    )
                    for t in last_valid_targets
                ]
            elif not has_video and not targets and not self.radar_timeline:
                targets = self._synthesize_radar_targets(frame_idx)

            self.frame_ready.emit(frame)
            self.targets_ready.emit(targets)
            self.raw_status_ready.emit([{"target": t, "status": "được giữ"} for t in targets[:3]])

            frame_idx += 1
            if not has_video and frame_idx > 360:
                frame_idx = 0

            elapsed = time.time() - t_start
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        if self.cap and self.cap.isOpened():
            try:
                self.cap.release()
            except Exception:
                pass

    def _synthesize_radar_targets(self, frame_idx: int) -> List[RadarTarget]:
        """Tạo mục tiêu radar đồng bộ di chuyển lại gần rồi lùi xa mượt mà (chu kỳ 180 khung ~ 6s)"""
        import math
        cycle = (frame_idx % 180) / 180.0
        dist = 1.0 + 4.0 * (1.0 - math.sin(cycle * math.pi))
        # Đạo hàm chính xác theo thời gian: d(dist)/dt -> tốc độ mượt không giật bậc
        closing_mps = (4.0 * math.pi / 6.0) * math.cos(cycle * math.pi)
        speed = -closing_mps * 3.6

        target = RadarTarget(
            target_id=1,
            x_m=0.0,
            y_m=dist,
            speed_kmh=speed,
            closing_speed_mps=closing_mps,
            valid=True,
            age_frames=5,
        )
        return [target]

    def _synthesize_simulation_frame(self, frame_idx: int) -> np.ndarray:
        """Tạo khung hình video mô phỏng HD 1280x720"""
        h, w = 720, 1280
        frame = np.zeros((h, w, 3), dtype=np.uint8)

        horizon_y = int(h * 0.42)
        frame[:horizon_y, :] = [32, 26, 22]
        frame[horizon_y:, :] = [48, 48, 48]

        cv2.line(frame, (int(w * 0.15), h), (int(w * 0.42), horizon_y), (180, 180, 180), 3)
        cv2.line(frame, (int(w * 0.85), h), (int(w * 0.58), horizon_y), (180, 180, 180), 3)

        cycle = (frame_idx % 180) / 180.0
        dist_scale = np.sin(cycle * np.pi)
        car_w = int(140 + dist_scale * 280)
        car_h = int(90 + dist_scale * 160)
        car_cx = int(w * 0.5)
        car_cy = int(horizon_y + 40 + dist_scale * (h - horizon_y - 120))

        x1, y1 = max(0, car_cx - car_w // 2), max(0, car_cy - car_h // 2)
        x2, y2 = min(w, car_cx + car_w // 2), min(h, car_cy + car_h // 2)

        cv2.rectangle(frame, (x1, y1), (x2, y2), (80, 95, 140), -1)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (200, 220, 240), 2)
        cv2.putText(frame, "SIMULATION REPLAY", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        return frame


def math_sin(val: float) -> float:
    import math
    return math.sin(val)
