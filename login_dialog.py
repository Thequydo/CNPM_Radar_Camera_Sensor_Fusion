# -*- coding: utf-8 -*-
"""
Module Giao diện Xác thực & Quản lý Người dùng (RBAC - Giai đoạn 7)
Tuân thủ đặc tả SRS: US-01..03, FR-01, FR-02
Bao gồm:
- Màn hình "Thiết lập lần đầu" (FirstRunSetupDialog) khi chưa có tài khoản nào
- Màn hình "Đăng nhập" (LoginDialog) hỗ trợ khóa 5 phút sau 5 lần sai
- Màn hình "Quản lý Người dùng" (UserManagementDialog) dành riêng cho Admin
- Màn hình "Đổi mật khẩu" (ChangePasswordDialog) dành cho mọi người dùng
"""

import os
import ctypes
from ctypes import byref, c_int, sizeof
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFrame, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QInputDialog
)
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPointF
import database


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


def create_dialog_radar_icon(size=56):
    """Icon vector phẳng sóng Radar trung tính kỹ thuật"""
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    center = size / 2.0

    painter.setPen(QPen(QColor(42, 49, 58), 1.5))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(QPointF(center, center), center - 4, center - 4)

    painter.setPen(QPen(QColor(42, 49, 58), 1.0))
    painter.drawEllipse(QPointF(center, center), (center - 4) * 0.6, (center - 4) * 0.6)

    pen_arc = QPen(QColor(43, 108, 176), 2.0)
    pen_arc.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen_arc)
    painter.drawArc(int(center - (center - 6)), int(center - (center - 6)),
                    int((center - 6) * 2), int((center - 6) * 2), 30 * 16, 75 * 16)

    r_core = max(4, int(size * 0.12))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(43, 108, 176))
    painter.drawEllipse(QPointF(center, center), r_core, r_core)
    painter.end()
    return pix


