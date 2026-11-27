# -*- coding: utf-8 -*-
"""
Kiểm thử Giai đoạn 6: Chế độ Mô phỏng Đồng bộ & Độ ổn định Hệ thống
- Kiểm tra nạp và đồng bộ mốc thời gian CSV trong SimulationPlayer
- Kiểm tra tạo khung hình mô phỏng và mục tiêu radar đồng bộ
- Kiểm tra cơ chế tắt luồng an toàn (graceful shutdown)
"""

import os
import pytest
import numpy as np

from simulation_player import SimulationPlayer
from radar_parser import RadarTarget


def test_simulation_player_load_csv_timeline(tmp_path):
    """Kiểm tra đọc timeline CSV t_ms, id, x_m, y_m, speed_kmh"""
    csv_file = str(tmp_path / "test_sim.csv")
    with open(csv_file, "w", encoding="utf-8-sig") as f:
        f.write("t_ms,id,x_m,y_m,speed_kmh\n")
        f.write("0,1,0.0,5.0,-15.0\n")
        f.write("33,1,0.0,4.8,-15.0\n")
        f.write("66,1,0.0,4.6,-15.0\n")

    player = SimulationPlayer(radar_csv_path=csv_file, fps=30.0)
    player.load_radar_csv(csv_file)

    assert len(player.radar_timeline) >= 2
    # Frame 0
    t0 = player.radar_timeline.get(0, [])
    assert len(t0) == 1
    assert t0[0].target_id == 1
    assert t0[0].y_m == 5.0
    assert t0[0].speed_kmh == -15.0


def test_simulation_player_synthesizes_radar_targets():
    """Kiểm tra tự động tổng hợp mục tiêu giả lập khi không có file CSV"""
    player = SimulationPlayer()
    targets_f0 = player._synthesize_radar_targets(0)
    assert len(targets_f0) == 1
    t = targets_f0[0]
    assert t.target_id == 1
    assert t.valid is True
    assert 0.8 <= t.y_m <= 6.0


def test_simulation_player_synthesizes_frame():
    """Kiểm tra tạo khung hình mô phỏng chuẩn kích thước 1280x720"""
    player = SimulationPlayer()
    frame = player._synthesize_simulation_frame(45)
    assert isinstance(frame, np.ndarray)
    assert frame.shape == (720, 1280, 3)
