# -*- coding: utf-8 -*-
"""
Module Thu thập Khung hình Camera (CameraWorker)
- Hỗ trợ Camera USB DirectShow trên Windows, RTSP/HTTP URL, và tệp video mô phỏng
- Thiết lập độ phân giải chuẩn 1280x720 @ 30 FPS
- Điểm lật gương ngang duy nhất (flip horizontal) tại nguồn, đảm bảo đồng bộ cho detector và UI
- Tự động chuyển fallback mô phỏng nếu không tìm thấy camera vật lý
"""

import os
import time
import subprocess
import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal


def get_available_cameras():
    """Quét và trả về danh sách các camera khả dụng trên Windows kèm tên thiết bị"""
    try:
        out = subprocess.check_output(
            ['powershell', '-Command', 'Get-PnpDevice -Class Camera | Select-Object -ExpandProperty FriendlyName'],
            creationflags=0x08000000
        ).decode('utf-8', errors='ignore')
        cams = [c.strip() for c in out.strip().splitlines() if c.strip()]
        if cams:
            return [f"Camera {i}: {name}" for i, name in enumerate(cams)]
    except Exception:
        pass

    # Fallback kiểm tra cổng OpenCV trực tiếp
    available = []
    for idx in range(3):
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if cap.isOpened():
            name = "Iriun Webcam" if idx == 1 else "Camera USB"
            available.append(f"Camera {idx}: {name}")
            cap.release()
    return available if available else ["Camera 0: Mặc định"]


