# -*- coding: utf-8 -*-
"""
Tầng Dữ liệu Radar HLK-LD2450 (24GHz FMCW) - Giai đoạn 1:
1. Giải mã khung nhị phân 30 byte (đồng bộ Header/Tail, chịu byte rác & cắt khung,
   giải mã dấu bit 15, đọc trường resolution, kiểm tra đủ 8 byte trống, bác bỏ Y <= 0).
2. Lọc theo phạm vi cự ly (min_range_m .. max_range_m) và góc quét (|angle_deg| <= max_angle_deg).
3. Mô hình Hiệu chuẩn nền (BackgroundModel): học các điểm phản xạ tĩnh cố định
   theo lưới ô 10 cm (ngưỡng hiện diện >= 70%), lưu/nạp background.json, lọc trước tracker.
4. Bộ theo dõi đa mục tiêu (RadarTracker): ghép Nearest Neighbor có cổng khoảng cách,
   làm mượt vị trí EMA (< 200ms), xác nhận >= 3 khung liên tiếp, xóa sau 5 khung mất dấu,
   tính closing_speed_mps từ đạo hàm khoảng cách theo thời gian và tính TTC.

Toàn bộ các lớp thuật toán (RadarTarget, RadarStreamDecoder, BackgroundModel,
RadarTracker, RadarPipeline) đều thuần Python, không phụ thuộc PyQt6 để kiểm thử tự động.
"""

import os
import json
import time
import math
import random
from collections import deque
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any

import numpy as np
import serial
import serial.tools.list_ports

from config import (
    BACKGROUND_JSON_PATH,
    LOGS_DIR,
    config_manager,
)

HEADER_BYTES = b'\xAA\xFF\x03\x00'
TAIL_BYTES = b'\x55\xCC'
FRAME_SIZE = 30
EMPTY_SLOT_BYTES = b'\x00\x00\x00\x00\x00\x00\x00\x00'

CMD_HEADER_BYTES = b'\xFD\xFC\xFB\xFA'
CMD_TAIL_BYTES = b'\x04\x03\x02\x01'

# Lệnh cấu hình cảm biến HLK-LD2450
LD2450_ENABLE_CONFIG_CMD = b'\xFD\xFC\xFB\xFA\x04\x00\xFF\x00\x01\x00\x04\x03\x02\x01'
LD2450_MULTI_TARGET_CMD  = b'\xFD\xFC\xFB\xFA\x02\x00\x90\x00\x04\x03\x02\x01'
LD2450_QUERY_MODE_CMD    = b'\xFD\xFC\xFB\xFA\x02\x00\x91\x00\x04\x03\x02\x01'
LD2450_END_CONFIG_CMD    = b'\xFD\xFC\xFB\xFA\x02\x00\xFE\x00\x04\x03\x02\x01'


def parse_ld2450_ack_frames(data: bytes) -> List[Tuple[int, int, bytes]]:
    """
    Giải mã các khung phản hồi ACK cấu hình của HLK-LD2450:
    Header (FD FC FB FA) + len (2B LE) + ack_cmd (2B LE) + status (2B LE) + extra + Tail (04 03 02 01).
    Trả về danh sách (ack_cmd_word, status, extra_bytes).
    """
    acks: List[Tuple[int, int, bytes]] = []
    if not data:
        return acks
    idx = 0
    n = len(data)
    while idx <= n - 12:
        pos = data.find(CMD_HEADER_BYTES, idx)
        if pos == -1 or pos + 10 > n:
            break
        payload_len = data[pos + 4] | (data[pos + 5] << 8)
        total_len = 6 + payload_len + 4
        if payload_len < 4 or pos + total_len > n:
            idx = pos + 1
            continue
        if data[pos + total_len - 4 : pos + total_len] != CMD_TAIL_BYTES:
            idx = pos + 1
            continue
        payload = data[pos + 6 : pos + 6 + payload_len]
        ack_word = payload[0] | (payload[1] << 8)
        status = payload[2] | (payload[3] << 8)
        extra = payload[4:]
        acks.append((ack_word, status, extra))
        idx = pos + total_len
    return acks


def _send_ld2450_cmd_wait_ack(
    ser: Any,
    cmd: bytes,
    expected_ack_word: int,
    timeout_s: float = 0.25,
) -> Optional[Tuple[int, int, bytes]]:
    """Gửi lệnh cấu hình HLK-LD2450 và chờ đọc khung ACK khớp expected_ack_word."""
    ser.write(cmd)
    if hasattr(ser, "flush"):
        try:
            ser.flush()
        except Exception:
            pass

    deadline = time.monotonic() + timeout_s
    buf = bytearray()
    while time.monotonic() < deadline:
        waiting = getattr(ser, "in_waiting", 0)
        chunk = ser.read(waiting if waiting > 0 else 1)
        if chunk:
            buf.extend(chunk)
            for ack_word, status, extra in parse_ld2450_ack_frames(bytes(buf)):
                if ack_word == expected_ack_word:
                    return (ack_word, status, extra)
        else:
            time.sleep(0.01)
    return None


def configure_ld2450_multitarget(
    ser: Any,
    logger: Optional["RadarDebugLogger"] = None,
) -> Dict[str, Any]:
    """
    Thực hiện bắt tay cấu hình Đa mục tiêu (0x0090) có kiểm tra ACK & truy vấn chế độ (0x0091) cho HLK-LD2450.
    Trả về dict trạng thái: {'enable_ack', 'multi_ack', 'mode', 'mode_label', 'end_ack'}.
    """
    result: Dict[str, Any] = {
        "enable_ack": False,
        "multi_ack": False,
        "mode": None,
        "mode_label": "Chưa rõ (không có ACK)",
        "end_ack": False,
    }
    try:
        if hasattr(ser, "reset_input_buffer"):
            ser.reset_input_buffer()

        # Bước 1: Enable Config (thử tối đa 2 lần phòng trường hợp radar đang bận xuất khung 10Hz)
        en_ack = _send_ld2450_cmd_wait_ack(ser, LD2450_ENABLE_CONFIG_CMD, 0x01FF, timeout_s=0.25)
        if en_ack is None:
            if hasattr(ser, "reset_input_buffer"):
                ser.reset_input_buffer()
            en_ack = _send_ld2450_cmd_wait_ack(ser, LD2450_ENABLE_CONFIG_CMD, 0x01FF, timeout_s=0.25)
        result["enable_ack"] = (en_ack is not None and en_ack[1] == 0)

        # Bước 2: Bật chế độ Đa mục tiêu (0x0090)
        mt_ack = _send_ld2450_cmd_wait_ack(ser, LD2450_MULTI_TARGET_CMD, 0x0190, timeout_s=0.25)
        result["multi_ack"] = (mt_ack is not None and mt_ack[1] == 0)

        # Bước 3: Truy vấn kiểm tra chế độ thực tế (0x0091 -> 0x0002 là Multi-Target, 0x0001 là Single-Target)
        q_ack = _send_ld2450_cmd_wait_ack(ser, LD2450_QUERY_MODE_CMD, 0x0191, timeout_s=0.25)
        if q_ack is not None and q_ack[1] == 0 and len(q_ack[2]) >= 2:
            mode_val = q_ack[2][0] | (q_ack[2][1] << 8)
            result["mode"] = mode_val
            if mode_val == 2:
                result["mode_label"] = "Multi-Target (0x0002)"
            elif mode_val == 1:
                result["mode_label"] = "Single-Target (0x0001)"
            else:
                result["mode_label"] = f"Unknown ({mode_val:#06x})"

        # Bước 4: End Config để radar quay lại luồng đo 10Hz bình thường
        end_ack = _send_ld2450_cmd_wait_ack(ser, LD2450_END_CONFIG_CMD, 0x01FE, timeout_s=0.25)
        result["end_ack"] = (end_ack is not None and end_ack[1] == 0)

        if hasattr(ser, "reset_input_buffer"):
            ser.reset_input_buffer()
        elif getattr(ser, "in_waiting", 0):
            ser.read(ser.in_waiting)
    except Exception as cmd_err:
        result["error"] = str(cmd_err)

    if logger is not None:
        logger.log_note(
            f"[INIT] HLK-LD2450 Config -> enable_ack={result['enable_ack']}, "
            f"multi_ack={result['multi_ack']}, mode={result['mode_label']}, end_ack={result['end_ack']}"
        )
    return result


