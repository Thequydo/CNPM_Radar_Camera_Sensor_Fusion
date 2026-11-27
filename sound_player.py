# -*- coding: utf-8 -*-
"""
Bộ phát Âm thanh Cảnh báo Đa luồng (Giai đoạn 2 - Mục 2.2)
- Luồng riêng biệt (Daemon Thread), không chặn luồng giao diện PyQt6.
- Mức Vàng ("Có vật trong vùng cảnh báo"): bíp ngắn mỗi 1.5 giây.
- Mức Đỏ ("Nguy cơ va chạm"): bíp dồn dập mỗi 0.4 giây.
- Hỗ trợ công tắc tắt tiếng (Mute) tức thời.
"""

import sys
import time
import threading
from typing import Optional

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


class SoundPlayer:
    """Quản lý phát âm thanh cảnh báo công nghiệp không chặn giao diện"""

    def __init__(self, is_muted: bool = False):
        self._is_muted = is_muted
        self._current_severity = "An toàn"
        self._running = True
        self._lock = threading.Lock()

        self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="SoundPlayerThread")
        self._thread.start()

    def set_severity(self, severity: str) -> None:
        """Cập nhật mức cảnh báo hiện tại từ AlertStateMachine"""
        with self._lock:
            self._current_severity = severity

    def set_muted(self, muted: bool) -> None:
        """Bật / tắt chế độ im lặng"""
        with self._lock:
            self._is_muted = bool(muted)

    def is_muted(self) -> bool:
        with self._lock:
            return self._is_muted

    def toggle_muted(self) -> bool:
        with self._lock:
            self._is_muted = not self._is_muted
            return self._is_muted

    def stop(self) -> None:
        """Dừng luồng âm thanh khi thoát ứng dụng"""
        self._running = False

    def _worker_loop(self) -> None:
        while self._running:
            with self._lock:
                muted = self._is_muted
                sev = self._current_severity

            if muted or sev == "An toàn":
                time.sleep(0.05)
                continue

            if sev == "Có vật trong vùng cảnh báo":
                # Mức VÀNG: Bíp ngắn (800 Hz, 100 ms) mỗi 1.5 giây
                self._play_beep(freq=800, duration_ms=100)
                # Ngủ ngắt quãng để phản ứng nhanh khi chuyển trạng thái
                self._sleep_interruptible(1.4)
            elif sev == "Nguy cơ va chạm":
                # Mức ĐỎ: Bíp dồn dập (1600 Hz, 150 ms) mỗi 0.4 giây
                self._play_beep(freq=1600, duration_ms=150)
                self._sleep_interruptible(0.25)
            else:
                time.sleep(0.05)

    def _sleep_interruptible(self, duration_sec: float) -> None:
        steps = int(duration_sec / 0.05)
        for _ in range(steps):
            if not self._running:
                break
            time.sleep(0.05)

    def _play_beep(self, freq: int, duration_ms: int) -> None:
        if HAS_WINSOUND:
            try:
                winsound.Beep(freq, duration_ms)
                return
            except Exception:
                pass

        # Fallback môi trường không hỗ trợ winsound
        try:
            sys.stdout.write('\a')
            sys.stdout.flush()
        except Exception:
            pass