class CameraWorker(QThread):
    """Luồng đọc khung hình camera độc lập, không block GUI"""
    frame_ready = pyqtSignal(np.ndarray)
    status_changed = pyqtSignal(str, bool)

    def __init__(self, source=0, flip_horizontal=False, target_width=1280, target_height=720, target_fps=30):
        super().__init__()
        self.source = source
        self.flip_horizontal = bool(flip_horizontal)
        self.target_width = target_width
        self.target_height = target_height
        self.target_fps = target_fps
        self.is_running = False
        self.is_simulation = False
        self.cap = None

    def set_source(self, source):
        self.source = source

    def set_flip(self, flip: bool):
        self.flip_horizontal = bool(flip)

    def set_simulation(self, sim_mode: bool):
        self.is_simulation = bool(sim_mode)

    def stop(self):
        self.is_running = False
        if self.cap and self.cap.isOpened():
            try:
                self.cap.release()
            except Exception:
                pass
        self.wait(1500)

    def _open_capture(self):
        src = self.source
        # Kiểm tra nếu là số nguyên hoặc chuỗi số nguyên
        is_index = False
        cam_idx = 0
        if isinstance(src, int):
            is_index = True
            cam_idx = src
        elif isinstance(src, str) and src.isdigit():
            is_index = True
            cam_idx = int(src)

        if is_index:
            # Mở qua DirectShow trên Windows
            cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(cam_idx)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)
                cap.set(cv2.CAP_PROP_FPS, self.target_fps)
                try:
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                except Exception:
                    pass
                return cap
        else:
            # Chuỗi RTSP, HTTP URL hoặc đường dẫn tệp video
            if isinstance(src, str) and os.path.exists(src):
                cap = cv2.VideoCapture(src)
                if cap.isOpened():
                    return cap
            elif isinstance(src, str) and (src.startswith("rtsp://") or src.startswith("http://") or src.startswith("https://")):
                cap = cv2.VideoCapture(src)
                if cap.isOpened():
                    return cap

        return None

    def _clean_iriun_splash(self, frame: np.ndarray) -> np.ndarray:
        """
        Tự động phát hiện và xóa dòng chữ phản chiếu lộn ngược (mirrored reflection text)
        trong khung hình chờ của Iriun Webcam khi chưa kết nối điện thoại.
        """
        if frame is None or frame.size == 0:
            return frame
        # Bỏ qua ngay lập tức nếu khung hình có độ sáng bình thường (camera đang hoạt động thực tế)
        if frame.mean() > 6.0:
            return frame
        h, w = frame.shape[:2]
        # Khung hình chờ Iriun có viền trên và dưới hoàn toàn màu đen
        top_check = frame[:int(h * 0.25), :]
        bot_check = frame[int(h * 0.75):, :]
        if np.count_nonzero(top_check > 40) > 0 or np.count_nonzero(bot_check > 40) > 0:
            return frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        thresh = (gray > 80).astype(np.uint8)
        nz = np.count_nonzero(thresh)
        if 400 < nz < 35000:
            y_idxs, _ = np.where(thresh > 0)
            y_min, y_max = y_idxs.min(), y_idxs.max()
            mid_y = (y_min + y_max) // 2
            # Tìm vị trí phân cách giữa dòng chữ thuận và dòng chữ ngược
            gap_y = mid_y
            for y in range(mid_y - 6, mid_y + 7):
                if np.count_nonzero(thresh[y, :]) == 0:
                    gap_y = y
                    break
            cleaned = frame.copy()
            cleaned[gap_y:, :] = 0
            return cleaned
        return frame

    def run(self):
        self.is_running = True

        if not self.is_simulation:
            self.cap = self._open_capture()
            if self.cap is None or not self.cap.isOpened():
                self.is_simulation = True
                self.status_changed.emit("Không tìm thấy Camera phần cứng. Đã chuyển sang mô phỏng video.", False)
            else:
                w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                self.status_changed.emit(f"Camera đã kết nối ({w}x{h} @ {self.target_fps}fps)", True)

        frame_count = 0
        interval = 1.0 / max(10, self.target_fps)

        while self.is_running:
            t0 = time.time()
            if not self.is_simulation and self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    # Tự động loại bỏ dòng chữ ngược trong khung hình chờ của Iriun Webcam
                    frame = self._clean_iriun_splash(frame)
                    # Điểm lật ngang duy nhất tại nguồn thu thập
                    if self.flip_horizontal:
                        frame = cv2.flip(frame, 1)
                    self.frame_ready.emit(frame)
                else:
                    # Nếu là tệp video và đã hết, tua lại từ đầu
                    if isinstance(self.source, str) and os.path.exists(self.source):
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    else:
                        time.sleep(0.02)
            else:
                # Chế độ mô phỏng khung hình giao thông
                frame = self._generate_simulated_frame(frame_count)
                if self.flip_horizontal:
                    frame = cv2.flip(frame, 1)
                self.frame_ready.emit(frame)
                frame_count += 1

            elapsed = time.time() - t0
            sleep_time = interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        if self.cap and self.cap.isOpened():
            try:
                self.cap.release()
            except Exception:
                pass

    def _generate_simulated_frame(self, frame_count: int) -> np.ndarray:
        """Tạo khung cảnh đường phố mô phỏng chân thực với kích thước 1280x720"""
        h, w = self.target_height, self.target_width
        frame = np.zeros((h, w, 3), dtype=np.uint8)

        # Bầu trời đêm
        horizon_y = int(h * 0.42)
        frame[:horizon_y, :] = [30, 24, 20]
        # Mặt đường bê tông/nhựa xám
        frame[horizon_y:, :] = [45, 45, 45]

        # Vạch kẻ đường hai bên
        cv2.line(frame, (int(w * 0.15), h), (int(w * 0.42), horizon_y), (180, 180, 180), 4)
        cv2.line(frame, (int(w * 0.85), h), (int(w * 0.58), horizon_y), (180, 180, 180), 4)

        # Vạch tim đường đứt đoạn chuyển động
        dash_offset = (frame_count * 16) % 100
        for y in range(horizon_y + dash_offset, h, 100):
            scale = (y - horizon_y) / (h - horizon_y)
            x_center = int(w * 0.5)
            width = int(5 + scale * 10)
            y_end = min(h, y + int(40 * scale))
            cv2.line(frame, (x_center, y), (x_center, y_end), (0, 215, 255), width)

        # Xe mô phỏng tiến lại gần rồi lùi xa (chu kỳ 6 giây)
        cycle = (frame_count % 180) / 180.0
        dist_scale = np.sin(cycle * np.pi)  # 0 -> 1 -> 0
        car_w = int(140 + dist_scale * 280)
        car_h = int(90 + dist_scale * 160)
        car_cx = int(w * 0.5 + np.sin(frame_count * 0.04) * 80)
        car_cy = int(horizon_y + 40 + dist_scale * (h - horizon_y - 120))

        x1 = max(0, car_cx - car_w // 2)
        y1 = max(0, car_cy - car_h // 2)
        x2 = min(w, car_cx + car_w // 2)
        y2 = min(h, car_cy + car_h // 2)

        # Thân xe
        cv2.rectangle(frame, (x1, y1), (x2, y2), (80, 95, 140), -1)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (200, 220, 240), 2)

        # Kính sau
        kw1 = int(x1 + car_w * 0.15)
        kw2 = int(x2 - car_w * 0.15)
        kh1 = int(y1 + car_h * 0.15)
        kh2 = int(y1 + car_h * 0.50)
        if kw2 > kw1 and kh2 > kh1:
            cv2.rectangle(frame, (kw1, kh1), (kw2, kh2), (25, 25, 30), -1)

        # Đèn hậu đỏ
        radius = max(6, int(car_h * 0.1))
        cv2.circle(frame, (x1 + 20, y2 - 20), radius, (0, 0, 255), -1)
        cv2.circle(frame, (x2 - 20, y2 - 20), radius, (0, 0, 255), -1)

        # Biển số
        cv2.rectangle(frame, (car_cx - 40, y2 - 30), (car_cx + 40, y2 - 10), (240, 240, 240), -1)
        cv2.rectangle(frame, (car_cx - 40, y2 - 30), (car_cx + 40, y2 - 10), (50, 50, 50), 1)

        # Watermark
        cv2.putText(frame, "CH\u1ebe \u0110\u1ed8 M\u00d4 PH\u1eceNG (SIMULATION)", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        return frame
