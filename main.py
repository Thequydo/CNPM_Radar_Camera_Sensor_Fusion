# -*- coding: utf-8 -*-
"""
HỆ THỐNG PHẦN MỀM GIÁM SÁT GIAO THÔNG VÀ CẢNH BÁO VA CHẠM THỜI GIAN THỰC (RADAR & CAMERA)
Smart Traffic & Collision Warning Desktop Application using Radar and Camera Fusion
Tuân thủ toàn diện Bản Đặc tả Yêu cầu Phần mềm (SRS - IEEE 830)
Bộ môn Công nghệ Phần mềm - Ngành Kỹ thuật Máy tính (Khoa Điện tử & AI - ĐH Bách Khoa ĐHĐN)
Kiến trúc QStackedWidget Chống Crash Tuyệt đối (Crash-Proof Architecture)
"""

import sys
import os
import csv
import time
import math
import traceback
import cv2
import numpy as np

# Bắt buộc cho PyInstaller trên Windows chống nhân bản tiến trình đệ quy
import multiprocessing
import ctypes
from ctypes import byref, c_int, sizeof

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QComboBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QMessageBox, QFrame, QGroupBox, QTabWidget, QSplitter,
    QLineEdit, QDoubleSpinBox, QStackedWidget, QDateEdit,
    QSlider, QProgressBar, QDialog, QSizePolicy, QMenu, QScrollArea,
    QGraphicsDropShadowEffect
)
from PyQt6.QtGui import (
    QImage, QPixmap, QFont, QColor, QIcon, QPainter, QPen, QAction,
    QBrush, QRadialGradient, QLinearGradient, QPolygonF
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPointF, QRectF, QDate, QEvent

from config import (
    CAPTURES_DIR, LOGS_DIR, DANGER_DISTANCE_M, WARN_DISTANCE_M, 
    DANGER_TTC_SEC, WARN_TTC_SEC, RADAR_DEFAULT_BAUDRATE,
    DEFAULT_OFFSET_X, DEFAULT_OFFSET_Y, config_manager
)
from radar_parser import RadarWorker, RadarTarget, get_available_ports
from camera_worker import CameraWorker, get_available_cameras
from simulation_player import SimulationPlayer
from detector_worker import DetectorWorker, Detection
from fusion_engine import FusionEngine, FusedObject, draw_fused_annotations
from radar_canvas import RadarCanvas
from alert_engine import AlertStateMachine, AlertSeverity, IncidentAggregator
from sound_worker import SoundWorker
from async_logger import AsyncLogWorker
import database
from login_dialog import (
    LoginDialog, FirstRunSetupDialog, UserManagementDialog, ChangePasswordDialog, RegisterDialog
)
from snapshot_dialog import SnapshotViewerDialog

# Bắt lỗi toàn cục ghi vào file log chống treo ứng dụng
def global_excepthook(exctype, value, tb):
    log_file = os.path.join(LOGS_DIR, "app.log")
    debug_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crash_debug.log")
    for fpath in (log_file, debug_file):
        try:
            with open(fpath, "a", encoding="utf-8") as f:
                f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] NGOẠI LỆ CHƯA XỬ LÝ:\n")
                traceback.print_exception(exctype, value, tb, file=f)
        except Exception:
            pass
    print("Ngoại lệ bắt được:", value)

sys.excepthook = global_excepthook

# Phong cách giao diện Dark Mode Công nghiệp chuẩn HMI Kỹ thuật (Grafana / Foxglove)
DARK_STYLE = """
* {
    font-family: 'Segoe UI', Arial, sans-serif;
    outline: none;
}
QMainWindow, QDialog, QMessageBox {
    background-color: #161A1F;
    color: #F1F5F9;
}
QWidget {
    color: #F1F5F9;
    font-size: 12px;
}

/* --- TABS --- */
QTabWidget::pane {
    border: 1px solid #2A313A;
    background-color: #161A1F;
    border-radius: 4px;
}
QTabBar::tab {
    background: #1E2329;
    color: #94A3B8;
    padding: 8px 20px;
    font-weight: 600;
    font-size: 12px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 4px;
    border: 1px solid #2A313A;
    border-bottom: none;
}
QTabBar::tab:selected {
    background: #2B6CB0;
    color: #FFFFFF;
    font-weight: 700;
}
QTabBar::tab:hover:!selected {
    background: #2A313A;
    color: #FFFFFF;
}

/* --- GROUP BOX (PANELS) --- */
QGroupBox {
    color: #F1F5F9;
    font-weight: 600;
    font-size: 12px;
    border: 1px solid #2A313A;
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 14px;
    background-color: #1E2329;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    background-color: #1E2329;
    color: #CBD5E1;
}

/* --- INPUTS & CONTROLS --- */
QComboBox, QLineEdit, QDoubleSpinBox {
    background-color: #161A1F;
    color: #FFFFFF;
    border: 1px solid #2A313A;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 12px;
    font-weight: 500;
}
QComboBox:focus, QLineEdit:focus, QDoubleSpinBox:focus {
    border: 1px solid #2B6CB0;
    background-color: #161A1F;
}
QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #1E2329;
    color: #FFFFFF;
    selection-background-color: #2B6CB0;
    border: 1px solid #2A313A;
    padding: 4px;
}
QCheckBox {
    color: #F1F5F9;
    font-size: 12px;
    font-weight: 500;
    spacing: 8px;
}

/* --- TABLE --- */
QTableWidget {
    background-color: #1E2329;
    alternate-background-color: #161A1F;
    color: #F1F5F9;
    gridline-color: #2A313A;
    border: 1px solid #2A313A;
    border-radius: 4px;
    font-size: 12px;
    selection-background-color: #2B6CB0;
}
QHeaderView::section {
    background-color: #161A1F;
    color: #94A3B8;
    font-weight: 600;
    font-size: 12px;
    padding: 6px;
    border: none;
    border-bottom: 1px solid #2A313A;
}

/* --- BUTTONS --- */
QPushButton {
    background-color: #1E2329;
    color: #F1F5F9;
    border: 1px solid #2A313A;
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #2A313A;
    border: 1px solid #3F4753;
}
QPushButton:pressed {
    background-color: #161A1F;
}
QPushButton#btnSuccess {
    background-color: #2ECC71;
    color: #161A1F;
    font-weight: 700;
    border: none;
}
QPushButton#btnSuccess:hover {
    background-color: #27AE60;
}
QPushButton#btnSuccess:disabled {
    background-color: #1B3B2B;
    color: #64748B;
}
QPushButton#btnDanger {
    background-color: #E74C3C;
    color: #FFFFFF;
    font-weight: 700;
    border: none;
}
QPushButton#btnDanger:hover {
    background-color: #C0392B;
}
QPushButton#btnDanger:disabled {
    background-color: #3B1E1E;
    color: #64748B;
}
QComboBox:disabled, QPushButton:disabled {
    color: #64748B;
}
QPushButton#btnLoginAction {
    background-color: #2B6CB0;
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 700;
    border-radius: 4px;
    padding: 10px;
    border: none;
}
QPushButton#btnLoginAction:hover {
    background-color: #3182CE;
}

/* --- DIALOGS & POPUPS --- */
QDialog {
    background-color: #161A1F;
    color: #F1F5F9;
}
QMessageBox {
    background-color: #1E2329;
    border: 1px solid #2A313A;
    border-radius: 4px;
}
QMessageBox QLabel {
    color: #F1F5F9;
    font-size: 12px;
    font-weight: 500;
    min-width: 300px;
    padding: 8px;
}
QMessageBox QPushButton {
    background-color: #161A1F;
    color: #F1F5F9;
    border: 1px solid #2A313A;
    border-radius: 4px;
    padding: 6px 18px;
    font-size: 12px;
    font-weight: 600;
    min-width: 80px;
    min-height: 26px;
}
QMessageBox QPushButton:hover {
    background-color: #2A313A;
}
"""

def show_confirm_dialog(parent, title, message, yes_text="Đăng xuất", no_text="Hủy bỏ", is_danger=True):
    """Hộp thoại xác nhận chuẩn Dark Mode với phông chữ độ tương phản cao, rõ ràng 100%"""
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(f"<div style='font-family: \"Segoe UI\"; font-size: 14px; color: #F1F5F9; line-height: 1.5;'>{message}</div>")
    msg_box.setIcon(QMessageBox.Icon.Question)
    btn_yes = msg_box.addButton(yes_text, QMessageBox.ButtonRole.YesRole)
    btn_no = msg_box.addButton(no_text, QMessageBox.ButtonRole.NoRole)
    
    if is_danger:
        btn_yes.setStyleSheet("background-color: #E74C3C; color: #FFFFFF; font-weight: 600; font-size: 12px; padding: 6px 18px; border-radius: 4px; border: none;")
    else:
        btn_yes.setStyleSheet("background-color: #2B6CB0; color: #FFFFFF; font-weight: 600; font-size: 12px; padding: 6px 18px; border-radius: 4px; border: none;")
    btn_no.setStyleSheet("background-color: #1E2329; color: #F1F5F9; font-weight: 600; font-size: 12px; padding: 6px 18px; border-radius: 4px; border: 1px solid #2A313A;")
    
    msg_box.exec()
    return msg_box.clickedButton() == btn_yes

def show_info_dialog(parent, title, message):
    """Hộp thoại thông báo thông tin chuẩn Dark Mode siêu nét"""
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(f"<div style='font-family: \"Segoe UI\"; font-size: 14px; color: #F1F5F9; line-height: 1.5;'>{message}</div>")
    msg_box.setIcon(QMessageBox.Icon.Information)
    btn = msg_box.addButton("Đã hiểu", QMessageBox.ButtonRole.AcceptRole)
    btn.setStyleSheet("background-color: #2ECC71; color: #161A1F; font-weight: 700; font-size: 12px; padding: 6px 20px; border-radius: 4px; border: none;")
    msg_box.exec()

def apply_dark_titlebar(window):
    """Kích hoạt thanh tiêu đề Dark Mode nguyên bản của Windows 10/11 qua DWM API (Yêu cầu 4)"""
    try:
        hwnd = int(window.winId())
        val = c_int(1)
        # Thuộc tính 20: DWMWA_USE_IMMERSIVE_DARK_MODE (Windows 11 / Windows 10 build 19041+)
        hr = ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, byref(val), sizeof(val))
        if hr != 0:
            # Fallback thuộc tính 19 cho Windows 10 các build cũ hơn
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, byref(val), sizeof(val))
    except Exception:
        pass

def ensure_window_resizable(window):
    """
    Đảm bảo cửa sổ có đầy đủ quyền phóng to (Maximize / Fullscreen),
    thu nhỏ (Minimize) và viền kéo giãn kích thước (ThickFrame / Resize) trên Windows.
    Khắc phục triệt để lỗi Qt vô hiệu hóa nút Maximize khi dùng QStackedWidget hoặc setFixedSize.
    """
    try:
        window.setWindowFlags(
            window.windowFlags()
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowMinimizeButtonHint
        )
        if sys.platform == "win32":
            hwnd = int(window.winId())
            GWL_STYLE = -16
            WS_MAXIMIZEBOX = 0x00010000
            WS_THICKFRAME = 0x00040000
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style | WS_MAXIMIZEBOX | WS_THICKFRAME)
            SWP_FLAGS = 0x0002 | 0x0001 | 0x0004 | 0x0020  # NOMOVE | NOSIZE | NOZORDER | FRAMECHANGED
            ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, SWP_FLAGS)
    except Exception:
        pass

def create_system_logo_icon(size=76):
    """
    Logo nhận diện thương hiệu của hệ thống: Biểu tượng Radar phát sóng thông minh
    (Được chuyển thể chính xác từ logo Radar người dùng cung cấp)
    """
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    logo_file = os.path.join(base_dir, "radar_logo_cyan.png")
    if os.path.exists(logo_file):
        pix = QPixmap(logo_file)
        if not pix.isNull():
            return pix.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    center_x = size / 2.0
    
    # 1. Vẽ hình Khiên an toàn (Security Shield)
    shield = QPolygonF([
        QPointF(center_x, 3),
        QPointF(size - 6, 8),
        QPointF(size - 6, size * 0.55),
        QPointF(center_x, size - 3),
        QPointF(6, size * 0.55),
        QPointF(6, 8),
    ])

    grad = QLinearGradient(0, 0, 0, size)
    grad.setColorAt(0.0, QColor(30, 41, 59))
    grad.setColorAt(1.0, QColor(15, 23, 42))

    p.setPen(QPen(QColor(56, 189, 248), 2.0))
    p.setBrush(grad)
    p.drawPolygon(shield)

    # 2. Sóng Radar phát xạ bên trong khiên (3 cung tròn hướng lên)
    p.setBrush(Qt.BrushStyle.NoBrush)
    
    # Cung 1
    p.setPen(QPen(QColor(56, 189, 248, 120), 1.5))
    p.drawArc(QRectF(center_x - 12, size * 0.42, 24, 24), 35 * 16, 110 * 16)
    
    # Cung 2
    p.setPen(QPen(QColor(56, 189, 248, 200), 1.8))
    p.drawArc(QRectF(center_x - 18, size * 0.30, 36, 36), 35 * 16, 110 * 16)

    # Cung 3
    p.setPen(QPen(QColor(56, 189, 248, 255), 2.0))
    p.drawArc(QRectF(center_x - 24, size * 0.18, 48, 48), 35 * 16, 110 * 16)

    # 3. Tâm phát sóng (Cảm biến Radar & Camera)
    p.setPen(QPen(QColor(15, 23, 42), 1.5))
    p.setBrush(QColor(56, 189, 248))
    p.drawEllipse(QPointF(center_x, size * 0.60), 4.5, 4.5)

    p.end()
    return pix

def format_short_datetime(dt_str: str) -> str:
    """Định dạng chuỗi ngày giờ gọn cho bảng: DD/MM HH:MM:SS"""
    if not dt_str:
        return "--"
    parts = str(dt_str).strip().split(" ")
    if len(parts) == 2:
        d_parts = parts[0].split("-")
        if len(d_parts) == 3:
            return f"{d_parts[2]}/{d_parts[1]} {parts[1]}"
    return str(dt_str)

def create_radar_vector_icon(size=72):
    """Tương thích ngược cho các header và thanh tiêu đề"""
    return create_system_logo_icon(size)

def create_user_icon(size=18):
    """Icon người dùng tinh tế đặt ở đầu ô nhập Tên đăng nhập"""
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(148, 163, 184))
    p.drawEllipse(QPointF(size / 2.0, 5.5), 3.2, 3.2)
    p.drawChord(QRectF(2, 8.5, size - 4, 10), 0, 180 * 16)
    p.end()
    return QIcon(pix)

def create_lock_icon(size=18):
    """Icon ổ khóa bảo mật đặt ở đầu ô nhập Mật khẩu"""
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(148, 163, 184), 1.6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawArc(QRectF(5, 2, 8, 8), 0, 180 * 16)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(148, 163, 184))
    p.drawRoundedRect(QRectF(3.5, 7.5, 11, 8.5), 1.5, 1.5)
    p.setBrush(QColor(15, 23, 42))
    p.drawEllipse(QPointF(size / 2.0, 11), 1.2, 1.2)
    p.end()
    return QIcon(pix)

def create_eye_icon(is_hidden: bool):
    """
    Tạo icon mắt xem/ẩn mật khẩu:
    - Khi đang ẩn (mật khẩu che): Mắt mở với đồng tử xanh cyan, tooltip 'Hiển thị mật khẩu'
    - Khi đang hiện (mật khẩu rõ): Mắt có đường gạch chéo đỏ nhẹ, tooltip 'Ẩn mật khẩu'
    """
    pix = QPixmap(22, 22)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    pen = QPen(QColor(148, 163, 184), 1.5)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    
    p.drawArc(2, 5, 18, 12, 35 * 16, 110 * 16)
    p.drawArc(2, 5, 18, 12, 215 * 16, 110 * 16)
    
    if is_hidden:
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(56, 189, 248))
        p.drawEllipse(QPointF(11, 11), 3.2, 3.2)
    else:
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(148, 163, 184))
        p.drawEllipse(QPointF(11, 11), 2.5, 2.5)
        pen_slash = QPen(QColor(239, 68, 68), 1.8)
        pen_slash.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen_slash)
        p.drawLine(4, 18, 18, 4)
        
    p.end()
    return QIcon(pix)