def get_available_ports() -> List[str]:
    """Quét và trả về danh sách các cổng COM đang khả dụng trên máy"""
    ports = serial.tools.list_ports.comports()
    return [p.device for p in ports]


def decode_signed_16bit(raw_u16: int) -> int:
    """
    Giải mã số nguyên 16-bit có dấu theo chuẩn Hi-Link LD2450:
    - Bit 15 (0x8000): 1 là Dương (+), 0 là Âm (-)
    - 15 bit thấp (0x7FFF): Độ lớn giá trị
    """
    magnitude = raw_u16 & 0x7FFF
    if magnitude == 0:
        return 0
    return magnitude if (raw_u16 & 0x8000) else -magnitude


def encode_signed_16bit(value: int) -> int:
    """
    Mã hóa số nguyên có dấu sang định dạng 16-bit Hi-Link LD2450
    (Phục vụ tạo gói tin kiểm thử tự động pytest).
    """
    if value == 0:
        return 0
    mag = min(0x7FFF, abs(int(value)))
    return (0x8000 | mag) if value > 0 else mag


def build_ld2450_frame(targets_tuples: List[Optional[Tuple[int, int, int, int]]]) -> bytes:
    """
    Tạo khung nhị phân 30 byte chuẩn LD2450 từ tối đa 3 bộ (x_mm, y_mm, v_cms, res_mm).
    Nếu ít hơn 3 mục tiêu hoặc phần tử là None, các khe đó điền 8 byte 0.
    """
    buf = bytearray(HEADER_BYTES)
    for i in range(3):
        if i < len(targets_tuples) and targets_tuples[i] is not None:
            x_mm, y_mm, v_cms, res_mm = targets_tuples[i]
            if x_mm == 0 and y_mm == 0 and v_cms == 0 and res_mm == 0:
                buf.extend(EMPTY_SLOT_BYTES)
            else:
                rx = encode_signed_16bit(x_mm)
                ry = encode_signed_16bit(y_mm)
                rv = encode_signed_16bit(v_cms)
                rr = max(0, min(0xFFFF, int(res_mm)))
                buf.extend([
                    rx & 0xFF, (rx >> 8) & 0xFF,
                    ry & 0xFF, (ry >> 8) & 0xFF,
                    rv & 0xFF, (rv >> 8) & 0xFF,
                    rr & 0xFF, (rr >> 8) & 0xFF,
                ])
        else:
            buf.extend(EMPTY_SLOT_BYTES)
    buf.extend(TAIL_BYTES)
    return bytes(buf)


class RadarTarget:
    """
    Đối tượng mục tiêu Radar chuẩn hóa (Mục 1.1).
    Hỗ trợ đồng thời thuộc tính `id` và `target_id` để tương thích ngược hoàn toàn.
    """

    def __init__(
        self,
        target_id: Optional[int] = None,
        x_m: Optional[float] = None,
        y_m: Optional[float] = None,
        speed_kmh: float = 0.0,
        valid: bool = True,
        resolution: int = 0,
        closing_speed_mps: Optional[float] = None,
        ttc_sec: Optional[float] = None,
        age_frames: int = 1,
        min_closing_speed_mps: float = 0.3,
        **kwargs
    ):
        # Hỗ trợ cả target_id / id
        tid = target_id if target_id is not None else kwargs.get("id", 0)
        xm = x_m if x_m is not None else kwargs.get("x", 0.0)
        ym = y_m if y_m is not None else kwargs.get("y", 0.0)
        ttc = ttc_sec if ttc_sec is not None else kwargs.get("ttc_s", None)
        hits = kwargs.get("hits", age_frames)

        self.id = int(tid)
        self.x_m = float(xm)
        self.y_m = float(ym)
        self.speed_kmh = float(speed_kmh)
        self.resolution = int(resolution)
        self.valid = bool(valid)
        self.age_frames = int(hits)

        # Khoảng cách Euclid (m) và góc phương vị (độ, âm = trái, dương = phải)
        self.distance_m = math.hypot(self.x_m, self.y_m) if self.valid or (self.x_m != 0 or self.y_m != 0) else 0.0
        self.angle_deg = math.degrees(math.atan2(self.x_m, self.y_m)) if (self.x_m != 0 or self.y_m != 0) else 0.0

        # Tốc độ tiến lại gần (m/s, dương = đang tiến lại gần cảm biến)
        if closing_speed_mps is not None:
            self.closing_speed_mps = float(closing_speed_mps)
        else:
            # Nếu khởi tạo độc lập không qua Tracker, suy ra từ speed_kmh (âm = tiến lại gần, dương = ra xa)
            self.closing_speed_mps = -self.speed_kmh / 3.6

        # Thời gian va chạm TTC (giây)
        if ttc_sec is not None:
            self.ttc_sec = float(ttc_sec)
        else:
            if self.valid and self.closing_speed_mps > min_closing_speed_mps and self.distance_m > 0:
                self.ttc_sec = self.distance_m / self.closing_speed_mps
            else:
                self.ttc_sec = None

    @property
    def target_id(self) -> int:
        return self.id

    @target_id.setter
    def target_id(self, val: int) -> None:
        self.id = int(val)

    @property
    def resolution_mm(self) -> int:
        return self.resolution

    @property
    def speed_mps(self) -> float:
        return self.speed_kmh / 3.6

    @property
    def x(self) -> float:
        return self.x_m

    @property
    def y(self) -> float:
        return self.y_m

    @property
    def distance(self) -> float:
        return self.distance_m

    @property
    def ttc_s(self) -> Optional[float]:
        return self.ttc_sec

    @property
    def hit_count(self) -> int:
        return self.age_frames

    @property
    def hits(self) -> int:
        return self.age_frames

    @property
    def confirmed(self) -> bool:
        return self.valid


    def __repr__(self) -> str:
        ttc_s = f"{self.ttc_sec:.2f}s" if self.ttc_sec is not None else "None"
        return (
            f"RadarTarget(id={self.id}, x={self.x_m:+.2f}m, y={self.y_m:.2f}m, "
            f"d={self.distance_m:.2f}m, ang={self.angle_deg:+.1f}deg, "
            f"v_raw={self.speed_kmh:+.1f}km/h, v_close={self.closing_speed_mps:+.2f}m/s, "
            f"ttc={ttc_s}, res={self.resolution}mm, age={self.age_frames}, valid={self.valid})"
        )


TrackedTarget = RadarTarget


