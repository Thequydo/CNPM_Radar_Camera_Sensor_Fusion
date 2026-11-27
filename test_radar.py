# -*- coding: utf-8 -*-
"""
Script Kiểm tra & Chẩn đoán Cảm biến Radar HLK-LD2450 (Giai đoạn 1)
Cách sử dụng:
    1. Kiểm tra qua toàn bộ Pipeline Giai đoạn 1 (Lọc + Nền + Tracker + Đối chiếu tốc độ):
       python test_radar.py COM5
    2. Hiệu chuẩn nền 5 giây để lọc bỏ mục tiêu ma tĩnh (lưu vào background.json) rồi giám sát tiếp:
       python test_radar.py COM5 --calibrate
    3. Xóa nền đã học (background.json):
       python test_radar.py COM5 --clear-bg
    4. Xem dữ liệu thô trực tiếp từ cảm biến (chưa lọc nền / chưa qua tracker):
       python test_radar.py COM5 --raw
"""

import sys
import time
import argparse
import serial
import serial.tools.list_ports

from radar_parser import (
    RadarPipeline,
    RadarStreamDecoder,
    LD2450_ENABLE_CONFIG_CMD,
    LD2450_MULTI_TARGET_CMD,
    LD2450_END_CONFIG_CMD,
)


def scan_ports():
    """Quét và trả về danh sách các cổng COM trên máy."""
    ports = list(serial.tools.list_ports.comports())
    return [p.device for p in ports]


