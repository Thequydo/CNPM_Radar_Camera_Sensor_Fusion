# HỆ THỐNG GIÁM SÁT GIAO THÔNG VÀ CẢNH BÁO VA CHẠM THỜI GIAN THỰC (RADAR & CAMERA FUSION)
> **Dự án Môn học:** Công nghệ Phần mềm (CNPM)  
> **Chuyên ngành:** Kỹ thuật Máy tính (23KTMT) - Khoa Điện tử & AI - Trường Đại học Bách Khoa, Đại học Đà Nẵng  
> **Tuân thủ chuẩn đặc tả:** IEEE 830 SRS (Software Requirements Specification)

---

## 1. GIỚI THIỆU TỔNG QUAN HỆ THỐNG
Hệ thống là giải pháp tích hợp cảm biến sóng milimet 24GHz (**Hi-Link HLK-LD2450**) và **Camera quang học HD** để phát hiện, theo dõi và cảnh báo nguy cơ va chạm giao thông sớm theo thời gian thực.

### Các thành phần chính (Kiến trúc phân tầng):
```
+-----------------------------------------------------------------------------------+
|                        GIAO DIỆN HMI CÔNG NGHIỆP (PyQt6)                          |
|  - Giám sát trực tiếp (Camera + Radar Canvas 2D) | Nhật ký sự cố | Cấu hình Admin |
+-----------------------------------------------------------------------------------+
        ^                               ^                              ^
        |                               |                              |
+-------------------+       +-----------------------+      +------------------------+
|  AlertStateMachine|       |     FusionEngine      |      |   AsyncLogWorker       |
|  & SoundWorker    |<------| (Pin-hole Projection  |----->| (SQLite WAL, Snapshot  |
|  (3 cấp cảnh báo) |       |  & 1-1 Association)   |      |  Queue & Excel export) |
+-------------------+       +-----------------------+      +------------------------+
        ^                               ^
        |                               |
+-------------------+       +-----------------------+
|   RadarPipeline   |       |   DetectorWorker      |
| (Decode, Filter,  |       | (YOLOv8n ONNX Runtime,|
|  BG Model, Tracker|       |  Letterbox, NMS)      |
+-------------------+       +-----------------------+
        ^                               ^
        |                               |
  [Radar HLK-LD2450]            [Camera USB / RTSP]
```

---

## 2. YÊU CẦU MÔI TRƯỜNG & CÀI ĐẶT

### 2.1. Yêu cầu hệ thống:
- Hệ điều hành: Windows 10 / Windows 11 (64-bit).
- Python: Phiên bản **Python 3.13** (`C:\Users\Lenovo\AppData\Local\Programs\Python\Python313\python.exe`).
- Cảm biến phần cứng (khi chạy thực tế):
  * Cảm biến Radar HLK-LD2450 (giao tiếp qua mạch chuyển đổi USB-UART CP2102/CH340, baudrate 256000).
  * Camera USB độ phân giải tối thiểu 1280x720 (hoặc Iriun Webcam / webcam tích hợp).

### 2.2. Cài đặt thư viện phụ thuộc:
Mở PowerShell hoặc Command Prompt và thực hiện:
```cmd
cd /d C:\CNPM_Project
"C:\Users\Lenovo\AppData\Local\Programs\Python\Python313\python.exe" -m pip install -r requirements.txt
```

---

## 3. HƯỚNG DẪN KHỞI CHẠY VÀ SỬ DỤNG

### 3.1. Thiết lập lần đầu tiên (First-run Setup):
- Khi chạy chương trình lần đầu (khi CSDL chưa có tài khoản), màn hình **"Thiết lập hệ thống lần đầu"** sẽ tự động hiển thị.
- Người dùng bắt buộc tạo tài khoản **Quản trị viên (Admin)** với mật khẩu từ 6 ký tự trở lên.
- Hệ thống áp dụng chuẩn bảo mật **PBKDF2-HMAC-SHA256** với chuỗi Salt ngẫu nhiên riêng biệt, tuyệt đối không lưu hay log mật khẩu thô. Không có tài khoản mặc định cố định sẵn trong mã nguồn.

### 3.2. Chạy ứng dụng giao diện chính:
```cmd
run_app.bat
```
Hoặc chạy trực tiếp bằng dòng lệnh:
```cmd
cd /d C:\CNPM_Project
"C:\Users\Lenovo\AppData\Local\Programs\Python\Python313\python.exe" main.py
```

### 3.3. Các thao tác chính trên giao diện:
1. **Đăng nhập:**
   - Nhập tên đăng nhập và mật khẩu (hiển thị `*`).
   - Nếu đăng nhập sai 5 lần liên tiếp: tài khoản sẽ tự động bị khóa an ninh 5 phút và ghi vết vào `login_log`.
