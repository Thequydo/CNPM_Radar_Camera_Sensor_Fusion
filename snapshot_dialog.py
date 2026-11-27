# -*- coding: utf-8 -*-
"""
Hộp thoại Xem Ảnh Bằng chứng Sự cố Va chạm (Evidence Viewer)
Chuẩn giao diện HMI Kỹ thuật Công nghiệp (Grafana / Foxglove)
"""

import os
import ctypes
from ctypes import byref, c_int, sizeof
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtGui import QPixmap, QFont, QIcon
from PyQt6.QtCore import Qt

def apply_dark_titlebar(window):
    """Kích hoạt thanh tiêu đề Dark Mode của Windows qua DWM API"""
    try:
        hwnd = int(window.winId())
        val = c_int(1)
        hr = ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, byref(val), sizeof(val))
        if hr != 0:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, byref(val), sizeof(val))
    except Exception:
        pass

class SnapshotViewerDialog(QDialog):
    """Hộp thoại phóng to ảnh chụp hiện trường và thông tin sự cố chi tiết"""
    def __init__(self, record_data, parent=None):
        super().__init__(parent)
        self.record_data = record_data
        self.setWindowTitle(f"Chi tiết bằng chứng sự cố #{record_data[0]}")
        self.resize(800, 620)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_titlebar(self)

        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "radar_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setStyleSheet("""
            QDialog {
                background-color: #161A1F;
                color: #F1F5F9;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #F1F5F9;
                font-size: 12px;
            }
            QFrame#cardFrame {
                background-color: #1E2329;
                border: 1px solid #2A313A;
                border-radius: 4px;
                padding: 10px;
            }
            QPushButton {
                background-color: #1E2329;
                color: #F1F5F9;
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

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # 1. Bảng Thông số
        if len(self.record_data) >= 9:
            rec_id = self.record_data[0]
            ts = self.record_data[1]
            obj_type = self.record_data[3]
            dist = self.record_data[4]
            vel = self.record_data[5]
            ttc = self.record_data[6]
            severity = self.record_data[7]
            img_path = self.record_data[8]
        else:
            rec_id, ts, obj_type, dist, vel, ttc, severity, img_path = self.record_data[:8]

        card = QFrame()
        card.setObjectName("cardFrame")
        card_layout = QHBoxLayout(card)

        col1 = QVBoxLayout()
        col1.addWidget(QLabel(f"<b>Mã sự cố:</b> #{rec_id}"))
        u_name = self.record_data[13] if len(self.record_data) > 13 and self.record_data[13] else "admin"
        col1.addWidget(QLabel(f"<b>Người vận hành:</b> <font color='#38BDF8'>👤 {u_name}</font>"))
        col1.addWidget(QLabel(f"<b>Thời điểm:</b> {ts}"))
        col1.addWidget(QLabel(f"<b>Đối tượng:</b> {obj_type}"))

        col2 = QVBoxLayout()
        col2.addWidget(QLabel(f"<b>Khoảng cách:</b> {dist:.2f} m"))
        closing_v = self.record_data[10] if len(self.record_data) > 10 else None
        raw_v = self.record_data[11] if len(self.record_data) > 11 else vel
        from config import format_speed_status
        speed_display = format_speed_status(raw_v, closing_v)
        col2.addWidget(QLabel(f"<b>Vận tốc:</b> {speed_display}"))
        ttc_text = f"{ttc:.2f} s" if (ttc is not None and ttc > 0.0) else "--"
        col2.addWidget(QLabel(f"<b>Thời gian va chạm (TTC):</b> {ttc_text}"))

        is_danger = ("ĐỎ" in severity or "DANGER" in severity or "Nguy cơ" in severity)
        badge_text = "Nguy cơ va chạm" if is_danger else "Có vật trong vùng cảnh báo"
        badge_color = "#E74C3C" if is_danger else "#F39C12"

        badge = QLabel(badge_text)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        badge.setStyleSheet(f"background-color: #161A1F; color: {badge_color}; border: 1px solid {badge_color}; border-radius: 4px; padding: 10px 16px;")

        card_layout.addLayout(col1)
        card_layout.addLayout(col2)
        card_layout.addWidget(badge)
        layout.addWidget(card)

        # 2. Khung hiển thị Ảnh chụp
        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label.setStyleSheet("background-color: #161A1F; border: 1px solid #2A313A; border-radius: 4px;")
        self.img_label.setMinimumSize(740, 420)

        if img_path and os.path.exists(img_path):
            pix = QPixmap(img_path)
            self.img_label.setPixmap(pix.scaled(740, 420, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.img_label.setText("Không tìm thấy tệp ảnh chụp hiện trường trên ổ đĩa.")
            self.img_label.setStyleSheet("color: #94A3B8; font-size: 14px; font-weight: 600;")

        layout.addWidget(self.img_label)

        # 3. Nút đóng
        btn_box = QHBoxLayout()
        btn_box.setSpacing(12)
        btn_box.addStretch()

        if img_path and os.path.exists(img_path):
            btn_folder = QPushButton("Mở thư mục")
            btn_folder.clicked.connect(lambda: os.startfile(os.path.dirname(img_path)))
            btn_box.addWidget(btn_folder)

        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)