class FirstRunSetupDialog(QDialog):
    """Màn hình Thiết lập Lần đầu - Tạo tài khoản Quản trị viên (Không dùng tài khoản mặc định cố định)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Thiết lập hệ thống lần đầu - Tạo Quản trị viên")
        self.setFixedSize(440, 480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

    def showEvent(self, event):
        super().showEvent(event)
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
            QLineEdit {
                background-color: #1E2329;
                color: #FFFFFF;
                border: 1px solid #2A313A;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #2B6CB0;
            }
            QPushButton#btnCreate {
                background-color: #2ECC71;
                color: #161A1F;
                font-weight: 700;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
                border: none;
            }
            QPushButton#btnCreate:hover {
                background-color: #27AE60;
            }
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(10)

        title = QLabel("KHỞI TẠO HỆ THỐNG")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)

        desc = QLabel("Hệ thống chưa có tài khoản nào. Vui lòng thiết lập tài khoản Quản trị viên tối cao (Admin) để bắt đầu sử dụng:")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #94A3B8; font-size: 12px; margin-bottom: 8px;")
        layout.addWidget(desc)

        layout.addWidget(QLabel("Tên đăng nhập Admin:"))
        self.txt_username = QLineEdit()
        self.txt_username.setText("admin")
        layout.addWidget(self.txt_username)

        layout.addWidget(QLabel("Họ và tên Quản trị viên:"))
        self.txt_fullname = QLineEdit()
        self.txt_fullname.setText("Quản trị viên Hệ thống")
        layout.addWidget(self.txt_fullname)

        layout.addWidget(QLabel("Mật khẩu mới (tối thiểu 6 ký tự):"))
        self.txt_pwd = QLineEdit()
        self.txt_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.txt_pwd)

        layout.addWidget(QLabel("Nhập lại mật khẩu để xác nhận:"))
        self.txt_confirm = QLineEdit()
        self.txt_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.txt_confirm)

        self.lbl_err = QLabel("")
        self.lbl_err.setStyleSheet("color: #E74C3C; font-size: 12px; font-weight: 600;")
        self.lbl_err.hide()
        layout.addWidget(self.lbl_err)

        btn_create = QPushButton("Tạo Quản trị viên & Bắt đầu")
        btn_create.setObjectName("btnCreate")
        btn_create.clicked.connect(self._create_admin)
        layout.addSpacing(6)
        layout.addWidget(btn_create)

    def _create_admin(self):
        uname = self.txt_username.text().strip()
        fname = self.txt_fullname.text().strip()
        pwd = self.txt_pwd.text().strip()
        confirm = self.txt_confirm.text().strip()

        if not uname:
            self.lbl_err.setText("Vui lòng nhập tên đăng nhập.")
            self.lbl_err.show()
            return

        if len(pwd) < 6:
            self.lbl_err.setText("Mật khẩu phải có độ dài từ 6 ký tự trở lên.")
            self.lbl_err.show()
            return

        if pwd != confirm:
            self.lbl_err.setText("Mật khẩu xác nhận không khớp.")
            self.lbl_err.show()
            return

        ok, msg = database.create_initial_admin(uname, pwd, fname)
        if ok:
            QMessageBox.information(self, "Thành công", "Đã khởi tạo tài khoản Quản trị viên thành công!\nVui lòng đăng nhập để tiếp tục.")
            self.accept()
        else:
            self.lbl_err.setText(msg)
            self.lbl_err.show()


class LoginDialog(QDialog):
    """Màn hình Đăng nhập hệ thống phân quyền Admin / Operator"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hệ thống giám sát giao thông và cảnh báo va chạm")
        self.setFixedSize(420, 470)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.user_session = None

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_titlebar(self)

        try:
            database.init_db()
        except Exception as e:
            print("Lỗi khởi tạo DB:", e)

        # Kiểm tra lần chạy đầu tiên
        if not database.has_any_users():
            dlg = FirstRunSetupDialog(self)
            dlg.exec()

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
                color: #CBD5E1;
                font-size: 12px;
            }
            QLineEdit {
                background-color: #1E2329;
                color: #FFFFFF;
                border: 1px solid #2A313A;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #2B6CB0;
            }
            QPushButton#btnLogin {
                background-color: #2B6CB0;
                color: #FFFFFF;
                font-weight: 600;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
                border: none;
            }
            QPushButton#btnLogin:hover {
                background-color: #3182CE;
            }
            QPushButton#btnLogin:pressed {
                background-color: #161A1F;
            }
        """)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(12)

        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setPixmap(create_dialog_radar_icon(56))
        layout.addWidget(logo_label)

        title = QLabel("Hệ thống giám sát giao thông\nvà cảnh báo va chạm")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF; line-height: 1.2;")
        layout.addWidget(title)

        subtitle = QLabel("Đăng nhập tài khoản vận hành")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #94A3B8; font-size: 12px; margin-bottom: 4px;")
        layout.addWidget(subtitle)

        layout.addWidget(QLabel("Tên đăng nhập:"))
        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText("Nhập tên đăng nhập")
        layout.addWidget(self.txt_username)

        layout.addWidget(QLabel("Mật khẩu:"))
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setPlaceholderText("Nhập mật khẩu (*)")
        self.txt_password.returnPressed.connect(self._handle_login)
        layout.addWidget(self.txt_password)

        self.lbl_error = QLabel("")
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_error.setWordWrap(True)
        self.lbl_error.setStyleSheet("color: #E74C3C; font-size: 12px; font-weight: 600;")
        self.lbl_error.hide()
        layout.addWidget(self.lbl_error)

        self.btn_login = QPushButton("Đăng nhập")
        self.btn_login.setObjectName("btnLogin")
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_login.clicked.connect(self._handle_login)
        layout.addWidget(self.btn_login)

        lbl_footer = QLabel("v1.0.0 | DUT - 23KTMT")
        lbl_footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_footer.setStyleSheet("color: #94A3B8; font-size: 12px; margin-top: 12px;")
        layout.addWidget(lbl_footer)

    def _handle_login(self):
        username = self.txt_username.text().strip()
        password = self.txt_password.text().strip()

        if not username or not password:
            self.lbl_error.setText("Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.")
            self.lbl_error.show()
            return

        try:
            ok, user_data, msg = database.authenticate_user(username, password)
            if ok and user_data:
                self.user_session = user_data
                self.accept()
            else:
                self.lbl_error.setText(msg)
                self.lbl_error.show()
                self.txt_password.selectAll()
                self.txt_password.setFocus()
        except Exception as e:
            self.lbl_error.setText(f"Lỗi hệ thống: {str(e)}")
            self.lbl_error.show()


class UserManagementDialog(QDialog):
    """Màn hình Quản lý Người dùng dành riêng cho Quản trị viên (Admin Only - US-02)"""
    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.setWindowTitle("Quản lý tài khoản người dùng (Admin)")
        self.resize(720, 480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_titlebar(self)
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
            QTableWidget {
                background-color: #1E2329;
                color: #FFFFFF;
                border: 1px solid #2A313A;
                gridline-color: #2A313A;
            }
            QTableWidget::item:selected {
                background-color: #2B6CB0;
            }
            QHeaderView::section {
                background-color: #161A1F;
                color: #CBD5E1;
                font-weight: 600;
                border: 1px solid #2A313A;
                padding: 6px;
            }
            QPushButton {
                background-color: #1E2329;
                color: #F1F5F9;
                border: 1px solid #2A313A;
                border-radius: 4px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2A313A;
            }
            QPushButton#btnPrimary {
                background-color: #2B6CB0;
                color: #FFFFFF;
                border: none;
            }
            QPushButton#btnPrimary:hover {
                background-color: #3182CE;
            }
            QPushButton#btnDanger {
                background-color: #E74C3C;
                color: #FFFFFF;
                border: none;
            }
            QPushButton#btnDanger:hover {
                background-color: #C0392B;
            }
        """)
        self._init_ui()
        self._load_users()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        lbl_header = QLabel("Danh sách tài khoản hệ thống (Phân quyền RBAC)")
        lbl_header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(lbl_header)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Tên đăng nhập", "Họ và tên", "Vai trò", "Trạng thái", "Ngày tạo"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_add = QPushButton("+ Thêm tài khoản")
        btn_add.setObjectName("btnPrimary")
        btn_add.clicked.connect(self._add_user)
        btn_row.addWidget(btn_add)

        btn_reset_pwd = QPushButton("Đặt lại mật khẩu")
        btn_reset_pwd.clicked.connect(self._reset_password)
        btn_row.addWidget(btn_reset_pwd)

        btn_toggle_lock = QPushButton("Khóa / Mở khóa")
        btn_toggle_lock.clicked.connect(self._toggle_lock)
        btn_row.addWidget(btn_toggle_lock)

        btn_change_role = QPushButton("Đổi vai trò")
        btn_change_role.clicked.connect(self._toggle_role)
        btn_row.addWidget(btn_change_role)

        btn_del = QPushButton("Xóa tài khoản")
        btn_del.setObjectName("btnDanger")
        btn_del.clicked.connect(self._delete_user)
        btn_row.addWidget(btn_del)

        btn_row.addStretch()

        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)

        layout.addLayout(btn_row)

    def _load_users(self):
        users = database.get_all_users()
        self.table.setRowCount(len(users))
        for row, u in enumerate(users):
            # u: (id, username, full_name, role, is_locked, failed_attempts, created_at)
            uid, uname, fname, role, is_locked, failed, created = u
            status_txt = "Đã khóa" if is_locked else "Hoạt động"
            color = "#E74C3C" if is_locked else "#2ECC71"

            self.table.setItem(row, 0, QTableWidgetItem(str(uid)))
            self.table.setItem(row, 1, QTableWidgetItem(uname))
            self.table.setItem(row, 2, QTableWidgetItem(fname))
            self.table.setItem(row, 3, QTableWidgetItem(role.upper()))

            status_item = QTableWidgetItem(status_txt)
            status_item.setForeground(QColor(color))
            self.table.setItem(row, 4, status_item)

            self.table.setItem(row, 5, QTableWidgetItem(str(created)))

    def _get_selected_user_id(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn một người dùng từ bảng.")
            return None, None, None
        uid = int(self.table.item(row, 0).text())
        uname = self.table.item(row, 1).text()
        role = self.table.item(row, 3).text().lower()
        return uid, uname, role

    def _add_user(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Thêm người dùng mới")
        dlg.setFixedSize(360, 320)
        d_layout = QVBoxLayout(dlg)
        d_layout.setSpacing(10)

        d_layout.addWidget(QLabel("Tên đăng nhập:"))
        txt_u = QLineEdit()
        d_layout.addWidget(txt_u)

        d_layout.addWidget(QLabel("Họ và tên:"))
        txt_f = QLineEdit()
        d_layout.addWidget(txt_f)

        d_layout.addWidget(QLabel("Mật khẩu ban đầu (>= 6 ký tự):"))
        txt_p = QLineEdit()
        txt_p.setEchoMode(QLineEdit.EchoMode.Password)
        d_layout.addWidget(txt_p)

        d_layout.addWidget(QLabel("Vai trò:"))
        cb_role = QComboBox()
        cb_role.addItems(["operator", "admin"])
        d_layout.addWidget(cb_role)

        btn_ok = QPushButton("Tạo tài khoản")
        btn_ok.setObjectName("btnPrimary")
        btn_ok.clicked.connect(dlg.accept)
        d_layout.addWidget(btn_ok)

        if dlg.exec():
            u = txt_u.text().strip()
            f = txt_f.text().strip()
            p = txt_p.text().strip()
            r = cb_role.currentText()
            ok, msg = database.create_user(self.current_user.get("role", "admin"), u, p, f, r)
            if ok:
                QMessageBox.information(self, "Thành công", msg)
                self._load_users()
            else:
                QMessageBox.warning(self, "Lỗi", msg)

    def _reset_password(self):
        uid, uname, _ = self._get_selected_user_id()
        if uid is None:
            return
        new_pwd, ok = QInputDialog.getText(self, "Đặt lại mật khẩu", f"Nhập mật khẩu mới cho '{uname}':", QLineEdit.EchoMode.Password)
        if ok and new_pwd:
            succ, msg = database.reset_user_password(self.current_user.get("role", "admin"), uid, new_pwd.strip())
            if succ:
                QMessageBox.information(self, "Thành công", msg)
            else:
                QMessageBox.warning(self, "Lỗi", msg)

    def _toggle_lock(self):
        uid, uname, _ = self._get_selected_user_id()
        if uid is None:
            return
        row = self.table.currentRow()
        current_status = self.table.item(row, 4).text()
        new_lock = (current_status == "Hoạt động")

        succ, msg = database.set_user_lock_status(
            self.current_user.get("role", "admin"),
            self.current_user.get("id", 0),
            uid,
            new_lock
        )
        if succ:
            QMessageBox.information(self, "Thành công", msg)
            self._load_users()
        else:
            QMessageBox.warning(self, "Lỗi", msg)

    def _toggle_role(self):
        uid, uname, current_role = self._get_selected_user_id()
        if uid is None:
            return
        new_role = "admin" if current_role == "operator" else "operator"
        succ, msg = database.change_user_role(
            self.current_user.get("role", "admin"),
            self.current_user.get("id", 0),
            uid,
            new_role
        )
        if succ:
            QMessageBox.information(self, "Thành công", msg)
            self._load_users()
        else:
            QMessageBox.warning(self, "Lỗi", msg)

    def _delete_user(self):
        uid, uname, _ = self._get_selected_user_id()
        if uid is None:
            return
        ans = QMessageBox.question(self, "Xác nhận xóa", f"Bạn có chắc muốn xóa tài khoản '{uname}'?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ans == QMessageBox.StandardButton.Yes:
            succ, msg = database.delete_user(
                self.current_user.get("role", "admin"),
                self.current_user.get("id", 0),
                uid
            )
            if succ:
                QMessageBox.information(self, "Thành công", msg)
                self._load_users()
            else:
                QMessageBox.warning(self, "Lỗi", msg)


class ChangePasswordDialog(QDialog):
    """Hộp thoại tự đổi mật khẩu người dùng (US-03)"""
    def __init__(self, username: str, parent=None):
        super().__init__(parent)
        self.username = username
        self.setWindowTitle(f"Đổi mật khẩu: {username}")
        self.setFixedSize(380, 320)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

    def showEvent(self, event):
        super().showEvent(event)
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
                font-weight: 600;
            }
            QLineEdit {
                background-color: #1E2329;
                color: #FFFFFF;
                border: 1px solid #2A313A;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #2B6CB0;
            }
            QPushButton {
                background-color: #2B6CB0;
                color: #FFFFFF;
                font-weight: 600;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #3182CE;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Mật khẩu hiện tại:"))
        self.txt_old = QLineEdit()
        self.txt_old.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.txt_old)

        layout.addWidget(QLabel("Mật khẩu mới (tối thiểu 6 ký tự):"))
        self.txt_new = QLineEdit()
        self.txt_new.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.txt_new)

        layout.addWidget(QLabel("Xác nhận mật khẩu mới:"))
        self.txt_confirm = QLineEdit()
        self.txt_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.txt_confirm)

        self.btn_submit = QPushButton("Cập nhật mật khẩu")
        self.btn_submit.clicked.connect(self._submit)
        layout.addSpacing(10)
        layout.addWidget(self.btn_submit)

    def _submit(self):
        old_p = self.txt_old.text().strip()
        new_p = self.txt_new.text().strip()
        confirm_p = self.txt_confirm.text().strip()

        if new_p != confirm_p:
            QMessageBox.warning(self, "Lỗi", "Mật khẩu mới và xác nhận mật khẩu không khớp nhau.")
            return

        success, msg = database.change_user_password(self.username, old_p, new_p)
        if success:
            QMessageBox.information(self, "Thành công", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Lỗi", msg)


class RegisterDialog(QDialog):
    """Màn hình Đăng ký tài khoản người dùng mới (vai trò Operator mặc định)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tạo tài khoản mới - Hệ thống Giám sát Giao thông")
        self.setFixedSize(420, 520)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.created_username = ""
        self._init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        apply_dark_titlebar(self)

    def _init_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0F172A;
                color: #F8FAFC;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #CBD5E1;
                font-size: 12px;
            }
            QLineEdit {
                background-color: #1E293B;
                color: #FFFFFF;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 9px 12px;
                font-size: 12.5px;
            }
            QLineEdit:focus {
                border: 1px solid #38BDF8;
                background-color: #1E293B;
            }
            QPushButton#btnRegister {
                background-color: #2563EB;
                color: #FFFFFF;
                font-size: 13.5px;
                font-weight: bold;
                border-radius: 6px;
                padding: 10px;
                border: none;
                margin-top: 6px;
            }
            QPushButton#btnRegister:hover {
                background-color: #1D4ED8;
            }
            QPushButton#btnRegister:pressed {
                background-color: #1E40AF;
            }
            QPushButton#btnCancel {
                background-color: transparent;
                color: #94A3B8;
                font-size: 12.5px;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton#btnCancel:hover {
                color: #F1F5F9;
                border: 1px solid #64748B;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(12)

        # Header Title
        title = QLabel("Tạo tài khoản người dùng")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #F8FAFC;")
        layout.addWidget(title)

        subtitle = QLabel("Đăng ký tài khoản Người vận hành (Operator)")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #94A3B8; font-size: 12px; margin-bottom: 4px;")
        layout.addWidget(subtitle)

        # Form: Tên đăng nhập
        lbl_user = QLabel("Tên đăng nhập")
        lbl_user.setStyleSheet("font-weight: 600; color: #E2E8F0;")
        layout.addWidget(lbl_user)

        self.edit_user = QLineEdit()
        self.edit_user.setPlaceholderText("Nhập tên đăng nhập (tối thiểu 3 ký tự)")
        layout.addWidget(self.edit_user)

        # Form: Họ và tên
        lbl_name = QLabel("Họ và tên")
        lbl_name.setStyleSheet("font-weight: 600; color: #E2E8F0;")
        layout.addWidget(lbl_name)

        self.edit_name = QLineEdit()
        self.edit_name.setPlaceholderText("Nhập họ và tên đầy đủ")
        layout.addWidget(self.edit_name)

        # Form: Mật khẩu
        lbl_pwd = QLabel("Mật khẩu")
        lbl_pwd.setStyleSheet("font-weight: 600; color: #E2E8F0;")
        layout.addWidget(lbl_pwd)

        self.edit_pwd = QLineEdit()
        self.edit_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_pwd.setPlaceholderText("Nhập mật khẩu (tối thiểu 6 ký tự)")
        layout.addWidget(self.edit_pwd)

        # Form: Nhập lại mật khẩu
        lbl_confirm = QLabel("Xác nhận mật khẩu")
        lbl_confirm.setStyleSheet("font-weight: 600; color: #E2E8F0;")
        layout.addWidget(lbl_confirm)

        self.edit_confirm = QLineEdit()
        self.edit_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_confirm.setPlaceholderText("Nhập lại mật khẩu để xác nhận")
        layout.addWidget(self.edit_confirm)

        # Thông báo lỗi / trạng thái
        self.lbl_status = QLabel("")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet("color: #EF4444; font-size: 11.5px; font-weight: 600;")
        self.lbl_status.hide()
        layout.addWidget(self.lbl_status)

        # Nút Đăng ký
        self.btn_submit = QPushButton("Đăng ký tài khoản")
        self.btn_submit.setObjectName("btnRegister")
        self.btn_submit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_submit.clicked.connect(self._do_register)
        layout.addWidget(self.btn_submit)

        # Nút Hủy / Quay lại
        self.btn_cancel = QPushButton("Quay lại đăng nhập")
        self.btn_cancel.setObjectName("btnCancel")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        layout.addWidget(self.btn_cancel)

        # Phím Enter kích hoạt đăng ký
        self.edit_user.returnPressed.connect(self._do_register)
        self.edit_name.returnPressed.connect(self._do_register)
        self.edit_pwd.returnPressed.connect(self._do_register)
        self.edit_confirm.returnPressed.connect(self._do_register)

    def _do_register(self):
        username = self.edit_user.text().strip()
        full_name = self.edit_name.text().strip()
        pwd = self.edit_pwd.text()
        confirm = self.edit_confirm.text()

        if not username:
            self._show_error("Vui lòng nhập tên đăng nhập.")
            self.edit_user.setFocus()
            return

        if len(username) < 3:
            self._show_error("Tên đăng nhập phải có ít nhất 3 ký tự.")
            self.edit_user.setFocus()
            return

        if not full_name:
            self._show_error("Vui lòng nhập họ và tên.")
            self.edit_name.setFocus()
            return

        if len(pwd) < 6:
            self._show_error("Mật khẩu phải có độ dài từ 6 ký tự trở lên.")
            self.edit_pwd.setFocus()
            return

        if pwd != confirm:
            self._show_error("Mật khẩu xác nhận không khớp.")
            self.edit_confirm.setFocus()
            return

        ok, msg = database.register_user(username, pwd, full_name)
        if ok:
            self.created_username = username
            QMessageBox.information(self, "Thành công", f"Đã tạo tài khoản '{username}' thành công!\nBạn có thể sử dụng tài khoản này để đăng nhập ngay bây giờ.")
            self.accept()
        else:
            self._show_error(msg)

    def _show_error(self, text: str):
        self.lbl_status.setText(text)
        self.lbl_status.show()