2. **Bắt đầu giám sát:**
   - Chọn cổng COM của Radar (ví dụ `COM5`), tốc độ `256000`, và Camera tương ứng.
   - Nếu không có phần cứng vật lý, tích chọn **"Chế độ mô phỏng"** để kiểm thử luồng hình ảnh và radar giả lập.
   - Nhấn **"Bắt đầu"**.
3. **Tương tác chọn mục tiêu 2 chiều (Bidirectional Selection):**
   - Nhấp trực tiếp vào khung chữ nhật nhận diện trên khung hình Camera hoặc nhấp vào chấm mục tiêu trên Radar Canvas 2D.
   - Cửa sổ nhỏ hiển thị chi tiết thông số: Loại vật cản, Khoảng cách ($d$), Vận tốc di chuyển ($v$), Vận tốc tiếp cận ($v_{close}$), Góc lệch ($\theta$), Thời gian va chạm ($TTC$).
   - Nhấn nút **"Mục tiêu gần nhất"** để hủy chọn thủ công và quay về tự động bám theo đối tượng nguy hiểm nhất.
4. **Hiệu chuẩn lọc nền tĩnh Radar (Settings Tab - Admin only):**
   - Đặt cảm biến radar cố định trước không gian có các vật cản đứng yên (bờ tường, cột mốc, biển báo).
   - Nhấn **"Bắt đầu hiệu chuẩn nền (5 giây)"**. Hệ thống sẽ học nền tĩnh vào `background.json` và loại trừ hoàn toàn các vật thể này khỏi cảnh báo va chạm.
   - Nhấn **"Xóa dữ liệu nền"** nếu chuyển sang vị trí đặt cảm biến mới.
5. **Xuất báo cáo sự cố:**
   - Chuyển sang Tab **"Nhật ký sự cố"**.
   - Có thể lọc theo mức độ (Vàng / Đỏ) và lọc theo ngày.
   - Nhấn **"Xuất báo cáo"** -> Chọn định dạng tệp **Excel (.xlsx)** hoặc **CSV UTF-8 BOM (.csv)**.
6. **Quản lý người dùng (Admin):**
   - Nhấn nút **"Quản lý người dùng"** trên thanh tiêu đề: Thêm tài khoản mới, Khóa/Mở khóa, Đổi vai trò, Đặt lại mật khẩu.
   - Hệ thống ngăn chặn việc tự khóa chính mình hoặc xóa/hạ quyền Quản trị viên cuối cùng.
   - Vai trò **Operator** (Nhân viên giám sát): Bị khóa/ẩn các chức năng cấu hình và quản trị ở cả tầng giao diện và tầng logic backend (RBAC).

---

## 4. BỘ CÔNG CỤ ĐO ĐẠC & KIỂM THỬ ĐỘC LẬP

### 4.1. Công cụ kiểm tra Radar Pipeline & Hiệu chuẩn nền độc lập:
```cmd
run_test_radar.bat
```
Hoặc dòng lệnh:
```cmd
"C:\Users\Lenovo\AppData\Local\Programs\Python\Python313\python.exe" test_radar.py COM5 --calibrate
```

### 4.2. Công cụ đánh giá nghiệm thu chuẩn NFR-05 (eval_accuracy.py):
Đo đạc sai số khoảng cách so với thước đo laser (ngưỡng $\le \pm 5\text{ cm}$) và tỉ lệ nhận diện Camera YOLOv8 (ngưỡng $\ge 90\%$):
```cmd
"C:\Users\Lenovo\AppData\Local\Programs\Python\Python313\python.exe" tools/eval_accuracy.py
```

### 4.3. Công cụ sinh kịch bản mô phỏng đồng bộ (generate_scenario.py):
Sinh tệp video MP4 và dữ liệu Radar CSV đồng bộ để phục vụ phát lại độc lập:
```cmd
"C:\Users\Lenovo\AppData\Local\Programs\Python\Python313\python.exe" tools/generate_scenario.py
```

### 4.4. Chạy toàn bộ 33 ca kiểm thử tự động (PyTest):
```cmd
"C:\Users\Lenovo\AppData\Local\Programs\Python\Python313\python.exe" -m pytest tests/ -v
```

---

## 5. MA TRẬN TRUY XUẤT YÊU CẦU PHẦN MỀM (SRS TRACEABILITY MATRIX) & DANH SÁCH KIỂM THỬ THỦ CÔNG