def run_radar_test(
    port_name: str = "COM5",
    baudrate: int = 256000,
    raw_mode: bool = False,
    calibrate_first: bool = False,
    clear_bg: bool = False,
):
    pipeline = RadarPipeline()
    pipeline.debug_speed = True  # Luôn bật đối chiếu speed_kmh và closing_speed_mps khi chạy test

    if clear_bg:
        pipeline.clear_background()
        print("[HIỆU CHUẨN NỀN] Đã xóa toàn bộ điểm nền tĩnh trong background.json.")

    print("=" * 78)
    print("      CHƯƠNG TRÌNH KIỂM TRA RADAR HLK-LD2450 - GIAI ĐOẠN 1")
    print("=" * 78)
    print(f"[CẤU HÌNH] Cổng: {port_name} | Baudrate: {baudrate} | Chế độ: {'THÔ (RAW)' if raw_mode else 'PIPELINE GIAI ĐOẠN 1'}")
    print(f"[NỀN TĨNH] Số ô lưới nền tĩnh đang nạp từ background.json: {len(pipeline.background.background_cells)}")

    try:
        ser = serial.Serial(port_name, baudrate, timeout=0.05)
    except serial.SerialException as e:
        print(f"\n[LỖI KHÔNG MỞ ĐƯỢC CỔNG {port_name}]")
        print(f"Chi tiết lỗi: {e}")
        print("\n-> HƯỚNG DẪN XỬ LÝ:")
        print("   1. Đảm bảo đã TẮT phần mềm giám sát chính vì một cổng COM chỉ mở được ở 1 nơi.")
        print("   2. Kiểm tra dây cáp USB-TTL.")
        avail = scan_ports()
        if avail:
            print(f"   3. Các cổng COM đang có trên máy: {', '.join(avail)}")
        return

    print(f"[KẾT NỐI] Đã mở thành công cổng {port_name}.")
    print("-> Đang kích hoạt chế độ Đa mục tiêu (Multi-Target Tracking)...")

    try:
        ser.write(LD2450_ENABLE_CONFIG_CMD)
        time.sleep(0.05)
        ser.write(LD2450_MULTI_TARGET_CMD)
        time.sleep(0.05)
        ser.write(LD2450_END_CONFIG_CMD)
        time.sleep(0.05)
        if ser.in_waiting:
            ser.read(ser.in_waiting)
    except Exception as e:
        print(f"[CẢNH BÁO] Lỗi gửi lệnh cấu hình (bỏ qua): {e}")

    if calibrate_first and not raw_mode:
        print("\n[HIỆU CHUẨN NỀN 5 GIÂY] Vui lòng ĐỂ TRỐNG vùng trước radar trong 5 giây...")
        pipeline.start_background_calibration(duration_sec=5.0)

    print("-> Bắt đầu đọc dữ liệu thời gian thực. Nhấn Ctrl + C để dừng.\n")
    print("-" * 78)

    raw_decoder = RadarStreamDecoder()
    packet_count = 0
    last_print_time = 0.0
    was_calibrating = pipeline.background.is_calibrating

    try:
        while True:
            n = ser.in_waiting
            if n > 0:
                data = ser.read(n)
                now = time.time()

                if raw_mode:
                    frames = raw_decoder.feed(data)
                    for targets in frames:
                        packet_count += 1
                        if targets:
                            for t in targets:
                                print(
                                    f"[THÔ] Slot #{t.target_id}: "
                                    f"Khoảng cách = {t.distance_m:.2f} m | "
                                    f"X = {t.x_m:+.2f} m | Y = {t.y_m:.2f} m | "
                                    f"Góc = {t.angle_deg:+.1f}° | "
                                    f"speed_kmh = {t.speed_kmh:+.2f} km/h | "
                                    f"res = {t.resolution_mm} mm"
                                )
                            last_print_time = now
                        else:
                            if now - last_print_time >= 0.5:
                                sys.stdout.write(
                                    f"\r[KHÔNG CÓ MỤC TIÊU THÔ] Đã nhận {packet_count} gói hợp lệ...    "
                                )
                                sys.stdout.flush()
                                last_print_time = now
                else:
                    # Tách từng gói qua decoder của pipeline để đếm số gói chính xác
                    frames = pipeline.decoder.feed(data)
                    for raw_targets in frames:
                        packet_count += 1
                        confirmed = pipeline.process_raw_targets(raw_targets, timestamp=now)

                        if was_calibrating and not pipeline.background.is_calibrating:
                            was_calibrating = False
                            print(
                                f"\n[HOÀN TẤT HIỆU CHUẨN NỀN] Đã lưu {len(pipeline.background.background_cells)} "
                                f"ô nền tĩnh vào background.json! Bắt đầu lọc mục tiêu ma...\n"
                            )

                        if pipeline.background.is_calibrating:
                            if now - last_print_time >= 0.25:
                                pct = int(pipeline.background.calibration_progress * 100)
                                sys.stdout.write(
                                    f"\r[ĐANG HIỆU CHUẨN NỀN] Tiến độ: {pct}% (Hãy để trống vùng quét)...    "
                                )
                                sys.stdout.flush()
                                last_print_time = now
                            continue

                        if confirmed:
                            for t in confirmed:
                                ttc_str = f"{t.ttc_sec:.2f}s" if t.ttc_sec is not None else "--"
                                print(
                                    f"[XÁC NHẬN] ID #{t.target_id} (hits={t.hit_count}): "
                                    f"Cự ly = {t.distance_m:.2f} m | "
                                    f"X = {t.x_m:+.2f} m | Y = {t.y_m:.2f} m | "
                                    f"speed_kmh(gốc) = {t.speed_kmh:+.2f} km/h | "
                                    f"closing_speed = {t.closing_speed_mps:+.2f} m/s ({t.closing_speed_mps * 3.6:+.2f} km/h) | "
                                    f"TTC = {ttc_str}"
                                )
                            last_print_time = now
                        else:
                            if now - last_print_time >= 0.5:
                                sys.stdout.write(
                                    f"\r[SẠCH NHIỄU / AN TOÀN] 0 mục tiêu xác nhận (Đã xử lý {packet_count} gói, "
                                    f"nền tĩnh: {len(pipeline.background.background_cells)} ô)    "
                                )
                                sys.stdout.flush()
                                last_print_time = now
            else:
                time.sleep(0.005)

    except KeyboardInterrupt:
        print("\n\n" + "=" * 78)
        print(f"Đã dừng kiểm tra. Tổng số gói tin hợp lệ đã xử lý: {packet_count}")
        print("=" * 78)
    finally:
        ser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Công cụ kiểm tra & hiệu chuẩn nền Radar HLK-LD2450")
    parser.add_argument("port", nargs="?", default=None, help="Cổng COM (mặc định: tự nhận hoặc COM5)")
    parser.add_argument("--raw", action="store_true", help="Hiển thị dữ liệu thô chưa lọc nền và chưa qua tracker")
    parser.add_argument("--calibrate", action="store_true", help="Học nền 5 giây đầu và lưu vào background.json")
    parser.add_argument("--clear-bg", action="store_true", help="Xóa dữ liệu nền trong background.json trước khi chạy")
    parser.add_argument("--debug-speed", action="store_true", help="In đối chiếu speed_kmh gốc và closing_speed_mps")
    args = parser.parse_args()

    target_port = args.port.upper() if args.port else None
    if not target_port:
        ports = scan_ports()
        target_port = "COM5" if "COM5" in ports else (ports[0] if ports else "COM5")

    run_radar_test(
        port_name=target_port,
        baudrate=256000,
        raw_mode=args.raw,
        calibrate_first=args.calibrate,
        clear_bg=args.clear_bg,
    )
