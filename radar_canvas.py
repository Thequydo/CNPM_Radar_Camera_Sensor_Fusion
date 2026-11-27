# -*- coding: utf-8 -*-
"""
Widget Bản đồ Không gian Radar 2D (Bird's-Eye View)
Chuẩn giao diện HMI Công nghiệp (Grafana / Foxglove)
Chính xác, tin cậy, không hiệu ứng trang trí thừa.
"""

import math
from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygonF
from PyQt6.QtCore import Qt, QPointF, pyqtSignal, QRectF
from config import (
    RADAR_MAX_RANGE_M, DANGER_DISTANCE_M, WARN_DISTANCE_M,
    DANGER_TTC_SEC, WARN_TTC_SEC, format_speed_status, format_operator_speed, config_manager
)

class RadarCanvas(QWidget):
    """Bản đồ Quét Radar 2D chuẩn HMI Kỹ thuật Công nghiệp"""
    target_clicked = pyqtSignal(object)  # Phát tín hiệu khi người dùng click vào mục tiêu

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.targets = []
        self.selected_target_id = None
        self.invert_x = True  # Đảo chiều X để đồng bộ với góc nhìn Camera
        self.is_monitoring = False
        self.setMouseTracking(True)

    def set_monitoring(self, active: bool):
        """Cập nhật trạng thái đang giám sát hay đã dừng"""
        if self.is_monitoring != active:
            self.is_monitoring = active
            self.update()

    def set_selected_target_id(self, target_id):
        """Đặt mục tiêu được chọn từ Camera hoặc giao diện điều khiển"""
        if self.selected_target_id != target_id:
            self.selected_target_id = target_id
            self.update()

    def set_invert_x(self, invert: bool):
        """Bật/Tắt đảo chiều trục X (Lật Trái/Phải)"""
        self.invert_x = invert
        self.update()

    def update_targets(self, targets):
        """Cập nhật danh sách mục tiêu và làm tươi canvas"""
        self.targets = targets
        self.update()

    def mousePressEvent(self, event):
        """Xử lý nhấp chuột chọn mục tiêu để kiểm tra chi tiết"""
        click_pos = event.position()
        w = self.width()
        h = self.height()
        origin_x = w / 2.0
        origin_y = h - 40.0
        max_r_px = origin_y - 28.0

        valid_targets = [t for t in self.targets if t.valid]
        max_dist = max([t.distance_m for t in valid_targets], default=0.0)
        display_max_range = 4.0 if (valid_targets and max_dist <= 3.2) else RADAR_MAX_RANGE_M
        scale = max_r_px / display_max_range

        found = None
        for t in self.targets:
            if not t.valid:
                continue
            eff_x = -t.x_m if self.invert_x else t.x_m
            px = origin_x + (eff_x * scale)
            py = origin_y - (t.y_m * scale)
            
            dist = math.hypot(click_pos.x() - px, click_pos.y() - py)
            if dist < 18:
                found = t
                break

        if found:
            self.selected_target_id = found.target_id
            self.target_clicked.emit(found)
        else:
            self.selected_target_id = None
            self.target_clicked.emit(None)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # 1. Nền Panel xám than trung tính (#1E2329)
        painter.fillRect(0, 0, w, h, QColor(0x1E, 0x23, 0x29))

        # Tọa độ gốc cảm biến
        origin_x = w / 2.0
        origin_y = h - 40.0
        max_r_px = origin_y - 28.0

        # Tự thu phóng (Auto-range) khi tất cả mục tiêu ở gần (< 3.2m -> thu phóng 4m để vùng gần dễ nhìn)
        valid_targets = [t for t in self.targets if t.valid]
        max_dist = max([t.distance_m for t in valid_targets], default=0.0)
        display_max_range = 4.0 if (valid_targets and max_dist <= 3.2) else RADAR_MAX_RANGE_M
        scale = max_r_px / display_max_range

        # 2. Vùng quạt quét FOV 120 độ (-60 đến +60 độ), nền #161A1F
        painter.setPen(QPen(QColor(0x2A, 0x31, 0x3A), 1))
        painter.setBrush(QColor(0x16, 0x1A, 0x1F))
        painter.drawPie(int(origin_x - max_r_px), int(origin_y - max_r_px), 
                        int(max_r_px * 2), int(max_r_px * 2), 30 * 16, 120 * 16)

        cfg = config_manager.data
        warn_d = float(cfg.get("warn_distance_m", WARN_DISTANCE_M))
        danger_d = float(cfg.get("danger_distance_m", DANGER_DISTANCE_M))
        warn_ttc = float(cfg.get("warn_ttc_sec", WARN_TTC_SEC))
        danger_ttc = float(cfg.get("danger_ttc_sec", DANGER_TTC_SEC))
        min_closing = float(cfg.get("min_closing_speed_mps", 0.3))

        # 3. Phân vùng an toàn kỹ thuật (đỏ / vàng tươi bán trong suốt)
        # Vùng cảnh báo vàng (r < warn_d)
        r_warn_px = warn_d * scale
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(245, 158, 11, 45))  # #F59E0B vàng hổ phách tươi bán trong suốt
        painter.drawPie(int(origin_x - r_warn_px), int(origin_y - r_warn_px), 
                        int(r_warn_px * 2), int(r_warn_px * 2), 30 * 16, 120 * 16)

        # Vùng nguy cơ va chạm đỏ (r < danger_d)
        r_danger_px = danger_d * scale
        painter.setBrush(QColor(239, 68, 68, 70))  # #EF4444 đỏ rực bán trong suốt
        painter.drawPie(int(origin_x - r_danger_px), int(origin_y - r_danger_px), 
                        int(r_danger_px * 2), int(r_danger_px * 2), 30 * 16, 120 * 16)

        # Chú giải vùng (Cảnh báo, Báo động) trực quan trên góc bản đồ
        painter.setPen(QPen(QColor(0x2A, 0x31, 0x3A), 1))
        painter.setBrush(QColor(0x16, 0x1A, 0x1F, 220))
        painter.drawRoundedRect(12, 12, 160, 48, 4, 4)

        font_legend = QFont("Segoe UI", 8)
        painter.setFont(font_legend)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(239, 68, 68))
        painter.drawEllipse(22, 22, 8, 8)
        painter.setPen(QColor(241, 245, 249))
        painter.drawText(36, 30, f"Báo động (< {danger_d:.1f}m)")

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(245, 158, 11))
        painter.drawEllipse(22, 38, 8, 8)
        painter.setPen(QColor(241, 245, 249))
        painter.drawText(36, 46, f"Cảnh báo (< {warn_d:.1f}m)")

        # 4. Các cung tròn cự ly kỹ thuật (nét liền mảnh #2A313A)
        font_metrics = QFont("Segoe UI", 9)
        painter.setFont(font_metrics)

        pen_ring = QPen(QColor(0x2A, 0x31, 0x3A), 1, Qt.PenStyle.SolidLine)
        for m in range(1, int(display_max_range) + 1):
            r_px = m * scale
            painter.setPen(pen_ring)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(int(origin_x - r_px), int(origin_y - r_px), 
                            int(r_px * 2), int(r_px * 2), 30 * 16, 120 * 16)

            # Nhãn khoảng cách
            painter.setPen(QColor(148, 163, 184))
            label_y = origin_y - r_px + 12
            painter.drawText(int(origin_x + 6), int(label_y), f"{m}m")

        # 5. Các tia phân chia góc quét (chuẩn 30 độ: -60, -30, 0, +30, +60 độ)
        angles = [-60, -30, 0, 30, 60]
        pen_ray = QPen(QColor(0x2A, 0x31, 0x3A), 1)
        painter.setPen(pen_ray)

        for ang in angles:
            rad = math.radians(ang)
            end_x = origin_x + max_r_px * math.sin(rad)
            end_y = origin_y - max_r_px * math.cos(rad)
            painter.drawLine(QPointF(origin_x, origin_y), QPointF(end_x, end_y))

            # Nhãn góc (0° chuẩn xác không dấu +, các góc khác hiển thị rõ)
            lbl_text = "0°" if ang == 0 else f"{ang:+d}°"
            lbl_x = origin_x + (max_r_px + 14) * math.sin(rad) - (8 if ang == 0 else 12)
            lbl_y = origin_y - (max_r_px + 14) * math.cos(rad) + 4
            painter.setPen(QColor(148, 163, 184))
            painter.drawText(int(lbl_x), int(lbl_y), lbl_text)
            painter.setPen(pen_ray)

        # 6. Vị trí cảm biến Radar trung tâm (HOST)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(43, 108, 176))  # Xanh dương dịu #2B6CB0
        triangle = QPolygonF([
            QPointF(origin_x, origin_y - 10),
            QPointF(origin_x - 8, origin_y + 6),
            QPointF(origin_x + 8, origin_y + 6)
        ])
        painter.drawPolygon(triangle)
        
        painter.setPen(QColor(148, 163, 184))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.drawText(int(origin_x - 18), int(origin_y + 20), "Radar")

        # 7. Vẽ các mục tiêu quan trắc thực tế (Không dùng glow, không dùng neon)
        for t in self.targets:
            if not t.valid:
                continue

            eff_x = -t.x_m if self.invert_x else t.x_m
            tx_px = origin_x + (eff_x * scale)
            ty_px = origin_y - (t.y_m * scale)

            # Màu trạng thái theo 3 mức chuẩn (vật đứng yên không bao giờ ra Đỏ)
            closing_v = getattr(t, 'closing_speed_mps', None)
            eff_closing = closing_v if closing_v is not None else (-t.speed_kmh / 3.6)
            is_closing = eff_closing > min_closing
            is_ttc_danger = (t.ttc_sec is not None and t.ttc_sec < danger_ttc)
            is_dist_danger = (t.distance_m < danger_d and is_closing)

            if is_closing and (is_ttc_danger or is_dist_danger):
                core_color = QColor(231, 76, 60)   # #E74C3C - Nguy cơ va chạm
            elif t.distance_m < warn_d or (t.ttc_sec is not None and t.ttc_sec < warn_ttc):
                core_color = QColor(243, 156, 18)  # #F39C12 - Vùng cảnh báo vàng
            else:
                core_color = QColor(46, 204, 113)  # #2ECC71 - An toàn

            # Nếu mục tiêu đang được chọn: vẽ vòng viền trắng nét liền mảnh
            if t.target_id == self.selected_target_id:
                painter.setPen(QPen(QColor(255, 255, 255), 1.5, Qt.PenStyle.SolidLine))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(QPointF(tx_px, ty_px), 12, 12)

            # Điểm mục tiêu đặc sắc nét (không quầng sáng glow)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(core_color)
            painter.drawEllipse(QPointF(tx_px, ty_px), 5, 5)

            # Véc-tơ vận tốc (đường thẳng chỉ hướng di chuyển khi thực sự chuyển động)
            if abs(eff_closing) >= min_closing or abs(t.speed_kmh) >= 0.5:
                vel_len = min(36, max(10, int(abs(t.speed_kmh) * 1.4)))
                angle_to_origin = math.atan2(origin_y - ty_px, origin_x - tx_px)
                if t.speed_kmh > 0:
                    angle_to_origin += math.pi

                arrow_end_x = tx_px + vel_len * math.cos(angle_to_origin)
                arrow_end_y = ty_px + vel_len * math.sin(angle_to_origin)

                painter.setPen(QPen(core_color, 1.5))
                painter.drawLine(QPointF(tx_px, ty_px), QPointF(arrow_end_x, arrow_end_y))

            # Nhãn thông số bên cạnh mục tiêu (Font Segoe UI 9pt, hiển thị đúng văn bản tốc độ không âm)
            painter.setPen(QColor(241, 245, 249))
            painter.setFont(QFont("Segoe UI", 9))
            speed_txt = format_operator_speed(t.speed_kmh, closing_v)
            dist_txt = f"{t.distance_m:.1f} m"
            lbl_full = f"Đối tượng {t.target_id}: {dist_txt}" if speed_txt == "Đứng yên" else f"Đối tượng {t.target_id}: {dist_txt} ({speed_txt})"
            # Tránh đè nhãn lên biểu tượng Radar ở tâm đáy (origin_x, origin_y)
            if abs(tx_px - origin_x) < 45 and (origin_y - ty_px) < 35:
                lbl_x = int(tx_px + 14)
                lbl_y = int(ty_px - 14)
            else:
                lbl_x = int(tx_px + 8)
                lbl_y = int(ty_px - 4)
            painter.drawText(lbl_x, lbl_y, lbl_full)

        # 7. Lớp phủ mờ khi chưa kích hoạt giám sát
        if not getattr(self, "is_monitoring", False):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(15, 23, 42, 190))
            painter.drawPie(int(origin_x - max_r_px), int(origin_y - max_r_px), 
                            int(max_r_px * 2), int(max_r_px * 2), 30 * 16, 120 * 16)
            
            painter.setPen(QColor(148, 163, 184))
            font_overlay = QFont("Segoe UI", 10, QFont.Weight.Bold)
            painter.setFont(font_overlay)
            overlay_rect = QRectF(origin_x - 130, origin_y - max_r_px * 0.55, 260, 48)
            painter.drawText(overlay_rect, Qt.AlignmentFlag.AlignCenter, "Chưa có dữ liệu radar\n(Hệ thống đang dừng)")
