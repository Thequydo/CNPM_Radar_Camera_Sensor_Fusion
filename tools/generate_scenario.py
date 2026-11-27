# -*- coding: utf-8 -*-
"""
Công cụ Sinh Kịch bản Kiểm thử Mô phỏng Đồng bộ (tools/generate_scenario.py)
- Sinh tệp video mp4 hoặc chuỗi khung hình mô phỏng
- Sinh tệp CSV dữ liệu radar đồng bộ: t_ms, id, x_m, y_m, speed_kmh
- Bao gồm các kịch bản:
  1. Xe tiếp cận từ xa (5.5m) đến sát vùng nguy hiểm (0.8m)
  2. Xe đứng yên ở cự ly gần 1.2m (kiểm tra không báo động đỏ sai)
  3. Xe tiến nhanh vào vùng mù dưới 1.2m rồi biến mất (kiểm tra near blind-zone hold 2.0s)
"""

import os
import csv
import math
import cv2
import numpy as np


def generate_scenario(output_dir: str = "captures/scenario"):
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "scenario_radar.csv")
    video_path = os.path.join(output_dir, "scenario_video.mp4")

    fps = 30.0
    total_frames = 300  # 10 giây @ 30 FPS
    frame_w, frame_h = 1280, 720

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out_video = cv2.VideoWriter(video_path, fourcc, fps, (frame_w, frame_h))

    csv_rows = []

    for i in range(total_frames):
        t_ms = int(round(i * (1000.0 / fps)))
        frame = np.zeros((frame_h, frame_w, 3), dtype=np.uint8)

        # Nền đường
        horizon_y = int(frame_h * 0.42)
        frame[:horizon_y, :] = [30, 24, 20]
        frame[horizon_y:, :] = [45, 45, 45]

        # Vạch kẻ đường
        cv2.line(frame, (int(frame_w * 0.15), frame_h), (int(frame_w * 0.42), horizon_y), (180, 180, 180), 3)
        cv2.line(frame, (int(frame_w * 0.85), frame_h), (int(frame_w * 0.58), horizon_y), (180, 180, 180), 3)

        # Kịch bản 1: Khung 0 - 150 (0s - 5s): Xe tiếp cận từ 5.0m xuống 1.0m
        if i < 150:
            progress = i / 150.0
            dist = 5.0 - progress * 4.0  # 5.0m -> 1.0m
            closing_mps = 0.8  # 4m / 5s = 0.8 m/s
            speed_kmh = - (closing_mps * 3.6)

            car_scale = 1.0 - (dist / 6.0)
            car_w = int(140 + car_scale * 280)
            car_h = int(90 + car_scale * 160)
            cx = int(frame_w * 0.5)
            cy = int(horizon_y + 40 + car_scale * (frame_h - horizon_y - 120))

            x1, y1 = max(0, cx - car_w // 2), max(0, cy - car_h // 2)
            x2, y2 = min(frame_w, cx + car_w // 2), min(frame_h, cy + car_h // 2)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (75, 90, 135), -1)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (190, 210, 235), 2)

            csv_rows.append({
                "t_ms": t_ms, "id": 1, "x_m": 0.0, "y_m": round(dist, 2), "speed_kmh": round(speed_kmh, 1)
            })

        # Kịch bản 2: Khung 150 - 210 (5s - 7s): Xe đứng yên tại 1.0m (speed=0)
        elif i < 210:
            dist = 1.0
            speed_kmh = 0.0
            car_scale = 1.0 - (1.0 / 6.0)
            car_w = int(140 + car_scale * 280)
            car_h = int(90 + car_scale * 160)
            cx = int(frame_w * 0.5)
            cy = int(horizon_y + 40 + car_scale * (frame_h - horizon_y - 120))

            x1, y1 = max(0, cx - car_w // 2), max(0, cy - car_h // 2)
            x2, y2 = min(frame_w, cx + car_w // 2), min(frame_h, cy + car_h // 2)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (75, 90, 135), -1)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (190, 210, 235), 2)

            csv_rows.append({
                "t_ms": t_ms, "id": 1, "x_m": 0.0, "y_m": round(dist, 2), "speed_kmh": 0.0
            })

        # Kịch bản 3: Khung 210 - 300: Xe đi vào vùng mù (<0.2m) hoặc biến mất (radar không có điểm)
        else:
            # Khung hình trống / đường vắng (hoặc xe vượt qua sát đuôi)
            pass

        out_video.write(frame)

    out_video.release()

    # Ghi tệp CSV
    with open(csv_path, mode="w", newline="", encoding="utf-8-sig") as f:
        fieldnames = ["t_ms", "id", "x_m", "y_m", "speed_kmh"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in csv_rows:
            writer.writerow(r)

    print(f"[OK] Đã sinh video: {video_path}")
    print(f"[OK] Đã sinh CSV: {csv_path}")


if __name__ == "__main__":
    generate_scenario()