def parse_ld2450_frame(frame: bytes) -> List[RadarTarget]:
    """
    Bóc tách 1 khung 30 byte của HLK-LD2450 thành danh sách các mục tiêu thô.
    - Kiểm tra Header AA FF 03 00 và Tail 55 CC.
    - Bỏ qua khe mục tiêu có cả 8 byte bằng 0 (Mục 3.1.2).
    - Đọc đầy đủ x, y, speed và resolution (Mục 3.1.2).
    - Không dùng abs(y); bác bỏ ngay mục tiêu có y_mm <= 0 (Mục 3.1.3).
    """
    if len(frame) != FRAME_SIZE:
        return []
    if frame[:4] != HEADER_BYTES or frame[28:30] != TAIL_BYTES:
        return []

    raw_targets: List[RadarTarget] = []
    for i in range(3):
        offset = 4 + i * 8
        slot = frame[offset : offset + 8]

        # Mục tiêu trống có cả 8 byte bằng 0 -> bỏ qua
        if slot == EMPTY_SLOT_BYTES:
            continue

        raw_x = slot[0] | (slot[1] << 8)
        raw_y = slot[2] | (slot[3] << 8)
        raw_v = slot[4] | (slot[5] << 8)
        raw_res = slot[6] | (slot[7] << 8)

        x_mm = decode_signed_16bit(raw_x)
        y_mm = decode_signed_16bit(raw_y)
        v_cms = decode_signed_16bit(raw_v)

        # Mục 3.1.3: Trục Y hướng ra phía trước radar phải > 0; không dùng abs()
        if y_mm <= 0:
            continue

        x_m = x_mm / 1000.0
        y_m = y_mm / 1000.0
        # 1 cm/s = 0.036 km/h
        speed_kmh = v_cms * 0.036

        target = RadarTarget(
            target_id=i + 1,
            x_m=x_m,
            y_m=y_m,
            speed_kmh=speed_kmh,
            valid=True,
            resolution=raw_res,
            closing_speed_mps=0.0,
            ttc_sec=None,
            age_frames=1,
        )
        raw_targets.append(target)

    return raw_targets


class RadarStreamDecoder:
    """
    Bộ đồng bộ và giải mã luồng byte nối tiếp từ cảm biến LD2450 (Mục 1.1).
    Chịu được byte rác xen kẽ và khung bị cắt đôi qua nhiều lần đọc.
    """

    def __init__(self):
        self.buffer = bytearray()

    def reset(self) -> None:
        self.buffer.clear()

    def feed(self, data: bytes) -> List[List[RadarTarget]]:
        """
        Nạp thêm byte vào bộ đệm và trả về danh sách các gói mục tiêu (mỗi phần tử ứng với 1 khung 30 byte hợp lệ).
        """
        if not data:
            return []
        self.buffer.extend(data)
        parsed_frames: List[List[RadarTarget]] = []

        while len(self.buffer) >= FRAME_SIZE:
            idx = self.buffer.find(HEADER_BYTES)
            if idx == -1:
                # Giữ lại tối đa 3 byte cuối phòng trường hợp Header bị cắt ngang
                self.buffer = self.buffer[-(len(HEADER_BYTES) - 1):]
                break
            if idx > 0:
                # Loại bỏ các byte rác đứng trước Header
                del self.buffer[:idx]

            if len(self.buffer) < FRAME_SIZE:
                break

            if self.buffer[28:30] == TAIL_BYTES:
                frame_bytes = bytes(self.buffer[:FRAME_SIZE])
                del self.buffer[:FRAME_SIZE]
                parsed_frames.append(parse_ld2450_frame(frame_bytes))
            else:
                # Header giả nằm trong dữ liệu -> dịch 1 byte để tìm Header tiếp theo
                del self.buffer[:1]

        return parsed_frames


def filter_targets_by_range(
    targets: List[RadarTarget],
    min_range_m: float = 0.5,
    max_range_m: float = 6.0,
    max_angle_deg: float = 60.0,
) -> List[RadarTarget]:
    """
    Mục 1.2: Lọc mục tiêu theo phạm vi khoảng cách [min_range_m, max_range_m]
    và góc phương vị [-max_angle_deg, +max_angle_deg].
    """
    filtered: List[RadarTarget] = []
    for t in targets:
        if t.y_m <= 0:
            continue
        if t.distance_m < min_range_m or t.distance_m > max_range_m:
            continue
        if abs(t.angle_deg) > max_angle_deg:
            continue
        filtered.append(t)
    return filtered


class BackgroundModel:
    """
    Mục 1.4: Mô hình hiệu chuẩn nền để loại bỏ vật phản xạ tĩnh và mục tiêu giả cố định.
    - Gom các mục tiêu thu được trong thời gian hiệu chuẩn theo ô lưới 10 cm (grid_size_m = 0.10).
    - Ô nào xuất hiện trong >= 70% tổng số khung hiệu chuẩn thì được ghi nhận là điểm nền.
    - Lưu và đọc từ tệp background.json.
    """

    def __init__(
        self,
        storage_path: str = BACKGROUND_JSON_PATH,
        grid_size_m: float = 0.10,
        occupancy_ratio: float = 0.70,
        tolerance_m: float = 0.15,
    ):
        self.storage_path = storage_path
        self.grid_size_m = float(grid_size_m)
        self.occupancy_ratio = float(occupancy_ratio)
        self.tolerance_m = float(tolerance_m)
        self.points: List[Tuple[float, float]] = []

        # Trạng thái thu thập hiệu chuẩn
        self._calibrating = False
        self._calib_end_time = 0.0
        self._calib_total_frames = 0
        self._calib_cell_counts: Dict[Tuple[int, int], int] = {}
        self._calib_cell_sums: Dict[Tuple[int, int], List[float]] = {}

        self.load()

    def _cell_key(self, x_m: float, y_m: float) -> Tuple[int, int]:
        gx = int(round(x_m / self.grid_size_m))
        gy = int(round(y_m / self.grid_size_m))
        return (gx, gy)

    def start_calibration(self, duration_s: float = 5.0) -> None:
        """Bắt đầu phiên thu thập hiệu chuẩn nền trong duration_s giây"""
        self._calibrating = True
        self._calib_duration_s = max(0.001, float(duration_s))
        self._calib_start_time = time.monotonic()
        self._calib_end_time = self._calib_start_time + self._calib_duration_s
        self._calib_total_frames = 0
        self._calib_cell_counts.clear()
        self._calib_cell_sums.clear()

    @property
    def is_calibrating(self) -> bool:
        return self._calibrating

    @property
    def background_cells(self) -> List[Tuple[float, float]]:
        return self.points

    @property
    def calibration_progress(self) -> float:
        if not self._calibrating:
            return 1.0
        elapsed = time.monotonic() - getattr(self, "_calib_start_time", time.monotonic())
        dur = getattr(self, "_calib_duration_s", 5.0)
        return min(1.0, max(0.0, elapsed / dur))

    def record_calibration_frame(self, targets: List[RadarTarget]) -> None:
        """Ghi nhận 1 khung dữ liệu mục tiêu vào bộ tích lũy hiệu chuẩn nền"""
        self._calib_total_frames += 1
        seen_cells_in_frame = set()
        for t in targets:
            key = self._cell_key(t.x_m, t.y_m)
            if key not in seen_cells_in_frame:
                seen_cells_in_frame.add(key)
                self._calib_cell_counts[key] = self._calib_cell_counts.get(key, 0) + 1
                if key not in self._calib_cell_sums:
                    self._calib_cell_sums[key] = [0.0, 0.0, 0]
            self._calib_cell_sums[key][0] += t.x_m
            self._calib_cell_sums[key][1] += t.y_m
            self._calib_cell_sums[key][2] += 1

    def finish_calibration(self) -> List[Tuple[float, float]]:
        """Kết thúc thu thập, tính các điểm nền đạt ngưỡng >= 70% số khung và lưu vào background.json"""
        self._calibrating = False
        new_points: List[Tuple[float, float]] = []
        if self._calib_total_frames > 0:
            min_count = math.ceil(self._calib_total_frames * self.occupancy_ratio - 1e-9)
            for key, count in self._calib_cell_counts.items():
                if count >= min_count and count > 0:
                    sx, sy, n = self._calib_cell_sums[key]
                    mean_x = round(sx / n, 4)
                    mean_y = round(sy / n, 4)
                    new_points.append((mean_x, mean_y))
        self.points = new_points
        self.save()
        return self.points

    def calibrate(
        self,
        duration_s: float = 5.0,
        frames: Optional[List[List[RadarTarget]]] = None,
        frame_provider=None,
    ) -> List[Tuple[float, float]]:
        """
        Thực hiện hiệu chuẩn nền:
        - Nếu truyền `frames` (danh sách các khung mục tiêu, dùng cho kiểm thử hoặc xử lý lô):
          tính ngay lập tức và lưu kết quả.
        - Nếu truyền `frame_provider` (hàm trả về List[RadarTarget]): thu thập trong `duration_s` giây.
        - Nếu không truyền gì: bật cờ `start_calibration(duration_s)` để luồng Radar tự động thu thập.
        """
        self.start_calibration(duration_s=duration_s)
        if frames is not None:
            for frame_targets in frames:
                self.record_calibration_frame(frame_targets)
            return self.finish_calibration()
        elif callable(frame_provider):
            while time.monotonic() < self._calib_end_time:
                batch = frame_provider()
                if batch is not None:
                    self.record_calibration_frame(batch)
                time.sleep(0.05)
            return self.finish_calibration()
        return self.points

    def is_background(self, target_or_x, y_m: Optional[float] = None) -> bool:
        """Kiểm tra mục tiêu (RadarTarget hoặc tọa độ x_m, y_m) có nằm trong bán kính tolerance_m quanh điểm nền không"""
        if y_m is None:
            tx, ty = target_or_x.x_m, target_or_x.y_m
        else:
            tx, ty = float(target_or_x), float(y_m)
        for bx, by in self.points:
            if math.hypot(tx - bx, ty - by) <= self.tolerance_m:
                return True
        return False

    def filter_foreground(self, targets: List[RadarTarget]) -> List[RadarTarget]:
        """Loại bỏ tất cả các mục tiêu trùng với nền"""
        return [t for t in targets if not self.is_background(t)]

    def clear(self) -> None:
        """Xóa toàn bộ điểm nền và cập nhật tệp lưu trữ"""
        self._calibrating = False
        self.points.clear()
        self.save()

    def save(self) -> None:
        """Ghi danh sách điểm nền xuống background.json"""
        if not self.storage_path:
            return
        payload = {
            "grid_size_m": self.grid_size_m,
            "occupancy_ratio": self.occupancy_ratio,
            "tolerance_m": self.tolerance_m,
            "points": [{"x_m": p[0], "y_m": p[1]} for p in self.points],
        }
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.storage_path)), exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print("Lỗi lưu background.json:", e)

    def load(self) -> List[Tuple[float, float]]:
        """Đọc danh sách điểm nền từ background.json nếu có"""
        if not self.storage_path or not os.path.exists(self.storage_path):
            self.points = []
            return self.points
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            pts = data.get("points", [])
            self.points = [(float(p["x_m"]), float(p["y_m"])) for p in pts if "x_m" in p and "y_m" in p]
        except Exception:
            self.points = []
        return self.points

    def get_points_count(self) -> int:
        """Trả về số lượng điểm nền đang áp dụng"""
        return len(self.points)


