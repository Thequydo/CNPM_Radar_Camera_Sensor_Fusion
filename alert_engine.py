# -*- coding: utf-8 -*-
"""
Động cơ Cảnh báo & Gom Sự cố Va chạm (Giai đoạn 2)
Tuân thủ chuẩn SRS và yêu cầu kỹ thuật:
- Máy trạng thái cảnh báo 3 mức: "An toàn", "Có vật trong vùng cảnh báo", "Nguy cơ va chạm"
- Hysteresis chống nhấp nháy: nâng mức tức thì, hạ mức sau trễ >= 1.0 giây
- Vật đứng yên (< min_closing_speed_mps = 0.3 m/s) dù ở cự ly gần (< danger_distance_m) chỉ ở mức Vàng
- Gom sự cố (Incident Aggregation): sự cố kéo dài chỉ ra 1 dòng; kết thúc khi an toàn liên tục >= 2 giây
- Module thuần Python, không phụ thuộc PyQt6 để kiểm thử tự động 100%.
"""

import time
import math
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from config import config_manager


class AlertSeverity:
    SAFE = "An toàn"
    WARN = "Có vật trong vùng cảnh báo"
    DANGER = "Nguy cơ va chạm"


SEVERITY_LEVELS = {
    AlertSeverity.SAFE: 0,
    AlertSeverity.WARN: 1,
    AlertSeverity.DANGER: 2,
}


@dataclass
class IncidentRecord:
    """Bản ghi sự cố gom theo sự kiện (FR-08, Giai đoạn 2)"""
    id: Optional[int] = None
    start_time: str = ""
    end_time: str = ""
    max_severity: str = AlertSeverity.WARN
    object_type: str = "Chưa xác định"
    min_distance_m: float = 999.0
    min_ttc_sec: Optional[float] = None
    max_speed_kmh: float = 0.0
    closing_speed_mps: float = 0.0
    speed_kmh_raw: float = 0.0
    image_path: str = ""
    notes: str = ""
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "max_severity": self.max_severity,
            "object_type": self.object_type,
            "min_distance_m": round(self.min_distance_m, 2),
            "min_ttc_sec": round(self.min_ttc_sec, 2) if self.min_ttc_sec is not None else None,
            "max_speed_kmh": round(self.max_speed_kmh, 1),
            "closing_speed_mps": round(self.closing_speed_mps, 2),
            "speed_kmh_raw": round(self.speed_kmh_raw, 1),
            "image_path": self.image_path,
            "notes": self.notes,
            "created_at": self.created_at,
        }


