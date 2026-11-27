# -*- coding: utf-8 -*-
"""
Hộp thoại Cấu hình Hệ thống, Ngưỡng An toàn & Hiệu chuẩn Bù lệch Cảm biến (Admin Only)
Tuân thủ đặc tả SRS: US-02, US-04, US-07, US-11, FR-02, FR-06, FR-07
"""

import os
import ctypes
from ctypes import byref, c_int, sizeof
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, 
    QSpinBox, QSlider, QComboBox, QPushButton, QTabWidget, 
    QWidget, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, pyqtSignal
import database
from radar_parser import get_available_ports
from camera_worker import get_available_cameras

def apply_dark_titlebar(window):
    """Kích hoạt thanh tiêu đề Dark Mode của Windows 10/11 qua DWM API"""
    try:
        hwnd = int(window.winId())
        val = c_int(1)
        hr = ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, byref(val), sizeof(val))
        if hr != 0:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, byref(val), sizeof(val))
    except Exception:
        pass

class SettingsDialog(QDialog):
    """Hộp thoại Cấu hình Toàn diện dành riêng cho Quản trị viên (Admin)"""
    settings_saved = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cấu hình hệ thống (Quản trị viên)")
        self.resize(600, 520)
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
            QTabWidget::pane {
                border: 1px solid #2A313A;
                background: #161A1F;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #1E2329;
                color: #94A3B8;
                padding: 8px 16px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: 600;
                font-size: 12px;
                border: 1px solid #2A313A;
                border-bottom: none;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background: #2B6CB0;
                color: #FFFFFF;
            }
            QGroupBox {
                color: #CBD5E1;
                font-weight: 600;
                border: 1px solid #2A313A;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 14px;
                background-color: #1E2329;
                font-size: 12px;
            }
            QDoubleSpinBox, QSpinBox, QComboBox, QLineEdit {
                background-color: #161A1F;
                color: #FFFFFF;
                border: 1px solid #2A313A;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus, QLineEdit:focus {
                border: 1px solid #2B6CB0;
            }
            QPushButton#btnSave {
                background-color: #2ECC71;
                color: #161A1F;
                font-weight: 700;
                border-radius: 4px;
                padding: 8px 18px;
                font-size: 12px;
                border: none;
            }
            QPushButton#btnSave:hover {
                background-color: #27AE60;
            }
            QPushButton#btnCancel {
                background-color: #1E2329;
                color: #F1F5F9;
                border: 1px solid #2A313A;
                border-radius: 4px;
                padding: 8px 18px;
                font-size: 12px;
            }
            QPushButton#btnCancel:hover {
                background-color: #2A313A;
            }
            QMessageBox {
                background-color: #1E2329;
                border: 1px solid #2A313A;
                border-radius: 4px;
            }
            QMessageBox QLabel {
                color: #F1F5F9;
                font-size: 12px;
            }
            QMessageBox QPushButton {
                background-color: #161A1F;
                color: #F1F5F9;
                border: 1px solid #2A313A;
                border-radius: 4px;
                padding: 6px 18px;
                font-size: 12px;
                font-weight: 600;
            }
        """)

        self._init_ui()
        self._load_current_settings()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        tabs = QTabWidget()

        # TAB 1: NGƯỠNG AN TOÀN & CẢNH BÁO (US-11)
        tab_thresholds = QWidget()
        t1_layout = QVBoxLayout(tab_thresholds)
        t1_layout.setSpacing(12)

        grp_warn = QGroupBox("Mức 1: Cảnh báo Tiềm ẩn (Vàng)")
        gw_layout = QVBoxLayout(grp_warn)
        gw_layout.addWidget(QLabel("Khoảng cách kích hoạt cự ly d (mét):"))
        self.spin_warn_dist = QDoubleSpinBox()
        self.spin_warn_dist.setRange(0.5, 6.0)
        self.spin_warn_dist.setSingleStep(0.1)
        self.spin_warn_dist.setValue(3.5)
        gw_layout.addWidget(self.spin_warn_dist)

        gw_layout.addWidget(QLabel("Thời gian va chạm TTC kích hoạt (giây):"))
        self.spin_warn_ttc = QDoubleSpinBox()
        self.spin_warn_ttc.setRange(0.5, 10.0)
        self.spin_warn_ttc.setSingleStep(0.1)
        self.spin_warn_ttc.setValue(3.0)
        gw_layout.addWidget(self.spin_warn_ttc)
        t1_layout.addWidget(grp_warn)

        grp_danger = QGroupBox("Mức 2: Báo động Nguy hiểm Khẩn cấp (Đỏ)")
        gd_layout = QVBoxLayout(grp_danger)
        gd_layout.addWidget(QLabel("Khoảng cách nguy hiểm d (mét):"))
        self.spin_danger_dist = QDoubleSpinBox()
        self.spin_danger_dist.setRange(0.3, 4.0)
        self.spin_danger_dist.setSingleStep(0.1)
        self.spin_danger_dist.setValue(1.8)
        gd_layout.addWidget(self.spin_danger_dist)

        gd_layout.addWidget(QLabel("Thời gian va chạm TTC khẩn cấp (giây):"))
        self.spin_danger_ttc = QDoubleSpinBox()
        self.spin_danger_ttc.setRange(0.3, 5.0)
        self.spin_danger_ttc.setSingleStep(0.1)
        self.spin_danger_ttc.setValue(1.8)
        gd_layout.addWidget(self.spin_danger_ttc)
        t1_layout.addWidget(grp_danger)
        t1_layout.addStretch()
        tabs.addTab(tab_thresholds, "Ngưỡng Cảnh báo (TTC)")

        # TAB 2: HIỆU CHUẨN BÙ LỆCH CẢM BIẾN (US-07)
        tab_calib = QWidget()
        t2_layout = QVBoxLayout(tab_calib)
        t2_layout.setSpacing(14)

        grp_calib = QGroupBox("Hiệu chuẩn Bù lệch Tọa độ Không gian (Sensor Spatial Calibration)")
        gc_layout = QVBoxLayout(grp_calib)
        gc_layout.addWidget(QLabel(
            "Tinh chỉnh khoảng cách lệch thực tế giữa vị trí gắn Radar và Camera.<br>"
            "Giá trị này dùng để ánh xạ chính xác điểm Radar vào khung hình xe trên Camera:"
        ))

        # Offset X
        gc_layout.addWidget(QLabel("<b>Độ lệch trục ngang Offset X (mét):</b> [-1.0m (trái) đến +1.0m (phải)]"))
        self.spin_offset_x = QDoubleSpinBox()
        self.spin_offset_x.setRange(-1.0, 1.0)
        self.spin_offset_x.setSingleStep(0.05)
        self.spin_offset_x.setValue(0.0)
        gc_layout.addWidget(self.spin_offset_x)

        # Offset Y
        gc_layout.addWidget(QLabel("<b>Độ lệch trục dọc Offset Y (mét):</b> [-1.0m (lùi) đến +1.0m (tiến)]"))
        self.spin_offset_y = QDoubleSpinBox()
        self.spin_offset_y.setRange(-1.0, 1.0)
        self.spin_offset_y.setSingleStep(0.05)
        self.spin_offset_y.setValue(0.0)
        gc_layout.addWidget(self.spin_offset_y)

        t2_layout.addWidget(grp_calib)
        t2_layout.addStretch()
        tabs.addTab(tab_calib, "Hiệu chuẩn Bù lệch (Offset)")

        # TAB 3: QUẢN LÝ TÀI KHOẢN (US-02)
        tab_users = QWidget()
        t3_layout = QVBoxLayout(tab_users)
        t3_layout.addWidget(QLabel("<b>Danh sách tài khoản hệ thống (Phân quyền RBAC):</b>"))

        self.user_table = QTableWidget(0, 4)
        self.user_table.setHorizontalHeaderLabels(["ID", "Tên đăng nhập", "Họ và tên", "Vai trò (Role)"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t3_layout.addWidget(self.user_table)
        tabs.addTab(tab_users, "Quản lý Người dùng")

        main_layout.addWidget(tabs)

        # Nút Lưu và Hủy
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Hủy bỏ")
        btn_cancel.setObjectName("btnCancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Lưu cấu hình")
        btn_save.setObjectName("btnSave")
        btn_save.clicked.connect(self._save_settings)
        btn_layout.addWidget(btn_save)

        main_layout.addLayout(btn_layout)

    def _load_current_settings(self):
        settings = database.get_all_settings()
        self.spin_warn_dist.setValue(float(settings.get("warn_distance_m", 3.5)))
        self.spin_warn_ttc.setValue(float(settings.get("warn_ttc_sec", 3.0)))
        self.spin_danger_dist.setValue(float(settings.get("danger_distance_m", 1.8)))
        self.spin_danger_ttc.setValue(float(settings.get("danger_ttc_sec", 1.8)))
        self.spin_offset_x.setValue(float(settings.get("offset_x_m", 0.0)))
        self.spin_offset_y.setValue(float(settings.get("offset_y_m", 0.0)))

        # Nạp bảng user
        users = database.get_all_users()
        self.user_table.setRowCount(len(users))
        for row, u in enumerate(users):
            self.user_table.setItem(row, 0, QTableWidgetItem(str(u[0])))
            self.user_table.setItem(row, 1, QTableWidgetItem(u[1]))
            self.user_table.setItem(row, 2, QTableWidgetItem(u[2]))
            self.user_table.setItem(row, 3, QTableWidgetItem(u[3].upper()))

    def _save_settings(self):
        new_settings = {
            "warn_distance_m": self.spin_warn_dist.value(),
            "warn_ttc_sec": self.spin_warn_ttc.value(),
            "danger_distance_m": self.spin_danger_dist.value(),
            "danger_ttc_sec": self.spin_danger_ttc.value(),
            "offset_x_m": self.spin_offset_x.value(),
            "offset_y_m": self.spin_offset_y.value()
        }
        database.save_bulk_settings(new_settings)
        self.settings_saved.emit(new_settings)
        QMessageBox.information(self, "Thành công", "Đã lưu và áp dụng toàn bộ cấu hình mới vào hệ thống!")
        self.accept()