def _hungarian_assign_radar(cost_matrix: np.ndarray, max_valid_cost: float = 1e5) -> List[Tuple[int, int]]:
    """Thuật toán Hungarian tối ưu 1-1 toàn cục cho ghép cặp mục tiêu Radar."""
    cost = np.asarray(cost_matrix, dtype=np.float64)
    if cost.size == 0 or cost.shape[0] == 0 or cost.shape[1] == 0:
        return []

    n_rows, n_cols = cost.shape
    transposed = False
    if n_rows > n_cols:
        cost = cost.T
        n_rows, n_cols = cost.shape
        transposed = True

    u = np.zeros(n_rows + 1, dtype=np.float64)
    v = np.zeros(n_cols + 1, dtype=np.float64)
    p = np.zeros(n_cols + 1, dtype=np.int32)
    way = np.zeros(n_cols + 1, dtype=np.int32)

    for i in range(1, n_rows + 1):
        p[0] = i
        j0 = 0
        minv = np.full(n_cols + 1, np.inf, dtype=np.float64)
        used = np.zeros(n_cols + 1, dtype=bool)
        row_i = cost[i - 1]
        while True:
            used[j0] = True
            i0 = int(p[j0])
            delta = np.inf
            j1 = 0
            cur_row = cost[i0 - 1] if i0 > 0 else row_i
            for j in range(1, n_cols + 1):
                if not used[j]:
                    cur = float(cur_row[j - 1]) - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            for j in range(n_cols + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = int(way[j0])
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    pairs: List[Tuple[int, int]] = []
    for j in range(1, n_cols + 1):
        if p[j] > 0:
            r_idx = int(p[j] - 1)
            c_idx = int(j - 1)
            if float(cost[r_idx, c_idx]) < max_valid_cost:
                if transposed:
                    pairs.append((c_idx, r_idx))
                else:
                    pairs.append((r_idx, c_idx))
    return pairs


class _TrackState:
    """Trạng thái nội bộ Kalman Filter 2D [x, y, vx, vy] & cửa sổ trượt TTC của một quỹ đạo Radar."""
    _H = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
    ], dtype=np.float64)

    def __init__(self, track_id: int, target: RadarTarget, timestamp: float):
        self.id = track_id
        self.x_m = float(target.x_m)
        self.y_m = float(target.y_m)
        self.distance_m = float(target.distance_m)
        self.prev_raw_distance_m = float(target.distance_m)
        self.speed_kmh = float(target.speed_kmh)
        self.closing_speed_mps = 0.0
        self.has_velocity_sample = False
        self.resolution = target.resolution
        self.age_frames = 1
        self.consecutive_hits = 1
        self.missed_frames = 0
        self.confirmed = False
        self.last_timestamp = timestamp
        self.vx_mps = 0.0
        self.vy_mps = 0.0

        # Kalman Filter 2D Constant-Velocity [x, y, vx, vy]
        init_vy = max(-15.0, min(15.0, float(target.speed_kmh) / 3.6)) if abs(target.speed_kmh) > 0.2 else 0.0
        self.kf_state = np.array([self.x_m, self.y_m, 0.0, init_vy], dtype=np.float64)
        self.kf_P = np.diag([0.05, 0.05, 1.2, 1.2]).astype(np.float64)
        self.pred_state = self.kf_state.copy()
        self.pred_P = self.kf_P.copy()

        # Cửa sổ trượt N=6 khung cho hồi quy tuyến tính khoảng cách theo thời gian -> closing_speed & TTC ổn định
        self.dist_history: deque = deque([(float(timestamp), float(target.distance_m))], maxlen=6)

    def predict_kf(self, dt: float) -> Tuple[np.ndarray, np.ndarray]:
        dt_c = max(0.01, min(0.50, float(dt)))
        F = np.array([
            [1.0, 0.0, dt_c, 0.0],
            [0.0, 1.0, 0.0, dt_c],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ], dtype=np.float64)
        Q = np.diag([0.012 * dt_c, 0.012 * dt_c, 0.65 * dt_c, 0.65 * dt_c]).astype(np.float64)
        self.pred_state = F @ self.kf_state
        self.pred_P = F @ self.kf_P @ F.T + Q
        return self.pred_state, self.pred_P

    def update_kf(self, det_x: float, det_y: float, r_var: float = 0.025) -> None:
        R = np.diag([r_var, r_var]).astype(np.float64)
        z = np.array([det_x, det_y], dtype=np.float64)
        y = z - (self._H @ self.pred_state)
        S = self._H @ self.pred_P @ self._H.T + R
        K = self.pred_P @ self._H.T @ np.linalg.inv(S)
        self.kf_state = self.pred_state + K @ y
        I4 = np.eye(4, dtype=np.float64)
        self.kf_P = (I4 - K @ self._H) @ self.pred_P


