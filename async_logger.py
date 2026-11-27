# -*- coding: utf-8 -*-
"""
Hàng đợi Ghi Nhật ký & Ảnh Hiện trường Bất đồng bộ (Giai đoạn 2 - Mục 2.3)
Tách toàn bộ tác vụ nén ảnh cv2.imwrite và ghi SQLite ra khỏi luồng giao diện chính PyQt6,
chống tuyệt đối hiện tượng sụt giảm FPS hoặc giật lag giao diện người dùng.
Giao diện chỉ nhận signal 'incident_saved(dict)' để cập nhật đúng dòng mới (insertRow(0)),
không dựng lại toàn bộ bảng mỗi lần.
"""

import os
import time
import queue
import threading
from typing import Optional, Dict, Any
import cv2
import numpy as np

from PyQt6.QtCore import QObject, pyqtSignal

from config import CAPTURES_DIR
import database


class AsyncLogWorker(QObject):
    """Xử lý ghi ảnh hiện trường và chèn dữ liệu sự cố vào SQLite trên luồng nền"""
    incident_saved = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.queue: queue.Queue = queue.Queue()
        self.running: bool = True

        self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="AsyncLogWorkerThread")
        self._thread.start()

    def stop(self) -> None:
        self.running = False
        self.queue.put(None)

    def queue_snapshot_capture(
        self,
        frame: np.ndarray,
        incident_id: int,
        target_info: dict,
    ) -> str:
        """
        Tạo tên tệp và đẩy việc ghi ảnh có OSD vào hàng đợi nền.
        Trả về đường dẫn tệp ảnh dự kiến.
        """
        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        filename = f"incident_{timestamp_str}_id{incident_id}.jpg"
        save_path = os.path.join(CAPTURES_DIR, filename)

        task = {
            "type": "SNAPSHOT",
            "frame": frame.copy(),
            "save_path": save_path,
            "target_info": target_info,
        }
        self.queue.put(task)
        return save_path

    def queue_save_incident(self, incident_data: dict) -> None:
        """Đẩy bản ghi sự cố vào hàng đợi ghi SQLite"""
        task = {
            "type": "SAVE_INCIDENT",
            "incident": incident_data,
        }
        self.queue.put(task)

    def _worker_loop(self) -> None:
        while self.running:
            try:
                task = self.queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if task is None:
                break

            try:
                t_type = task.get("type")
                if t_type == "SNAPSHOT":
                    self._process_snapshot(task)
                elif t_type == "SAVE_INCIDENT":
                    self._process_save_incident(task)
            except Exception as e:
                print("[LỖI ASYNC LOG WORKER]:", e)
            finally:
                self.queue.task_done()

    def _process_snapshot(self, task: dict) -> None:
        frame = task["frame"]
        save_path = task["save_path"]
        info = task.get("target_info", {})

        dist = float(info.get("distance_m", 0.0))
        speed = float(info.get("speed_kmh", 0.0))
        closing_v = float(info.get("closing_speed_mps", 0.0) or 0.0)
        ttc = info.get("ttc_sec", None)
        # Point 3: Không bao giờ in TTC: 0.0s khi ttc_sec là None hoặc <= 0
        ttc_txt = f"{ttc:.1f}s" if (ttc is not None and ttc > 0.0) else "--"
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")

        # Point 4: Hiển thị "Tien lai gan X km/h" / "Ra xa X km/h" / "Dung yen"
        from config import format_speed_status
        speed_status = format_speed_status(speed, closing_v)
        if "lại gần" in speed_status or "lai gan" in speed_status:
            speed_osd = f"Tien lai gan {abs(speed):.1f}km/h"
        elif "Ra xa" in speed_status:
            speed_osd = f"Ra xa {abs(speed):.1f}km/h"
        else:
            speed_osd = "Dung yen"

        # Vẽ dải thông tin OSD sắc nét lên ảnh hiện trường
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (0, 0), (w, 54), (22, 26, 31), -1)
        cv2.rectangle(frame, (0, 52), (w, 54), (231, 76, 60), -1)

        osd_title = f"NGUY CO VA CHAM - {now_str}"
        osd_metrics = f"Cu ly: {dist:.2f}m | Toc do: {speed_osd} | TTC: {ttc_txt}"

        cv2.putText(frame, osd_title, (16, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (231, 76, 60), 2)
        cv2.putText(frame, osd_metrics, (16, 44), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        cv2.imwrite(save_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])

    def _process_save_incident(self, task: dict) -> None:
        inc = task["incident"]
        inc_id = database.insert_incident(
            start_time=inc.get("start_time", ""),
            end_time=inc.get("end_time", ""),
            max_severity=inc.get("max_severity", "Có vật trong vùng cảnh báo"),
            object_type=inc.get("object_type", "Chưa xác định"),
            min_distance_m=inc.get("min_distance_m", 0.0),
            min_ttc_sec=inc.get("min_ttc_sec", None),
            max_speed_kmh=inc.get("max_speed_kmh", 0.0),
            image_path=inc.get("image_path", ""),
            notes=inc.get("notes", ""),
            closing_speed_mps=inc.get("closing_speed_mps", 0.0),
            speed_kmh_raw=inc.get("speed_kmh_raw", 0.0),
            user_id=inc.get("user_id", None),
            username=inc.get("username", ""),
        )
        saved_dict = dict(inc)
        saved_dict["id"] = inc_id
        # Phát tín hiệu an toàn về luồng GUI Qt
        self.incident_saved.emit(saved_dict)
