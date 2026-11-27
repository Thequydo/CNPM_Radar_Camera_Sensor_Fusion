# -*- coding: utf-8 -*-
"""
Quản lý Cấu hình Hệ thống Giám sát Giao thông & Cảnh báo Va chạm sớm
- Nguồn cấu hình chuẩn duy nhất: config.json (và background.json cho hiệu chuẩn nền)
- Lần chạy đầu tiên (khi chưa có config.json): nhập một lần từ hằng số mặc định
  và bảng system_settings trong SQLite (nếu có), sau đó độc lập hoàn toàn.
"""

import sys
import os
import json
import sqlite3
from typing import Optional, Dict, Any
from copy import deepcopy

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CAPTURES_DIR = os.path.join(BASE_DIR, "captures")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
DB_PATH = os.path.join(BASE_DIR, "traffic_radar_system.db")
CONFIG_JSON_PATH = os.path.join(BASE_DIR, "config.json")
BACKGROUND_JSON_PATH = os.path.join(BASE_DIR, "background.json")

os.makedirs(CAPTURES_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Các hằng số mặc định ban đầu
RADAR_DEFAULT_BAUDRATE = 256000
RADAR_MIN_RANGE_M = 0.5
RADAR_MAX_RANGE_M = 6.0
RADAR_FOV_DEG = 120

CAMERA_INDEX = 1
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30

WARN_DISTANCE_M = 3.5
WARN_TTC_SEC = 3.0
DANGER_DISTANCE_M = 1.8
DANGER_TTC_SEC = 1.8

def format_speed_status(speed_kmh: float, closing_speed_mps: Optional[float] = None) -> str:
    """
    Quy ước người dùng (Point 4):
    - speed_kmh ÂM: tiến lại gần, DƯƠNG: ra xa
    - closing_speed_mps DƯƠNG: tiến lại gần, ÂM: ra xa
    - |closing_speed_mps| < 0.3 m/s (hoặc đứng yên): 'Đứng yên'
    - Nếu đang tiến lại gần: 'Tiến lại gần X km/h'
    - Nếu đang ra xa: 'Ra xa X km/h'
    với X là trị tuyệt đối của tốc độ (km/h).
    """
    mag_kmh = abs(float(speed_kmh)) if speed_kmh is not None else 0.0
    c_mps = float(closing_speed_mps) if closing_speed_mps is not None else None

    if c_mps is not None:
        if abs(c_mps) < 0.3 or mag_kmh < 0.5:
            return "Đứng yên"
        elif c_mps >= 0.3:
            return f"Tiến lại gần {mag_kmh:.1f} km/h"
        else:
            return f"Ra xa {mag_kmh:.1f} km/h"
    else:
        if mag_kmh < 0.5:
            return "Đứng yên"
        elif float(speed_kmh) < 0:
            return f"Tiến lại gần {mag_kmh:.1f} km/h"
        else:
            return f"Ra xa {mag_kmh:.1f} km/h"

def format_operator_speed(speed_kmh: float, closing_speed_mps: Optional[float] = None) -> str:
    """
    Quy ước hiển thị cho Người vận hành (Operator):
    - 'Đứng yên'
    - 'Đang lại gần X km/h'
    - 'Đang ra xa X km/h'
    """
    raw = format_speed_status(speed_kmh, closing_speed_mps)
    if raw.startswith("Tiến lại gần"):
        return raw.replace("Tiến lại gần", "Đang lại gần")
    elif raw.startswith("Ra xa"):
        return raw.replace("Ra xa", "Đang ra xa")
    return raw

DEFAULT_OFFSET_X = 0.0
DEFAULT_OFFSET_Y = 0.0
UI_REFRESH_RATE_MS = 33

DEFAULT_CONFIG = {
    # Kết nối phần cứng
    "com_port": "COM5",
    "baudrate": RADAR_DEFAULT_BAUDRATE,
    "camera_source": CAMERA_INDEX,
    "flip_camera_horizontal": False,
    "invert_radar_x": True,
    "max_reconnect_attempts": 5,
    "reconnect_interval_sec": 1.5,

    # Lọc phạm vi Radar (Mục 1.2) - Giới hạn vật lý 20cm (0.2m)
    "min_range_m": RADAR_MIN_RANGE_M,
    "max_range_m": RADAR_MAX_RANGE_M,
    "max_angle_deg": 60.0,

    # Bộ theo dõi mục tiêu Tracker & TTC (Mục 1.3)
    "association_gate_m": 0.5,
    "confirm_frames": 3,
    "max_missed_frames": 5,
    "smoothing_alpha": 0.6,
    "min_closing_speed_mps": 0.3,
    "radar_sample_rate_hz": 10.0,

    # Hiệu chuẩn nền (Mục 1.4)
    "background_grid_m": 0.10,
    "background_occupancy_ratio": 0.70,
    "background_tolerance_m": 0.15,
    "background_calib_duration_sec": 5.0,

    # Ngưỡng cảnh báo (Giai đoạn 2)
    "warn_distance_m": WARN_DISTANCE_M,
    "warn_ttc_sec": WARN_TTC_SEC,
    "danger_distance_m": DANGER_DISTANCE_M,
    "danger_ttc_sec": DANGER_TTC_SEC,
    "hysteresis_sec": 1.0,
    "near_hold_range_m": 1.2,
    "near_hold_sec": 2.0,

    # Hiệu chuẩn quang học (Giai đoạn 4)
    "camera_hfov_deg": 65.0,
    "offset_x_m": DEFAULT_OFFSET_X,
    "offset_y_m": DEFAULT_OFFSET_Y,

    # Nhận diện hình ảnh YOLOv8 (Giai đoạn 3)
    "detector_model_path": "models/yolov8n.onnx",
    "detector_conf_threshold": 0.5,
    "detector_iou_threshold": 0.45,

    # Bảo mật và Người dùng (Giai đoạn 7)
    "auth_pbkdf2_iterations": 100000,
    "max_failed_logins": 5,
    "lockout_duration_sec": 300,

    # Cơ sở dữ liệu MySQL (Mặc định bắt buộc theo đặc tả đồ án)
    "db_backend": "mysql",
    "mysql_host": "127.0.0.1",
    "mysql_port": 3306,
    "mysql_user": "root",
    "mysql_password": "",
    "mysql_database": "traffic_radar_db",

    # Chế độ gỡ lỗi
    "debug_radar_speed": False,
    "debug_radar_mode": False
}


def _import_legacy_sqlite_settings(db_path: str) -> dict:
    """Đọc một lần các thiết lập cũ từ bảng system_settings trong SQLite (nếu tồn tại)"""
    imported = {}
    if not os.path.exists(db_path):
        return imported
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_settings'")
            if not cursor.fetchone():
                return imported
            cursor.execute("SELECT key, value FROM system_settings")
            rows = dict(cursor.fetchall())
            float_keys = [
                "warn_distance_m", "warn_ttc_sec",
                "danger_distance_m", "danger_ttc_sec",
                "offset_x_m", "offset_y_m"
            ]
            for fk in float_keys:
                if fk in rows:
                    try:
                        imported[fk] = float(rows[fk])
                    except ValueError:
                        pass
            if "default_com" in rows and rows["default_com"]:
                imported["com_port"] = str(rows["default_com"])
            if "default_baud" in rows:
                try:
                    imported["baudrate"] = int(rows["default_baud"])
                except ValueError:
                    pass
    except Exception:
        pass
    return imported


class ConfigManager:
    """Quản lý đọc/ghi cấu hình từ tệp config.json"""

    def __init__(self, config_path: str = CONFIG_JSON_PATH, db_path: str = DB_PATH, legacy_db_path: str = None):
        self.config_path = config_path
        self.db_path = legacy_db_path if legacy_db_path is not None else db_path
        self.data = deepcopy(DEFAULT_CONFIG)
        self.load()

    def load(self) -> dict:
        """Nạp cấu hình từ config.json; nếu chưa có thì khởi tạo một lần từ config.py + SQLite"""
        if not os.path.exists(self.config_path):
            self.data = deepcopy(DEFAULT_CONFIG)
            legacy = _import_legacy_sqlite_settings(self.db_path)
            self.data.update(legacy)
            self.save()
        else:
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                merged = deepcopy(DEFAULT_CONFIG)
                if isinstance(loaded, dict):
                    merged.update(loaded)
                self.data = merged
            except Exception:
                self.data = deepcopy(DEFAULT_CONFIG)
        self._sync_module_globals()
        return self.data

    def save(self, new_values: dict = None) -> None:
        """Lưu cấu hình hiện tại xuống config.json"""
        if new_values:
            self.data.update(new_values)
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print("Lỗi ghi config.json:", e)
        self._sync_module_globals()

    def update(self, new_values: dict) -> None:
        """Cập nhật một phần cấu hình và lưu xuống config.json"""
        self.save(new_values)

    def reset_defaults(self) -> dict:
        """Khôi phục toàn bộ cấu hình về mặc định chuẩn"""
        self.data = deepcopy(DEFAULT_CONFIG)
        self.save()
        return self.data

    def get(self, key: str, default=None):
        return self.data.get(key, DEFAULT_CONFIG.get(key, default))

    def _sync_module_globals(self):
        """Cập nhật các hằng số module để tương thích ngược với các file hiện có"""
        global RADAR_MIN_RANGE_M, RADAR_MAX_RANGE_M
        global WARN_DISTANCE_M, WARN_TTC_SEC, DANGER_DISTANCE_M, DANGER_TTC_SEC
        global DEFAULT_OFFSET_X, DEFAULT_OFFSET_Y
        RADAR_MIN_RANGE_M = float(self.data.get("min_range_m", 0.5))
        RADAR_MAX_RANGE_M = float(self.data.get("max_range_m", 6.0))
        WARN_DISTANCE_M = float(self.data.get("warn_distance_m", 3.5))
        WARN_TTC_SEC = float(self.data.get("warn_ttc_sec", 3.0))
        DANGER_DISTANCE_M = float(self.data.get("danger_distance_m", 1.8))
        DANGER_TTC_SEC = float(self.data.get("danger_ttc_sec", 1.8))
        DEFAULT_OFFSET_X = float(self.data.get("offset_x_m", 0.0))
        DEFAULT_OFFSET_Y = float(self.data.get("offset_y_m", 0.0))


# Khởi tạo singleton cấu hình toàn cục
config_manager = ConfigManager()


def get_config() -> dict:
    return config_manager.data


def save_config(updates: dict = None) -> None:
    config_manager.save(updates)