class RadarTracker:
    """
    Mục 1.3: Bộ theo dõi mục tiêu đa khung (Kalman Filter 2D + Hungarian Assignment + Rolling TTC):
    - Ghép 1-1 tối ưu toàn cục bằng Hungarian Algorithm kết hợp khoảng cách Mahalanobis & tính nhất quán vận tốc,
      tránh hoán đổi ID khi hai mục tiêu cắt ngang nhau.
    - Lọc nhiễu vị trí và vận tốc bằng Kalman Filter 2D [x, y, vx, vy] (hoặc đạo hàm thô khi alpha=1.0).
    - Tính `closing_speed_mps` từ hồi quy tuyến tính cửa sổ trượt N=6 khung kết hợp vận tốc hướng tâm Kalman.
    - Xác nhận mục tiêu hợp lệ khi xuất hiện liên tục >= `confirm_frames` (3 khung), xóa sau `max_missed_frames` (5 khung).
    """

    def __init__(
        self,
        association_gate_m: float = 0.5,
        confirm_frames: int = 3,
        max_missed_frames: int = 5,
        smoothing_alpha: float = 0.6,
        min_closing_speed_mps: float = 0.3,
        default_dt_sec: float = 0.1,
    ):
        self.association_gate_m = float(association_gate_m)
        self.confirm_frames = int(confirm_frames)
        self.max_missed_frames = int(max_missed_frames)
        self.smoothing_alpha = float(smoothing_alpha)
        self.min_closing_speed_mps = float(min_closing_speed_mps)
        self.default_dt_sec = float(default_dt_sec)

        self.tracks: Dict[int, _TrackState] = {}
        self._next_id = 1
        self._last_step_time: Optional[float] = None

    def reset(self) -> None:
        self.tracks.clear()
        self._next_id = 1
        self._last_step_time = None

    @staticmethod
    def _rolling_closing_speed(history: deque) -> Optional[float]:
        """Hồi quy tuyến tính OLS d(t) trên cửa sổ trượt N khung -> trả về -dD/dt mượt."""
        if len(history) < 3:
            return None
        t0 = history[0][0]
        ts = [p[0] - t0 for p in history]
        ds = [p[1] for p in history]
        if ts[-1] < 0.08:
            return None
        n = float(len(ts))
        mean_t = sum(ts) / n
        mean_d = sum(ds) / n
        denom = sum((t - mean_t) ** 2 for t in ts)
        if denom <= 1e-8:
            return None
        num = sum((t - mean_t) * (d - mean_d) for t, d in zip(ts, ds))
        slope = num / denom
        return -slope

    def update_with_status(
        self,
        detections: List[RadarTarget],
        timestamp: Optional[float] = None,
    ) -> Tuple[List[RadarTarget], List[str]]:
        """
        Cập nhật bộ theo dõi với danh sách mục tiêu của khung hiện tại.
        Trả về: (confirmed_targets, detection_statuses)
        """
        if timestamp is None:
            if self._last_step_time is None:
                now = 0.0
            else:
                now = self._last_step_time + self.default_dt_sec
        else:
            now = float(timestamp)
        self._last_step_time = now

        track_ids = list(self.tracks.keys())
        unmatched_tracks = set(track_ids)
        unmatched_dets = set(range(len(detections)))

        # 1. Dự đoán Kalman và xây ma trận chi phí Mahalanobis + Hungarian Assignment
        INF_COST = 1e6
        n_t = len(track_ids)
        n_d = len(detections)
        cost_mat = np.full((n_t, n_d), INF_COST, dtype=np.float64)
        R_gate = np.diag([0.04, 0.04]).astype(np.float64)

        for r, tid in enumerate(track_ids):
            tr = self.tracks[tid]
            dt_pred = now - tr.last_timestamp
            if dt_pred <= 1e-4:
                dt_pred = self.default_dt_sec
            pred_state, pred_P = tr.predict_kf(dt_pred)
            pred_x = float(pred_state[0])
            pred_y = float(pred_state[1])
            S_inv = np.linalg.inv(pred_P[:2, :2] + R_gate)
            eff_gate = self.association_gate_m * (1.0 + 0.15 * min(tr.missed_frames, 3))

            for c, det in enumerate(detections):
                eucl = math.hypot(det.x_m - pred_x, det.y_m - pred_y)
                if eucl <= eff_gate:
                    nu = np.array([det.x_m - pred_x, det.y_m - pred_y], dtype=np.float64)
                    maha_sq = float(nu.T @ S_inv @ nu)
                    vel_pen = 0.0
                    if abs(det.speed_kmh) >= 1.5 and abs(tr.speed_kmh) >= 1.5:
                        if (det.speed_kmh * tr.speed_kmh) < 0.0:
                            vel_pen = 0.8
                    cost_mat[r, c] = eucl + 0.18 * math.sqrt(max(0.0, maha_sq)) + vel_pen

        matched_pairs: List[Tuple[int, int]] = []
        if n_t > 0 and n_d > 0:
            for r_idx, c_idx in _hungarian_assign_radar(cost_mat, max_valid_cost=1e5):
                tid = track_ids[r_idx]
                matched_pairs.append((tid, c_idx))
                unmatched_tracks.discard(tid)
                unmatched_dets.discard(c_idx)

        alpha = self.smoothing_alpha
        det_status_map: Dict[int, str] = {}

        # 2. Cập nhật các Track ghép được
        for tid, d_idx in matched_pairs:
            tr = self.tracks[tid]
            det = detections[d_idx]

            dt = now - tr.last_timestamp
            if dt <= 1e-4:
                dt = self.default_dt_sec

            tr.dist_history.append((now, float(det.distance_m)))

            if alpha >= 0.999:
                # Chế độ không làm mượt (alpha = 1.0, giữ nguyên đạo hàm tức thời chuẩn xác cho kiểm thử)
                tr.vx_mps = (det.x_m - tr.x_m) / dt
                tr.vy_mps = (det.y_m - tr.y_m) / dt
                inst_closing_mps = (tr.prev_raw_distance_m - det.distance_m) / dt
                tr.closing_speed_mps = inst_closing_mps
                tr.has_velocity_sample = True
                tr.prev_raw_distance_m = det.distance_m
                tr.x_m = float(det.x_m)
                tr.y_m = float(det.y_m)
                tr.distance_m = math.hypot(tr.x_m, tr.y_m)
                tr.speed_kmh = float(det.speed_kmh)
                tr.kf_state = np.array([tr.x_m, tr.y_m, tr.vx_mps, tr.vy_mps], dtype=np.float64)
            else:
                # Kalman Filter 2D kết hợp Adaptive Measurement Noise theo smoothing_alpha
                alpha_c = max(0.15, min(0.95, alpha))
                r_var = 0.025 * ((0.60 / alpha_c) ** 1.5)
                tr.update_kf(det.x_m, det.y_m, r_var=r_var)

                tr.x_m = float(tr.kf_state[0])
                tr.y_m = max(0.05, float(tr.kf_state[1]))
                tr.vx_mps = float(tr.kf_state[2])
                tr.vy_mps = float(tr.kf_state[3])
                tr.distance_m = math.hypot(tr.x_m, tr.y_m)

                # Kết hợp tốc độ tiến gần từ: (1) Hồi quy trượt N=6 khung + (2) Vận tốc hướng tâm Kalman
                inst_closing_mps = (tr.prev_raw_distance_m - det.distance_m) / dt
                kf_closing = -(tr.x_m * tr.vx_mps + tr.y_m * tr.vy_mps) / max(0.15, tr.distance_m)
                reg_closing = self._rolling_closing_speed(tr.dist_history)

                if reg_closing is not None:
                    fused_closing = 0.62 * reg_closing + 0.38 * kf_closing
                elif tr.has_velocity_sample:
                    fused_closing = 0.55 * inst_closing_mps + 0.45 * kf_closing
                else:
                    fused_closing = inst_closing_mps

                vel_alpha = min(alpha * 0.50, 0.28)
                if not tr.has_velocity_sample:
                    tr.closing_speed_mps = fused_closing
                    tr.has_velocity_sample = True
                else:
                    # EMA chống gai đột biến trong khi vẫn bám nhanh xu hướng hồi quy N khung
                    close_alpha = max(vel_alpha, 0.45)
                    tr.closing_speed_mps = close_alpha * fused_closing + (1.0 - close_alpha) * tr.closing_speed_mps

                tr.prev_raw_distance_m = det.distance_m
                # Làm mượt vận tốc Doppler từ radar (giữ nguyên dấu âm = lại gần, dương = ra xa)
                tr.speed_kmh = vel_alpha * float(det.speed_kmh) + (1.0 - vel_alpha) * tr.speed_kmh

            tr.resolution = det.resolution
            tr.last_timestamp = now

            tr.age_frames += 1
            tr.consecutive_hits += 1
            tr.missed_frames = 0
            if tr.consecutive_hits >= self.confirm_frames:
                tr.confirmed = True

            det_status_map[d_idx] = "được giữ" if tr.confirmed else "chưa đủ khung xác nhận"

        # 3. Xử lý các Track không có Detection trong khung này (trượt Kalman nhẹ qua vùng mất dấu tạm)
        to_delete: List[int] = []
        for tid in unmatched_tracks:
            tr = self.tracks[tid]
            tr.missed_frames += 1
            if not tr.confirmed:
                # Cho phép nhấp nháy tối đa 1 khung trước khi xóa để mục tiêu thứ 2 không bị đặt lại liên tục
                if tr.missed_frames >= 2:
                    tr.consecutive_hits = 0
                    to_delete.append(tid)
            elif tr.missed_frames >= self.max_missed_frames:
                to_delete.append(tid)
            else:
                tr.kf_state = tr.pred_state.copy()
                tr.kf_P = tr.pred_P.copy()
                tr.kf_state[2] *= 0.85
                tr.kf_state[3] *= 0.85
                tr.x_m = float(tr.kf_state[0])
                tr.y_m = max(0.05, float(tr.kf_state[1]))
                tr.distance_m = math.hypot(tr.x_m, tr.y_m)
                tr.last_timestamp = now

        for tid in to_delete:
            del self.tracks[tid]

        # 4. Tạo Track mới cho các Detection chưa ghép
        for d_idx in sorted(unmatched_dets):
            det = detections[d_idx]
            tid = self._next_id
            self._next_id += 1
            tr = _TrackState(tid, det, now)
            if self.confirm_frames <= 1:
                tr.confirmed = True
                det_status_map[d_idx] = "được giữ"
            else:
                det_status_map[d_idx] = "chưa đủ khung xác nhận"
            self.tracks[tid] = tr

        # 5. Xuất danh sách mục tiêu hợp lệ (đã xác nhận)
        confirmed_targets: List[RadarTarget] = []
        for tid in sorted(self.tracks.keys()):
            tr = self.tracks[tid]
            if not tr.confirmed:
                continue

            if tr.closing_speed_mps > self.min_closing_speed_mps and tr.distance_m > 0:
                ttc = tr.distance_m / tr.closing_speed_mps
            else:
                ttc = None

            out_target = RadarTarget(
                target_id=tr.id,
                x_m=tr.x_m,
                y_m=tr.y_m,
                speed_kmh=float(tr.speed_kmh),
                valid=True,
                resolution=tr.resolution,
                closing_speed_mps=tr.closing_speed_mps,
                ttc_sec=ttc,
                age_frames=tr.age_frames,
                min_closing_speed_mps=self.min_closing_speed_mps,
            )
            confirmed_targets.append(out_target)

        det_statuses = [det_status_map.get(i, "chưa đủ khung xác nhận") for i in range(len(detections))]
        return confirmed_targets, det_statuses

    def update(
        self,
        detections: List[RadarTarget],
        timestamp: Optional[float] = None,
    ) -> List[RadarTarget]:
        """Tương thích ngược: chỉ trả về danh sách mục tiêu đã xác nhận"""
        confirmed, _ = self.update_with_status(detections, timestamp=timestamp)
        return confirmed