def ensure_checkmark_icon():
    """Đảm bảo file checkmark.png luôn tồn tại để hiển thị dấu tick checkbox chuẩn"""
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    target_path = os.path.join(base_dir, "checkmark.png")
    if not os.path.exists(target_path):
        try:
            size = 16
            pix = QPixmap(size, size)
            pix.fill(Qt.GlobalColor.transparent)
            p = QPainter(pix)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            pen = QPen(QColor(255, 255, 255), 2.2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            p.setPen(pen)
            p.drawLine(QPointF(3.8, 8.2), QPointF(6.8, 11.5))
            p.drawLine(QPointF(6.8, 11.5), QPointF(12.2, 4.8))
            p.end()
            pix.save(target_path)
        except Exception:
            pass
    return target_path.replace("\\", "/")

class LoginBackgroundWidget(QWidget):
    """Nền phong cách giám sát với lưới họa tiết mờ và vòng tròn radar tạo chiều sâu"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #0A0F1D;")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(10, 15, 29))

        # Lưới kỹ thuật rất mờ
        pen_grid = QPen(QColor(30, 41, 59, 45), 1.0)
        p.setPen(pen_grid)
        step = 40
        w = self.width()
        h = self.height()
        for x in range(0, w, step):
            p.drawLine(x, 0, x, h)
        for y in range(0, h, step):
            p.drawLine(0, y, w, y)

        # Vòng tròn radar rất mờ tạo chiều sâu
        cx = w / 2.0
        cy = h / 2.0
        pen_radar = QPen(QColor(56, 189, 248, 20), 1.0, Qt.PenStyle.DashLine)
        p.setPen(pen_radar)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for r in (120, 240, 360, 480):
            p.drawEllipse(QPointF(cx, cy), r, r)

        p.end()
        super().paintEvent(event)


class TargetDetailDialog(QDialog):
    """Cửa sổ thông tin chi tiết mục tiêu khi người dùng nhấp chọn (Giai đoạn 8)"""
    def __init__(self, target, det_name="Chưa xác định", parent=None):
        super().__init__(parent)
        tid = getattr(target, 'target_id', getattr(target, 'id', 1))
        self.setWindowTitle(f"Chi tiết đối tượng #{tid}")
        self.setFixedSize(380, 310)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        apply_dark_titlebar(self)
        self.setStyleSheet("""
            QDialog {
                background-color: #161A1F;
                color: #F1F5F9;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #CBD5E1;
                font-size: 12px;
            }
            QPushButton {
                background-color: #1E2329;
                color: #FFFFFF;
                border: 1px solid #2A313A;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2A313A;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        title = QLabel(f"THÔNG SỐ ĐỐI TƯỢNG #{tid}")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(8)

        grid.addWidget(QLabel("Loại đối tượng:"), 0, 0)
        lbl_type = QLabel(det_name)
        lbl_type.setStyleSheet("color: #2ECC71; font-weight: 700;")
        grid.addWidget(lbl_type, 0, 1)

        grid.addWidget(QLabel("Khoảng cách (d):"), 1, 0)
        d_val = getattr(target, 'distance_m', getattr(target, 'distance', 0.0))
        grid.addWidget(QLabel(f"<b>{d_val:.2f} m</b>"), 1, 1)

        grid.addWidget(QLabel("Tốc độ:"), 2, 0)
        from config import format_operator_speed
        v_status = format_operator_speed(getattr(target, 'speed_kmh', 0.0), getattr(target, 'closing_speed_mps', 0.0))
        grid.addWidget(QLabel(f"<b>{v_status}</b>"), 2, 1)

        grid.addWidget(QLabel("Tốc độ tiếp cận:"), 3, 0)
        v_close = getattr(target, 'closing_speed_mps', 0.0) or 0.0
        grid.addWidget(QLabel(f"<b>{v_close:+.2f} m/s</b>"), 3, 1)

        grid.addWidget(QLabel("Góc lệch phương vị:"), 4, 0)
        ang_val = getattr(target, 'angle_deg', 0.0)
        grid.addWidget(QLabel(f"<b>{ang_val:+.1f}°</b>"), 4, 1)

        grid.addWidget(QLabel("Thời gian va chạm (TTC):"), 5, 0)
        ttc = getattr(target, 'ttc_sec', getattr(target, 'ttc_s', None))
        ttc_str = f"<b style='color:#E74C3C;'>{ttc:.1f} s</b>" if (ttc is not None and ttc > 0.0) else "<i>Không lại gần</i>"
        grid.addWidget(QLabel(ttc_str), 5, 1)

        x_val = getattr(target, 'x_m', getattr(target, 'x', 0.0))
        y_val = getattr(target, 'y_m', getattr(target, 'y', 0.0))
        grid.addWidget(QLabel("Tọa độ không gian:"), 6, 0)
        grid.addWidget(QLabel(f"<b>X = {x_val:+.2f} m &nbsp;|&nbsp; Y = {y_val:.2f} m</b>"), 6, 1)

        layout.addLayout(grid)
        layout.addSpacing(6)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)


class MainWindow(QMainWindow):
    """Cửa sổ Chính Tích hợp Quản lý Phiên & Bàn điều khiển Giám sát Đa cảm biến"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hệ thống Giám sát Giao thông & Cảnh báo Va chạm")
        self.setStyleSheet(DARK_STYLE)

        # Nạp icon chương trình
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, "radar_icon.ico")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "radar_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Dữ liệu nội bộ
        self.user_session = None
        self.current_targets = []
        self.smoothed_targets = []
        self.current_frame = None
        self.current_detections = []
        self.current_fused_objects = []
        self.selected_target = None
        self.selected_target_id = None
        self.last_snapshot_time = 0
        self.fps_counter = 0
        self.last_fps_time = time.time()
        self.current_fps = 30.0
        self._last_frame_render_t = 0.0
        self._last_telemetry_render_t = 0.0
        self._last_debug_table_t = 0.0
        self._last_telemetry_sev = None
        self._last_telemetry_tid = None
        self._telemetry_ema = {}
        self._prev_flow_gray = None
        self._detections_fresh = False

        # Động cơ Cảnh báo, Gom sự cố & Luồng âm thanh / ghi nền (Giai đoạn 2)
        self.alert_state_machine = AlertStateMachine()
        self.incident_aggregator = IncidentAggregator(cooldown_sec=float(config_manager.get("incident_cooldown_sec", 2.0)))
        self.sound_worker = SoundWorker(is_muted=not bool(config_manager.get("audio_alert_enabled", True)))
        self.async_logger = AsyncLogWorker(self)
        self.async_logger.incident_saved.connect(self._on_new_incident_saved)

        # Bộ đếm nhấp nháy viền cảnh báo (Đỏ cho DANGER, Vàng cho WARN)
        self.flash_timer = QTimer(self)
        self.flash_state = False
        self.current_flash_color = "#E74C3C"
        self.flash_timer.timeout.connect(self._toggle_danger_flash)

        # Bộ đếm cập nhật tiến trình hiệu chuẩn nền 5 giây
        self.calib_timer = QTimer(self)
        self.calib_timer.timeout.connect(self._on_calib_tick)

        # Khởi tạo CSDL & nạp cấu hình
        try:
            database.init_db()
        except Exception as e:
            print("Lỗi CSDL:", e)
        self._load_dynamic_settings()

        # Kiến trúc QStackedWidget: Chuyển trang mượt mà không bao giờ bị đóng tiến trình
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Trang 0: Đăng nhập Xác thực (Login Page - FR-01, US-01) - Giao diện đơn khối liền mạch
        self.page_login = QWidget()
        self.page_login.setStyleSheet("background-color: #141C2B;")
        self._build_login_page(self.page_login)
        self.stack.addWidget(self.page_login)

        # Trang 1: Bàn điều khiển Giám sát Thương mại (Dashboard Page)
        self.page_dashboard = QWidget()
        self._build_dashboard_page(self.page_dashboard)
        self.stack.addWidget(self.page_dashboard)

        # Trang 2: Đăng ký tài khoản mới (Register Page) - chuyển trang trực tiếp trong cùng cửa sổ
        self.page_register = QWidget()
        self.page_register.setStyleSheet("background-color: #141C2B;")
        self._build_register_page(self.page_register)
        self.stack.addWidget(self.page_register)

        # Khởi động hiển thị màn hình đăng nhập chuẩn kích thước gọn gàng, không bị lồng khối
        self.setMinimumSize(440, 560)
        self.resize(460, 620)
        self.stack.setCurrentIndex(0)
        apply_dark_titlebar(self)
        ensure_window_resizable(self)

        # Khởi tạo luồng xử lý phần cứng
        self._init_workers()

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_titlebar(self)
        ensure_window_resizable(self)
        # Kiểm tra thiết lập lần đầu nếu chưa có tài khoản nào (Giai đoạn 7)
        if not database.has_any_users():
            dlg = FirstRunSetupDialog(self)
            dlg.exec()

    def _load_dynamic_settings(self):
        """Nạp các thông số ngưỡng an toàn và bù lệch cảm biến từ config.json (nguồn cấu hình duy nhất)"""
        cfg = config_manager.load()
        self.warn_dist = float(cfg.get("warn_distance_m", WARN_DISTANCE_M))
        self.warn_ttc = float(cfg.get("warn_ttc_sec", WARN_TTC_SEC))
        self.danger_dist = float(cfg.get("danger_distance_m", DANGER_DISTANCE_M))
        self.danger_ttc = float(cfg.get("danger_ttc_sec", DANGER_TTC_SEC))
        self.offset_x = float(cfg.get("offset_x_m", DEFAULT_OFFSET_X))
        self.offset_y = float(cfg.get("offset_y_m", DEFAULT_OFFSET_Y))

    # ================= 1. TRANG ĐĂNG NHẬP (LOGIN PAGE) =================
    def _build_login_page(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(44, 28, 44, 24)
        layout.setSpacing(10)

        layout.addStretch()

        # 1. Logo vector kỹ thuật cố định của hệ thống (Radar + Cảm biến kết hợp, không spinner)
        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("background: transparent;")
        logo.setPixmap(create_system_logo_icon(74))
        layout.addWidget(logo)

        # 2. Typography tiêu đề HMI phân cấp rõ ràng
        lbl_title = QLabel("Hệ thống giám sát giao thông\nvà cảnh báo va chạm")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #FFFFFF; line-height: 1.25; margin-top: 4px; background: transparent;")
        layout.addWidget(lbl_title)

        lbl_sub = QLabel("Đăng nhập tài khoản của bạn")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setFont(QFont("Segoe UI", 11))
        lbl_sub.setStyleSheet("color: #94A3B8; margin-top: 4px; margin-bottom: 12px; background: transparent;")
        layout.addWidget(lbl_sub)

        # Kiểu dáng ô nhập đồng bộ: viền hover/focus mượt mà
        field_style = """
            QLineEdit {
                background-color: #0F172A;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #F8FAFC;
                font-size: 13px;
                padding: 8px 10px;
            }
            QLineEdit:hover {
                border: 1px solid #475569;
            }
            QLineEdit:focus {
                border: 1px solid #2563EB;
                background-color: #0B1120;
            }
        """

        # 3. Ô Tên đăng nhập (Bỏ dấu hai chấm, placeholder, icon người dùng)
        lbl_user_title = QLabel("Tên đăng nhập")
        lbl_user_title.setStyleSheet("color: #CBD5E1; font-size: 12px; font-weight: 600; margin-top: 2px; background: transparent;")
        layout.addWidget(lbl_user_title)

        self.login_user = QLineEdit()
        self.login_user.setStyleSheet(field_style)
        self.login_user.setPlaceholderText("Nhập tên đăng nhập")
        self.login_user.addAction(create_user_icon(18), QLineEdit.ActionPosition.LeadingPosition)

        saved_user = config_manager.get("remembered_username", "")
        saved_pwd = config_manager.get("remembered_password", "")
        remember_checked = bool(config_manager.get("remember_login", True))

        if remember_checked and saved_user:
            self.login_user.setText(saved_user)
        elif not saved_user:
            self.login_user.setText("admin")

        self.login_user.returnPressed.connect(self._do_login)
        layout.addWidget(self.login_user)

        # 4. Ô Mật khẩu (Bỏ dấu hai chấm, placeholder, icon ổ khóa, icon mắt đổi trạng thái)
        lbl_pwd_title = QLabel("Mật khẩu")
        lbl_pwd_title.setStyleSheet("color: #CBD5E1; font-size: 12px; font-weight: 600; margin-top: 6px; background: transparent;")
        layout.addWidget(lbl_pwd_title)

        self.login_pwd = QLineEdit()
        self.login_pwd.setStyleSheet(field_style)
        self.login_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_pwd.setPlaceholderText("Nhập mật khẩu")

        if remember_checked and saved_user:
            self.login_pwd.setText(saved_pwd)
        elif not saved_user:
            self.login_pwd.setText("admin123")

        self.login_pwd.addAction(create_lock_icon(18), QLineEdit.ActionPosition.LeadingPosition)
        self.login_pwd.returnPressed.connect(self._do_login)

        # Lắng nghe thay đổi tên đăng nhập sau khi cả 2 ô đã khởi tạo
        self.login_user.textChanged.connect(self._on_login_user_changed)

        # Action xem/ẩn mật khẩu: Icon đổi theo trạng thái và có Tooltip
        self.action_toggle_pwd = self.login_pwd.addAction(
            create_eye_icon(is_hidden=True),
            QLineEdit.ActionPosition.TrailingPosition
        )
        self.action_toggle_pwd.setToolTip("Hiển thị mật khẩu")
        self.action_toggle_pwd.triggered.connect(self._toggle_pwd_visibility)
        layout.addWidget(self.login_pwd)

        # Cảnh báo khi bật Caps Lock
        self.lbl_caps_warn = QLabel("⚠️ Đang bật Caps Lock")
        self.lbl_caps_warn.setStyleSheet("color: #F59E0B; font-size: 11px; font-weight: 600; padding: 2px 0; background: transparent;")
        self.lbl_caps_warn.hide()
        layout.addWidget(self.lbl_caps_warn)
        self.login_pwd.installEventFilter(self)

        # 5. Tiện ích: Ghi nhớ đăng nhập (với dấu tick chuẩn) + Quên mật khẩu
        util_row = QHBoxLayout()
        util_row.setContentsMargins(0, 4, 0, 6)

        chk_icon_url = ensure_checkmark_icon()

        self.chk_remember = QCheckBox("Ghi nhớ đăng nhập")
        self.chk_remember.setChecked(remember_checked)
        self.chk_remember.toggled.connect(self._on_chk_remember_toggled)
        self.chk_remember.setStyleSheet(f"""
            QCheckBox {{
                color: #94A3B8;
                font-size: 11.5px;
                background: transparent;
            }}
            QCheckBox::indicator {{
                width: 15px;
                height: 15px;
                border: 1px solid #475569;
                border-radius: 4px;
                background-color: #0F172A;
            }}
            QCheckBox::indicator:hover {{
                border-color: #38BDF8;
            }}
            QCheckBox::indicator:checked {{
                background-color: #2563EB;
                border-color: #2563EB;
                image: url('{chk_icon_url}');
            }}
        """)

        lbl_forgot = QLabel("<a href='#forgot' style='color: #60A5FA; text-decoration: none;'>Quên mật khẩu?</a>")
        lbl_forgot.setStyleSheet("font-size: 11.5px; background: transparent;")
        lbl_forgot.setCursor(Qt.CursorShape.PointingHandCursor)
        lbl_forgot.linkActivated.connect(self._on_forgot_password)

        util_row.addWidget(self.chk_remember)
        util_row.addStretch()
        util_row.addWidget(lbl_forgot)
        layout.addLayout(util_row)

        # 6. Thông báo lỗi rõ ràng inline bằng màu đỏ nhẹ, không dùng popup
        self.login_err = QLabel("")
        self.login_err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.login_err.setWordWrap(True)
        self.login_err.setStyleSheet("""
            QLabel {
                background-color: #3F1D1D;
                border: 1px solid #EF4444;
                color: #FCA5A5;
                font-size: 11.5px;
                font-weight: 600;
                border-radius: 6px;
                padding: 7px 10px;
            }
        """)
        self.login_err.hide()
        layout.addWidget(self.login_err)

        # 7. Nút Đăng nhập xanh đồng nhất với màu toàn app, hiệu ứng hover & loading
        self.btn_login = QPushButton("Đăng nhập")
        self.btn_login.setObjectName("btnLoginAction")
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_login.setStyleSheet("""
            QPushButton#btnLoginAction {
                background-color: #2563EB;
                color: #FFFFFF;
                font-size: 13.5px;
                font-weight: bold;
                border-radius: 6px;
                padding: 10px;
                border: none;
                margin-top: 4px;
            }
            QPushButton#btnLoginAction:hover {
                background-color: #1D4ED8;
            }
            QPushButton#btnLoginAction:pressed {
                background-color: #1E40AF;
            }
            QPushButton#btnLoginAction:disabled {
                background-color: #1E3A5F;
                color: #94A3B8;
            }
        """)
        self.btn_login.clicked.connect(self._do_login)
        layout.addWidget(self.btn_login)

        # 8. Mục Đăng ký / Tạo tài khoản mới trực tiếp bên ngoài
        reg_row = QHBoxLayout()
        reg_row.setContentsMargins(0, 8, 0, 0)
        reg_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_no_account = QLabel("Chưa có tài khoản?")
        lbl_no_account.setStyleSheet("color: #94A3B8; font-size: 12px; background: transparent;")

        self.btn_open_register = QPushButton("Tạo tài khoản")
        self.btn_open_register.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_register.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #38BDF8;
                font-size: 12px;
                font-weight: 600;
                border: none;
                padding: 0 4px;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #7DD3FC;
            }
        """)
        self.btn_open_register.clicked.connect(self._switch_to_register)
        reg_row.addWidget(lbl_no_account)
        reg_row.addWidget(self.btn_open_register)
        layout.addLayout(reg_row)

        # Footer phiên bản
        lbl_footer = QLabel("v1.0.0 | DUT - 23KTMT")
        lbl_footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_footer.setStyleSheet("color: #64748B; font-size: 11px; margin-top: 10px; background: transparent;")
        layout.addWidget(lbl_footer)

        layout.addStretch()

    # ================= 1.1 TRANG ĐĂNG KÝ TÀI KHOẢN (REGISTER PAGE) =================
    def _build_register_page(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(44, 20, 44, 20)
        layout.setSpacing(8)

        layout.addStretch()

        # 1. Logo vector cố định của hệ thống
        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("background: transparent;")
        logo.setPixmap(create_system_logo_icon(60))
        layout.addWidget(logo)

        # 2. Typography tiêu đề phân cấp rõ ràng
        lbl_title = QLabel("Hệ thống giám sát giao thông\nvà cảnh báo va chạm")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #FFFFFF; line-height: 1.25; margin-top: 2px; background: transparent;")
        layout.addWidget(lbl_title)

        lbl_sub = QLabel("Đăng ký tài khoản mới")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_sub.setStyleSheet("color: #38BDF8; margin-top: 2px; margin-bottom: 8px; background: transparent;")
        layout.addWidget(lbl_sub)

        # Kiểu dáng ô nhập đồng bộ
        field_style = """
            QLineEdit {
                background-color: #0F172A;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #F8FAFC;
                font-size: 13px;
                padding: 7px 10px;
            }
            QLineEdit:hover {
                border: 1px solid #475569;
            }
            QLineEdit:focus {
                border: 1px solid #2563EB;
                background-color: #0B1120;
            }
        """

        # Tên đăng nhập
        lbl_user_title = QLabel("Tên đăng nhập")
        lbl_user_title.setStyleSheet("color: #CBD5E1; font-size: 12px; font-weight: 600; margin-top: 2px; background: transparent;")
        layout.addWidget(lbl_user_title)

        self.reg_user = QLineEdit()
        self.reg_user.setStyleSheet(field_style)
        self.reg_user.setPlaceholderText("Nhập tên đăng nhập (tối thiểu 3 ký tự)")
        self.reg_user.addAction(create_user_icon(18), QLineEdit.ActionPosition.LeadingPosition)
        layout.addWidget(self.reg_user)

        # Họ và tên
        lbl_name_title = QLabel("Họ và tên")
        lbl_name_title.setStyleSheet("color: #CBD5E1; font-size: 12px; font-weight: 600; margin-top: 4px; background: transparent;")
        layout.addWidget(lbl_name_title)

        self.reg_name = QLineEdit()
        self.reg_name.setStyleSheet(field_style)
        self.reg_name.setPlaceholderText("Nhập họ và tên đầy đủ")
        layout.addWidget(self.reg_name)

        # Mật khẩu
        lbl_pwd_title = QLabel("Mật khẩu")
        lbl_pwd_title.setStyleSheet("color: #CBD5E1; font-size: 12px; font-weight: 600; margin-top: 4px; background: transparent;")
        layout.addWidget(lbl_pwd_title)

        self.reg_pwd = QLineEdit()
        self.reg_pwd.setStyleSheet(field_style)
        self.reg_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_pwd.setPlaceholderText("Nhập mật khẩu (tối thiểu 6 ký tự)")
        self.reg_pwd.addAction(create_lock_icon(18), QLineEdit.ActionPosition.LeadingPosition)
        self.action_toggle_reg_pwd = self.reg_pwd.addAction(
            create_eye_icon(is_hidden=True),
            QLineEdit.ActionPosition.TrailingPosition
        )
        self.action_toggle_reg_pwd.setToolTip("Hiển thị mật khẩu")
        self.action_toggle_reg_pwd.triggered.connect(lambda: self._toggle_line_edit_pwd(self.reg_pwd, self.action_toggle_reg_pwd))
        layout.addWidget(self.reg_pwd)

        # Xác nhận mật khẩu
        lbl_confirm_title = QLabel("Xác nhận mật khẩu")
        lbl_confirm_title.setStyleSheet("color: #CBD5E1; font-size: 12px; font-weight: 600; margin-top: 4px; background: transparent;")
        layout.addWidget(lbl_confirm_title)

        self.reg_confirm = QLineEdit()
        self.reg_confirm.setStyleSheet(field_style)
        self.reg_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_confirm.setPlaceholderText("Nhập lại mật khẩu để xác nhận")
        self.reg_confirm.addAction(create_lock_icon(18), QLineEdit.ActionPosition.LeadingPosition)
        self.action_toggle_reg_confirm = self.reg_confirm.addAction(
            create_eye_icon(is_hidden=True),
            QLineEdit.ActionPosition.TrailingPosition
        )
        self.action_toggle_reg_confirm.setToolTip("Hiển thị mật khẩu")
        self.action_toggle_reg_confirm.triggered.connect(lambda: self._toggle_line_edit_pwd(self.reg_confirm, self.action_toggle_reg_confirm))
        layout.addWidget(self.reg_confirm)

        # Thông báo lỗi
        self.reg_err = QLabel("")
        self.reg_err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.reg_err.setWordWrap(True)
        self.reg_err.setStyleSheet("""
            QLabel {
                background-color: #3F1D1D;
                border: 1px solid #EF4444;
                color: #FCA5A5;
                font-size: 11.5px;
                font-weight: 600;
                border-radius: 6px;
                padding: 6px 10px;
                margin-top: 4px;
            }
        """)
        self.reg_err.hide()
        layout.addWidget(self.reg_err)

        # Nút Đăng ký tài khoản (CSS chống đè chữ, chiều cao rõ ràng)
        self.btn_submit_reg = QPushButton("Đăng ký tài khoản")
        self.btn_submit_reg.setObjectName("btnRegisterSubmit")
        self.btn_submit_reg.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_submit_reg.setStyleSheet("""
            QPushButton#btnRegisterSubmit {
                background-color: #2563EB;
                color: #FFFFFF;
                font-size: 13.5px;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px 12px;
                min-height: 24px;
                border: none;
                margin-top: 6px;
            }
            QPushButton#btnRegisterSubmit:hover {
                background-color: #1D4ED8;
            }
            QPushButton#btnRegisterSubmit:pressed {
                background-color: #1E40AF;
            }
        """)
        self.btn_submit_reg.clicked.connect(self._do_register)
        layout.addWidget(self.btn_submit_reg)

        # Nút Quay lại đăng nhập
        self.btn_back_login = QPushButton("Quay lại đăng nhập")
        self.btn_back_login.setObjectName("btnBackToLogin")
        self.btn_back_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back_login.setStyleSheet("""
            QPushButton#btnBackToLogin {
                background-color: transparent;
                color: #94A3B8;
                font-size: 12px;
                font-weight: 500;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 10px;
                min-height: 20px;
                margin-top: 2px;
            }
            QPushButton#btnBackToLogin:hover {
                color: #F8FAFC;
                border-color: #64748B;
                background-color: #1E293B;
            }
        """)
        self.btn_back_login.clicked.connect(self._switch_to_login)
        layout.addWidget(self.btn_back_login)

        # Enter triggers register
        self.reg_user.returnPressed.connect(self._do_register)
        self.reg_name.returnPressed.connect(self._do_register)
        self.reg_pwd.returnPressed.connect(self._do_register)
        self.reg_confirm.returnPressed.connect(self._do_register)

        layout.addStretch()

    def _switch_to_register(self):
        """Chuyển trực tiếp từ màn hình đăng nhập sang đăng ký tài khoản (không mở cửa sổ mới)"""
        self.reg_user.clear()
        self.reg_name.clear()
        self.reg_pwd.clear()
        self.reg_confirm.clear()
        if hasattr(self, 'reg_err'):
            self.reg_err.hide()
        self.stack.setCurrentWidget(self.page_register)
        self.reg_user.setFocus()

    def _switch_to_login(self):
        """Chuyển trực tiếp từ màn hình đăng ký quay lại đăng nhập"""
        if hasattr(self, 'login_err'):
            self.login_err.hide()
        self.stack.setCurrentWidget(self.page_login)
        self.login_user.setFocus()

    def _toggle_line_edit_pwd(self, line_edit, action):
        """Ẩn/hiện mật khẩu cho ô nhập liệu bất kỳ"""
        if line_edit.echoMode() == QLineEdit.EchoMode.Password:
            line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            action.setIcon(create_eye_icon(is_hidden=False))
            action.setToolTip("Ẩn mật khẩu")
        else:
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)
            action.setIcon(create_eye_icon(is_hidden=True))
            action.setToolTip("Hiển thị mật khẩu")

    def _show_reg_error(self, text: str):
        """Hiển thị thông báo lỗi trên trang đăng ký"""
        if hasattr(self, 'reg_err'):
            self.reg_err.setText(text)
            self.reg_err.setStyleSheet("""
                QLabel {
                    background-color: #3F1D1D;
                    border: 1px solid #EF4444;
                    color: #FCA5A5;
                    font-size: 11.5px;
                    font-weight: 600;
                    border-radius: 6px;
                    padding: 6px 10px;
                    margin-top: 4px;
                }
            """)
            self.reg_err.show()

    def _show_login_success(self, text: str):
        """Hiển thị thông báo thành công xanh ngọc trên trang đăng nhập"""
        if hasattr(self, 'login_err'):
            self.login_err.setText(text)
            self.login_err.setStyleSheet("""
                QLabel {
                    background-color: #064E3B;
                    border: 1px solid #10B981;
                    color: #A7F3D0;
                    font-size: 11.5px;
                    font-weight: 600;
                    border-radius: 6px;
                    padding: 7px 10px;
                }
            """)
            self.login_err.show()

    def _do_register(self):
        """Xử lý đăng ký tài khoản người dùng mới và kiểm tra chặt chẽ tính hợp lệ"""
        username = self.reg_user.text().strip()
        full_name = self.reg_name.text().strip()
        pwd = self.reg_pwd.text()
        confirm = self.reg_confirm.text()

        if not username:
            self._show_reg_error("Vui lòng nhập tên đăng nhập.")
            self.reg_user.setFocus()
            return

        if len(username) < 3:
            self._show_reg_error("Tên đăng nhập phải có ít nhất 3 ký tự.")
            self.reg_user.setFocus()
            return

        if not full_name:
            self._show_reg_error("Vui lòng nhập họ và tên.")
            self.reg_name.setFocus()
            return

        if len(pwd) < 6:
            self._show_reg_error("Mật khẩu phải có độ dài từ 6 ký tự trở lên.")
            self.reg_pwd.setFocus()
            return

        if pwd != confirm:
            self._show_reg_error("Mật khẩu xác nhận không khớp.")
            self.reg_confirm.setFocus()
            return

        ok, msg = database.register_user(username, pwd, full_name)
        if ok:
            # Thành công: Chuyển về màn hình đăng nhập, điền sẵn tài khoản & mật khẩu vừa tạo
            self.login_user.setText(username)
            self.login_pwd.setText(pwd)
            if hasattr(self, 'chk_remember') and self.chk_remember.isChecked():
                config_manager.update({
                    "remembered_username": username,
                    "remembered_password": pwd,
                    "remember_login": True
                })
            self._show_login_success(f"Tạo tài khoản '{username}' thành công! Bạn có thể đăng nhập ngay.")
            self.stack.setCurrentWidget(self.page_login)
            self.btn_login.setFocus()
        else:
            # Lỗi (bao gồm trùng tên đăng nhập): Hiển thị thông báo màu đỏ
            self._show_reg_error(msg)

    def _on_login_user_changed(self, text: str):
        """Tự động kiểm tra tài khoản khi người dùng nhập tên đăng nhập:
        Nếu khớp với tài khoản ghi nhớ gần nhất, tự động khôi phục mật khẩu tương ứng.
        Nếu thay đổi sang tên đăng nhập khác, xóa trường mật khẩu để tránh nhầm lẫn mật khẩu tài khoản khác."""
        input_user = text.strip()
        saved_user = str(config_manager.get("remembered_username", "")).strip()
        saved_pwd = str(config_manager.get("remembered_password", ""))

        if hasattr(self, 'login_pwd'):
            if input_user and input_user == saved_user:
                if saved_pwd:
                    self.login_pwd.setText(saved_pwd)
            else:
                self.login_pwd.clear()

    def _on_chk_remember_toggled(self, checked: bool):
        """Cập nhật tùy chọn ghi nhớ đăng nhập"""
        config_manager.update({"remember_login": checked})
        if not checked:
            config_manager.update({
                "remembered_username": "",
                "remembered_password": ""
            })



    def _toggle_pwd_visibility(self):
        """Chuyển đổi hiển thị mật khẩu bằng mắt thần và cập nhật icon tooltip"""
        if self.login_pwd.echoMode() == QLineEdit.EchoMode.Password:
            self.login_pwd.setEchoMode(QLineEdit.EchoMode.Normal)
            self.action_toggle_pwd.setIcon(create_eye_icon(is_hidden=False))
            self.action_toggle_pwd.setToolTip("Ẩn mật khẩu")
        else:
            self.login_pwd.setEchoMode(QLineEdit.EchoMode.Password)
            self.action_toggle_pwd.setIcon(create_eye_icon(is_hidden=True))
            self.action_toggle_pwd.setToolTip("Hiển thị mật khẩu")

    def _on_forgot_password(self):
        """Hiển thị hướng dẫn liên hệ quản trị viên khi quên mật khẩu"""
        self.login_err.setStyleSheet("""
            QLabel {
                background-color: #1E293B;
                border: 1px solid #38BDF8;
                color: #38BDF8;
                font-size: 11.5px;
                font-weight: 600;
                border-radius: 6px;
                padding: 7px 10px;
            }
        """)
        self.login_err.setText("Vui lòng liên hệ Admin để được cấp lại mật khẩu !")
        self.login_err.show()

    def _do_login(self):
        """Xử lý đăng nhập và chuyển trang mượt mà không phá hủy cửa sổ (Giai đoạn 7)"""
        username = self.login_user.text().strip()
        password = self.login_pwd.text().strip()

        # Đặt lại phong cách lỗi màu đỏ nhẹ
        self.login_err.setStyleSheet("""
            QLabel {
                background-color: #3F1D1D;
                border: 1px solid #EF4444;
                color: #FCA5A5;
                font-size: 11.5px;
                font-weight: 600;
                border-radius: 6px;
                padding: 7px 10px;
            }
        """)

        if not username or not password:
            self.login_err.setText("Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.")
            self.login_err.show()
            return

        # Hiển thị trạng thái loading trong nút đăng nhập
        self.btn_login.setEnabled(False)
        self.btn_login.setText("Đang xác thực...")
        QApplication.processEvents()

        try:
            ok, user, msg = database.authenticate_user(username, password)
            if ok and user:
                # Lưu tùy chọn ghi nhớ tài khoản và mật khẩu gần nhất
                if hasattr(self, 'chk_remember') and self.chk_remember.isChecked():
                    config_manager.update({
                        "remembered_username": username,
                        "remembered_password": password,
                        "remember_login": True
                    })
                else:
                    config_manager.update({
                        "remembered_username": "",
                        "remembered_password": "",
                        "remember_login": False
                    })

                self.user_session = user
                self.login_err.hide()
                self.btn_login.setEnabled(True)
                self.btn_login.setText("Đăng nhập")
                self._enter_dashboard()
            else:
                self.btn_login.setEnabled(True)
                self.btn_login.setText("Đăng nhập")
                self.login_err.setText(msg)
                self.login_err.show()
                self.login_pwd.selectAll()
                self.login_pwd.setFocus()
        except Exception as e:
            self.btn_login.setEnabled(True)
            self.btn_login.setText("Đăng nhập")
            self.login_err.setText(f"Lỗi xác thực: {str(e)}")
            self.login_err.show()

    def _enter_dashboard(self):
        """Kích hoạt giao diện chính theo quyền hạn người dùng (RBAC)"""
        user_role_str = "Quản trị viên" if self.user_session['role'] == 'admin' else "User"
        role_color = "#38BDF8" if self.user_session['role'] == 'admin' else "#2ECC71"
        if hasattr(self, 'btn_account_menu'):
            self.btn_account_menu.setText(f"👤 {user_role_str} ▾")
        if hasattr(self, 'user_badge'):
            self.user_badge.setText(f"Vai trò : <font color='{role_color}'><b>{user_role_str}</b></font>")

        # Áp dụng phân quyền RBAC cho Menu Quản lý Người dùng & Các tab quản trị nâng cao
        is_admin = (self.user_session['role'] == 'admin')
        if hasattr(self, 'act_user_mgmt'):
            self.act_user_mgmt.setVisible(is_admin)

        # Cập nhật huy hiệu trạng thái Cơ sở dữ liệu (MySQL / SQLite)
        if hasattr(self, 'db_status_label'):
            db_info = database.get_active_db_info()
            if db_info.get("is_mysql"):
                self.db_status_label.setText(f"<font color='#10B981'>●</font> CSDL: MySQL ({db_info.get('mysql_database')})")
                self.db_status_label.setToolTip(f"Đang kết nối CSDL MySQL tại {db_info.get('mysql_host')}:{db_info.get('mysql_port')}")
            else:
                self.db_status_label.setText("<font color='#F59E0B'>●</font> CSDL: SQLite Cục bộ")
                self.db_status_label.setToolTip("MySQL chưa kết nối - Bật XAMPP (Port 3306) để chuyển sang MySQL")

        # Cập nhật danh sách tài khoản cho bộ lọc sự cố (Lưu riêng theo từng tài khoản)
        if hasattr(self, 'combo_user_filter'):
            self.combo_user_filter.blockSignals(True)
            self.combo_user_filter.clear()
            if is_admin:
                self.combo_user_filter.addItem("Tất cả tài khoản", None)
                try:
                    all_u = database.get_all_users()
                    for u in all_u:
                        self.combo_user_filter.addItem(f"👤 {u[1]}", u[0])
                except Exception:
                    pass
                self.combo_user_filter.setEnabled(True)
            else:
                self.combo_user_filter.addItem(f"👤 {self.user_session['username']} (Cá nhân)", self.user_session['id'])
                self.combo_user_filter.setEnabled(False)
            self.combo_user_filter.blockSignals(False)

        if hasattr(self, 'tab_settings_locked') and hasattr(self, 'tab_settings_admin'):
            if is_admin:
                self.tab_settings_locked.hide()
                self.tab_settings_admin.show()
            else:
                self.tab_settings_locked.show()
                self.tab_settings_admin.hide()

        # Người vận hành chỉ thấy: Giám sát trực tiếp (Tab 0) và Nhật ký sự cố (Tab 1)
        # Quản trị viên thấy thêm: Thiết bị (Tab 2), Chẩn đoán (Tab 3), Mô phỏng (Tab 4), Cấu hình (Tab 5)
        if hasattr(self, 'tabs'):
            for t_idx in range(2, self.tabs.count()):
                self.tabs.setTabVisible(t_idx, is_admin)
            if not is_admin and self.tabs.currentIndex() >= 2:
                self.tabs.setCurrentIndex(0)

        # Nạp dữ liệu sự cố
        self._refresh_incident_table()

        # Chuyển trang và mở rộng cửa sổ làm việc (tối thiểu 1200x680 tương thích 1366x768 và 1920x1080)
        self.setMinimumSize(1200, 680)
        self.setMaximumSize(16777215, 16777215)
        self.stack.setCurrentIndex(1)
        self.showMaximized()
        apply_dark_titlebar(self)
        ensure_window_resizable(self)

    # ================= 2. TRANG BÀN ĐIỀU KHIỂN (DASHBOARD) =================
    def _build_dashboard_page(self, parent):
        main_layout = QVBoxLayout(parent)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Header một hàng duy nhất: tên hệ thống | trạng thái | người dùng
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #1E2329; border: 1px solid #2A313A; border-radius: 4px; padding: 4px 8px;")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(8, 4, 8, 4)
        header_layout.setSpacing(6)

        header_icon = QLabel()
        header_icon.setPixmap(create_radar_vector_icon(24))
        header_layout.addWidget(header_icon)

        title_label = QLabel("HỆ THỐNG GIÁM SÁT GIAO THÔNG AI")
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #38BDF8; letter-spacing: 0.5px;")
        title_label.setToolTip("Hệ thống giám sát giao thông và cảnh báo va chạm thông minh (Radar 24GHz & Camera)")

        # Dải chip trạng thái kỹ thuật đồng nhất (chấm màu: xám = chờ/dừng, xanh = hoạt động, đỏ = lỗi)
        chip_style = (
            "background-color: #161A1F; border: 1px solid #2A313A; border-radius: 4px; "
            "padding: 3px 8px; font-size: 11px; font-weight: 600; color: #E2E8F0;"
        )

        self.radar_conn_label = QLabel("<font color='#64748B'>●</font> Radar: Chờ kết nối")
        self.radar_conn_label.setStyleSheet(chip_style)
        self.radar_conn_label.setToolTip("Trạng thái kết nối cảm biến Radar (UART)")

        self.cam_conn_label = QLabel("<font color='#64748B'>●</font> Camera: Đã dừng")
        self.cam_conn_label.setStyleSheet(chip_style)
        self.cam_conn_label.setToolTip("Trạng thái thiết bị Camera (USB/RTSP)")

        self.btn_mute = QPushButton("● Âm thanh: Bật")
        self.btn_mute.setFont(QFont("Segoe UI", 11))
        self.btn_mute.setStyleSheet(
            "background-color: #161A1F; border: 1px solid #2A313A; border-radius: 4px; "
            "padding: 3px 8px; font-size: 11px; font-weight: 600; color: #2ECC71;"
        )
        self.btn_mute.setToolTip("Bật / tắt âm thanh cảnh báo")
        self.btn_mute.clicked.connect(self._toggle_sound_mute)

        self.fps_label = QLabel("<font color='#38BDF8'>●</font> FPS: --")
        self.fps_label.setStyleSheet(chip_style)
        self.fps_label.setToolTip("Tốc độ khung hình xử lý thời gian thực")

        self.obstacle_count_label = QLabel("<font color='#F59E0B'>●</font> Đối tượng: 0")
        self.obstacle_count_label.setStyleSheet(chip_style)
        self.obstacle_count_label.setToolTip("Số lượng đối tượng phát hiện trong vùng quét cảm biến")

        self.db_status_label = QLabel("<font color='#64748B'>●</font> CSDL: Đang kết nối...")
        self.db_status_label.setStyleSheet(chip_style)
        self.db_status_label.setToolTip("Trạng thái kết nối cơ sở dữ liệu (MySQL / SQLite)")

        # Menu tài khoản gom "Đổi mật khẩu", "Quản lý người dùng", "Đăng xuất"
        self.btn_account_menu = QPushButton("👤 User ▾")
        self.btn_account_menu.setStyleSheet("""
            QPushButton {
                background-color: #161A1F;
                color: #F1F5F9;
                border: 1px solid #2A313A;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1E2329;
                border-color: #38BDF8;
            }
            QPushButton::menu-indicator { image: none; }
        """)
        account_menu = QMenu(self)
        account_menu.setStyleSheet("""
            QMenu {
                background-color: #161A1F;
                color: #F1F5F9;
                border: 1px solid #2A313A;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 3px;
                font-size: 11px;
            }
            QMenu::item:selected {
                background-color: #2B6CB0;
            }
        """)
        self.act_change_pwd = account_menu.addAction("Đổi mật khẩu", self._open_change_password)
        self.act_user_mgmt = account_menu.addAction("Quản lý người dùng", self._open_user_management)
        account_menu.addSeparator()
        self.act_logout = account_menu.addAction("Đăng xuất", self._handle_logout)
        self.btn_account_menu.setMenu(account_menu)

        # Các thuộc tính tương thích ngược cho kiểm thử & các hàm nội bộ (gắn parent=parent chống bung tab độc lập)
        self.user_badge = QLabel("", parent=parent)
        self.user_badge.setVisible(False)
        self.btn_user_mgmt = QPushButton("Quản lý người dùng", parent=parent)
        self.btn_user_mgmt.setVisible(False)
        self.btn_user_mgmt.clicked.connect(self._open_user_management)
        btn_change_pwd = QPushButton("Đổi mật khẩu", parent=parent)
        btn_change_pwd.setVisible(False)
        btn_change_pwd.clicked.connect(self._open_change_password)
        btn_logout = QPushButton("Đăng xuất", parent=parent)
        btn_logout.setVisible(False)
        btn_logout.clicked.connect(self._handle_logout)
        self.btn_change_pwd = btn_change_pwd
        self.btn_logout = btn_logout

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.radar_conn_label)
        header_layout.addWidget(self.cam_conn_label)
        header_layout.addWidget(self.btn_mute)
        header_layout.addWidget(self.fps_label)
        header_layout.addWidget(self.obstacle_count_label)
        header_layout.addWidget(self.db_status_label)
        header_layout.addWidget(self.btn_account_menu)
        main_layout.addWidget(header_frame)

        # Tabs không emoji, chữ chuẩn tiếng Việt
        self.tabs = QTabWidget()

        # TAB 0: Giám sát trực tiếp
        self.tab_monitor = QWidget()
        self._build_monitor_content(self.tab_monitor)
        self.tabs.addTab(self.tab_monitor, "Giám sát trực tiếp")

        # TAB 1: Nhật ký sự cố
        self.tab_audit = QWidget()
        self._build_audit_content(self.tab_audit)
        self.tabs.addTab(self.tab_audit, "Nhật ký sự cố")

        # TAB 2: Thiết bị (Chỉ Quản trị viên)
        self.tab_device = QWidget()
        self._build_device_content(self.tab_device)
        self.tabs.addTab(self.tab_device, "Thiết bị")

        # TAB 3: Chẩn đoán (Chỉ Quản trị viên)
        self.tab_diagnostics = QWidget()
        self._build_diagnostics_content(self.tab_diagnostics)
        self.tabs.addTab(self.tab_diagnostics, "Chẩn đoán")

        # TAB 4: Mô phỏng (Chỉ Quản trị viên)
        self.tab_simulation = QWidget()
        self._build_simulation_content(self.tab_simulation)
        self.tabs.addTab(self.tab_simulation, "Mô phỏng")

        # TAB 5: Cấu hình an toàn (Chỉ Quản trị viên)
        self.tab_settings = QWidget()
        self._build_settings_content(self.tab_settings)
        self.tabs.addTab(self.tab_settings, "Cấu hình")

        main_layout.addWidget(self.tabs)

    def _build_monitor_content(self, parent_widget):
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # 1. Băng thông báo Mô phỏng (ở đầu trang, chỉ hiện khi chạy Chế độ mô phỏng)
        self.sim_banner = QLabel("⚠ ĐANG CHẠY MÔ PHỎNG (DỮ LIỆU THỬ NGHIỆM)")
        self.sim_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sim_banner.setStyleSheet("""
            QLabel {
                background-color: #B45309;
                color: #FEF3C7;
                font-size: 13px;
                font-weight: 700;
                padding: 6px 12px;
                border: 1px solid #F59E0B;
                border-radius: 4px;
                letter-spacing: 0.5px;
            }
        """)
        self.sim_banner.setVisible(False)
        layout.addWidget(self.sim_banner)

        # 2. Thanh trạng thái lớn (SRS: An toàn / Cảnh báo / Báo động kèm lý do)
        self.status_bar_frame = QFrame()
        self.status_bar_frame.setStyleSheet("background-color: #161A1F; border: 1px solid #2A313A; border-radius: 6px; padding: 4px 8px;")
        status_layout = QHBoxLayout(self.status_bar_frame)
        status_layout.setContentsMargins(12, 6, 12, 6)
        status_layout.setSpacing(14)

        lbl_status_title = QLabel("TRẠNG THÁI:")
        lbl_status_title.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        status_layout.addWidget(lbl_status_title)

        self.status_banner = QLabel("CHƯA GIÁM SÁT")
        self.status_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_banner.setMinimumWidth(130)
        self.status_banner.setStyleSheet("background-color: #334155; color: #94A3B8; border: 1px solid #475569; border-radius: 4px; padding: 5px 16px; font-weight: 800; font-size: 14px;")
        self.status_banner.setToolTip("Trạng thái: Hệ thống đang dừng - Chưa kích hoạt cảm biến")
        status_layout.addWidget(self.status_banner)

        self.status_reason_label = QLabel("Hệ thống đang dừng - Nhấn 'Bắt đầu giám sát' để kích hoạt cảm biến")
        self.status_reason_label.setStyleSheet("color: #E2E8F0; font-size: 13px; font-weight: 500;")
        status_layout.addWidget(self.status_reason_label, stretch=1)
        layout.addWidget(self.status_bar_frame)

        # 3. Dual view: Camera (Trái) & Bản đồ Radar (Phải)
        dual_view = QHBoxLayout()
        dual_view.setSpacing(16)

        # Cột Trái: Camera (Giữ đúng tỉ lệ, không viền thừa)
        self.cam_group = QGroupBox("Camera giám sát")
        cam_layout = QVBoxLayout(self.cam_group)
        cam_layout.setContentsMargins(4, 8, 4, 4)
        self.camera_view = QLabel()
        self.camera_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_view.setMinimumSize(320, 200)
        self.camera_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.camera_view.setMouseTracking(True)
        self.camera_view.installEventFilter(self)
        self._set_camera_idle_placeholder()
        cam_layout.addWidget(self.camera_view)
        dual_view.addWidget(self.cam_group, stretch=5)

        # Cột Phải: Bản đồ radar
        radar_group = QGroupBox("Bản đồ radar")
        radar_layout = QVBoxLayout(radar_group)
        radar_layout.setContentsMargins(8, 8, 8, 8)
        self.radar_canvas = RadarCanvas()
        self.radar_canvas.target_clicked.connect(self._on_radar_target_clicked)
        radar_layout.addWidget(self.radar_canvas)
        dual_view.addWidget(radar_group, stretch=4)

        layout.addLayout(dual_view, stretch=7)

        # 4. Bottom Panel: Chỉ có 3 thành phần cho Người vận hành
        bottom_panel = QHBoxLayout()
        bottom_panel.setSpacing(16)

        # Panel 1: Điều khiển giám sát (Nút duy nhất Bắt đầu / Dừng)
        ctrl_group = QGroupBox("Điều khiển giám sát")
        ctrl_group.setMinimumWidth(260)
        ctrl_layout = QVBoxLayout(ctrl_group)
        ctrl_layout.setContentsMargins(14, 12, 14, 12)
        ctrl_layout.setSpacing(8)
        ctrl_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.lbl_system_status = QLabel("Trạng thái: <font color='#94A3B8'><b>Đã dừng</b></font>")
        self.lbl_system_status.setStyleSheet("font-size: 13px; font-weight: 600;")
        self.lbl_system_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ctrl_layout.addWidget(self.lbl_system_status)

        self.btn_monitor_toggle = QPushButton("Bắt đầu giám sát")
        self.btn_monitor_toggle.setMinimumHeight(42)
        self.btn_monitor_toggle.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 700;
                border-radius: 6px;
                padding: 8px 16px;
                border: 1px solid #059669;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
        """)
        self.btn_monitor_toggle.clicked.connect(self._toggle_monitoring)
        ctrl_layout.addWidget(self.btn_monitor_toggle)


        # Nút ẩn duy trì tính tương thích ngược cho backend & test scripts
        self.btn_start = QPushButton("Bắt đầu")
        self.btn_start.setObjectName("btnSuccess")
        self.btn_start.setVisible(False)
        self.btn_start.clicked.connect(self._start_system)
        self.btn_stop = QPushButton("Tạm dừng")
        self.btn_stop.setObjectName("btnDanger")
        self.btn_stop.setVisible(False)
        self.btn_stop.clicked.connect(self._stop_system)
        ctrl_layout.addWidget(self.btn_start)
        ctrl_layout.addWidget(self.btn_stop)

        bottom_panel.addWidget(ctrl_group, stretch=3)

        # Panel 2: Thẻ Đối tượng gần nhất
        telemetry_group = QGroupBox("Đối tượng gần nhất")
        telemetry_group.setMinimumWidth(345)
        telemetry_layout = QVBoxLayout(telemetry_group)
        telemetry_layout.setContentsMargins(12, 12, 12, 12)
        telemetry_layout.setSpacing(6)
        telemetry_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.lbl_telemetry = QLabel()
        self.lbl_telemetry.setStyleSheet("color: #F1F5F9; padding: 2px;")
        self._update_telemetry_default()
        telemetry_layout.addWidget(self.lbl_telemetry)

        self.btn_detail = QPushButton("🔍 Xem chi tiết đối tượng")
        self.btn_detail.setStyleSheet("background-color: #262C36; color: #38BDF8; border: 1px solid #38BDF8; border-radius: 4px; padding: 6px 12px; font-size: 11px; font-weight: 600;")
        self.btn_detail.setToolTip("Xem cửa sổ thông số chi tiết của đối tượng")
        self.btn_detail.clicked.connect(self._open_selected_target_detail)
        telemetry_layout.addWidget(self.btn_detail)

        # Nút ẩn duy trì tương thích ngược
        self.btn_nearest = QPushButton("Đối tượng gần nhất")
        self.btn_nearest.setVisible(False)
        self.btn_nearest.clicked.connect(self._reset_selection_to_nearest)
        telemetry_layout.addWidget(self.btn_nearest)

        bottom_panel.addWidget(telemetry_group, stretch=4)

        # Panel 3: Sự cố gần đây (3 dòng, 4 cột, nút Xem tất cả)
        hot_log_group = QGroupBox("Sự cố gần đây")
        hot_log_group.setMinimumWidth(360)
        hot_log_layout = QVBoxLayout(hot_log_group)
        hot_log_layout.setContentsMargins(12, 12, 12, 12)
        hot_log_layout.setSpacing(6)
        hot_log_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.hot_log_table = QTableWidget(0, 4)
        self.hot_log_table.verticalHeader().setVisible(False)
        self.hot_log_table.setHorizontalHeaderLabels(["Ngày giờ", "Đối tượng", "Khoảng cách", "Mức độ"])
        hl_hdr = self.hot_log_table.horizontalHeader()
        hl_hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.hot_log_table.setColumnWidth(0, 110)
        hl_hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)          # Đối tượng co giãn
        hl_hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.hot_log_table.setColumnWidth(2, 85)
        hl_hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.hot_log_table.setColumnWidth(3, 95)
        hl_hdr.setMinimumSectionSize(40)

        # Căn lề tiêu đề cột đồng nhất:
        self.hot_log_table.horizontalHeaderItem(0).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hot_log_table.horizontalHeaderItem(1).setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.hot_log_table.horizontalHeaderItem(2).setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.hot_log_table.horizontalHeaderItem(3).setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        self.hot_log_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.hot_log_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.hot_log_table.setFixedHeight(120)
        hot_log_layout.addWidget(self.hot_log_table)

        self.btn_view_all = QPushButton("Xem tất cả sự cố ➔")
        self.btn_view_all.setStyleSheet("padding: 5px 12px; font-size: 11px; background-color: #262C36; color: #38BDF8; border: 1px solid #38BDF8; border-radius: 4px;")
        self.btn_view_all.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        hot_log_layout.addWidget(self.btn_view_all)

        bottom_panel.addWidget(hot_log_group, stretch=4)
        layout.addLayout(bottom_panel, stretch=3)

    def _build_audit_content(self, parent_widget):
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(12)

        lbl_u = QLabel("Tài khoản:")
        lbl_u.setStyleSheet("color: #CBD5E1; font-weight: 600;")
        filter_bar.addWidget(lbl_u)
        self.combo_user_filter = QComboBox()
        self.combo_user_filter.addItem("Tất cả tài khoản", None)
        self.combo_user_filter.currentIndexChanged.connect(self._refresh_incident_table)
        filter_bar.addWidget(self.combo_user_filter)

        lbl_sev = QLabel("Mức độ:")
        lbl_sev.setStyleSheet("color: #CBD5E1; font-weight: 600;")
        filter_bar.addWidget(lbl_sev)
        self.combo_filter_sev = QComboBox()
        self.combo_filter_sev.addItems(["Tất cả", "Nguy cơ va chạm", "Có vật trong vùng cảnh báo"])
        self.combo_filter_sev.currentIndexChanged.connect(self._refresh_incident_table)
        filter_bar.addWidget(self.combo_filter_sev)

        self.check_filter_date = QCheckBox("Theo ngày:")
        self.check_filter_date.setStyleSheet("color: #CBD5E1; font-weight: 600;")
        self.check_filter_date.stateChanged.connect(self._refresh_incident_table)
        filter_bar.addWidget(self.check_filter_date)

        self.date_filter_edit = QDateEdit()
        self.date_filter_edit.setDate(QDate.currentDate())
        self.date_filter_edit.setCalendarPopup(True)
        self.date_filter_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_filter_edit.setStyleSheet("background-color: #161A1F; color: #FFFFFF; border: 1px solid #2A313A; padding: 4px; border-radius: 4px;")
        self.date_filter_edit.dateChanged.connect(self._refresh_incident_table)
        filter_bar.addWidget(self.date_filter_edit)

        lbl_s = QLabel("Tìm kiếm:")
        lbl_s.setStyleSheet("color: #CBD5E1; font-weight: 600;")
        filter_bar.addWidget(lbl_s)
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Nhập mã sự cố, đối tượng hoặc thời gian...")
        self.txt_search.returnPressed.connect(self._refresh_incident_table)
        filter_bar.addWidget(self.txt_search)

        btn_filter = QPushButton("Lọc dữ liệu")
        btn_filter.clicked.connect(self._refresh_incident_table)
        filter_bar.addWidget(btn_filter)

        filter_bar.addStretch()

        btn_export = QPushButton("Xuất báo cáo")
        btn_export.setStyleSheet("background-color: #2B6CB0; color: #FFFFFF; font-weight: 600; border: none; border-radius: 4px; padding: 6px 16px;")
        btn_export.clicked.connect(self._export_csv)
        filter_bar.addWidget(btn_export)

        layout.addLayout(filter_bar)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.audit_table = QTableWidget(0, 8)
        self.audit_table.setHorizontalHeaderLabels([
            "ID", "Tài khoản", "Thời gian", "Đối tượng", "Cự ly (m)", "Tốc độ (km/h)", "TTC (s)", "Mức độ"
        ])
        a_hdr = self.audit_table.horizontalHeader()
        a_hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        a_hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        a_hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        a_hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        a_hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        a_hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        a_hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        a_hdr.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        a_hdr.setMinimumSectionSize(45)
        self.audit_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.audit_table.itemSelectionChanged.connect(self._on_audit_selection_changed)
        self.audit_table.itemDoubleClicked.connect(self._on_audit_double_clicked)
        splitter.addWidget(self.audit_table)

        preview_box = QGroupBox("Hình ảnh hiện trường")
        preview_layout = QVBoxLayout(preview_box)
        self.lbl_preview_img = QLabel("Chọn một dòng sự cố để xem ảnh")
        self.lbl_preview_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview_img.setStyleSheet("background-color: #161A1F; border: 1px solid #2A313A; border-radius: 4px; color: #94A3B8;")
        self.lbl_preview_img.setMinimumSize(200, 140)
        self.lbl_preview_img.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        preview_layout.addWidget(self.lbl_preview_img)
        
        self.btn_open_full_img = QPushButton("Xem ảnh phóng to")
        self.btn_open_full_img.setEnabled(False)
        self.btn_open_full_img.clicked.connect(self._open_current_selected_dialog)
        preview_layout.addWidget(self.btn_open_full_img)

        splitter.addWidget(preview_box)
        splitter.setSizes([750, 450])
        layout.addWidget(splitter)

    def _build_device_content(self, parent_widget):
        scroll = QScrollArea(parent_widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # 1. Cấu hình Cổng kết nối Radar
        grp_radar_conn = QGroupBox("Cổng kết nối Cảm biến Radar (HLK-LD2450)")
        gl_r = QGridLayout(grp_radar_conn)
        gl_r.setContentsMargins(12, 16, 12, 12)
        gl_r.setSpacing(10)

        lbl_port = QLabel("Cổng COM kết nối:")
        lbl_port.setStyleSheet("color: #CBD5E1;")
        gl_r.addWidget(lbl_port, 0, 0)
        self.combo_ports = QComboBox()
        self.combo_ports.setMinimumWidth(160)
        self._refresh_ports()
        gl_r.addWidget(self.combo_ports, 0, 1)

        self.btn_refresh_ports = QPushButton("Quét cổng COM")
        self.btn_refresh_ports.clicked.connect(self._refresh_ports)
        gl_r.addWidget(self.btn_refresh_ports, 0, 2)

        lbl_baud = QLabel("Tốc độ truyền (Baudrate):")
        lbl_baud.setStyleSheet("color: #CBD5E1;")
        gl_r.addWidget(lbl_baud, 1, 0)
        self.combo_baud = QComboBox()
        self.combo_baud.addItems(["256000", "115200", "9600"])
        gl_r.addWidget(self.combo_baud, 1, 1, 1, 2)
        layout.addWidget(grp_radar_conn)

        # 2. Cấu hình Nguồn hình ảnh Camera
        grp_cam_conn = QGroupBox("Nguồn hình ảnh Camera & Đồng bộ hướng")
        gl_c = QGridLayout(grp_cam_conn)
        gl_c.setContentsMargins(12, 16, 12, 12)
        gl_c.setSpacing(10)

        lbl_cam = QLabel("Nguồn hình ảnh:")
        lbl_cam.setStyleSheet("color: #CBD5E1;")
        gl_c.addWidget(lbl_cam, 0, 0)
        self.combo_camera = QComboBox()
        self.combo_camera.setMinimumWidth(160)
        self._refresh_cameras()
        gl_c.addWidget(self.combo_camera, 0, 1)

        self.btn_refresh_cams = QPushButton("Quét camera")
        self.btn_refresh_cams.clicked.connect(self._refresh_cameras)
        gl_c.addWidget(self.btn_refresh_cams, 0, 2)

        self.check_invert_x = QCheckBox("Lật ngang hình ảnh Radar (Đồng bộ hướng quan sát)")
        self.check_invert_x.setChecked(True)
        self.check_invert_x.setToolTip("Lật ngang để góc nhìn Radar và Camera đồng bộ hướng Trái/Phải")
        self.check_invert_x.stateChanged.connect(self._toggle_invert_x)
        gl_c.addWidget(self.check_invert_x, 1, 0, 1, 3)
        layout.addWidget(grp_cam_conn)

        # 3. Hiệu chuẩn quang học & bù lệch không gian cảm biến
        grp_calib = QGroupBox("Hiệu chuẩn quang học & Bù lệch không gian cảm biến")
        gl_cal = QGridLayout(grp_calib)
        gl_cal.setContentsMargins(12, 16, 12, 12)
        gl_cal.setSpacing(10)

        cfg = config_manager.get_all() if hasattr(config_manager, 'get_all') else config_manager.data
        curr_hfov = float(cfg.get("camera_hfov_deg", 65.0))
        gl_cal.addWidget(QLabel("Góc mở ngang Camera HFOV (°):"), 0, 0)
        self.spin_cfg_hfov = QDoubleSpinBox()
        self.spin_cfg_hfov.setRange(40.0, 120.0)
        self.spin_cfg_hfov.setSingleStep(1.0)
        self.spin_cfg_hfov.setValue(curr_hfov)
        self.slider_cfg_hfov = QSlider(Qt.Orientation.Horizontal)
        self.slider_cfg_hfov.setRange(40, 120)
        self.slider_cfg_hfov.setValue(int(curr_hfov))
        self.slider_cfg_hfov.valueChanged.connect(lambda v: self.spin_cfg_hfov.setValue(float(v)))
        self.spin_cfg_hfov.valueChanged.connect(lambda v: self.slider_cfg_hfov.setValue(int(v)))
        gl_cal.addWidget(self.slider_cfg_hfov, 0, 1)
        gl_cal.addWidget(self.spin_cfg_hfov, 0, 2)

        gl_cal.addWidget(QLabel("Bù lệch ngang Offset X (m):"), 1, 0)
        self.spin_cfg_ox = QDoubleSpinBox()
        self.spin_cfg_ox.setRange(-1.0, 1.0)
        self.spin_cfg_ox.setSingleStep(0.05)
        self.spin_cfg_ox.setValue(self.offset_x)
        self.slider_cfg_ox = QSlider(Qt.Orientation.Horizontal)
        self.slider_cfg_ox.setRange(-100, 100)
        self.slider_cfg_ox.setValue(int(self.offset_x * 100))
        self.slider_cfg_ox.valueChanged.connect(lambda v: self.spin_cfg_ox.setValue(v / 100.0))
        self.spin_cfg_ox.valueChanged.connect(lambda v: self.slider_cfg_ox.setValue(int(v * 100)))
        gl_cal.addWidget(self.slider_cfg_ox, 1, 1)
        gl_cal.addWidget(self.spin_cfg_ox, 1, 2)

        gl_cal.addWidget(QLabel("Bù lệch dọc Offset Y (m):"), 2, 0)
        self.spin_cfg_oy = QDoubleSpinBox()
        self.spin_cfg_oy.setRange(-1.0, 1.0)
        self.spin_cfg_oy.setSingleStep(0.05)
        self.spin_cfg_oy.setValue(self.offset_y)
        self.slider_cfg_oy = QSlider(Qt.Orientation.Horizontal)
        self.slider_cfg_oy.setRange(-100, 100)
        self.slider_cfg_oy.setValue(int(self.offset_y * 100))
        self.slider_cfg_oy.valueChanged.connect(lambda v: self.spin_cfg_oy.setValue(v / 100.0))
        self.spin_cfg_oy.valueChanged.connect(lambda v: self.slider_cfg_oy.setValue(int(v * 100)))
        gl_cal.addWidget(self.slider_cfg_oy, 2, 1)
        gl_cal.addWidget(self.spin_cfg_oy, 2, 2)

        self.check_cfg_invert_radar_x = QCheckBox("Lật ngang hình ảnh Radar (Invert Radar X)")
        self.check_cfg_invert_radar_x.setChecked(bool(cfg.get("invert_radar_x", True)))
        gl_cal.addWidget(self.check_cfg_invert_radar_x, 3, 0, 1, 2)

        self.check_cfg_flip_cam = QCheckBox("Lật ngang hình ảnh Camera (Flip Camera Horizontal)")
        self.check_cfg_flip_cam.setChecked(bool(cfg.get("flip_camera_horizontal", False)))
        gl_cal.addWidget(self.check_cfg_flip_cam, 3, 2)
        layout.addWidget(grp_calib)

        # Hàng nút lưu cấu hình
        row_act = QHBoxLayout()
        row_act.addStretch()
        btn_save = QPushButton("Lưu cấu hình thiết bị")
        btn_save.setStyleSheet("padding: 8px 20px; font-weight: 700; background-color: #10B981; color: #FFFFFF; border: 1px solid #059669; border-radius: 4px;")
        btn_save.clicked.connect(self._save_admin_settings)
        row_act.addWidget(btn_save)
        layout.addLayout(row_act)
        layout.addStretch()

        outer = QVBoxLayout(parent_widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        scroll.setWidget(content)

    def _build_diagnostics_content(self, parent_widget):
        scroll = QScrollArea(parent_widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # 1. Bảng Gỡ lỗi Radar (Đối tượng thô 1..3)
        self.radar_debug_group = QGroupBox("Chẩn đoán & Gỡ lỗi Radar (Đối tượng thô 1..3)")
        dbg_layout = QVBoxLayout(self.radar_debug_group)
        dbg_layout.setContentsMargins(12, 16, 12, 12)
        dbg_layout.setSpacing(10)

        cfg = config_manager.get_all() if hasattr(config_manager, 'get_all') else config_manager.data
        self.check_cfg_debug_radar = QCheckBox("Bật chế độ gỡ lỗi Radar (Cập nhật bảng 3 đối tượng thô và trạng thái lọc)")
        self.check_cfg_debug_radar.setChecked(bool(cfg.get("debug_radar_mode", True)))
        dbg_layout.addWidget(self.check_cfg_debug_radar)

        self.radar_debug_table = QTableWidget(3, 5)
        self.radar_debug_table.setHorizontalHeaderLabels(["Đối tượng", "X (m)", "Y (m)", "V (km/h)", "Trạng thái"])
        rd_hdr = self.radar_debug_table.horizontalHeader()
        rd_hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.radar_debug_table.setColumnWidth(0, 100)
        rd_hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.radar_debug_table.setColumnWidth(1, 80)
        rd_hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.radar_debug_table.setColumnWidth(2, 80)
        rd_hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.radar_debug_table.setColumnWidth(3, 100)
        rd_hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        rd_hdr.setMinimumSectionSize(50)
        self.radar_debug_table.verticalHeader().setVisible(False)
        for r_idx in range(3):
            self.radar_debug_table.setItem(r_idx, 0, QTableWidgetItem(f"Đối tượng {r_idx+1}"))
            self.radar_debug_table.setItem(r_idx, 1, QTableWidgetItem("--"))
            self.radar_debug_table.setItem(r_idx, 2, QTableWidgetItem("--"))
            self.radar_debug_table.setItem(r_idx, 3, QTableWidgetItem("--"))
            self.radar_debug_table.setItem(r_idx, 4, QTableWidgetItem("trống"))
        dbg_layout.addWidget(self.radar_debug_table)
        layout.addWidget(self.radar_debug_group)

        # 2. Hiệu chuẩn Lọc nền tĩnh Radar
        grp_bg = QGroupBox("Hiệu chuẩn Lọc nền tĩnh Radar (Background Calibration)")
        gl_bg = QVBoxLayout(grp_bg)
        gl_bg.setContentsMargins(12, 16, 12, 12)
        gl_bg.setSpacing(10)

        lbl_bg_desc = QLabel(
            "Hệ thống sẽ thu thập các đối tượng đứng yên liên tục trong 5 giây (cột mốc, bờ tường, biển báo)<br>"
            "và loại bỏ chúng khỏi cảnh báo va chạm động để giảm thiểu báo động giả."
        )
        lbl_bg_desc.setStyleSheet("color: #94A3B8; font-size: 12px;")
        gl_bg.addWidget(lbl_bg_desc)

        calib_ctrl_row = QHBoxLayout()
        self.btn_calib_bg = QPushButton("Bắt đầu hiệu chuẩn nền (5 giây)")
        self.btn_calib_bg.clicked.connect(self._start_bg_calibration)
        calib_ctrl_row.addWidget(self.btn_calib_bg)

        self.btn_clear_bg = QPushButton("Xóa dữ liệu nền")
        self.btn_clear_bg.clicked.connect(self._clear_background)
        calib_ctrl_row.addWidget(self.btn_clear_bg)
        calib_ctrl_row.addStretch()
        gl_bg.addLayout(calib_ctrl_row)

        self.calib_prog_bar = QProgressBar()
        self.calib_prog_bar.setRange(0, 100)
        self.calib_prog_bar.setValue(0)
        gl_bg.addWidget(self.calib_prog_bar)

        bg_pts_count = self._get_bg_points_count()
        bg_info_txt = (
            f"Điểm nền đang áp dụng: {bg_pts_count} điểm (từ background.json)."
            if bg_pts_count > 0
            else "Điểm nền đang áp dụng: 0 điểm (không lọc nền tĩnh; hãy hiệu chuẩn khi khu vực quan sát trống)."
        )
        self.lbl_calib_info = QLabel(bg_info_txt)
        self.lbl_calib_info.setStyleSheet("color: #94A3B8; font-size: 12px; font-style: italic;")
        gl_bg.addWidget(self.lbl_calib_info)
        layout.addWidget(grp_bg)

        # 3. Thông số suy luận & chẩn đoán hiệu năng
        grp_perf = QGroupBox("Thời gian suy luận & Hiệu năng xử lý AI")
        perf_layout = QVBoxLayout(grp_perf)
        perf_layout.setContentsMargins(12, 16, 12, 12)
        self.lbl_perf_diag = QLabel(
            "• Mô hình nhận diện: YOLOv8n (ONNX Runtime)<br>"
            "• Thời gian suy luận YOLO trung bình: ~15 - 28 ms/khung hình<br>"
            "• Thuật toán theo vết: DetectionTracker (Kalman Filter + Hungarian Algorithm)<br>"
            "• Thuật toán kết hợp cảm biến: Sensor Fusion (Chiếu không gian 3D sang 2D)"
        )
        self.lbl_perf_diag.setStyleSheet("color: #CBD5E1; font-size: 12px; line-height: 1.6;")
        perf_layout.addWidget(self.lbl_perf_diag)
        layout.addWidget(grp_perf)
        layout.addStretch()

        outer = QVBoxLayout(parent_widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        scroll.setWidget(content)

    def _build_simulation_content(self, parent_widget):
        scroll = QScrollArea(parent_widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Group Mô phỏng
        grp_sim = QGroupBox("Chế độ Mô phỏng Kiểm thử (Offline Simulation)")
        sim_layout = QVBoxLayout(grp_sim)
        sim_layout.setContentsMargins(12, 16, 12, 12)
        sim_layout.setSpacing(12)

        self.check_sim = QCheckBox("Kích hoạt Chế độ Mô phỏng (Dữ liệu ngoại tuyến thay cho cảm biến thật)")
        self.check_sim.setChecked(False)
        self.check_sim.setStyleSheet("font-size: 13px; font-weight: 600; color: #FCD34D;")
        self.check_sim.stateChanged.connect(self._toggle_simulation_mode)
        sim_layout.addWidget(self.check_sim)

        self.sim_controls_box = QWidget()
        sim_box_layout = QGridLayout(self.sim_controls_box)
        sim_box_layout.setContentsMargins(0, 6, 0, 6)
        sim_box_layout.setSpacing(10)

        lbl_sim = QLabel("Kịch bản video kiểm thử:")
        lbl_sim.setStyleSheet("color: #CBD5E1;")
        sim_box_layout.addWidget(lbl_sim, 0, 0)

        self.combo_sim_scenario = QComboBox()
        self.combo_sim_scenario.setMinimumWidth(260)
        sim_box_layout.addWidget(self.combo_sim_scenario, 0, 1)

        self.btn_browse_sim = QPushButton("Chọn video khác...")
        self.btn_browse_sim.clicked.connect(self._browse_sim_video)
        sim_box_layout.addWidget(self.btn_browse_sim, 0, 2)

        self.check_sim_jump = QCheckBox("Vào trước sự cố (-5s) để demo nhanh cảnh báo va chạm")
        self.check_sim_jump.setChecked(True)
        self.check_sim_jump.setToolTip("Tự động tua đến trước mốc cảnh báo 5 giây đối với video có sự cố")
        sim_box_layout.addWidget(self.check_sim_jump, 1, 0, 1, 3)

        self._refresh_sim_scenarios()
        self.sim_controls_box.setEnabled(False)
        sim_layout.addWidget(self.sim_controls_box)

        lbl_sim_desc = QLabel(
            "Chế độ mô phỏng cho phép phát lại video hiện trường kết hợp tập dữ liệu CSV của Radar<br>"
            "đã được ghi đồng bộ thời gian thực để kiểm tra tính năng phát hiện, cảnh báo và nhật ký."
        )
        lbl_sim_desc.setStyleSheet("color: #94A3B8; font-size: 12px; line-height: 1.5;")
        sim_layout.addWidget(lbl_sim_desc)
        layout.addWidget(grp_sim)
        layout.addStretch()

        outer = QVBoxLayout(parent_widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        scroll.setWidget(content)

    def _build_settings_content(self, parent_widget):
        scroll = QScrollArea(parent_widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Màn hình khóa khi là Operator (Phân quyền RBAC)
        self.tab_settings_locked = QFrame()
        self.tab_settings_locked.setStyleSheet("background-color: #1E2329; border: 1px solid #E74C3C; border-radius: 4px; padding: 32px;")
        l_layout = QVBoxLayout(self.tab_settings_locked)
        lbl_lock = QLabel("Truy cập bị giới hạn")
        lbl_lock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_lock.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        lbl_lock.setStyleSheet("color: #E74C3C;")
        lbl_desc = QLabel(
            "Tài khoản hiện tại có vai trò <b>User</b>.<br>"
            "Chỉ Quản trị viên mới có quyền thay đổi ngưỡng cảnh báo và tham số hiệu chuẩn phần cứng.<br><br>"
            "<i>Vui lòng đăng xuất và đăng nhập tài khoản Quản trị viên để thực hiện cấu hình.</i>"
        )
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_desc.setStyleSheet("color: #94A3B8; font-size: 12px; line-height: 1.6;")
        l_layout.addWidget(lbl_lock)
        l_layout.addWidget(lbl_desc)
        layout.addWidget(self.tab_settings_locked)

        # Màn hình Admin
        self.tab_settings_admin = QWidget()
        a_layout = QVBoxLayout(self.tab_settings_admin)
        a_layout.setContentsMargins(0, 0, 0, 0)
        a_layout.setSpacing(14)

        grp_th = QGroupBox("Ngưỡng đánh giá an toàn & Thời gian va chạm (TTC)")
        gl_th = QGridLayout(grp_th)
        gl_th.setContentsMargins(12, 16, 12, 12)
        gl_th.setSpacing(10)

        gl_th.addWidget(QLabel("Khoảng cách cảnh báo vàng (m):"), 0, 0)
        self.spin_cfg_warn_d = QDoubleSpinBox()
        self.spin_cfg_warn_d.setRange(0.5, 6.0)
        self.spin_cfg_warn_d.setSingleStep(0.1)
        self.spin_cfg_warn_d.setValue(self.warn_dist)
        gl_th.addWidget(self.spin_cfg_warn_d, 0, 1)

        gl_th.addWidget(QLabel("Thời gian va chạm TTC vàng (s):"), 0, 2)
        self.spin_cfg_warn_ttc = QDoubleSpinBox()
        self.spin_cfg_warn_ttc.setRange(0.5, 10.0)
        self.spin_cfg_warn_ttc.setSingleStep(0.1)
        self.spin_cfg_warn_ttc.setValue(self.warn_ttc)
        gl_th.addWidget(self.spin_cfg_warn_ttc, 0, 3)

        gl_th.addWidget(QLabel("Khoảng cách nguy cơ đỏ (m):"), 1, 0)
        self.spin_cfg_danger_d = QDoubleSpinBox()
        self.spin_cfg_danger_d.setRange(0.3, 4.0)
        self.spin_cfg_danger_d.setSingleStep(0.1)
        self.spin_cfg_danger_d.setValue(self.danger_dist)
        gl_th.addWidget(self.spin_cfg_danger_d, 1, 1)

        gl_th.addWidget(QLabel("Thời gian va chạm TTC đỏ (s):"), 1, 2)
        self.spin_cfg_danger_ttc = QDoubleSpinBox()
        self.spin_cfg_danger_ttc.setRange(0.3, 5.0)
        self.spin_cfg_danger_ttc.setSingleStep(0.1)
        self.spin_cfg_danger_ttc.setValue(self.danger_ttc)
        gl_th.addWidget(self.spin_cfg_danger_ttc, 1, 3)
        a_layout.addWidget(grp_th)

        btn_action_row = QHBoxLayout()
        btn_action_row.setSpacing(12)
        btn_action_row.addStretch()

        self.btn_reset_cfg = QPushButton("Khôi phục mặc định")
        self.btn_reset_cfg.setStyleSheet("padding: 8px 16px; font-weight: 600; background-color: #2A313A; color: #CBD5E1; border: 1px solid #3E4856; border-radius: 4px;")
        self.btn_reset_cfg.clicked.connect(self._reset_default_settings)
        btn_action_row.addWidget(self.btn_reset_cfg)

        self.btn_save_cfg = QPushButton("Lưu cấu hình an toàn")
        self.btn_save_cfg.setStyleSheet("padding: 8px 20px; font-weight: 700; background-color: #10B981; color: #FFFFFF; border: 1px solid #059669; border-radius: 4px;")
        self.btn_save_cfg.clicked.connect(self._save_admin_settings)
        btn_action_row.addWidget(self.btn_save_cfg)

        a_layout.addLayout(btn_action_row)
        a_layout.addStretch()

        layout.addWidget(self.tab_settings_admin)

        outer = QVBoxLayout(parent_widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        scroll.setWidget(content)

    # ================= 3. ĐIỀU KHIỂN & LUỒNG DỮ LIỆU THỜI GIAN THỰC =================
    def _init_workers(self):
        is_sim = self.check_sim.isChecked()
        cam_flip = bool(config_manager.get("flip_camera_horizontal", False))
        self.camera_worker = CameraWorker(source=0, flip_horizontal=cam_flip, target_width=1280, target_height=720, target_fps=30)
        self.camera_worker.frame_ready.connect(self._on_camera_frame_captured)

        # Bộ nhận diện đối tượng YOLOv8n (ONNX Runtime)
        model_path = str(config_manager.get("detector_model_path", "models/yolov8n.onnx"))
        conf_th = float(config_manager.get("detector_conf_threshold", 0.50))
        iou_th = float(config_manager.get("detector_iou_threshold", 0.45))
        self.detector_worker = DetectorWorker(model_path=model_path, conf_thresh=conf_th, iou_thresh=iou_th)
        self.detector_worker.detections_ready.connect(self._on_detections_ready)

        # Bộ máy Sensor Fusion kết hợp Radar & Camera
        self.fusion_engine = FusionEngine(
            hfov_deg=float(config_manager.get("camera_hfov_deg", 65.0)),
            offset_x_m=float(config_manager.get("offset_x_m", 0.0)),
            offset_y_m=float(config_manager.get("offset_y_m", 0.0)),
            invert_radar_x=bool(config_manager.get("invert_radar_x", True))
        )

        self.radar_worker = RadarWorker(is_simulation=is_sim)
        self.radar_worker.targets_ready.connect(self._on_radar_targets_ready)
        self.radar_worker.raw_status_ready.connect(self._on_raw_status_ready)
        self.radar_worker.status_changed.connect(self._on_radar_status_changed)

        # Luồng phát lại Video thật + Radar CSV đồng bộ cho Chế độ mô phỏng
        self.sim_player = SimulationPlayer()
        self.sim_player.frame_ready.connect(self._on_camera_frame_captured)
        self.sim_player.targets_ready.connect(self._on_radar_targets_ready)
        self.sim_player.raw_status_ready.connect(self._on_raw_status_ready)
        self.sim_player.status_changed.connect(self._on_sim_status_changed)

    def _get_bg_points_count(self) -> int:
        if hasattr(self, "radar_worker") and hasattr(self.radar_worker, "pipeline"):
            return self.radar_worker.pipeline.background.get_points_count()
        try:
            from radar_parser import BackgroundModel
            return BackgroundModel().get_points_count()
        except Exception:
            return 0

    def _on_raw_status_ready(self, raw_status_list: list):
        """Cập nhật bảng gỡ lỗi 3 slot thô của Radar (Bước E) - làm mượt tần suất ~5 Hz để dễ đọc"""
        if not hasattr(self, "radar_debug_table") or not self.radar_debug_group.isVisible():
            return
        now = time.monotonic()
        if now - self._last_debug_table_t < 0.20:
            return
        self._last_debug_table_t = now
        for row_idx in range(3):
            if row_idx < len(raw_status_list):
                entry = raw_status_list[row_idx]
                t = entry["target"]
                st = entry["status"]
                it_name = QTableWidgetItem(f"Đối tượng {t.target_id}")
                it_name.setToolTip(f"Mục tiêu bám vết: Đối tượng {t.target_id}")
                self.radar_debug_table.setItem(row_idx, 0, it_name)
                
                it_x = QTableWidgetItem(f"{t.x_m:+.2f}")
                it_x.setToolTip(f"Tọa độ X: {t.x_m:+.2f} m")
                self.radar_debug_table.setItem(row_idx, 1, it_x)
                
                it_y = QTableWidgetItem(f"{t.y_m:.2f}")
                it_y.setToolTip(f"Tọa độ Y (cự ly tiến): {t.y_m:.2f} m")
                self.radar_debug_table.setItem(row_idx, 2, it_y)
                
                it_v = QTableWidgetItem(f"{t.speed_kmh:+.1f}")
                it_v.setToolTip(f"Vận tốc Doppler: {t.speed_kmh:+.1f} km/h")
                self.radar_debug_table.setItem(row_idx, 3, it_v)
                
                st_item = QTableWidgetItem(st)
                st_item.setToolTip(f"Trạng thái lọc: {st}")
                if st == "được giữ":
                    st_item.setForeground(QColor("#2ECC71"))
                elif st == "trùng nền":
                    st_item.setForeground(QColor("#94A3B8"))
                else:
                    st_item.setForeground(QColor("#F39C12"))
                self.radar_debug_table.setItem(row_idx, 4, st_item)
            else:
                it_slot = QTableWidgetItem(f"Đối tượng {row_idx+1}")
                it_slot.setToolTip(f"Kênh Radar #{row_idx+1} (Chưa phát hiện)")
                self.radar_debug_table.setItem(row_idx, 0, it_slot)
                self.radar_debug_table.setItem(row_idx, 1, QTableWidgetItem("--"))
                self.radar_debug_table.setItem(row_idx, 2, QTableWidgetItem("--"))
                self.radar_debug_table.setItem(row_idx, 3, QTableWidgetItem("--"))
                st_item = QTableWidgetItem("trống")
                st_item.setForeground(QColor("#64748B"))
                self.radar_debug_table.setItem(row_idx, 4, st_item)

    def _on_radar_status_changed(self, message: str, ok: bool):
        if hasattr(self, "radar_conn_label"):
            color = "#2ECC71" if ok else "#64748B"
            if "Ngừng kết nối" in message or "Lỗi" in message or "Không tìm thấy" in message:
                color = "#E74C3C" if not ok else "#2ECC71"
            bg_cnt = self._get_bg_points_count()
            bg_suffix = f" | Nền: {bg_cnt} điểm" if ok else ""
            full_msg = f"{message}{bg_suffix}"
            self.radar_conn_label.setToolTip(f"Trạng thái Radar: {full_msg}")
            
            # Hiển thị gọn trên thanh Header với chấm màu kỹ thuật đồng nhất
            if ok and "COM" in message:
                port_part = message.split("|")[0].replace("Đã kết nối", "").replace("(", "").replace(")", "").strip()
                disp_msg = f"<font color='{color}'>●</font> Radar: {port_part}"
            elif ok:
                disp_msg = f"<font color='{color}'>●</font> Radar: Đã kết nối"
            elif "Chờ" in message or "đang dừng" in message.lower():
                disp_msg = f"<font color='{color}'>●</font> Radar: Chờ kết nối"
            else:
                disp_msg = f"<font color='{color}'>●</font> Radar: Mất kết nối"

            self.radar_conn_label.setText(disp_msg)
            chip_style = (
                "background-color: #161A1F; border: 1px solid #2A313A; border-radius: 4px; "
                "padding: 3px 8px; font-size: 11px; font-weight: 600; color: #E2E8F0;"
            )
            self.radar_conn_label.setStyleSheet(chip_style)

    def _set_camera_idle_placeholder(self):
        self.camera_view.setText(
            "<div style='text-align: center; padding: 24px;'>"
            "<div style='font-size: 34px; color: #475569; margin-bottom: 8px;'>📷</div>"
            "<div style='font-size: 14px; font-weight: 700; color: #CBD5E1;'>Camera chưa kích hoạt</div>"
            "<div style='font-size: 12px; color: #64748B; margin-top: 4px;'>Nhấn \"Bắt đầu giám sát\" để truyền nhận dữ liệu hình ảnh trực tiếp</div>"
            "</div>"
        )
        self.camera_view.setStyleSheet("background-color: #161A1F; border: none; border-radius: 4px;")

    def _refresh_ports(self):
        self.combo_ports.clear()
        ports = get_available_ports()
        if ports:
            self.combo_ports.addItems(ports)
            for i, p in enumerate(ports):
                if "COM5" in p or "CP210" in p or "Silicon" in p:
                    self.combo_ports.setCurrentIndex(i)
                    break
        else:
            self.combo_ports.addItem("Không tìm thấy COM")

    def _refresh_cameras(self):
        self.combo_camera.clear()
        cams = get_available_cameras()
        self.combo_camera.addItems(cams)
        for i, c in enumerate(cams):
            if "Iriun" in c or "1" in c:
                self.combo_camera.setCurrentIndex(i)
                break

    def _resolve_captures_dir(self) -> str:
        """Tìm thư mục captures tương thích cả chạy .py lẫn PyInstaller .exe (ở gốc hoặc dist/)"""
        candidates = [
            CAPTURES_DIR,
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "captures"),
            os.path.abspath(os.path.join(os.path.dirname(CAPTURES_DIR), "..", "captures")),
        ]
        for c in candidates:
            if os.path.isdir(os.path.join(c, "nexar_samples")) or os.path.isdir(os.path.join(c, "scenario")):
                return c
        return CAPTURES_DIR

    def _refresh_sim_scenarios(self):
        """Nạp danh sách video mô phỏng thực tế (Nexar & kịch bản mặc định)"""
        if not hasattr(self, "combo_sim_scenario"):
            return
        self.combo_sim_scenario.clear()
        captures_dir = self._resolve_captures_dir()

        # 1. Đọc danh sách video Nexar đã tải
        nexar_root = os.path.join(captures_dir, "nexar_samples", "train")
        scene_vi = {
            "Urban": "Đô thị", "Highway": "Cao tốc", "Sub-urban": "Ngoại thành",
            "Rural": "Nông thôn", "Industrial": "KCN", "Nature": "Đường đồi",
        }
        weather_vi = {"Clear": "Quang", "Rain": "Mưa", "Cloudy": "Âm u", "Snow": "Tuyết"}
        light_vi = {"Normal": "Ngày", "Dark": "Đêm", "Twilight": "Chạng vạng", "Bright": "Nắng gắt"}

        for sub, tag in (("positive", "Sự cố"), ("negative", "Bình thường")):
            sub_dir = os.path.join(nexar_root, sub)
            if not os.path.isdir(sub_dir):
                continue
            meta_map = {}
            meta_csv = os.path.join(sub_dir, "metadata.csv")
            if os.path.exists(meta_csv):
                try:
                    with open(meta_csv, "r", encoding="utf-8") as f:
                        for row in csv.DictReader(f):
                            meta_map[row.get("file_name", "")] = row
                except Exception:
                    pass

            for fname in sorted(os.listdir(sub_dir)):
                if not fname.lower().endswith((".mp4", ".avi")):
                    continue
                vpath = os.path.join(sub_dir, fname)
                cpath = os.path.splitext(vpath)[0] + ".csv"
                info = meta_map.get(fname, {})
                l_txt = light_vi.get(info.get("light_conditions", ""), "")
                w_txt = weather_vi.get(info.get("weather", ""), "")
                s_txt = scene_vi.get(info.get("scene", ""), "")
                desc_parts = [p for p in (tag, s_txt, w_txt, l_txt) if p]
                label = f"[{' · '.join(desc_parts)}] {fname}"

                alert_start = 0.0
                if sub == "positive" and info.get("time_of_alert"):
                    try:
                        alert_start = max(0.0, float(info["time_of_alert"]) - 5.0)
                    except Exception:
                        alert_start = 0.0

                self.combo_sim_scenario.addItem(label, {
                    "video": vpath,
                    "csv": cpath if os.path.exists(cpath) else "",
                    "alert_start": alert_start,
                })

        # 2. Kịch bản hình hộp mặc định (nếu có)
        scen_vid = os.path.join(captures_dir, "scenario", "scenario_video.mp4")
        scen_csv = os.path.join(captures_dir, "scenario", "scenario_radar.csv")
        if os.path.exists(scen_vid):
            self.combo_sim_scenario.addItem("[Mặc định · Hình hộp 2D] scenario_video.mp4", {
                "video": scen_vid,
                "csv": scen_csv if os.path.exists(scen_csv) else "",
                "alert_start": 0.0,
            })

        # 3. Fallback tổng hợp hình hộp tự động không cần tệp
        self.combo_sim_scenario.addItem("[Tự động] Mô phỏng hình hộp 2D (Không cần tệp)", {
            "video": "",
            "csv": "",
            "alert_start": 0.0,
        })

    def _browse_sim_video(self):
        """Cho phép người dùng chọn bất kỳ tệp video (.mp4/.avi) nào để chạy mô phỏng"""
        start_dir = self._resolve_captures_dir()
        vpath, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn tệp Video cho Chế độ Mô phỏng",
            start_dir if os.path.isdir(start_dir) else "",
            "Tệp Video (*.mp4 *.avi *.mkv);;Tất cả tệp (*.*)",
        )
        if not vpath:
            return

        cpath = os.path.splitext(vpath)[0] + ".csv"
        if not os.path.exists(cpath):
            cpath = ""
        label = f"[Tệp tự chọn] {os.path.basename(vpath)}" + (" (+CSV)" if cpath else " (chỉ Video + YOLO)")
        self.combo_sim_scenario.insertItem(0, label, {
            "video": vpath,
            "csv": cpath,
            "alert_start": 0.0,
        })
        self.combo_sim_scenario.setCurrentIndex(0)

    def _on_sim_status_changed(self, msg: str, ok: bool):
        if hasattr(self, "status_bar_msg"):
            self.status_bar_msg.setText(msg)

    def _toggle_simulation_mode(self):
        sim = self.check_sim.isChecked()
        self.camera_worker.set_simulation(sim)
        self.radar_worker.set_simulation(sim)
        if hasattr(self, "sim_controls_box"):
            self.sim_controls_box.setEnabled(sim)
        if hasattr(self, "sim_banner"):
            self.sim_banner.setVisible(sim)
        for w in (self.combo_ports, self.btn_refresh_ports, self.combo_baud, self.combo_camera, self.btn_refresh_cams):
            w.setEnabled(not sim)

    def _toggle_invert_x(self):
        inv = self.check_invert_x.isChecked()
        self.radar_canvas.set_invert_x(inv)
        if hasattr(self, "fusion_engine"):
            self.fusion_engine.invert_radar_x = inv

    def _toggle_monitoring(self):
        """Bật hoặc dừng giám sát hệ thống qua nút bấm duy nhất của Người vận hành"""
        is_running = False
        if hasattr(self, 'camera_worker') and self.camera_worker.isRunning():
            is_running = True
        elif hasattr(self, 'sim_player') and self.sim_player.isRunning():
            is_running = True

        if is_running:
            self._stop_system()
        else:
            self._start_system()

    def _start_system(self):
        port = self.combo_ports.currentText()
        baud = int(self.combo_baud.currentText())
        sim = self.check_sim.isChecked()

        self._telemetry_ema.clear()
        self._last_telemetry_render_t = 0.0
        self._last_telemetry_sev = None
        self._last_telemetry_tid = None
        self._last_frame_render_t = 0.0
        self._prev_flow_gray = None
        self._detections_fresh = False
        if hasattr(self, "detector_worker"):
            self.detector_worker.reset_tracker()

        if sim:
            scen = self.combo_sim_scenario.currentData() if hasattr(self, "combo_sim_scenario") else None
            if scen is None:
                scen = {"video": "", "csv": "", "alert_start": 0.0}
            start_sec = scen.get("alert_start", 0.0) if (hasattr(self, "check_sim_jump") and self.check_sim_jump.isChecked()) else 0.0
            self.sim_player.set_paths(scen.get("video", ""), scen.get("csv", ""), start_sec=start_sec)
            self.detector_worker.start()
            self.sim_player.start()
            if hasattr(self, "combo_sim_scenario"):
                self.combo_sim_scenario.setEnabled(False)
                self.btn_browse_sim.setEnabled(False)
                self.check_sim_jump.setEnabled(False)
        else:
            cam_text = self.combo_camera.currentText()
            cam_idx = 0
            try:
                parts = cam_text.split(":")
                cam_idx = int(parts[0].replace("Camera", "").strip())
            except Exception:
                cam_idx = 1 if "Iriun" in cam_text else 0

            self.radar_worker.port = port
            self.radar_worker.baudrate = baud
            self.radar_worker.set_simulation(False)

            self.camera_worker.set_source(cam_idx)
            self.camera_worker.set_flip(self.check_cfg_flip_cam.isChecked() if hasattr(self, 'check_cfg_flip_cam') else False)
            self.camera_worker.set_simulation(False)

            self.camera_worker.start()
            self.detector_worker.start()
            self.radar_worker.start()

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.check_sim.setEnabled(False)

        if hasattr(self, 'btn_monitor_toggle'):
            self.btn_monitor_toggle.setText("Dừng giám sát")
            self.btn_monitor_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #EF4444;
                    color: #FFFFFF;
                    font-size: 14px;
                    font-weight: 700;
                    border-radius: 6px;
                    padding: 8px 16px;
                    border: 1px solid #DC2626;
                }
                QPushButton:hover {
                    background-color: #DC2626;
                }
                QPushButton:pressed {
                    background-color: #B91C1C;
                }
            """)
        if hasattr(self, 'lbl_system_status'):
            self.lbl_system_status.setText("Trạng thái: <font color='#34D399'><b>Đang giám sát</b></font>")
        if hasattr(self, 'cam_conn_label'):
            self.cam_conn_label.setText("<font color='#2ECC71'>●</font> Camera: Hoạt động")
        if hasattr(self, 'status_banner'):
            self.status_banner.setText("AN TOÀN")
            self.status_banner.setStyleSheet("background-color: #064E3B; color: #34D399; border: 1px solid #059669; border-radius: 4px; padding: 5px 16px; font-weight: 800; font-size: 14px;")
            self.status_banner.setToolTip("Trạng thái: An toàn - Không có nguy cơ")
        if hasattr(self, 'status_reason_label'):
            self.status_reason_label.setText("Đang giám sát - Không phát hiện nguy cơ va chạm trong vùng quét")
        if hasattr(self, 'radar_canvas'):
            self.radar_canvas.set_monitoring(True)

    def _stop_system(self):
        if hasattr(self, 'sim_player') and self.sim_player.isRunning():
            self.sim_player.stop()
        if hasattr(self, 'camera_worker') and self.camera_worker.isRunning():
            self.camera_worker.stop()
        if hasattr(self, 'detector_worker') and self.detector_worker.isRunning():
            self.detector_worker.stop()
        if hasattr(self, 'radar_worker') and self.radar_worker.isRunning():
            self.radar_worker.stop()

        if hasattr(self, "combo_sim_scenario"):
            self.combo_sim_scenario.setEnabled(True)
            self.btn_browse_sim.setEnabled(True)
            self.check_sim_jump.setEnabled(True)

        self.current_targets = []
        self.smoothed_targets = []
        self.current_detections = []
        self.current_fused_objects = []
        self.current_frame = None
        self._telemetry_ema.clear()
        self._last_telemetry_render_t = 0.0
        self._last_telemetry_sev = None
        self._last_telemetry_tid = None
        self._last_frame_render_t = 0.0
        self._prev_flow_gray = None
        self._detections_fresh = False
        if hasattr(self, "detector_worker"):
            self.detector_worker.reset_tracker()
        if hasattr(self, "radar_canvas"):
            self.radar_canvas.update_targets([])

        if hasattr(self, 'incident_aggregator'):
            comp = self.incident_aggregator.finish_active_incident()
            if comp and hasattr(self, 'async_logger'):
                d = comp.to_dict()
                if hasattr(self, 'user_session') and self.user_session:
                    d['user_id'] = self.user_session.get('id')
                    d['username'] = self.user_session.get('username')
                self.async_logger.queue_save_incident(d)

        if hasattr(self, 'sound_worker'):
            self.sound_worker.set_severity(AlertSeverity.SAFE)

        if hasattr(self, 'flash_timer') and self.flash_timer.isActive():
            self.flash_timer.stop()
            self._reset_camera_border()

        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.check_sim.setEnabled(True)

        if hasattr(self, 'btn_monitor_toggle'):
            self.btn_monitor_toggle.setText("Bắt đầu giám sát")
            self.btn_monitor_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #10B981;
                    color: #FFFFFF;
                    font-size: 14px;
                    font-weight: 700;
                    border-radius: 6px;
                    padding: 8px 16px;
                    border: 1px solid #059669;
                }
                QPushButton:hover {
                    background-color: #059669;
                }
                QPushButton:pressed {
                    background-color: #047857;
                }
            """)
        if hasattr(self, 'lbl_system_status'):
            self.lbl_system_status.setText("Trạng thái: <font color='#94A3B8'><b>Đã dừng</b></font>")
        if hasattr(self, 'cam_conn_label'):
            self.cam_conn_label.setText("<font color='#64748B'>●</font> Camera: Đã dừng")
        if hasattr(self, 'status_reason_label'):
            self.status_reason_label.setText("Hệ thống đã dừng giám sát")
        if hasattr(self, 'status_banner'):
            self.status_banner.setText("CHƯA GIÁM SÁT")
            self.status_banner.setStyleSheet("background-color: #334155; color: #94A3B8; border: 1px solid #475569; border-radius: 4px; padding: 5px 16px; font-weight: 800; font-size: 14px;")
            self.status_banner.setToolTip("Trạng thái: Hệ thống đang dừng - Chưa kích hoạt cảm biến")
        if hasattr(self, 'radar_canvas'):
            self.radar_canvas.set_monitoring(False)

        self._update_telemetry_default()
        self._set_camera_idle_placeholder()

    def _smooth_target_for_ui(self, target: RadarTarget) -> RadarTarget:
        """Làm mượt thông số hiển thị (khoảng cách, vận tốc, TTC) để số KPI ổn định, dễ đọc."""
        tid = target.target_id
        alpha_d = 0.30
        alpha_v = 0.22
        st = self._telemetry_ema.get(tid)
        if st is None:
            st = {
                "x": float(target.x_m),
                "y": float(target.y_m),
                "speed": float(target.speed_kmh),
                "closing": float(getattr(target, "closing_speed_mps", 0.0)),
            }
            self._telemetry_ema[tid] = st
        else:
            st["x"] = alpha_d * float(target.x_m) + (1.0 - alpha_d) * st["x"]
            st["y"] = alpha_d * float(target.y_m) + (1.0 - alpha_d) * st["y"]
            st["speed"] = alpha_v * float(target.speed_kmh) + (1.0 - alpha_v) * st["speed"]
            raw_c = float(getattr(target, "closing_speed_mps", -target.speed_kmh / 3.6))
            st["closing"] = alpha_v * raw_c + (1.0 - alpha_v) * st["closing"]

        min_closing = float(config_manager.get("min_closing_speed_mps", 0.3))
        eff_dist = math.hypot(st["x"], st["y"])
        eff_ttc = (eff_dist / st["closing"]) if (st["closing"] > min_closing and eff_dist > 0.0) else None
        if eff_ttc is not None and eff_ttc > 20.0:
            eff_ttc = None

        return RadarTarget(
            target_id=tid,
            x_m=st["x"],
            y_m=st["y"],
            speed_kmh=st["speed"],
            valid=target.valid,
            resolution=target.resolution,
            closing_speed_mps=st["closing"],
            ttc_sec=eff_ttc,
            age_frames=target.age_frames,
            min_closing_speed_mps=min_closing,
        )

    def _on_radar_targets_ready(self, targets):
        self.current_targets = targets
        self._evaluate_collision_risk()

        # Dọn cache EMA cho các ID đã rời khỏi vùng quan sát
        active_ids = {t.target_id for t in targets if t.valid}
        for stale_id in [k for k in self._telemetry_ema.keys() if k not in active_ids]:
            del self._telemetry_ema[stale_id]

        smooth_targets = [self._smooth_target_for_ui(t) if t.valid else t for t in targets]
        if self.current_frame is not None and self.current_detections:
            smooth_targets = self.fusion_engine.deduplicate_radar_by_detections(
                smooth_targets, self.current_detections, self.current_frame.shape[:2]
            )
        self.smoothed_targets = smooth_targets
        self.radar_canvas.update_targets(smooth_targets)

        # Tìm mục tiêu ưu tiên hiển thị (đang chọn hoặc gần nhất)
        display_target = None
        is_nearest = True
        if self.selected_target_id is not None:
            updated = next((t for t in smooth_targets if t.target_id == self.selected_target_id and t.valid), None)
            if updated:
                self.selected_target = updated
                display_target = updated
                is_nearest = False
            else:
                self.selected_target = None
                self.selected_target_id = None
                self.radar_canvas.set_selected_target_id(None)

        if display_target is None:
            valid_smooth = [t for t in smooth_targets if t.valid]
            if valid_smooth:
                display_target = min(valid_smooth, key=lambda t: t.distance_m)

        # Làm mới bảng số KPI ở nhịp ~5.5 Hz (180ms) trừ khi đổi mục tiêu / đổi mức cảnh báo tức thì
        now = time.monotonic()
        curr_sev = self.alert_state_machine.evaluate_target(display_target) if display_target else AlertSeverity.SAFE
        curr_tid = display_target.target_id if display_target else None
        must_refresh = (
            curr_sev != self._last_telemetry_sev
            or curr_tid != self._last_telemetry_tid
            or (now - self._last_telemetry_render_t) >= 0.18
        )
        if must_refresh:
            self._last_telemetry_render_t = now
            self._last_telemetry_sev = curr_sev
            self._last_telemetry_tid = curr_tid
            if display_target is not None:
                self._update_telemetry_label(display_target, is_nearest=is_nearest, smooth_list=smooth_targets)
            else:
                self._update_telemetry_default()

        if self.current_frame is None and hasattr(self, 'obstacle_count_label'):
            valid_cnt = len([t for t in targets if t.valid])
            self.obstacle_count_label.setText(f"Đối tượng trong vùng quét: {valid_cnt}")

    def _on_radar_target_clicked(self, target):
        if target:
            self.selected_target = target
            self.selected_target_id = target.target_id
            self.radar_canvas.set_selected_target_id(self.selected_target_id)
            self._update_telemetry_label(target, is_nearest=False)
            det_name = "Chưa nhận dạng (Camera)"
            for obj in getattr(self, "current_fused_objects", []):
                if obj.id == target.target_id and obj.detection:
                    det_name = obj.detection.class_name
                    break
            self._open_target_detail_popup(target, det_name)
        else:
            self.selected_target = None
            self.selected_target_id = None
            self.radar_canvas.set_selected_target_id(None)
            self._update_telemetry_default()

    def _update_telemetry_default(self):
        """Mặc định luôn hiển thị thông số đối tượng GẦN NHẤT"""
        valid_targets = [t for t in self.current_targets if t.valid] if hasattr(self, 'current_targets') else []
        if valid_targets:
            nearest = min(valid_targets, key=lambda t: t.distance_m)
            self._update_telemetry_label(nearest, is_nearest=True)
        else:
            self.lbl_telemetry.setText(
                "<div style='font-family: \"Segoe UI\"; padding: 2px;'>"
                "<div style='margin-bottom: 8px;'>"
                "<span style='color: #CBD5E1; font-size: 12px; font-weight: 600;'>Trạng thái:</span> &nbsp;"
                "<span style='background-color: #1E293B; color: #94A3B8; border: 1px solid #475569; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 600;'>Chưa có mục tiêu</span>"
                "</div>"
                "<table width='100%' style='border-collapse: collapse; margin-top: 4px;'>"
                "<tr>"
                "<td width='32%' style='padding-right: 4px; vertical-align: top;'>"
                "<div style='color: #CBD5E1; font-size: 11px; font-weight: 600;'>Khoảng cách</div>"
                "<div style='font-size: 28px; font-weight: 800; color: #64748B; line-height: 1.2; margin-top: 2px;'>--<span style='font-size: 12px; font-weight: 400; color: #64748B;'> m</span></div>"
                "</td>"
                "<td width='34%' style='padding-right: 4px; vertical-align: top;'>"
                "<div style='color: #CBD5E1; font-size: 11px; font-weight: 600;'>Tốc độ</div>"
                "<div style='font-size: 24px; font-weight: 700; color: #64748B; line-height: 1.2; margin-top: 4px; white-space: nowrap;'>--<span style='font-size: 12px; font-weight: 400; color: #64748B;'> km/h</span></div>"
                "</td>"
                "<td width='34%' style='vertical-align: top;'>"
                "<div style='color: #CBD5E1; font-size: 11px; font-weight: 600;'>Thời gian va chạm</div>"
                "<div style='font-size: 24px; font-weight: 700; color: #64748B; line-height: 1.2; margin-top: 4px; white-space: nowrap;'>--<span style='font-size: 12px; font-weight: 400; color: #64748B;'> s</span></div>"
                "</td>"
                "</tr>"
                "</table>"
                "<div style='margin-top: 8px; color: #94A3B8; font-size: 11px; font-weight: 500;'>"
                "Không có đối tượng trong vùng quan sát"
                "</div>"
                "</div>"
            )

    def _update_telemetry_label(self, t, is_nearest=False, smooth_list=None):
        """Hiển thị thông số dạng thẻ KPI công nghiệp chuẩn Người vận hành"""
        target_sev = self.alert_state_machine.evaluate_target(t)
        if target_sev == AlertSeverity.DANGER:
            threat_color = "#E74C3C"
            threat_text = "Báo động"
        elif target_sev == AlertSeverity.WARN:
            threat_color = "#F39C12"
            threat_text = "Cảnh báo"
        else:
            threat_color = "#2ECC71"
            threat_text = "An toàn"

        dist_val = f"{t.distance_m:.2f}"
        closing_v = getattr(t, 'closing_speed_mps', 0.0)
        from config import format_operator_speed
        speed_status = format_operator_speed(t.speed_kmh, closing_v)

        if t.ttc_sec is not None and t.ttc_sec > 0.0:
            ttc_val = f"{t.ttc_sec:.1f}"
            ttc_unit = "s"
            ttc_font_size = "24px"
            ttc_margin = "2px"
            ttc_color = threat_color
        else:
            ttc_val = "Không lại gần"
            ttc_unit = ""
            ttc_font_size = "13px"
            ttc_margin = "8px"
            ttc_color = "#94A3B8"

        target_title = f"Đối tượng {t.target_id} (Gần nhất)" if is_nearest else f"Đối tượng {t.target_id}"

        # Danh sách nhỏ cho mọi đối tượng hợp lệ
        source_targets = smooth_list if smooth_list is not None else getattr(self, "current_targets", [])
        valid_targets = [tgt for tgt in source_targets if getattr(tgt, "valid", True)]
        sub_list_html = ""
        if valid_targets:
            sub_list_html = "<div style='margin-top: 8px; padding-top: 6px; border-top: 1px solid #2A313A; font-size: 11px;'>"
            for vt in valid_targets[:3]:
                vt_sev = self.alert_state_machine.evaluate_target(vt)
                if vt_sev == AlertSeverity.DANGER:
                    vt_c = "#E74C3C"
                    vt_short_sev = "Báo động"
                elif vt_sev == AlertSeverity.WARN:
                    vt_c = "#F39C12"
                    vt_short_sev = "Cảnh báo"
                else:
                    vt_c = "#2ECC71"
                    vt_short_sev = "An toàn"
                vt_spd = format_operator_speed(vt.speed_kmh, getattr(vt, "closing_speed_mps", None))
                sub_list_html += (
                    f"<div style='margin-bottom: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>"
                    f"<b style='color: #F1F5F9;'>Đối tượng {vt.target_id}:</b> {vt.distance_m:.2f}m &nbsp;|&nbsp; {vt_spd} &nbsp;|&nbsp; "
                    f"<span style='color: {vt_c}; font-weight: 600;'>{vt_short_sev}</span>"
                    f"</div>"
                )
            sub_list_html += "</div>"

        self.lbl_telemetry.setText(
            f"<div style='font-family: \"Segoe UI\"; padding: 2px;'>"
            f"<div style='margin-bottom: 8px;'>"
            f"<span style='color: #CBD5E1; font-size: 12px; font-weight: 600;'>{target_title}</span> &nbsp;"
            f"<span style='background-color: #161A1F; color: {threat_color}; border: 1px solid {threat_color}; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 600;'>{threat_text}</span>"
            f"</div>"
            f"<table width='100%' style='border-collapse: collapse; margin-top: 4px;'>"
            f"<tr>"
            f"<td width='32%' style='padding-right: 4px; vertical-align: top;'>"
            f"<div style='color: #CBD5E1; font-size: 11px; font-weight: 600;'>Khoảng cách</div>"
            f"<div style='font-size: 28px; font-weight: 800; color: {threat_color}; line-height: 1.2; margin-top: 2px;'>{dist_val}<span style='font-size: 12px; font-weight: 500; color: #94A3B8;'> m</span></div>"
            f"</td>"
            f"<td width='34%' style='padding-right: 4px; vertical-align: top;'>"
            f"<div style='color: #CBD5E1; font-size: 11px; font-weight: 600;'>Tốc độ</div>"
            f"<div style='font-size: 20px; font-weight: 700; color: #FFFFFF; line-height: 1.2; margin-top: 4px; white-space: nowrap;'>{speed_status}</div>"
            f"</td>"
            f"<td width='34%' style='vertical-align: top;'>"
            f"<div style='color: #CBD5E1; font-size: 11px; font-weight: 600;'>Thời gian va chạm</div>"
            f"<div style='font-size: {ttc_font_size}; font-weight: 700; color: {ttc_color}; line-height: 1.2; margin-top: {ttc_margin}; white-space: nowrap;'>{ttc_val}<span style='font-size: 12px; font-weight: 400; color: #94A3B8;'> {ttc_unit}</span></div>"
            f"</td>"
            f"</tr>"
            f"</table>"
            f"{sub_list_html}"
            f"</div>"
        )

    def _toggle_sound_mute(self):
        """Bật / tắt âm thanh cảnh báo độc lập không ảnh hưởng hình ảnh (Mục 2.2)"""
        if hasattr(self, "sound_worker"):
            muted = self.sound_worker.toggle_muted()
            chip_style = (
                "background-color: #161A1F; border: 1px solid #2A313A; border-radius: 4px; "
                "padding: 3px 8px; font-size: 11px; font-weight: 600; color: #E2E8F0;"
            )
            if muted:
                self.btn_mute.setText("● Âm thanh: Tắt")
                self.btn_mute.setStyleSheet(
                    "background-color: #161A1F; border: 1px solid #2A313A; border-radius: 4px; "
                    "padding: 3px 8px; font-size: 11px; font-weight: 600; color: #64748B;"
                )
            else:
                self.btn_mute.setText("● Âm thanh: Bật")
                self.btn_mute.setStyleSheet(
                    "background-color: #161A1F; border: 1px solid #2A313A; border-radius: 4px; "
                    "padding: 3px 8px; font-size: 11px; font-weight: 600; color: #2ECC71;"
                )

    def _test_siren_sound(self):
        """Thử còi báo động khẩn cấp trong 1.2 giây để người vận hành kiểm tra loa"""
        if hasattr(self, 'sound_worker'):
            orig_sev = getattr(self.sound_worker, '_current_severity', AlertSeverity.SAFE)
            orig_mute = getattr(self.sound_worker, '_is_muted', False)
            self.sound_worker._is_muted = False
            self.sound_worker.set_severity(AlertSeverity.DANGER)
            
            def _restore_sound():
                if hasattr(self, 'sound_worker'):
                    self.sound_worker.set_severity(orig_sev)
                    self.sound_worker._is_muted = orig_mute
            
            QTimer.singleShot(1200, _restore_sound)

    def _create_severity_badge_widget(self, severity_str: str) -> QWidget:
        """Tạo widget huy hiệu (Badge) nền màu chữ trắng kèm icon cho cột Mức độ"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl = QLabel()
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        sev_lower = str(severity_str).lower()
        if "đỏ" in sev_lower or "nguy cơ" in sev_lower or "danger" in sev_lower or "báo động" in sev_lower:
            lbl.setText("🚨 Báo động")
            lbl.setStyleSheet("""
                background-color: #991B1B;
                color: #FFFFFF;
                font-weight: 700;
                font-size: 11px;
                border-radius: 4px;
                padding: 3px 8px;
            """)
        elif "cảnh báo" in sev_lower or "vàng" in sev_lower or "warn" in sev_lower:
            lbl.setText("⚠️ Cảnh báo")
            lbl.setStyleSheet("""
                background-color: #D97706;
                color: #FFFFFF;
                font-weight: 700;
                font-size: 11px;
                border-radius: 4px;
                padding: 3px 8px;
            """)
        else:
            lbl.setText("✅ An toàn")
            lbl.setStyleSheet("""
                background-color: #059669;
                color: #FFFFFF;
                font-weight: 700;
                font-size: 11px;
                border-radius: 4px;
                padding: 3px 8px;
            """)
        
        layout.addWidget(lbl)
        return container

    def _toggle_danger_flash(self):
        """Nhấp nháy viền cảnh báo quanh khung camera (Đỏ cho DANGER, Vàng cho WARN - Giai đoạn 8)"""
        self.flash_state = not self.flash_state
        if hasattr(self, "cam_group"):
            color = getattr(self, "current_flash_color", "#E74C3C")
            if self.flash_state:
                self.cam_group.setStyleSheet(f"QGroupBox {{ border: 2px solid {color}; border-radius: 4px; margin-top: 6px; padding-top: 10px; }} QGroupBox::title {{ color: {color}; subcontrol-origin: margin; left: 8px; }}")
            else:
                self.cam_group.setStyleSheet(f"QGroupBox {{ border: 2px solid transparent; border-radius: 4px; margin-top: 6px; padding-top: 10px; }} QGroupBox::title {{ color: {color}; subcontrol-origin: margin; left: 8px; }}")

    def _reset_camera_border(self):
        if hasattr(self, "cam_group"):
            self.cam_group.setStyleSheet("")

    def _evaluate_collision_risk(self):
        """Đánh giá trạng thái an toàn qua AlertStateMachine và gom sự cố IncidentAggregator (Giai đoạn 2 & 8)"""
        alert_state, primary_target, latency_ms = self.alert_state_machine.evaluate(
            self.current_targets, timestamp=time.monotonic()
        )

        if alert_state == AlertSeverity.DANGER:
            self.status_banner.setText("BÁO ĐỘNG")
            self.status_banner.setToolTip("Mức độ: Nguy cơ va chạm cao - Báo động khẩn cấp")
            self.status_banner.setStyleSheet("background-color: #7F1D1D; color: #FCA5A5; border: 1px solid #DC2626; border-radius: 4px; padding: 4px 16px; font-weight: 700; font-size: 13px;")
            if hasattr(self, 'status_reason_label'):
                if primary_target:
                    ttc_part = f", TTC = {primary_target.ttc_sec:.1f} s" if (primary_target.ttc_sec is not None and primary_target.ttc_sec > 0) else ""
                    self.status_reason_label.setText(
                        f"Đối tượng {primary_target.target_id} cách {primary_target.distance_m:.2f} m, nhỏ hơn ngưỡng nguy cơ {self.danger_dist:.1f} m{ttc_part}"
                    )
                else:
                    self.status_reason_label.setText(f"Có đối tượng trong cự ly nguy cơ (< {self.danger_dist:.1f} m)")
            self.current_flash_color = "#E74C3C"
            if not self.flash_timer.isActive():
                self.flash_timer.start(300)
        elif alert_state == AlertSeverity.WARN:
            self.status_banner.setText("CẢNH BÁO")
            self.status_banner.setToolTip("Mức độ: Có đối tượng trong vùng cảnh báo")
            self.status_banner.setStyleSheet("background-color: #78350F; color: #FCD34D; border: 1px solid #D97706; border-radius: 4px; padding: 4px 16px; font-weight: 700; font-size: 13px;")
            if hasattr(self, 'status_reason_label'):
                if primary_target:
                    self.status_reason_label.setText(
                        f"Đối tượng {primary_target.target_id} cách {primary_target.distance_m:.2f} m, nhỏ hơn ngưỡng an toàn {self.warn_dist:.1f} m"
                    )
                else:
                    self.status_reason_label.setText(f"Có đối tượng trong vùng cảnh báo (< {self.warn_dist:.1f} m)")
            self.current_flash_color = "#F39C12"
            if not self.flash_timer.isActive():
                self.flash_timer.start(500)
        else:
            self.status_banner.setText("AN TOÀN")
            self.status_banner.setToolTip("Mức độ: An toàn - Không có nguy cơ")
            self.status_banner.setStyleSheet("background-color: #064E3B; color: #34D399; border: 1px solid #059669; border-radius: 4px; padding: 4px 16px; font-weight: 700; font-size: 13px;")
            if hasattr(self, 'status_reason_label'):
                self.status_reason_label.setText("Không phát hiện nguy cơ va chạm trong vùng quét cảm biến")
            if self.flash_timer.isActive():
                self.flash_timer.stop()
                self._reset_camera_border()

        # Phát âm thanh trên luồng riêng
        if hasattr(self, "sound_worker"):
            self.sound_worker.set_severity(alert_state)

        # Cập nhật gom sự cố (kèm loại đối tượng thực tế từ Camera/Fusion & ghi chú nếu vào vùng mù)
        detected_obj_type = "Chưa xác định"
        if hasattr(self, "current_fused_objects") and self.current_fused_objects:
            for fo in self.current_fused_objects:
                if fo.detection:
                    detected_obj_type = fo.detection.class_name
                    break
        elif hasattr(self, "current_detections") and self.current_detections:
            detected_obj_type = self.current_detections[0].class_name

        inc_note = "mục tiêu vào vùng mù" if getattr(self.alert_state_machine, "blind_zone_active", False) else ""
        should_snapshot, completed_incident = self.incident_aggregator.update(
            current_state=alert_state,
            targets=self.current_targets,
            timestamp=time.monotonic(),
            object_type=detected_obj_type,
            notes=inc_note
        )

        # Chụp MỘT ảnh hiện trường khi sự cố lên mức ĐỎ lần đầu (bất đồng bộ qua hàng đợi nền)
        if should_snapshot and self.current_frame is not None and primary_target is not None:
            target_info = {
                "distance_m": primary_target.distance_m,
                "speed_kmh": primary_target.speed_kmh,
                "closing_speed_mps": getattr(primary_target, "closing_speed_mps", 0.0),
                "ttc_sec": primary_target.ttc_sec,
            }
            inc_id = getattr(self.incident_aggregator.current_incident, "id", int(time.time()))
            img_path = self.async_logger.queue_snapshot_capture(self.current_frame, inc_id, target_info)
            if self.incident_aggregator.current_incident:
                self.incident_aggregator.current_incident.image_path = img_path

        # Đẩy sự cố đã kết thúc vào hàng đợi ghi CSDL (luồng nền, không chặn giao diện)
        if completed_incident is not None:
            d = completed_incident.to_dict()
            if hasattr(self, 'user_session') and self.user_session:
                d['user_id'] = self.user_session.get('id')
                d['username'] = self.user_session.get('username')
            self.async_logger.queue_save_incident(d)

    def _on_new_incident_saved(self, inc_dict: dict):
        """
        Nhận signal từ AsyncLogWorker khi đã lưu xong vào CSDL:
        Cập nhật ĐÚNG dòng mới (insertRow(0)), phân quyền hiển thị theo từng tài khoản.
        """
        # Multi-user isolation: Nếu tài khoản là operator, chỉ cập nhật sự cố do chính tài khoản tạo
        if hasattr(self, 'user_session') and self.user_session:
            curr_u = self.user_session.get('username')
            curr_role = self.user_session.get('role', 'operator')
            inc_user = inc_dict.get('username', '')
            if curr_role != 'admin' and inc_user and curr_u and inc_user != curr_u:
                return

        time_part = str(inc_dict.get("start_time", "")).split(" ")[-1]
        sev_txt = inc_dict.get("max_severity", "")
        sev_color = QColor("#E74C3C" if "Nguy cơ" in sev_txt else "#F39C12")

        closing_v = inc_dict.get("closing_speed_mps", 0.0)
        speed_raw = inc_dict.get("speed_kmh_raw", inc_dict.get("max_speed_kmh", 0.0))
        from config import format_operator_speed
        speed_display = format_operator_speed(speed_raw, closing_v)

        # 1. Cập nhật bảng Sự cố gần nhất trên Dashboard (hot_log_table) - 4 cột, tối đa 3 dòng
        self.hot_log_table.insertRow(0)
        
        dt_display = format_short_datetime(inc_dict.get('start_time', time_part))
        it_time = QTableWidgetItem(dt_display)
        it_time.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        it_time.setToolTip(f"Thời gian: {inc_dict.get('start_time', dt_display)}")
        self.hot_log_table.setItem(0, 0, it_time)
        
        it_obj = QTableWidgetItem(str(inc_dict.get("object_type", "Chưa xác định")))
        it_obj.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        it_obj.setToolTip(f"Đối tượng: {inc_dict.get('object_type', 'Chưa xác định')}")
        self.hot_log_table.setItem(0, 1, it_obj)
        
        it_dist = QTableWidgetItem(f"{inc_dict.get('min_distance_m', 0.0):.1f} m")
        it_dist.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        it_dist.setToolTip(f"Khoảng cách gần nhất: {inc_dict.get('min_distance_m', 0.0):.2f} m")
        self.hot_log_table.setItem(0, 2, it_dist)
        
        self.hot_log_table.setCellWidget(0, 3, self._create_severity_badge_widget(sev_txt))
        if self.hot_log_table.rowCount() > 3:
            self.hot_log_table.removeRow(3)

        # 2. Cập nhật bảng Nhật ký sự cố (audit_table) - 8 cột có phân tách User
        self.audit_table.insertRow(0)
        u_name_display = inc_dict.get("username", "admin")
        rec_row = (
            inc_dict.get("id", ""),
            inc_dict.get("start_time", ""),
            inc_dict.get("end_time", ""),
            inc_dict.get("object_type", "Phương tiện"),
            inc_dict.get("min_distance_m", 0.0),
            inc_dict.get("max_speed_kmh", 0.0),
            inc_dict.get("min_ttc_sec", None),
            sev_txt,
            inc_dict.get("image_path", ""),
            inc_dict.get("notes", ""),
            closing_v,
            speed_raw,
            inc_dict.get("user_id", None),
            u_name_display,
        )
        if hasattr(self, "audit_records"):
            self.audit_records.insert(0, rec_row)

        a_id = QTableWidgetItem(f"#{inc_dict.get('id', '')}")
        a_id.setToolTip(f"Mã sự cố: #{inc_dict.get('id', '')}")
        self.audit_table.setItem(0, 0, a_id)

        a_u = QTableWidgetItem(f"👤 {u_name_display}")
        a_u.setToolTip(f"Tài khoản ghi nhận: {u_name_display}")
        a_u.setForeground(QColor("#38BDF8"))
        self.audit_table.setItem(0, 1, a_u)
        
        a_time = QTableWidgetItem(str(inc_dict.get("start_time", "")))
        a_time.setToolTip(f"Thời gian bắt đầu: {inc_dict.get('start_time', '')}")
        self.audit_table.setItem(0, 2, a_time)
        
        a_obj = QTableWidgetItem(str(inc_dict.get("object_type", "Phương tiện")))
        a_obj.setToolTip(f"Đối tượng: {inc_dict.get('object_type', 'Phương tiện')}")
        self.audit_table.setItem(0, 3, a_obj)
        
        a_dist = QTableWidgetItem(f"{inc_dict.get('min_distance_m', 0.0):.2f}")
        a_dist.setToolTip(f"Cự ly gần nhất: {inc_dict.get('min_distance_m', 0.0):.2f} m")
        self.audit_table.setItem(0, 4, a_dist)
        
        a_spd = QTableWidgetItem(speed_display)
        a_spd.setToolTip(f"Tốc độ: {speed_display}")
        self.audit_table.setItem(0, 5, a_spd)
        
        ttc_val = inc_dict.get("min_ttc_sec", None)
        ttc_str = f"{ttc_val:.2f}" if (ttc_val is not None and ttc_val > 0.0) else "Không lại gần"
        a_ttc = QTableWidgetItem(ttc_str)
        a_ttc.setToolTip(f"Thời gian va chạm (TTC): {ttc_str}")
        self.audit_table.setItem(0, 6, a_ttc)
        
        it_audit_sev = QTableWidgetItem(sev_txt)
        it_audit_sev.setToolTip(f"Mức độ: {sev_txt}")
        it_audit_sev.setForeground(sev_color)
        self.audit_table.setItem(0, 7, it_audit_sev)

        if self.audit_table.rowCount() > 100:
            self.audit_table.removeRow(100)

    def _propagate_detections_lk(self, prev_gray: np.ndarray, curr_gray: np.ndarray, detections: list, frame_shape) -> list:
        """Nội suy dịch chuyển hộp Bounding Box giữa các khung hình YOLO bằng Sparse Lucas-Kanade Optical Flow (~0.4ms)."""
        if not detections or prev_gray is None or curr_gray is None:
            return detections
        orig_h, orig_w = float(frame_shape[0]), float(frame_shape[1])
        fh, fw = float(curr_gray.shape[0]), float(curr_gray.shape[1])
        sx = fw / max(1.0, orig_w)
        sy = fh / max(1.0, orig_h)

        pts = []
        box_slices = []
        for det in detections:
            x1, y1, x2, y2 = det.x1 * sx, det.y1 * sy, det.x2 * sx, det.y2 * sy
            cx, cy = (x1 + x2) * 0.5, (y1 + y2) * 0.5
            dx_q, dy_q = (x2 - x1) * 0.25, (y2 - y1) * 0.25
            cand = [
                (cx, cy),
                (cx - dx_q, cy - dy_q),
                (cx + dx_q, cy - dy_q),
                (cx - dx_q, cy + dy_q),
                (cx + dx_q, cy + dy_q),
            ]
            start = len(pts)
            for px, py in cand:
                if 1.0 <= px < fw - 1.0 and 1.0 <= py < fh - 1.0:
                    pts.append([[px, py]])
            box_slices.append((start, len(pts)))

        if not pts:
            return detections

        p0 = np.array(pts, dtype=np.float32)
        try:
            p1, st, _ = cv2.calcOpticalFlowPyrLK(
                prev_gray, curr_gray, p0, None,
                winSize=(15, 15), maxLevel=2,
                criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03),
            )
        except Exception:
            return detections

        if p1 is None or st is None:
            return detections

        shifted = []
        inv_sx = 1.0 / max(1e-6, sx)
        inv_sy = 1.0 / max(1e-6, sy)
        for det, (s_idx, e_idx) in zip(detections, box_slices):
            dxs = []
            dys = []
            for k in range(s_idx, e_idx):
                if st[k, 0] == 1:
                    dxs.append(float(p1[k, 0, 0] - p0[k, 0, 0]) * inv_sx)
                    dys.append(float(p1[k, 0, 1] - p0[k, 0, 1]) * inv_sy)
            if dxs:
                dx = max(-24.0, min(24.0, float(np.median(dxs))))
                dy = max(-18.0, min(18.0, float(np.median(dys))))
            else:
                dx, dy = 0.0, 0.0

            nx1 = max(0.0, min(orig_w - 4.0, det.x1 + dx))
            ny1 = max(0.0, min(orig_h - 4.0, det.y1 + dy))
            nx2 = max(nx1 + 4.0, min(orig_w, det.x2 + dx))
            ny2 = max(ny1 + 4.0, min(orig_h, det.y2 + dy))
            shifted.append(Detection(
                x1=nx1, y1=ny1, x2=nx2, y2=ny2,
                confidence=det.confidence,
                class_id=det.class_id,
                class_name=det.class_name,
                track_id=getattr(det, "track_id", -1),
            ))
        return shifted

    def _on_camera_frame_captured(self, frame):
        """Thu nhận khung hình từ CameraWorker / SimulationPlayer (30 FPS + Optical Flow giữa các nhịp YOLO)"""
        self.current_frame = frame
        if hasattr(self, 'detector_worker') and self.detector_worker.isRunning():
            self.detector_worker.push_frame(frame)
            try:
                small = cv2.resize(frame, (320, 180), interpolation=cv2.INTER_NEAREST)
                curr_gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            except Exception:
                curr_gray = None

            if (
                curr_gray is not None
                and self._prev_flow_gray is not None
                and self.current_detections
                and not self._detections_fresh
            ):
                self.current_detections = self._propagate_detections_lk(
                    self._prev_flow_gray, curr_gray, self.current_detections, frame.shape[:2]
                )

            self._detections_fresh = False
            self._prev_flow_gray = curr_gray
            self._render_fused_frame(frame, self.current_detections)
        else:
            self._display_raw_frame(frame)

    def _on_frame_ready(self, frame):
        """Bí danh tương thích ngược cho CameraWorker"""
        self._on_camera_frame_captured(frame)

    def _render_fused_frame(self, frame, detections):
        """Thực hiện Sensor Fusion và vẽ khung hình lên Camera View với độ mượt tối đa"""
        now = time.time()
        self._last_frame_render_t = now
        self.fps_counter += 1
        if now - self.last_fps_time >= 1.0:
            self.current_fps = self.fps_counter / (now - self.last_fps_time)
            self.fps_counter = 0
            self.last_fps_time = now
            self.fps_label.setText(f"FPS: {self.current_fps:.1f}")

        radar_for_fusion = self.smoothed_targets if self.smoothed_targets else self.current_targets
        fused_objects = self.fusion_engine.fuse(
            radar_targets=radar_for_fusion,
            detections=detections,
            frame_shape=frame.shape[:2],
            warn_dist_m=self.warn_dist,
            warn_ttc_s=self.warn_ttc,
            danger_dist_m=self.danger_dist,
            danger_ttc_s=self.danger_ttc
        )
        self.current_fused_objects = fused_objects

        obs_count = len([f for f in fused_objects if f.is_associated or f.radar_target is not None])
        if hasattr(self, 'obstacle_count_label'):
            self.obstacle_count_label.setText(f"Đối tượng trong vùng quét: {obs_count}")

        annotated = draw_fused_annotations(frame, fused_objects, selected_target_id=self.selected_target_id)

        h, w, ch = annotated.shape
        bytes_per_line = ch * w
        rgb_frame = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        qt_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
        self.camera_view.setPixmap(QPixmap.fromImage(qt_img).scaled(
            self.camera_view.width(), self.camera_view.height(),
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        ))

    def _on_detections_ready(self, detections, frame, latency_ms):
        """
        Cập nhật danh sách Bounding Box đã được DetectionTracker (Kalman + Hungarian) làm mượt từ DetectorWorker.
        """
        self.current_detections = detections
        self._detections_fresh = True
        # Fallback: nếu luồng gọi trực tiếp ngoài vòng phát 30 FPS hoặc đã quá 80ms chưa vẽ
        if time.time() - self._last_frame_render_t >= 0.08:
            self._render_fused_frame(frame, detections)

    def _display_raw_frame(self, frame):
        """Hiển thị khung hình thô khi detector đang tải hoặc tắt"""
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        qt_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
        self.camera_view.setPixmap(QPixmap.fromImage(qt_img).scaled(
            self.camera_view.width(), self.camera_view.height(),
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        ))

    def eventFilter(self, source, event):
        """Xử lý sự kiện nhấp chuột Camera View & Bắt trạng thái Caps Lock ô Mật khẩu"""
        if hasattr(self, 'login_pwd') and source == self.login_pwd:
            if event.type() in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease, QEvent.Type.FocusIn):
                self._check_caps_lock()
            elif event.type() == QEvent.Type.FocusOut:
                if hasattr(self, 'lbl_caps_warn'):
                    self.lbl_caps_warn.hide()

        if hasattr(self, 'camera_view') and source == self.camera_view and event.type() == QEvent.Type.MouseButtonPress:
            self._on_camera_view_clicked(event.position())
            return True
        return super().eventFilter(source, event)

    def _check_caps_lock(self):
        """Kiểm tra phím Caps Lock qua Win32 API GetKeyState"""
        try:
            if sys.platform == "win32":
                caps_on = bool(ctypes.windll.user32.GetKeyState(0x14) & 1)
                if hasattr(self, 'lbl_caps_warn'):
                    self.lbl_caps_warn.setVisible(caps_on)
        except Exception:
            pass

    def _on_camera_view_clicked(self, pos):
        """Tìm mục tiêu tương ứng với vị trí nhấp chuột trên khung hình Camera"""
        if not self.current_fused_objects or self.current_frame is None:
            return

        lbl_w = self.camera_view.width()
        lbl_h = self.camera_view.height()
        img_h, img_w = self.current_frame.shape[:2]

        scale = min(lbl_w / img_w, lbl_h / img_h)
        disp_w = img_w * scale
        disp_h = img_h * scale
        off_x = (lbl_w - disp_w) / 2.0
        off_y = (lbl_h - disp_h) / 2.0

        clk_x = (pos.x() - off_x) / scale
        clk_y = (pos.y() - off_y) / scale

        matched = None
        for obj in self.current_fused_objects:
            if obj.detection is not None:
                d = obj.detection
                if d.x1 <= clk_x <= d.x2 and d.y1 <= clk_y <= d.y2:
                    matched = obj
                    break

        if matched:
            self.selected_target_id = matched.id
            self.selected_target = matched.radar_target
            self.radar_canvas.set_selected_target_id(self.selected_target_id)
            if matched.radar_target is not None:
                self._update_telemetry_label(matched.radar_target, is_nearest=False)
                det_cls = matched.detection.class_name if matched.detection else "Chưa xác định"
                self._open_target_detail_popup(matched.radar_target, det_cls)
        else:
            self.selected_target_id = None
            self.selected_target = None
            self.radar_canvas.set_selected_target_id(None)
            self._update_telemetry_default()

    def _open_user_management(self):
        """Mở cửa sổ Quản lý Người dùng (Chỉ Quản trị viên - Giai đoạn 7)"""
        if self.user_session and self.user_session.get("role") == "admin":
            dlg = UserManagementDialog(self.user_session, self)
            dlg.exec()
        else:
            show_info_dialog(self, "Từ chối truy cập", "Chỉ Quản trị viên mới có quyền mở Quản lý Người dùng.")

    def _open_target_detail_popup(self, target, det_name="Chưa xác định"):
        """Mở cửa sổ nhỏ hiển thị thông số chi tiết của mục tiêu được nhấp (Giai đoạn 8)"""
        dlg = TargetDetailDialog(target, det_name, self)
        dlg.exec()

    def _reset_selection_to_nearest(self):
        """Đặt lại chọn lựa về mục tiêu gần nhất (Giai đoạn 5)"""
        self.selected_target_id = None
        self.selected_target = None
        self.radar_canvas.set_selected_target_id(None)
        self._update_telemetry_default()

    def _open_selected_target_detail(self):
        """Mở cửa sổ thông số chi tiết cho mục tiêu đang được chọn hoặc mục tiêu gần nhất"""
        if self.selected_target:
            det_name = "Chưa xác định"
            for obj in getattr(self, "current_fused_objects", []):
                if obj.id == self.selected_target.target_id and obj.detection:
                    det_name = obj.detection.class_name
                    break
            self._open_target_detail_popup(self.selected_target, det_name)
        else:
            valid_targets = [t for t in self.current_targets if t.valid] if hasattr(self, 'current_targets') else []
            if valid_targets:
                nearest = min(valid_targets, key=lambda t: t.distance_m)
                self._open_target_detail_popup(nearest, "Đối tượng gần nhất")
            else:
                show_info_dialog(self, "Thông báo", "Hiện tại không có đối tượng nào trong vùng quan sát.")

    def _start_bg_calibration(self):
        """Bắt đầu phiên hiệu chuẩn lọc nền tĩnh 5 giây (Giai đoạn 1 & 5)"""
        if not hasattr(self, "radar_worker") or not self.radar_worker.isRunning():
            show_info_dialog(self, "Chưa bật Radar", "Vui lòng nhấn 'Bắt đầu' để kết nối Radar trước khi hiệu chuẩn nền.")
            return
        if hasattr(self.radar_worker, "pipeline"):
            self.radar_worker.pipeline.start_background_calibration(5.0)
            self.btn_calib_bg.setEnabled(False)
            self.calib_prog_bar.setValue(0)
            self.calib_timer.start(100)

    def _clear_background(self):
        """Xóa toàn bộ dữ liệu nền tĩnh đã học (Giai đoạn 1 & 5)"""
        if hasattr(self, "radar_worker") and hasattr(self.radar_worker, "pipeline"):
            self.radar_worker.pipeline.clear_background()
            self.calib_prog_bar.setValue(0)
            self.lbl_calib_info.setText("Điểm nền đang áp dụng: 0 điểm (đã xóa toàn bộ dữ liệu nền).")
            show_info_dialog(self, "Đã xóa nền", "Dữ liệu nền tĩnh đã được dọn sạch trong bộ nhớ và background.json.")

    def _on_calib_tick(self):
        """Đồng hồ cập nhật thanh tiến trình hiệu chuẩn nền 5 giây"""
        if not hasattr(self, "radar_worker") or not hasattr(self.radar_worker, "pipeline"):
            self.calib_timer.stop()
            self.btn_calib_bg.setEnabled(True)
            return
        bg = self.radar_worker.pipeline.background
        prog = bg.calibration_progress
        self.calib_prog_bar.setValue(int(prog * 100))
        cells = bg.get_points_count()
        self.lbl_calib_info.setText(f"Đang thu thập nền tĩnh: {int(prog * 100)}%...")
        if prog >= 1.0 or not bg.is_calibrating:
            self.calib_timer.stop()
            self.btn_calib_bg.setEnabled(True)
            self.calib_prog_bar.setValue(100)
            self.lbl_calib_info.setText(f"Điểm nền đang áp dụng: {cells} điểm (đã lưu vào background.json).")

    def _reset_default_settings(self):
        """Khôi phục cấu hình hệ thống về mặc định chuẩn (Giai đoạn 5)"""
        if show_confirm_dialog(self, "Khôi phục Mặc định", "Bạn có chắc muốn khôi phục toàn bộ tham số về mặc định ban đầu?", "Khôi phục", "Hủy", is_danger=True):
            config_manager.reset_defaults()
            self._load_dynamic_settings()
            cfg = config_manager.data
            self.spin_cfg_warn_d.setValue(float(cfg.get("warn_distance_m", 3.5)))
            self.spin_cfg_warn_ttc.setValue(float(cfg.get("warn_ttc_sec", 3.0)))
            self.spin_cfg_danger_d.setValue(float(cfg.get("danger_distance_m", 1.8)))
            self.spin_cfg_danger_ttc.setValue(float(cfg.get("danger_ttc_sec", 1.8)))
            self.spin_cfg_hfov.setValue(float(cfg.get("camera_hfov_deg", 65.0)))
            self.spin_cfg_ox.setValue(float(cfg.get("offset_x_m", 0.0)))
            self.spin_cfg_oy.setValue(float(cfg.get("offset_y_m", 0.0)))
            self.check_cfg_invert_radar_x.setChecked(bool(cfg.get("invert_radar_x", True)))
            self.check_cfg_flip_cam.setChecked(bool(cfg.get("flip_camera_horizontal", False)))
            is_dbg = bool(cfg.get("debug_radar_mode", False))
            self.check_cfg_debug_radar.setChecked(is_dbg)
            if hasattr(self, "radar_debug_group"):
                self.radar_debug_group.setVisible(is_dbg)
            show_info_dialog(self, "Thành công", "Đã khôi phục toàn bộ cài đặt về mặc định chuẩn.")

    def _refresh_incident_table(self):
        raw_filter = self.combo_filter_sev.currentText() if hasattr(self, 'combo_filter_sev') else "Tất cả"
        if "Nguy cơ" in raw_filter or "ĐỎ" in raw_filter:
            sev_filter = "ĐỎ"
        elif "cảnh báo" in raw_filter or "VÀNG" in raw_filter:
            sev_filter = "VÀNG"
        else:
            sev_filter = "TẤT CẢ"

        search_txt = self.txt_search.text().strip() if hasattr(self, 'txt_search') else ""
        date_filter = ""
        if hasattr(self, 'check_filter_date') and self.check_filter_date.isChecked():
            date_filter = self.date_filter_edit.date().toString("yyyy-MM-dd")

        # Lọc theo người dùng (Mỗi tài khoản lưu trữ và xem sự cố của riêng mình)
        user_id_filter = None
        username_filter = None
        if hasattr(self, 'user_session') and self.user_session:
            cur_role = self.user_session.get('role', 'operator')
            if cur_role != 'admin':
                # Người vận hành chỉ xem sự cố của chính mình
                user_id_filter = self.user_session.get('id')
                username_filter = self.user_session.get('username')
            else:
                # Quản trị viên có thể xem tất cả hoặc lọc theo tài khoản chọn trên combo_user_filter
                if hasattr(self, 'combo_user_filter'):
                    sel_u = self.combo_user_filter.currentData()
                    if sel_u is not None:
                        user_id_filter = sel_u

        try:
            records = database.get_filtered_incidents(
                severity_filter=sev_filter, date_filter=date_filter, search_text=search_txt, limit=100,
                user_id=user_id_filter, username=username_filter
            )
        except Exception as e:
            print("Lỗi đọc incidents:", e)
            return

        self.audit_table.setRowCount(len(records))
        self.audit_records = records
        for row, r in enumerate(records):
            rec_id = r[0]
            s_time = r[1]
            e_time = r[2]
            obj_type = r[3]
            min_d = r[4]
            max_v = r[5]
            min_ttc = r[6]
            severity = r[7]
            img_path = r[8] if len(r) > 8 else ""
            notes = r[9] if len(r) > 9 else ""
            closing_v = r[10] if len(r) > 10 else None
            raw_v = r[11] if len(r) > 11 else max_v
            r_user = r[13] if len(r) > 13 and r[13] else (self.user_session.get('username', 'admin') if hasattr(self, 'user_session') else 'admin')
            
            from config import format_operator_speed
            speed_display = format_operator_speed(raw_v, closing_v)

            it_aid = QTableWidgetItem(f"#{rec_id}")
            it_aid.setToolTip(f"Mã sự cố: #{rec_id}")
            self.audit_table.setItem(row, 0, it_aid)

            it_auser = QTableWidgetItem(f"👤 {r_user}")
            it_auser.setToolTip(f"Tài khoản ghi nhận: {r_user}")
            it_auser.setForeground(QColor("#38BDF8"))
            self.audit_table.setItem(row, 1, it_auser)
            
            it_atime = QTableWidgetItem(str(s_time))
            it_atime.setToolTip(f"Thời gian: {s_time}")
            self.audit_table.setItem(row, 2, it_atime)
            
            it_aobj = QTableWidgetItem(str(obj_type))
            it_aobj.setToolTip(f"Đối tượng: {obj_type}")
            self.audit_table.setItem(row, 3, it_aobj)
            
            it_adist = QTableWidgetItem(f"{min_d:.2f}")
            it_adist.setToolTip(f"Cự ly gần nhất: {min_d:.2f} m")
            self.audit_table.setItem(row, 4, it_adist)
            
            it_aspd = QTableWidgetItem(speed_display)
            it_aspd.setToolTip(f"Tốc độ: {speed_display}")
            self.audit_table.setItem(row, 5, it_aspd)
            
            ttc_str = f"{min_ttc:.2f}" if (min_ttc is not None and min_ttc > 0.0) else "Không lại gần"
            it_attc = QTableWidgetItem(ttc_str)
            it_attc.setToolTip(f"Thời gian va chạm (TTC): {ttc_str}")
            self.audit_table.setItem(row, 6, it_attc)
            
            sev_item = QTableWidgetItem(str(severity))
            sev_item.setToolTip(f"Mức độ: {severity}")
            if "ĐỎ" in severity or "DANGER" in severity or "Nguy cơ" in severity:
                sev_item.setForeground(QColor("#E74C3C"))
            else:
                sev_item.setForeground(QColor("#F39C12"))
            self.audit_table.setItem(row, 7, sev_item)

        hot_recs = records[:3]
        self.hot_log_table.setRowCount(len(hot_recs))
        for row, r in enumerate(hot_recs):
            rec_id, s_time, e_time, obj_type, min_d, max_v, min_ttc, severity, img_path = r[:9]
            dt_display = format_short_datetime(s_time)
            
            it_htime = QTableWidgetItem(dt_display)
            it_htime.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_htime.setToolTip(f"Thời gian: {s_time}")
            self.hot_log_table.setItem(row, 0, it_htime)
            
            it_hobj = QTableWidgetItem(str(obj_type))
            it_hobj.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            it_hobj.setToolTip(f"Đối tượng: {obj_type}")
            self.hot_log_table.setItem(row, 1, it_hobj)
            
            it_hdist = QTableWidgetItem(f"{min_d:.1f} m")
            it_hdist.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            it_hdist.setToolTip(f"Khoảng cách gần nhất: {min_d:.2f} m")
            self.hot_log_table.setItem(row, 2, it_hdist)
            
            self.hot_log_table.setCellWidget(row, 3, self._create_severity_badge_widget(severity))

    def _on_audit_selection_changed(self):
        selected_rows = self.audit_table.selectedItems()
        if not selected_rows:
            return
        row = self.audit_table.currentRow()
        if hasattr(self, 'audit_records') and 0 <= row < len(self.audit_records):
            rec = self.audit_records[row]
            img_path = rec[8] if len(rec) >= 9 else rec[7]
            if img_path and os.path.exists(img_path):
                pix = QPixmap(img_path)
                self.lbl_preview_img.setPixmap(pix.scaled(
                    self.lbl_preview_img.width(), self.lbl_preview_img.height(), 
                    Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                ))
                self.btn_open_full_img.setEnabled(True)
            else:
                self.lbl_preview_img.setText("Không có tệp ảnh cho sự cố này.")
                self.btn_open_full_img.setEnabled(False)

    def _on_audit_double_clicked(self, item):
        self._open_current_selected_dialog()

    def _open_current_selected_dialog(self):
        row = self.audit_table.currentRow()
        if hasattr(self, 'audit_records') and 0 <= row < len(self.audit_records):
            rec = self.audit_records[row]
            dlg = SnapshotViewerDialog(rec, self)
            dlg.exec()

    def _export_csv(self):
        """Xuất báo cáo sự cố ra Excel (.xlsx) hoặc CSV (utf-8-sig) - Giai đoạn 8"""
        default_name = f"Bao_Cao_Su_Co_Giao_Thong_{time.strftime('%Y%m%d_%H%M%S')}.xlsx"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Xuất Báo cáo Sự cố (Excel / CSV)", default_name,
            "Tệp Excel (*.xlsx);;Tệp CSV UTF-8 (*.csv)"
        )
        if not save_path:
            return

        sev_filter = self.combo_filter_sev.currentText()
        date_filter = ""
        if hasattr(self, 'check_filter_date') and self.check_filter_date.isChecked():
            date_filter = self.date_filter_edit.date().toString("yyyy-MM-dd")

        user_id_filter = None
        username_filter = None
        if hasattr(self, 'user_session') and self.user_session:
            cur_role = self.user_session.get('role', 'operator')
            if cur_role != 'admin':
                user_id_filter = self.user_session.get('id')
                username_filter = self.user_session.get('username')
            elif hasattr(self, 'combo_user_filter') and self.combo_user_filter.currentData() is not None:
                user_id_filter = self.combo_user_filter.currentData()

        count = database.export_incidents(
            save_path, severity_filter=sev_filter, date_filter=date_filter,
            user_id=user_id_filter, username=username_filter
        )
        show_info_dialog(self, "Xuất Báo Cáo Thành Công", f"Đã xuất thành công {count} bản ghi sự cố vào tệp:<br><b>{save_path}</b>")

    def _save_admin_settings(self):
        """Lưu toàn diện cấu hình ngưỡng, quang học và cảm biến xuống config.json"""
        is_dbg = self.check_cfg_debug_radar.isChecked()
        new_settings = {
            "warn_distance_m": self.spin_cfg_warn_d.value(),
            "warn_ttc_sec": self.spin_cfg_warn_ttc.value(),
            "danger_distance_m": self.spin_cfg_danger_d.value(),
            "danger_ttc_sec": self.spin_cfg_danger_ttc.value(),
            "camera_hfov_deg": self.spin_cfg_hfov.value(),
            "offset_x_m": self.spin_cfg_ox.value(),
            "offset_y_m": self.spin_cfg_oy.value(),
            "invert_radar_x": self.check_cfg_invert_radar_x.isChecked(),
            "flip_camera_horizontal": self.check_cfg_flip_cam.isChecked(),
            "debug_radar_mode": is_dbg
        }
        config_manager.update(new_settings)
        self._load_dynamic_settings()
        if hasattr(self, "radar_debug_group"):
            self.radar_debug_group.setVisible(is_dbg)
        if hasattr(self, "fusion_engine"):
            self.fusion_engine.update_calibration(
                self.spin_cfg_hfov.value(),
                self.spin_cfg_ox.value(),
                self.spin_cfg_oy.value(),
                self.check_cfg_invert_radar_x.isChecked()
            )
        if hasattr(self, "camera_worker"):
            self.camera_worker.set_flip(self.check_cfg_flip_cam.isChecked())
        if hasattr(self, "radar_canvas"):
            self.radar_canvas.set_invert_x(self.check_cfg_invert_radar_x.isChecked())
        if hasattr(self, "radar_worker") and hasattr(self.radar_worker, "pipeline"):
            self.radar_worker.pipeline.reload_config()
        if hasattr(self, "alert_state_machine"):
            self.alert_state_machine.reload_config()
        show_info_dialog(self, "Cập nhật Thành Công", "Đã lưu và áp dụng toàn bộ cấu hình mới vào config.json!")

    def _open_change_password(self):
        if self.user_session:
            dlg = ChangePasswordDialog(self.user_session['username'], self)
            dlg.exec()

    def _handle_logout(self):
        if show_confirm_dialog(self, "Xác nhận Đăng xuất", "Bạn có chắc chắn muốn đăng xuất khỏi phiên làm việc hiện tại?", "Đăng xuất", "Hủy bỏ", is_danger=True):
            self._stop_system()
            self.user_session = None
            self.login_pwd.clear()
            if hasattr(self, 'login_err'):
                self.login_err.hide()
            if hasattr(self, 'btn_login'):
                self.btn_login.setEnabled(True)
                self.btn_login.setText("Đăng nhập")
            self.showNormal()
            self.setMinimumSize(420, 520)
            self.setMaximumSize(16777215, 16777215)
            self.resize(460, 580)
            self.stack.setCurrentIndex(0)
            apply_dark_titlebar(self)
            ensure_window_resizable(self)

    def toggle_fullscreen(self):
        """Bật/tắt chế độ toàn màn hình (Fullscreen / F11)"""
        if self.isFullScreen():
            self.showNormal()
            ensure_window_resizable(self)
        else:
            self.showFullScreen()

    def keyPressEvent(self, event):
        """Xử lý phím tắt toàn cục F11 (Fullscreen) và Esc (Thoát Fullscreen)"""
        if event.key() == Qt.Key.Key_F11:
            self.toggle_fullscreen()
            event.accept()
            return
        elif event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            self.toggle_fullscreen()
            event.accept()
            return
        super().keyPressEvent(event)

    def changeEvent(self, event):
        """Duy trì viền kéo giãn khi thay đổi trạng thái cửa sổ"""
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            if not self.isFullScreen():
                ensure_window_resizable(self)

    def closeEvent(self, event):
        """Dừng sạch sẽ toàn bộ luồng phần cứng và công nhân nền trước khi thoát app để chống crash (Giai đoạn 6)"""
        try:
            self._stop_system()
            if hasattr(self, 'async_logger'):
                self.async_logger.stop()
            if hasattr(self, 'sound_worker'):
                self.sound_worker.stop()
            if hasattr(self, 'calib_timer') and self.calib_timer.isActive():
                self.calib_timer.stop()
        except Exception as e:
            try:
                with open(os.path.join(LOGS_DIR, "app.log"), "a", encoding="utf-8") as f:
                    f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Lỗi khi thoát: {e}\n")
            except Exception:
                pass
        event.accept()


def main():
    # Hỗ trợ PyInstaller multiprocessing an toàn
    multiprocessing.freeze_support()

    # Định danh ứng dụng độc lập trên Windows Taskbar để hiển thị đúng icon và không bị lồng tiến trình
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("DUT.23KTMT.GiamSatGiaoThong.1.0")
        except Exception:
            pass

    app = QApplication(sys.argv)
    
    # Nạp font chuẩn Segoe UI hỗ trợ tiếng Việt sắc nét, chống răng cưa
    font = QFont("Segoe UI", 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)
    
    # Áp dụng Dark Mode toàn hệ thống (bao gồm mọi hộp thoại thông báo)
    app.setStyleSheet(DARK_STYLE)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