class AlertStateMachine:
    """
    Máy trạng thái cảnh báo 3 mức (Mục 2.1):
    - An toàn: Không có mục tiêu hợp lệ trong vùng cảnh báo.
    - Có vật trong vùng cảnh báo (#F39C12): distance_m < warn_distance_m HOẶC ttc_sec < warn_ttc.
    - Nguy cơ va chạm (#E74C3C): ttc_sec < danger_ttc HOẶC (distance_m < danger_distance_m VÀ closing_speed_mps > 0.3).
      *Vật đứng yên dù rất gần chỉ ở mức Vàng*.
    - Hysteresis: Chuyển lên mức cao ngay lập tức (0ms). Chuyển xuống mức thấp chỉ khi
      điều kiện hạ mức duy trì liên tục >= hysteresis_sec (mặc định 1.0 giây).
    - Hỗ trợ reload_config tức thời khi Admin thay đổi ngưỡng.
    """

    def __init__(self, cfg: Optional[Dict[str, Any]] = None):
        self.cfg = cfg if cfg is not None else config_manager.data
        self.approaching_history: Dict[int, dict] = {}
        self.near_hold_active_until: float = 0.0
        self.near_hold_target: Optional[Any] = None
        self.blind_zone_active: bool = False
        self.reload_config(self.cfg)

        self.current_state: str = AlertSeverity.SAFE
        self.pending_lower_state: Optional[str] = None
        self.deescalate_start_time: Optional[float] = None
        self.last_transition_time: float = 0.0

    def reload_config(self, cfg: Optional[Dict[str, Any]] = None) -> None:
        """Cập nhật các ngưỡng từ cấu hình config.json"""
        if cfg is not None:
            self.cfg = cfg
        else:
            self.cfg = config_manager.data

        self.warn_distance_m = float(self.cfg.get("warn_distance_m", 3.5))
        self.warn_ttc_sec = float(self.cfg.get("warn_ttc_sec", 3.0))
        self.danger_distance_m = float(self.cfg.get("danger_distance_m", 1.8))
        self.danger_ttc_sec = float(self.cfg.get("danger_ttc_sec", 1.8))
        self.min_closing_speed_mps = float(self.cfg.get("min_closing_speed_mps", 0.3))
        self.hysteresis_sec = float(self.cfg.get("hysteresis_sec", 1.0))
        self.near_hold_range_m = float(self.cfg.get("near_hold_range_m", 1.2))
        self.near_hold_sec = float(self.cfg.get("near_hold_sec", 2.0))
        self.confirm_frames = int(self.cfg.get("confirm_frames", 3))
        self.min_range_m = float(self.cfg.get("min_range_m", 0.5))
        self.debug_alert_latency = bool(self.cfg.get("debug_alert_latency", False))

    def evaluate_target(self, target) -> str:
        """
        Đánh giá mức độ đe dọa của một mục tiêu đơn lẻ theo chuẩn:
        - DANGER: ttc_sec < danger_ttc HOẶC (distance_m < danger_distance_m VÀ closing_speed_mps > 0.3)
        - WARN: distance_m < warn_distance_m HOẶC (ttc_sec is not None VÀ ttc_sec < warn_ttc)
        - SAFE: các trường hợp còn lại
        """
        if not getattr(target, "valid", True):
            return AlertSeverity.SAFE

        d = float(target.distance_m)
        ttc = target.ttc_sec
        closing_v = getattr(target, "closing_speed_mps", 0.0)

        # QUY TẮC BẢO VỆ NGƯỠNG AN TOÀN (FR-07 & Chú giải Radar):
        # 1. Nếu ngoài cự ly cảnh báo (d >= warn_distance_m = 3.5m): Luôn là SAFE (Không bao giờ báo động ở cự ly xa)
        if d >= self.warn_distance_m:
            return AlertSeverity.SAFE

        # QUY TẮC BẮT BUỘC: Vật đứng yên (closing_v <= 0.3 m/s) TUYỆT ĐỐI KHÔNG ĐƯỢC ra mức ĐỎ (Nguy cơ va chạm)
        # Chỉ khi đang TIẾN LẠI GẦN (closing_v > min_closing_speed_mps) mới có thể kích hoạt mức ĐỎ
        is_closing = (closing_v > self.min_closing_speed_mps)

        # Điều kiện ĐỎ (Nguy cơ va chạm): Phải nằm trong cự ly theo dõi (d < warn_distance_m) VÀ
        # (cự ly < danger_distance_m HOẶC ttc < danger_ttc_sec) VÀ đang tiến lại gần
        is_ttc_danger = (ttc is not None and ttc < self.danger_ttc_sec)
        is_dist_danger_and_closing = (d < self.danger_distance_m and is_closing)

        if is_closing and (is_ttc_danger or is_dist_danger_and_closing):
            return AlertSeverity.DANGER

        # Điều kiện VÀNG (Có vật trong vùng cảnh báo): Cự ly d < warn_distance_m
        return AlertSeverity.WARN

    def evaluate(
        self,
        targets: list,
        timestamp: Optional[float] = None,
    ) -> Tuple[str, Optional[Any], float]:
        """
        Đánh giá trạng thái khung hình, giữ cảnh báo khi mục tiêu vào vùng mù (< near_hold_range_m)
        và áp dụng Hysteresis chống nhấp nháy.
        Trả về: (current_state, primary_target, latency_ms)
        """
        t_now = time.monotonic() if timestamp is None else float(timestamp)
        eval_start_wall = time.perf_counter()

        valid_targets = [t for t in targets if getattr(t, "valid", True)]
        current_valid_ids = set()

        # 1. Quản lý các mục tiêu đã xác nhận đang tiến lại gần (closing_speed_mps > min_closing_speed_mps)
        for t in valid_targets:
            current_valid_ids.add(t.target_id)
            hit_count = getattr(t, "hit_count", getattr(t, "age_frames", 1))
            # Chỉ ghi nhận khi mục tiêu đã xác nhận (>= confirm_frames) VÀ đang tiến lại gần
            if hit_count >= self.confirm_frames and t.closing_speed_mps > self.min_closing_speed_mps:
                self.approaching_history[t.target_id] = {
                    "last_time": t_now,
                    "distance_m": t.distance_m,
                    "closing_speed_mps": t.closing_speed_mps,
                    "target": t
                }

        # 2. Xử lý mục tiêu biến mất trong vùng gần (< near_hold_range_m = 1.2m)
        for tid, info in list(self.approaching_history.items()):
            if tid not in current_valid_ids:
                # Mục tiêu vừa biến mất! Nếu cự ly cuối < near_hold_range_m
                if info["distance_m"] < self.near_hold_range_m:
                    hold_until = info["last_time"] + self.near_hold_sec
                    if hold_until > self.near_hold_active_until:
                        self.near_hold_active_until = hold_until
                        self.near_hold_target = info["target"]
                # Dọn dẹp bản ghi cũ đã quá hạn
                if t_now > info["last_time"] + self.near_hold_sec:
                    del self.approaching_history[tid]

        # Kiểm tra trạng thái giữ vùng mù
        is_near_hold_triggered = (t_now < self.near_hold_active_until)
        self.blind_zone_active = is_near_hold_triggered and (
            len(valid_targets) == 0 or all(t.distance_m >= self.near_hold_range_m for t in valid_targets)
        )

        # 3. Xác định mức thô của khung hình (raw_severity = mức cao nhất của các mục tiêu)
        raw_severity = AlertSeverity.SAFE
        primary_target = None
        max_level_val = 0

        for t in valid_targets:
            sev = self.evaluate_target(t)
            lvl = SEVERITY_LEVELS[sev]
            if lvl > max_level_val:
                max_level_val = lvl
                raw_severity = sev
                primary_target = t
            elif lvl == max_level_val and primary_target is not None:
                # Cùng mức thì ưu tiên mục tiêu cự ly gần hơn
                if t.distance_m < primary_target.distance_m:
                    primary_target = t

        # Nếu đang kích hoạt giữ cảnh báo vùng gần (near hold) -> ép lên mức ĐỎ (Nguy cơ va chạm)
        if is_near_hold_triggered:
            if SEVERITY_LEVELS[raw_severity] < SEVERITY_LEVELS[AlertSeverity.DANGER]:
                raw_severity = AlertSeverity.DANGER
                if primary_target is None and self.near_hold_target is not None:
                    primary_target = self.near_hold_target

        if primary_target is None and valid_targets:
            primary_target = min(valid_targets, key=lambda x: x.distance_m)

        # 4. Xử lý Chuyển trạng thái & Hysteresis
        current_lvl = SEVERITY_LEVELS[self.current_state]
        raw_lvl = SEVERITY_LEVELS[raw_severity]

        if raw_lvl > current_lvl:
            # NÂNG MỨC: Tức thời 0ms
            self.current_state = raw_severity
            self.pending_lower_state = None
            self.deescalate_start_time = None
            self.last_transition_time = t_now
        elif raw_lvl == current_lvl:
            # Giữ nguyên mức: hủy bộ đếm hạ mức nếu có
            self.pending_lower_state = None
            self.deescalate_start_time = None
        else:
            # HẠ MỨC: Chỉ chuyển xuống khi điều kiện hạ mức duy trì liên tục >= hysteresis_sec
            if self.deescalate_start_time is None:
                self.deescalate_start_time = t_now
                self.pending_lower_state = raw_severity
            else:
                # Nếu mức thô còn thấp hơn nữa thì cập nhật mức đích
                if raw_lvl < SEVERITY_LEVELS[self.pending_lower_state]:
                    self.pending_lower_state = raw_severity

                elapsed = t_now - self.deescalate_start_time
                if elapsed >= self.hysteresis_sec:
                    self.current_state = self.pending_lower_state
                    self.pending_lower_state = None
                    self.deescalate_start_time = None
                    self.last_transition_time = t_now

        latency_ms = (time.perf_counter() - eval_start_wall) * 1000.0
        if self.debug_alert_latency and latency_ms > 0:
            print(f"[ĐỘ TRỄ CẢNH BÁO] Trạng thái: {self.current_state} | Thời gian đánh giá: {latency_ms:.2f} ms")

        return (self.current_state, primary_target, latency_ms)