RADAR_DEBUG_LOG_PATH = os.path.join(LOGS_DIR, "radar_debug.log")


class RadarDebugLogger:
    """
    Bộ ghi log gỡ lỗi Radar (Giai đoạn 2A - Bước A & B):
    Ghi tệp logs/radar_debug.log, mỗi giây một dòng tổng hợp:
    - số mục tiêu thô
    - số bị loại theo từng lý do: dưới min_range, ngoài góc, trùng nền, chưa đủ khung xác nhận
    - số track đang sống
    - cảnh báo khi 2 mục tiêu gần nhau < association_gate_m
    """

    def __init__(self, log_path: Optional[str] = None, interval_sec: float = 1.0):
        self.log_path = log_path if log_path is not None else RADAR_DEBUG_LOG_PATH
        self.interval_sec = interval_sec
        self.last_log_time: Optional[float] = None
        self.raw_count = 0
        self.rej_min_range = 0
        self.rej_angle_range = 0
        self.rej_background = 0
        self.pending_confirm = 0
        self.live_tracks = 0
        self.bg_points_count = 0
        self.proximity_warnings: List[str] = []
        os.makedirs(os.path.dirname(os.path.abspath(self.log_path)), exist_ok=True)

    def log_note(self, message: str) -> None:
        """Ghi ngay một dòng thông tin chẩn đoán/khởi tạo vào logs/radar_debug.log"""
        ts_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.log_path)), exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(f"[{ts_str}] {message}\n")
        except Exception:
            pass

    def record_frame(
        self,
        raw_count: int,
        rej_min_range: int,
        rej_angle_range: int,
        rej_background: int,
        pending_confirm: int,
        live_tracks: int,
        bg_points_count: int,
        proximity_warning: Optional[str] = None,
        timestamp: Optional[float] = None,
    ) -> None:
        self.raw_count += raw_count
        self.rej_min_range += rej_min_range
        self.rej_angle_range += rej_angle_range
        self.rej_background += rej_background
        self.pending_confirm += pending_confirm
        self.live_tracks = live_tracks
        self.bg_points_count = bg_points_count
        if proximity_warning and proximity_warning not in self.proximity_warnings:
            self.proximity_warnings.append(proximity_warning)

        now = time.monotonic() if timestamp is None else float(timestamp)
        if self.last_log_time is None or now < self.last_log_time:
            self.last_log_time = now
        if now - self.last_log_time >= self.interval_sec:
            self.flush(now)

    def flush(self, now: Optional[float] = None) -> None:
        if now is None:
            now = time.monotonic()
        ts_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = (
            f"[{ts_str}] Thô: {self.raw_count:2d} | "
            f"Dưới min_range: {self.rej_min_range:2d} | "
            f"Ngoài góc/tầm: {self.rej_angle_range:2d} | "
            f"Trùng nền: {self.rej_background:2d} | "
            f"Chưa đủ khung: {self.pending_confirm:2d} | "
            f"Đang sống: {self.live_tracks:2d} | "
            f"Điểm nền: {self.bg_points_count}"
        )
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.log_path)), exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
                for w in self.proximity_warnings:
                    f.write(f"[{ts_str}] [PROXIMITY WARNING] {w}\n")
        except Exception:
            pass
        self.last_log_time = now
        self.raw_count = 0
        self.rej_min_range = 0
        self.rej_angle_range = 0
        self.rej_background = 0
        self.pending_confirm = 0
        self.proximity_warnings = []