| Mã Yêu Cầu (SRS) | Tên Chức Năng / Yêu Cầu | Thành Phần Phần Mềm | Quy Trình Kiểm Thử Thủ Công | Tiêu Chuẩn Nghiệm Thu |
| :--- | :--- | :--- | :--- | :--- |
| **US-01, FR-01** | Đăng nhập & Xác thực PBKDF2 | `login_dialog.py`, `database.py` | 1. Nhập sai mật khẩu 5 lần.<br>2. Thử đăng nhập lại bằng mật khẩu đúng. | Báo lỗi rõ ràng, sau 5 lần bị khóa 5 phút. Sau 5 phút mở khóa bình thường. |
| **US-02, FR-02** | Phân quyền RBAC & Quản lý User | `login_dialog.py`, `database.py` | 1. Đăng nhập Operator -> Kiểm tra Tab Cấu hình và nút Quản lý User.<br>2. Đăng nhập Admin -> Thử xóa Admin duy nhất. | Operator bị chặn truy cập. Admin không thể tự khóa mình hoặc xóa Admin cuối cùng. |
| **US-03** | Tự đổi mật khẩu cá nhân | `login_dialog.py`, `database.py` | 1. Nhấn "Đổi mật khẩu".<br>2. Nhập sai pass cũ hoặc pass mới < 6 ký tự. | Báo lỗi chính xác. Khi nhập đúng và khớp, mật khẩu mới có hiệu lực ngay. |
| **US-04, FR-03** | Thu thập dữ liệu Radar HLK-LD2450 | `radar_parser.py` | 1. Cắm radar COM5.<br>2. Nhấn "Bắt đầu". | Đọc đúng 30-byte frame sync, bóc tách $X, Y, v$ chuẩn dấu và mét. |
| **US-05, FR-04** | Nhận diện Camera YOLOv8n | `detector_worker.py` | 1. Hướng camera vào người hoặc xe cộ.<br>2. Quan sát khung hình. | Nhận diện đúng Người, Ô tô, Xe máy, Xe tải, Xe buýt với conf $\ge 0.5$, không lag GUI. |
| **US-06, FR-05** | Sensor Fusion Radar & Camera | `fusion_engine.py` | 1. Người/xe di chuyển trước hệ thống.<br>2. Quan sát bounding box. | Hộp nhận diện hiển thị tên đối tượng kèm khoảng cách, tốc độ, TTC thực từ Radar. Vật ngoài tầm chỉ hiện trên Radar map. |
| **US-07, FR-06** | Hiệu chuẩn không gian & Lọc nền | `radar_parser.py`, `settings_dialog.py` | 1. Đặt vật cố định, nhấn "Hiệu chuẩn nền 5 giây".<br>2. Di chuyển người qua lại gần vật đó. | Vật cố định biến mất khỏi cảnh báo; người di chuyển vẫn được nhận diện và cảnh báo chính xác. |
| **US-08, FR-07** | Máy trạng thái cảnh báo 3 mức | `alert_engine.py`, `main.py` | 1. Người đứng yên ở cự ly 1.5m.<br>2. Người đi nhanh lại gần sensor. | Đứng yên chỉ ra mức VÀNG; đi nhanh lại gần ra mức ĐỎ kèm âm thanh bíp dồn dập. |
| **US-09, FR-08** | Cảnh báo vùng mù gần (<1.2m) | `alert_engine.py`, `main.py` | 1. Đối tượng tiến nhanh vào vùng sát mắt sensor rồi khuất bóng.<br>2. Quan sát banner cảnh báo. | Giữ trạng thái ĐỎ thêm 2.0s, lưu sự cố kèm ghi chú "mục tiêu vào vùng mù". |
| **US-10, FR-09** | Âm thanh cảnh báo luồng riêng | `sound_worker.py` | 1. Kích hoạt mức Vàng và Đỏ.<br>2. Nhấn nút "Âm thanh: Tắt". | Phát âm thanh nhịp nhàng không giật khung hình; nút tắt tiếng hoạt động tức thì. |
| **US-11, FR-10** | Tự động gom sự cố & Lưu ảnh | `alert_engine.py`, `async_logger.py` | 1. Tạo 1 sự cố va chạm kéo dài 3 giây.<br>2. Kiểm tra nhật ký. | Chỉ tạo đúng 1 dòng sự cố trong bảng (thay vì hàng chục dòng), chụp 1 ảnh hiện trường lúc bắt đầu nguy hiểm. |
| **US-12, FR-11** | Tra cứu nhật ký & Xuất Excel/CSV | `main.py`, `database.py` | 1. Lọc sự cố theo ngày và mức Đỏ.<br>2. Nhấn Xuất báo cáo chọn .xlsx. | Xuất ra tệp Excel định dạng chuẩn bảng tính, mở được trên Excel không lỗi font. |
| **NFR-05** | Độ chính xác đo cự ly & Nhận diện | `tools/eval_accuracy.py` | 1. Chạy `tools/eval_accuracy.py`. | Sai số khoảng cách $\le \pm 5\text{ cm}$, tỉ lệ nhận diện $\ge 90\%$. |
| **NFR-06** | Khả năng phục hồi & Chống treo | `main.py` | 1. Rút đột ngột cáp radar hoặc camera khi đang chạy.<br>2. Cắm lại cáp. | Ứng dụng không bị crash, ghi log vào `logs/app.log`, tự kết nối lại thành công. |