class IncidentAggregator:
    """
    Bộ Gom Sự cố Va chạm theo Sự kiện (Mục 2.3):
    - Một sự cố bắt đầu khi trạng thái lên mức VÀNG hoặc ĐỎ.
    - Kết thúc khi trạng thái trở về 'An toàn' liên tục >= cooldown_sec (mặc định 2.0 giây).
    - Chuỗi 60 khung liên tục chỉ xuất đúng 1 dòng sự cố.
    - Chụp 1 ảnh hiện trường khi sự cố lần đầu đạt mức ĐỎ (Nguy cơ va chạm).
    """

    def __init__(self, cooldown_sec: float = 2.0):
        self.cooldown_sec = float(cooldown_sec)
        self.current_incident: Optional[IncidentRecord] = None
        self.safe_start_time: Optional[float] = None
        self.snapshot_taken_for_incident: bool = False
        self._next_incident_counter: int = 1

    def update(
        self,
        current_state: str,
        targets: list,
        timestamp: Optional[float] = None,
        object_type: str = "Chưa xác định",
        notes: str = "",
    ) -> Tuple[bool, Optional[IncidentRecord]]:
        """
        Cập nhật gom sự cố.
        Trả về: (should_take_snapshot, completed_incident)
        """
        t_now = time.monotonic() if timestamp is None else float(timestamp)
        now_dt_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        should_snapshot = False
        completed_incident = None

        if current_state in (AlertSeverity.WARN, AlertSeverity.DANGER):
            self.safe_start_time = None  # Đang có sự cố, xóa bộ đếm an toàn
            self.last_threat_timestamp = t_now

            if self.current_incident is None:
                # Bắt đầu một sự cố mới!
                inc_id = self._next_incident_counter
                self._next_incident_counter += 1
                self.snapshot_taken_for_incident = False

                self.current_incident = IncidentRecord(
                    id=inc_id,
                    start_time=now_dt_str,
                    end_time=now_dt_str,
                    max_severity=current_state,
                    object_type=object_type,
                    min_distance_m=999.0,
                    min_ttc_sec=None,
                    max_speed_kmh=0.0,
                    image_path="",
                    notes=notes,
                    created_at=now_dt_str,
                )

            # Cập nhật ghi chú nếu có (ví dụ: mục tiêu vào vùng mù)
            if notes:
                if not self.current_incident.notes:
                    self.current_incident.notes = notes
                elif notes not in self.current_incident.notes:
                    self.current_incident.notes = f"{self.current_incident.notes}; {notes}"

            # Cập nhật mức cao nhất đạt được
            if SEVERITY_LEVELS[current_state] > SEVERITY_LEVELS[self.current_incident.max_severity]:
                self.current_incident.max_severity = current_state

            # Kiểm tra yêu cầu chụp ảnh: Chụp khi lên mức ĐỎ lần đầu trong sự cố này
            if current_state == AlertSeverity.DANGER and not self.snapshot_taken_for_incident:
                should_snapshot = True
                self.snapshot_taken_for_incident = True

            # Cập nhật thời gian kết thúc và các thông số cực trị
            self.current_incident.end_time = now_dt_str
            for t in targets:
                if not getattr(t, "valid", True):
                    continue
                d = float(t.distance_m)
                if d < self.current_incident.min_distance_m:
                    self.current_incident.min_distance_m = d

                ttc = t.ttc_sec
                if ttc is not None:
                    if self.current_incident.min_ttc_sec is None or ttc < self.current_incident.min_ttc_sec:
                        self.current_incident.min_ttc_sec = ttc

                spd = abs(float(t.speed_kmh))
                if spd > self.current_incident.max_speed_kmh:
                    self.current_incident.max_speed_kmh = spd
                    self.current_incident.speed_kmh_raw = float(getattr(t, "speed_kmh", 0.0))

                c_v = float(getattr(t, "closing_speed_mps", 0.0) or 0.0)
                if abs(c_v) > abs(self.current_incident.closing_speed_mps):
                    self.current_incident.closing_speed_mps = c_v

        else:
            # Trạng thái hiện tại là AN TOÀN
            if self.current_incident is not None:
                if self.safe_start_time is None:
                    self.safe_start_time = getattr(self, "last_threat_timestamp", t_now)

                if (t_now - self.safe_start_time) >= self.cooldown_sec:
                    # Đã duy trì An toàn >= cooldown_sec (2.0s) -> Chốt kết thúc sự cố!
                    if self.current_incident.min_distance_m == 999.0:
                        self.current_incident.min_distance_m = 0.0

                    completed_incident = self.current_incident
                    self.current_incident = None
                    self.safe_start_time = None
                    self.snapshot_taken_for_incident = False

        return (should_snapshot, completed_incident)

    def finish_active_incident(self) -> Optional[IncidentRecord]:
        """Chốt cưỡng bức sự cố đang mở (ví dụ khi nhấn Dừng hệ thống hoặc thoát ứng dụng)"""
        if self.current_incident is not None:
            if self.current_incident.min_distance_m == 999.0:
                self.current_incident.min_distance_m = 0.0
            inc = self.current_incident
            self.current_incident = None
            self.safe_start_time = None
            self.snapshot_taken_for_incident = False
            return inc
        return None