class RadarPipeline:
    """
    Chuỗi xử lý hợp nhất Tầng dữ liệu Radar (Giai đoạn 1 & 2A):
    Raw Targets -> Lọc phạm vi (1.2) -> Lọc nền BackgroundModel (1.4) -> RadarTracker & TTC (1.3).
    """

    def __init__(
        self,
        cfg: Optional[dict] = None,
        background_model: Optional[BackgroundModel] = None,
    ):
        self.cfg = cfg if cfg is not None else config_manager.data
        self.decoder = RadarStreamDecoder()
        self.background = (
            background_model
            if background_model is not None
            else BackgroundModel(
                storage_path=BACKGROUND_JSON_PATH,
                grid_size_m=float(self.cfg.get("background_grid_m", 0.10)),
                occupancy_ratio=float(self.cfg.get("background_occupancy_ratio", 0.70)),
                tolerance_m=float(self.cfg.get("background_tolerance_m", 0.15)),
            )
        )
        self.tracker = RadarTracker(
            association_gate_m=float(self.cfg.get("association_gate_m", 0.5)),
            confirm_frames=int(self.cfg.get("confirm_frames", 3)),
            max_missed_frames=int(self.cfg.get("max_missed_frames", 5)),
            smoothing_alpha=float(self.cfg.get("smoothing_alpha", 0.6)),
            min_closing_speed_mps=float(self.cfg.get("min_closing_speed_mps", 0.3)),
            default_dt_sec=1.0 / float(self.cfg.get("radar_sample_rate_hz", 10.0)),
        )
        self.debug_logger = RadarDebugLogger()
        self.last_raw_status: List[Dict[str, Any]] = []

    def reload_config(self, cfg: Optional[dict] = None) -> None:
        """Cập nhật tức thời các tham số từ config mà không cần khởi động lại"""
        if cfg is not None:
            self.cfg = cfg
        else:
            self.cfg = config_manager.data

        self.background.grid_size_m = float(self.cfg.get("background_grid_m", 0.10))
        self.background.occupancy_ratio = float(self.cfg.get("background_occupancy_ratio", 0.70))
        self.background.tolerance_m = float(self.cfg.get("background_tolerance_m", 0.15))
        self.background.load()

        self.tracker.association_gate_m = float(self.cfg.get("association_gate_m", 0.5))
        self.tracker.confirm_frames = int(self.cfg.get("confirm_frames", 3))
        self.tracker.max_missed_frames = int(self.cfg.get("max_missed_frames", 5))
        self.tracker.smoothing_alpha = float(self.cfg.get("smoothing_alpha", 0.6))
        self.tracker.min_closing_speed_mps = float(self.cfg.get("min_closing_speed_mps", 0.3))

    @property
    def debug_speed(self) -> bool:
        return bool(self.cfg.get("debug_radar_speed", False))

    @debug_speed.setter
    def debug_speed(self, val: bool) -> None:
        self.cfg["debug_radar_speed"] = bool(val)

    def start_background_calibration(self, duration_sec: float = 5.0) -> None:
        self.tracker.reset()
        self.background.start_calibration(duration_s=duration_sec)

    def clear_background(self) -> None:
        self.background.clear()

    def process_raw_targets(
        self,
        raw_targets: List[RadarTarget],
        timestamp: Optional[float] = None,
    ) -> List[RadarTarget]:
        """Xử lý 1 khung mục tiêu thô qua Lọc phạm vi -> Hiệu chuẩn/Lọc nền -> Tracker"""
        now = time.monotonic() if timestamp is None else float(timestamp)
        min_r = float(self.cfg.get("min_range_m", 0.5))
        max_r = float(self.cfg.get("max_range_m", 6.0))
        max_ang = float(self.cfg.get("max_angle_deg", 60.0))
        gate_m = float(self.cfg.get("association_gate_m", 0.5))

        raw_count = len(raw_targets)
        rej_min_range = 0
        rej_angle_range = 0
        rej_background = 0

        raw_status_list: List[Dict[str, Any]] = []
        in_range: List[RadarTarget] = []

        # 1. Lọc theo phạm vi và góc quét
        for t in raw_targets:
            if t.y_m <= 0 or t.distance_m < min_r:
                rej_min_range += 1
                raw_status_list.append({"target": t, "status": "dưới min_range"})
            elif t.distance_m > max_r or abs(t.angle_deg) > max_ang:
                rej_angle_range += 1
                raw_status_list.append({"target": t, "status": "ngoài góc"})
            else:
                in_range.append(t)

        # 2. Nếu đang trong thời gian thu thập hiệu chuẩn nền
        if self.background.is_calibrating:
            self.background.record_calibration_frame(in_range)
            if time.monotonic() >= self.background._calib_end_time:
                self.background.finish_calibration()
            self.last_raw_status = raw_status_list
            return []

        # 3. Loại bỏ các mục tiêu trùng với nền tĩnh trước khi đưa vào Tracker
        # Nền tĩnh chỉ áp dụng khi background.json tồn tại và có điểm
        foreground: List[RadarTarget] = []
        has_bg_points = (len(self.background.points) > 0)
        for t in in_range:
            if has_bg_points and self.background.is_background(t):
                rej_background += 1
                raw_status_list.append({"target": t, "status": "trùng nền"})
            else:
                foreground.append(t)

        # Cảnh báo khi 2 phát hiện gần nhau < association_gate_m
        prox_warn = None
        for i in range(len(foreground)):
            for j in range(i + 1, len(foreground)):
                d_ij = math.hypot(foreground[i].x_m - foreground[j].x_m, foreground[i].y_m - foreground[j].y_m)
                if d_ij < gate_m:
                    prox_warn = f"2 mục tiêu cách nhau {d_ij:.2f}m < gate {gate_m:.2f}m (Slot {foreground[i].target_id} và {foreground[j].target_id})"
                    break
            if prox_warn:
                break

        # 4. Theo dõi ID ổn định, làm mượt và tính đạo hàm khoảng cách (closing_speed_mps & TTC)
        tracked, det_statuses = self.tracker.update_with_status(foreground, timestamp=now)

        pending_confirm = 0
        for t, st in zip(foreground, det_statuses):
            raw_status_list.append({"target": t, "status": st})
            if st == "chưa đủ khung xác nhận":
                pending_confirm += 1

        raw_status_list.sort(key=lambda item: item["target"].target_id)
        self.last_raw_status = raw_status_list

        self.debug_logger.record_frame(
            raw_count=raw_count,
            rej_min_range=rej_min_range,
            rej_angle_range=rej_angle_range,
            rej_background=rej_background,
            pending_confirm=pending_confirm,
            live_tracks=len(tracked),
            bg_points_count=len(self.background.points),
            proximity_warning=prox_warn,
            timestamp=now,
        )

        # Chế độ gỡ lỗi đối chiếu chiều dấu tốc độ radar vs tốc độ đạo hàm
        if self.cfg.get("debug_radar_speed", False) and tracked:
            for t in tracked:
                ttc_s = f"{t.ttc_sec:.2f}s" if t.ttc_sec is not None else "None"
                print(
                    f"[DEBUG RADAR] ID={t.id} | dist={t.distance_m:.2f}m | "
                    f"speed_kmh(radar)={t.speed_kmh:+.2f} km/h ({t.speed_kmh / 3.6:+.2f} m/s) | "
                    f"closing_speed_mps( đạo hàm )={t.closing_speed_mps:+.2f} m/s | TTC={ttc_s}"
                )

        return tracked

    def process_bytes(
        self,
        data: bytes,
        timestamp: Optional[float] = None,
    ) -> List[List[RadarTarget]]:
        """Giải mã luồng byte và xử lý từng khung qua toàn bộ pipeline"""
        frames = self.decoder.feed(data)
        results: List[List[RadarTarget]] = []
        for raw_targets in frames:
            results.append(self.process_raw_targets(raw_targets, timestamp=timestamp))
        return results


