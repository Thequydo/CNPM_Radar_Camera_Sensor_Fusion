# -*- coding: utf-8 -*-
"""
Script kiểm tra Camera USB, Webcam laptop hoặc Camera Điện thoại
Cách chạy: python test_camera.py
Nhấn phím 'q' trên cửa sổ video để thoát.
"""

import cv2
import sys

def scan_available_cameras(max_tested=4):
    """Quét tìm các camera đang kết nối với máy tính"""
    print("[INFO] Đang quét các cổng Camera khả dụng trên máy...")
    available = []
    for idx in range(max_tested):
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                available.append(idx)
            cap.release()
    return available

def test_camera(source=0):
    print(f"\n[INFO] Đang mở Camera nguồn: {source}...")
    if isinstance(source, int):
        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(source)
    else:
        # Nếu là URL luồng IP Webcam (ví dụ: http://192.168.1.15:8080/video)
        cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        print(f"[LỖI] Không thể mở Camera nguồn {source}!")
        print("-> Nếu dùng điện thoại qua Iriun/DroidCam: Hãy kiểm tra app trên điện thoại đã bật chưa.")
        print("-> Nếu dùng IP Webcam: Kiểm tra máy tính và điện thoại đã kết nối chung mạng Wi-Fi chưa.")
        return False

    print(f"[THÀNH CÔNG] Camera [{source}] đã hoạt động mượt mà!")
    print("-> Nhấn phím 'q' trên cửa sổ video để tắt.\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[CẢNH BÁO] Mất tín hiệu hình ảnh.")
            break

        cv2.putText(frame, f"CAMERA NGUON: {source} - NHAN 'Q' DE THOAT", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
        cv2.imshow(f"Kiem tra Camera - {source}", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Đã đóng cửa sổ Camera.")
    return True

if __name__ == "__main__":
    cams = scan_available_cameras()
    if cams:
        print(f"[TÌM THẤY] Các camera sẵn sàng: {cams}")
        print(f"-> Đang mở camera đầu tiên (index = {cams[-1] if len(cams) > 1 else cams[0]})...")
        # Ưu tiên mở camera rời / camera điện thoại (thường có index = 1 nếu index 0 là webcam laptop)
        chosen = cams[-1] if len(cams) > 1 else cams[0]
        test_camera(chosen)
    else:
        print("[THÔNG BÁO] Không tìm thấy camera nào cắm cổng USB.")
        print("-> Đang thử mở mặc định index 0...")
        test_camera(0)