# ================= TẦNG QTHREAD DRIVER CHO GIAO DIỆN PYQT6 =================
try:
    from PyQt6.QtCore import QThread, pyqtSignal

    class RadarWorker(QThread):
        """
        Luồng nền QThread đọc dữ liệu Radar liên tục và phát tín hiệu về MainWindow.
        Hỗ trợ tự động kết nối lại có giới hạn khi rút/lỏng cáp COM (Mục 3.2).
        """
        targets_ready = pyqtSignal(list)       # Phát danh sách List[RadarTarget]
        raw_status_ready = pyqtSignal(list)    # Phát danh sách trạng thái mục tiêu thô (Debug Mode)
        status_changed = pyqtSignal(str, bool) # (Thông điệp trạng thái, là_đã_kết_nối)

        def __init__(self, port: str = "COM5", baudrate: int = 256000, is_simulation: bool = False):
            super().__init__()
            self.port = port
            self.baudrate = baudrate
            self.is_simulation = is_simulation
            self.is_running = False
            self.serial_conn: Optional[serial.Serial] = None
            self.pipeline = RadarPipeline()

        def set_simulation(self, sim_mode: bool) -> None:
            self.is_simulation = sim_mode

        def start_background_calibration(self, duration_s: float = 5.0) -> None:
            """Kích hoạt hiệu chuẩn nền trong duration_s giây"""
            self.pipeline.tracker.reset()
            self.pipeline.background.start_calibration(duration_s=duration_s)
            self.status_changed.emit(f"Đang hiệu chuẩn nền ({duration_s:.0f}s)...", True)

        def clear_background(self) -> None:
            """Xóa dữ liệu nền đã lưu"""
            self.pipeline.background.clear()
            self.status_changed.emit("Đã xóa dữ liệu nền", True)

        def stop(self) -> None:
            self.is_running = False
            if self.serial_conn and self.serial_conn.is_open:
                try:
                    self.serial_conn.close()
                except Exception:
                    pass
            self.wait(2000)

        def run(self) -> None:
            self.is_running = True
            self.pipeline.reload_config()
            self.pipeline.tracker.reset()
            self.pipeline.decoder.reset()

            if self.is_simulation:
                self._run_simulation()
            else:
                self._run_hardware()

        def _run_simulation(self) -> None:
            """Mô phỏng dữ liệu di chuyển khi chạy chế độ Demo"""
            self.status_changed.emit("Đã kết nối (Mô phỏng)", True)

            t1_y = 5.6
            t1_x = 0.3
            t1_v_mps = -2.2  # Đang tiến lại gần 2.2 m/s (~ -7.9 km/h)

            t2_x = -2.0
            t2_y = 3.2

            dt = 0.1
            sim_time = time.monotonic()

            while self.is_running and self.is_simulation:
                sim_time += dt
                t1_y += t1_v_mps * dt
                if t1_y <= 1.0:
                    t1_v_mps = 1.8  # Lùi ra xa
                elif t1_y >= 5.6:
                    t1_v_mps = -2.2  # Tiến lại gần
                    t1_x = random.uniform(-0.5, 0.5)

                t2_x += 0.05
                if t2_x > 2.0:
                    t2_x = -2.0

                raw_list = [
                    RadarTarget(1, t1_x, t1_y, speed_kmh=t1_v_mps * 3.6, valid=True, resolution=300),
                    RadarTarget(2, t2_x, t2_y, speed_kmh=0.0, valid=True, resolution=300),
                ]
                tracked = self.pipeline.process_raw_targets(raw_list, timestamp=sim_time)
                self.targets_ready.emit(tracked)
                self.raw_status_ready.emit(self.pipeline.last_raw_status)
                time.sleep(dt)

        def _send_multitarget_init(self, ser: serial.Serial) -> Dict[str, Any]:
            """Gửi chuỗi lệnh bật chế độ Đa mục tiêu (0x0090) có kiểm tra ACK & truy vấn chế độ (0x0091) cho HLK-LD2450"""
            return configure_ld2450_multitarget(ser, logger=self.pipeline.debug_logger)

        def _run_hardware(self) -> None:
            """
            Kết nối cổng COM thật, giải mã luồng nhị phân và tự động kết nối lại
            có giới hạn số lần khi mất kết nối (Mục 3.2).
            """
            max_attempts = int(self.pipeline.cfg.get("max_reconnect_attempts", 5))
            retry_interval = float(self.pipeline.cfg.get("reconnect_interval_sec", 1.5))
            attempt = 0

            while self.is_running and not self.is_simulation:
                # 1. Mở cổng Serial nếu chưa mở
                if self.serial_conn is None or not self.serial_conn.is_open:
                    try:
                        self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=0.2)
                        init_res = self._send_multitarget_init(self.serial_conn)
                        self.pipeline.decoder.reset()
                        attempt = 0
                        mode_tag = ""
                        if init_res.get("mode") == 2:
                            mode_tag = " | Multi-Target"
                        elif init_res.get("mode") == 1:
                            mode_tag = " | CẢNH BÁO: Single-Target!"
                        elif not init_res.get("enable_ack"):
                            mode_tag = " | Chưa xác nhận ACK"
                        self.status_changed.emit(f"Đã kết nối ({self.port}{mode_tag})", True)
                    except Exception as e:
                        attempt += 1
                        if attempt > max_attempts:
                            self.status_changed.emit(
                                f"Mất kết nối ({self.port}) - Quá {max_attempts} lần thử", False
                            )
                            self.is_running = False
                            break
                        self.status_changed.emit(
                            f"Mất kết nối ({self.port}) - Thử lại {attempt}/{max_attempts}...", False
                        )
                        # Ngủ từng bước nhỏ để có thể dừng luồng tức thì khi đóng ứng dụng
                        slept = 0.0
                        while slept < retry_interval and self.is_running:
                            time.sleep(0.1)
                            slept += 0.1
                        continue

                # 2. Đọc và giải mã gói tin
                try:
                    waiting = self.serial_conn.in_waiting
                    data = self.serial_conn.read(waiting if waiting > 0 else 1)
                    if not data:
                        continue

                    now = time.monotonic()
                    batches = self.pipeline.process_bytes(data, timestamp=now)
                    for tracked_targets in batches:
                        self.targets_ready.emit(tracked_targets)
                        self.raw_status_ready.emit(self.pipeline.last_raw_status)

                except Exception:
                    # Rút cáp hoặc lỗi I/O giữa chừng -> đóng cổng và chuyển sang chu kỳ tự kết nối lại
                    try:
                        if self.serial_conn:
                            self.serial_conn.close()
                    except Exception:
                        pass
                    self.serial_conn = None
                    self.targets_ready.emit([])
                    self.status_changed.emit(f"Mất kết nối ({self.port})", False)

except ImportError:
    pass
