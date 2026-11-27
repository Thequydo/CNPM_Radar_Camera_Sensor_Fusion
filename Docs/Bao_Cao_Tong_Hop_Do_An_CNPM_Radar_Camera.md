# TRƯỜNG ĐẠI HỌC BÁCH KHOA – ĐẠI HỌC ĐÀ NẴNG
## KHOA ĐIỆN TỬ VÀ TRÍ TUỆ NHÂN TẠO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# BÁO CÁO ĐỒ ÁN HỌC PHẦN: CÔNG NGHỆ PHẦN MỀM

### ĐỀ TÀI:
## HỆ THỐNG PHẦN MỀM GIÁM SÁT GIAO THÔNG VÀ CẢNH BÁO VA CHẠM THỜI GIAN THỰC (RADAR 24GHz & CAMERA SENSOR FUSION)

- **Giảng viên hướng dẫn:** TS. Đào Duy Tuấn
- **Lớp sinh hoạt:** 23KTMT
- **Nhóm thực hiện:** Nhóm 5
- **Sinh viên thực hiện:**
  1. Ngô Quang Thế — MSSV: 106230028
  2. Lê Anh Khoa — MSSV: 106230016
  3. Huỳnh Ngọc Tịnh Phong — MSSV: 106230022

**ĐÀ NẴNG, NĂM 2026**

---

## LỜI NÓI ĐẦU VÀ LỜI CẢM ƠN

Trong kỷ nguyên bùng nổ của cuộc Cách mạng Công nghiệp 4.0 và xu hướng thông minh hóa giao thông đô thị, các hệ thống hỗ trợ lái xe nâng cao (ADAS – Advanced Driver Assistance Systems) và phương tiện tự hành đang trở thành một trong những mũi nhọn công nghệ cốt lõi nhằm giải quyết bài toán giảm thiểu tai nạn giao thông, bảo vệ an toàn tính mạng con người và tài sản.

Học phần Công nghệ Phần mềm tại Trường Đại học Bách Khoa – Đại học Đà Nẵng là môn học chuyên sâu nền tảng, trang bị cho sinh viên ngành Kỹ thuật Máy tính tư duy kỹ nghệ phần mềm chuyên nghiệp, quy trình phát triển Agile/Scrum kết hợp V-Model, năng lực mô hình hóa hướng đối tượng bằng chuẩn UML 2.5, đặc tả yêu cầu phần mềm theo tiêu chuẩn IEEE 830, và kỹ năng triển khai hệ thống an toàn thời gian thực đáp ứng các ràng buộc khắt khe về độ trễ và độ tin cậy.

Được sự phân công và hướng dẫn tận tình của Thầy TS. Đào Duy Tuấn, nhóm sinh viên chúng em đã tiến hành nghiên cứu, thiết kế và triển khai đề tài: *"Hệ thống phần mềm giám sát giao thông và cảnh báo va chạm thời gian thực (Radar 24GHz & Camera Sensor Fusion)"*. Đề tài giải quyết bài toán hạn chế vật lý của từng cảm biến đơn lẻ (Camera không đo được chính xác cự ly và suy giảm trong bóng tối; Radar không phân loại được đối tượng và dễ báo động giả do vật cản tĩnh) thông qua việc dung hợp dữ liệu không gian thời gian thực, triệt tiêu báo động giả bằng thuật toán học nền tĩnh 5 giây, bám vết Kalman Filter và máy trạng thái cảnh báo 3 mức kết hợp độ trễ Hysteresis.

Nhóm sinh viên chúng em xin bày tỏ lòng biết ơn chân thành và sâu sắc nhất tới Thầy TS. Đào Duy Tuấn đã luôn định hướng khoa học, chỉ bảo phương pháp phân tích yêu cầu nghiêm ngặt và đóng góp những ý kiến phản biện quý báu giúp nhóm hoàn thiện đề tài. Đặc biệt, nhóm đã nghiêm túc tiếp thu các chỉ dẫn của Thầy về hệ thống biểu đồ kỹ nghệ phần mềm, hoàn thành đầy đủ 5 loại biểu đồ UML với tối thiểu 2 biểu đồ cho mỗi loại (tổng cộng 10 biểu đồ UML) theo đúng yêu cầu đề tài Final Project.

Mặc dù đã rất nỗ lực kết hợp giữa lý thuyết kỹ nghệ phần mềm và đo kiểm thực nghiệm phần cứng, song do giới hạn thời gian và kinh nghiệm, báo cáo khó tránh khỏi những điểm thiếu sót nhất định. Tập thể nhóm rất mong nhận được những góp ý, chỉ dẫn của Thầy để hệ thống ngày càng hoàn thiện hơn.

*Đà Nẵng, năm 2026*  
**Sinh viên thực hiện đề tài:**  
Ngô Quang Thế – Lê Anh Khoa – Huỳnh Ngọc Tịnh Phong

---

## MỤC LỤC TỔNG QUAN

- LỜI NÓI ĐẦU VÀ LỜI CẢM ƠN
- DANH MỤC CÁC TỪ VIẾT TẮT
- DANH MỤC CÁC HÌNH VẼ VÀ ĐỒ THỊ
- DANH MỤC CÁC BẢNG BIỂU
- PHẦN MỞ ĐẦU: THÔNG TIN DỰ ÁN & ĐÓNG GÓP CỦA CÁC THÀNH VIÊN
  - Bảng phân công nhiệm vụ, sản phẩm bàn giao và tỷ lệ đóng góp (Bảng 1)
- CHƯƠNG 1: TÍNH CẤP THIẾT VÀ Ý NGHĨA CỦA ĐỀ TÀI
  - 1.1. Bối cảnh thực tế của hệ thống giám sát an toàn giao thông và ADAS
  - 1.2. Vấn đề thực tế cần giải quyết: Hạn chế vật lý của Camera và Radar đơn lẻ
  - 1.3. Hạn chế của các giải pháp và công cụ hiện tại
  - 1.4. Mục tiêu của đề tài
  - 1.5. Ý nghĩa ứng dụng và nghiên cứu
- CHƯƠNG 2: SƠ ĐỒ KIẾN TRÚC VÀ THIẾT KẾ HỆ THỐNG
  - 2.1. Sơ đồ kiến trúc tổng thể của hệ thống phần mềm (5 tầng phân lập)
  - 2.2. Đặc tả các thành phần và Quy hoạch giao tiếp / cổng kết nối
  - 2.3. Luồng dữ liệu (Data Flow) và Nguyên lý hoạt động theo các trạng thái an toàn
  - 2.4. Lý do lựa chọn giải pháp, So sánh hệ thống hiện có và Điểm cải tiến kiến trúc
- CHƯƠNG 3: MÔ HÌNH TOÁN HỌC, MÔ HÌNH TRẠNG THÁI VÀ PHÁT BIỂU BÀI TOÁN
  - 3.1. Tập biến, Tham số, Đầu vào, Đầu ra, Giả thiết và Ràng buộc
  - 3.2. Mô hình Toán học Chiếu quang học Pin-hole Camera và Bài toán Ghép cặp Cảm biến
  - 3.3. Mô hình Dữ liệu, Mô hình Xử lý và Mô hình Máy Trạng thái Hữu hạn (FSM)
  - 3.4. Điểm điều chỉnh trong mô hình toán học và Thuật toán Lọc nền tĩnh
- CHƯƠNG 4: TRIỂN KHAI HỆ THỐNG VÀ THIẾT KẾ GIẢI THUẬT
  - 4.1. Các bước triển khai và Công nghệ sử dụng
  - 4.2. Thiết kế Giải thuật Thu thập Radar Đa luồng và Giải mã Giao thức Nhị phân HLK-LD2450 (Lưu đồ & Thuật toán 1: Mã giả Pseudocode)
  - 4.3. Thiết kế Giải thuật Dung hợp Cảm biến và Máy Trạng thái Cảnh báo Thời gian Thực (Lưu đồ & Thuật toán 2: Mã giả Pseudocode)
  - 4.4. Cấu hình thử nghiệm và Hai điểm cải tiến kỹ thuật nổi bật trong triển khai
  - 4.5. Thiết kế và Đặc tả Chi tiết 10 Biểu đồ UML Chuẩn mực Kỹ nghệ Phần mềm (Final Project):
    - 4.5.1. Nhóm Biểu đồ Use Case (2 biểu đồ)
    - 4.5.2. Nhóm Biểu đồ Hoạt động (Activity Diagrams) (2 biểu đồ)
    - 4.5.3. Nhóm Biểu đồ Lớp (Class Diagrams) (2 biểu đồ)
    - 4.5.4. Nhóm Biểu đồ Tuần tự (Sequence Diagrams) (2 biểu đồ)
    - 4.5.5. Nhóm Biểu đồ Máy Trạng thái (State Diagrams) (2 biểu đồ)
- CHƯƠNG 5: PHÂN TÍCH VÀ ĐÁNH GIÁ HIỆU NĂNG THỰC NGHIỆM
  - 5.1. Kịch bản thử nghiệm và Hệ thống 6 nhóm chỉ số đánh giá định lượng
  - 5.2. Kết quả thực nghiệm và Phân tích chuyên sâu Biểu đồ 4 thành phần
  - 5.3. Kiểm chứng UART COM5, Giao diện HMI Người vận hành và Bảng sự cố
  - 5.4. So sánh với Hệ thống Tham chiếu (Baseline) và Phân tích Độ nhạy
  - 5.5. Phân tích Sử dụng Tài nguyên và Đánh giá Độ phức tạp Thuật toán Big-O
- CHƯƠNG 6: KẾT LUẬN, HẠN CHẾ VÀ ĐIỀU KIỆN TRIỂN KHAI THỰC TẾ
  - 6.1. Kết quả đạt được và Mức độ hoàn thành mục tiêu
  - 6.2. Các hạn chế của mô hình hiện tại
  - 6.3. Các điều kiện kỹ thuật để triển khai trên phương tiện giao thông thực tế
- PHẦN PHỤ LỤC: TÀI LIỆU THAM KHẢO & LIÊN KẾT MÃ NGUỒN

---

## DANH MỤC CÁC TỪ VIẾT TẮT

| Từ viết tắt | Tên tiếng Anh đầy đủ | Ý nghĩa / Định nghĩa kỹ thuật trong đề tài |
| :--- | :--- | :--- |
| **ADAS** | Advanced Driver Assistance Systems | Hệ thống hỗ trợ lái xe nâng cao cảnh báo va chạm chủ động |
| **AI** | Artificial Intelligence | Trí tuệ nhân tạo nhận diện và phân loại phương tiện |
| **API** | Application Programming Interface | Giao diện lập trình ứng dụng kết nối mô đun |
| **BBox** | Bounding Box | Hộp giới hạn tọa độ nhận diện đối tượng trên ảnh camera (x1, y1, x2, y2) |
| **CAN-Bus** | Controller Area Network Bus | Mạng truyền thông bus nối tiếp chuẩn công nghiệp trên ô tô |
| **CPU** | Central Processing Unit | Bộ vi xử lý trung tâm máy tính thực thi thuật toán |
| **CSV** | Comma-Separated Values | Định dạng tệp lưu trữ bảng dữ liệu phân cách bởi dấu phẩy |
| **DoA** | Direction of Arrival | Góc định hướng sóng vô tuyến tới cảm biến radar |
| **EMA** | Exponential Moving Average | Bộ lọc trung bình trượt hàm mũ làm mượt tín hiệu |
| **FMCW** | Frequency Modulated Continuous Wave | Radar sóng liên tục điều tần phát hiện cự ly và Doppler |
| **FPS** | Frames Per Second | Tốc độ xử lý khung hình hiển thị trên giây của luồng video |
| **FR** | Functional Requirement | Yêu cầu chức năng của hệ thống phần mềm (IEEE 830) |
| **FSM** | Finite State Machine | Mô hình máy trạng thái hữu hạn điều khiển chu trình cảnh báo |
| **GUI / HMI** | Graphical User Interface / Human-Machine Interface | Giao diện đồ họa tương tác giữa con người và máy tính |
| **HFOV** | Horizontal Field of View | Góc mở quan sát theo phương ngang của ống kính Camera (độ) |
| **HMAC** | Hash-based Message Authentication Code | Mã xác thực thông điệp dựa trên hàm băm mật mã học |
| **IEEE** | Institute of Electrical and Electronics Engineers | Viện Kỹ sư Điện và Điện tử quốc tế |
| **IMU** | Inertial Measurement Unit | Khối đo lường quán tính xác định gia tốc và vận tốc góc |
| **IPC** | Inter-Process Communication | Cơ chế giao tiếp truyền thông liên tiến trình / đa luồng |
| **LoS** | Line of Sight | Tầm nhìn thẳng trực diện giữa cảm biến và chướng ngại vật |
| **NFR** | Non-Functional Requirement | Yêu cầu phi chức năng về hiệu năng, an toàn và độ tin cậy |
| **ONNX** | Open Neural Network Exchange | Định dạng chuẩn mở trao đổi và tối ưu mô hình học sâu |
| **PBKDF2** | Password-Based Key Derivation Function 2 | Thuật toán chuẩn băm mật khẩu khóa an toàn chống brute-force |
| **PID** | Proportional-Integral-Derivative | Bộ điều khiển vi tích phân tỷ lệ khép kín phản hồi |
| **RBAC** | Role-Based Access Control | Mô hình kiểm soát truy cập và phân quyền dựa trên vai trò |
| **SDK** | Software Development Kit | Bộ công cụ phát triển phần mềm chuyên dụng |
| **SNR** | Signal-to-Noise Ratio | Tỷ số tín hiệu trên tạp âm nền đo đạc cảm biến |
| **SRS** | Software Requirements Specification | Bản đặc tả yêu cầu phần mềm theo tiêu chuẩn IEEE 830 |
| **TTC** | Time-To-Collision | Chỉ số thời gian dự tính va chạm va chạm thời gian thực (giây) |
| **UART** | Universal Asynchronous Receiver-Transmitter | Giao thức truyền thông nối tiếp bất đồng bộ phần cứng |
| **UML** | Unified Modeling Language | Ngôn ngữ mô hình hóa thống nhất thiết kế phần mềm |
| **WAL** | Write-Ahead Logging | Cơ chế ghi nhật ký trước tối ưu hóa ghi đĩa SQLite bất đồng bộ |
| **YOLO** | You Only Look Once | Họ mạng nơ-ron tích chập nhận diện đối tượng thời gian thực |

---

## DANH MỤC CÁC HÌNH VẼ VÀ ĐỒ THỊ

- **Hình 2.1:** Sơ đồ kiến trúc 5 tầng phân lập (Layered Architecture) của hệ thống phần mềm
- **Hình 2.2:** Sơ đồ chuyển tuyến luồng dữ liệu thời gian thực và đánh giá an toàn đa cảm biến
- **Hình 3.1:** Mô hình hình học chiếu quang học Pin-hole Camera ánh xạ không gian 3D sang 2D
- **Hình 3.2:** Sơ đồ đường ống xử lý dữ liệu và luồng sự kiện liên tiến trình (Processing Pipeline)
- **Hình 3.3:** Sơ đồ máy trạng thái hữu hạn (FSM) phân loại cảnh báo 3 mức kèm độ trễ Hysteresis
- **Hình 4.1:** Môi trường phần cứng tích hợp Radar sóng milimet 24GHz và Camera quang học HD
- **Hình 4.2:** Lưu đồ giải thuật thu thập đa luồng và giải mã gói tin UART Radar HLK-LD2450 (Flowchart 1)
- **Hình 4.3:** Lưu đồ giải thuật dung hợp cảm biến Pin-hole và động cơ cảnh báo TTC (Flowchart 2)
- **Hình 4.4:** Biểu đồ Use Case 1 - Tổng quan Phân quyền Vai trò Người dùng (RBAC Overview)
- **Hình 4.5:** Biểu đồ Use Case 2 - Chi tiết Phân hệ Giám sát, Dung hợp Cảm biến & Cảnh báo Va chạm
- **Hình 4.6:** Biểu đồ Hoạt động 1 (Activity Diagram 1) - Luồng Thu thập Song song & Dung hợp Cảm biến
- **Hình 4.7:** Biểu đồ Hoạt động 2 (Activity Diagram 2) - Quy trình Đánh giá Nguy cơ & Xử lý Cảnh báo Khẩn
- **Hình 4.8:** Biểu đồ Lớp 1 (Class Diagram 1) - Cấu trúc Thực thể Dữ liệu Miền Nghiệp vụ (Domain Entities)
- **Hình 4.9:** Biểu đồ Lớp 2 (Class Diagram 2) - Kiến trúc Phần mềm Đa luồng và Tương tác Tầng
- **Hình 4.10:** Biểu đồ Tuần tự 1 (Sequence Diagram 1) - Kịch bản Giám sát Trực tiếp & Báo Động Va Chạm
- **Hình 4.11:** Biểu đồ Tuần tự 2 (Sequence Diagram 2) - Kịch bản Quản trị viên Hiệu chuẩn Lọc Nền Tĩnh 5s
- **Hình 4.12:** Biểu đồ Máy Trạng thái 1 (State Diagram 1) - Động cơ Cảnh báo 3 Mức & Lọc Trễ Hysteresis
- **Hình 4.13:** Biểu đồ Máy Trạng thái 2 (State Diagram 2) - Vòng đời Vận hành Hệ thống Phần mềm
- **Hình 5.1:** Bộ đồ thị 4 thành phần phân tích hiệu năng toàn diện của hệ thống Sensor Fusion
- **Hình 5.2:** Kiểm chứng truyền nhận thực tế mở cổng COM5 @ 256000 bps đọc liên tục tọa độ X, Y, V
- **Hình 5.3:** Giao diện Người vận hành HMI ở chế độ Báo động va chạm (Độ phân giải 1920x1080)
- **Hình 5.4:** Khung Camera thực tế hiển thị nhãn cự ly kết hợp font TrueType Segoe UI có dấu tiếng Việt
- **Hình 5.5:** Cửa sổ Popup tra cứu thông số chi tiết của Đối tượng khi Người vận hành nhấp chọn
- **Hình 5.6:** Bộ đồ thị đối sánh hiệu năng toàn diện giữa Kịch bản Baseline và Phương pháp Đề xuất

---

## DANH MỤC CÁC BẢNG BIỂU

- **Bảng 1:** Bảng phân công nhiệm vụ, sản phẩm bàn giao cụ thể và tỷ lệ đóng góp của thành viên
- **Bảng 2.1:** Bảng quy hoạch cổng kết nối, thông số giao tiếp phần cứng và luồng xử lý đa tuyến
- **Bảng 2.2:** Phân tích lý do lựa chọn, tính phù hợp và ưu/nhược điểm của các kiến trúc cảm biến
- **Bảng 3.1:** Bảng chuyển trạng thái FSM động cơ cảnh báo va chạm và các điều kiện kích hoạt
- **Bảng 4.1:** Bảng tổng hợp công nghệ phần mềm và công cụ sử dụng trong hệ thống
- **Bảng 4.2:** Bảng thông số cấu hình thử nghiệm và tham số kỹ thuật toàn diện
- **Bảng 5.1:** Bảng số liệu đo kiểm thực nghiệm tổng hợp giữa các kịch bản thử nghiệm
- **Bảng 5.2:** Bảng đối chiếu kiểm chứng 52 bài kiểm thử tự động hóa (100% PyTest Passed)
- **Bảng 5.3:** Bảng đối sánh định lượng giữa Phương pháp đề xuất và 2 Kịch bản tham chiếu (Baseline)
- **Bảng 5.4:** Bảng kết quả đo kiểm thực nghiệm độ nhạy theo ngưỡng cự ly và thời gian va chạm TTC
- **Bảng 5.5:** So sánh hiệu năng thực nghiệm định lượng giữa thuật toán có lọc nền và không lọc nền
- **Bảng 5.6:** Đánh giá độ phức tạp thuật toán Big-O (Thời gian và Không gian bộ nhớ) cho các phân hệ

---

## PHẦN MỞ ĐẦU: THÔNG TIN DỰ ÁN & ĐÓNG GÓP CỦA CÁC THÀNH VIÊN

Dự án đồ án học phần Công nghệ Phần mềm được thực hiện bởi Nhóm 5 (Lớp 23KTMT, Khoa Điện tử và Trí tuệ Nhân tạo, Trường Đại học Bách Khoa – Đại học Đà Nẵng). Đề tài tập trung giải quyết bài toán cấp thiết trong an toàn giao thông thông qua hệ thống giám sát cảnh báo va chạm đa cảm biến thời gian thực. Nhằm đảm bảo tính minh bạch, công bằng và phản ánh chính xác khối lượng lao động kỹ nghệ phần mềm của từng cá nhân, toàn bộ dự án được phân rã thành các gói nhiệm vụ gắn liền với sản phẩm bàn giao có thể đo lường và kiểm chứng độc lập.

### Bảng phân công nhiệm vụ, sản phẩm bàn giao và tỷ lệ đóng góp (Bảng 1):

| STT | Họ và tên | Mã SV | Nhiệm vụ chi tiết trong dự án | Sản phẩm bàn giao cụ thể | Tỷ lệ(%) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Ngô Quang Thế** | 106230028 | • Thiết kế kiến trúc phần mềm đa luồng PyQt6, cơ chế bảo mật xác thực PBKDF2 và phân quyền RBAC.<br>• Xây dựng bộ phát giả lập SimulationPlayer đồng bộ video MP4 và dữ liệu radar CSV.<br>• Tái cấu trúc giao diện HMI Người vận hành qua 5 bước chuẩn hóa, sửa lỗi cắt chữ 1366x768 & 1920x1080.<br>• Đóng gói file thực thi độc lập GiamSatGiaoThong.exe bằng PyInstaller. | • Module main.py, auth_manager.py, simulation_player.py.<br>• File cấu hình GiamSatGiaoThong.spec, shortcut desktop.<br>• Biên soạn Chương 2, Chương 4 & Tổng hợp báo cáo. | **33.4%** |
| **2** | **Lê Anh Khoa** | 106230016 | • Xây dựng driver giao tiếp RadarWorker giải mã giao thức UART nhị phân HLK-LD2450 @ 256000 bps.<br>• Thiết kế thuật toán lọc nền tĩnh 5s (background.json) và bộ lọc làm mượt EMA/Kalman.<br>• Thiết kế hệ thống 10 biểu đồ UML chuẩn mực (2 Use Case, 2 Activity, 2 Class, 2 Sequence, 2 State).<br>• Triển khai bộ kiểm thử tự động hóa 52 bài test PyTest và đo kiểm thực nghiệm COM5. | • Module radar_driver.py, background_filter.py, test suite tests/ (52 tests passed).<br>• 10 tệp ảnh biểu đồ UML độ phân giải cao tại Hinh_Anh_UML/.<br>• Biên soạn Chương 3 & Mục 4.5 Biểu đồ UML. | **33.3%** |
| **3** | **Huỳnh Ngọc Tịnh Phong** | 106230022 | • Tích hợp mô hình AI thị giác máy tính YOLOv8n qua ONNX Runtime và bộ bám vết DetectionTracker.<br>• Hiện thực hóa thuật toán Sensor Fusion chiếu quang học Pin-hole và ghép cặp Greedy 1-1.<br>• Xây dựng Động cơ cảnh báo va chạm AlertStateMachine tính toán chỉ số TTC và lọc trễ Hysteresis.<br>• Triển khai luồng ghi dữ liệu bất đồng bộ AsyncLogWorker và quản trị CSDL SQLite WAL. | • Module detector_worker.py, fusion_engine.py, alert_engine.py, db_manager.py.<br>• CSDL traffic_radar_system.db (84 bản ghi sự cố thực nghiệm).<br>• Biên soạn Chương 1, Chương 5 & Chương 6. | **33.3%** |
| **Tổng** | | | **Tổng tỷ lệ đóng góp của toàn thể thành viên trong nhóm** | **Toàn bộ mã nguồn dự án, CSDL, 52 bài test, 10 biểu đồ UML và báo cáo tổng hợp** | **100.0%** |

> **CAM KẾT TRÁCH NHIỆM VÀ ĐỒNG THUẬN CỦA TẬP THỂ NHÓM:**  
> Tất cả các thành viên trong Nhóm 5 (Lớp 23KTMT) nhất trí hoàn toàn về tỷ lệ phân công và đánh giá mức độ đóng góp trên, đồng thời cùng chịu trách nhiệm trước Giảng viên hướng dẫn và Bộ môn về tính chính xác, tính trung thực khoa học của toàn bộ mã nguồn phần mềm, dữ liệu đo kiểm thực nghiệm và nội dung bản báo cáo đồ án này.

---

## CHƯƠNG 1: TÍNH CẤP THIẾT VÀ Ý NGHĨA CỦA ĐỀ TÀI

### 1.1. Bối cảnh thực tế của hệ thống giám sát an toàn giao thông và ADAS
Trong những năm gần đây, sự gia tăng nhanh chóng của lưu lượng phương tiện cơ giới tại các đô thị lớn đã dẫn đến tình trạng ùn tắc và tai nạn giao thông diễn biến phức tạp. Theo thống kê của Ủy ban An toàn Giao thông Quốc gia, phần lớn các vụ va chạm nghiêm trọng xuất phát từ sự hạn chế tầm nhìn của người điều khiển, điểm mù xung quanh thân xe, và sự mất tập trung trong các tình huống phát sinh đột ngột ở cự ly gần. Các hệ thống hỗ trợ lái xe nâng cao (ADAS – Advanced Driver Assistance Systems) đã được chứng minh là công cụ đắc lực giúp tài xế chủ động nhận diện hiểm họa và phát tín hiệu cảnh báo sớm trước khi va chạm xảy ra.

### 1.2. Vấn đề thực tế cần giải quyết: Hạn chế vật lý của Camera và Radar đơn lẻ
Tuy nhiên, khi triển khai trên thực tế, việc sử dụng đơn lẻ một loại cảm biến thị giác quang học hoặc cảm biến radar thuần túy luôn gặp phải những rào cản vật lý cố hữu không thể vượt qua:
- **Cảm biến Camera thị giác quang học (Visual Camera):** Rất mạnh mẽ trong việc phân loại đối tượng (người đi bộ, xe máy, ô tô, xe tải, chướng ngại vật) nhờ cung cấp độ phân giải hình học cao, đường nét và màu sắc phong phú. Mặc dù vậy, camera quang học bị suy giảm nghiêm trọng khi hoạt động trong điều kiện thiếu sáng ban đêm, mưa lớn, sương mù dày hoặc ngược sáng chói lóa. Đặc biệt, camera KHÔNG THỂ đo đạc trực tiếp, chính xác cự ly vật lý (Distance) và vận tốc Doppler tương đối tức thời của vật cản.
- **Cảm biến Radar sóng milimet 24GHz (Hi-Link HLK-LD2450):** Sở hữu khả năng xuyên thấu tuyệt vời qua mưa gió, sương mù, khói bụi; hoạt động bền bỉ bất kể ngày đêm 24/7. Radar đo trực tiếp cự ly, tọa độ không gian (X, Y) và vận tốc Doppler tức thời với độ trễ cực thấp (< 10ms). Tuy nhiên, nhược điểm cốt tử của Radar là độ phân giải góc bị giới hạn và hoàn toàn KHÔNG CÓ khả năng phân loại đối tượng (không thể phân biệt một cụm nhiễu, một người đi bộ hay một chiếc ô tô).

### 1.3. Hạn chế của các giải pháp và công cụ hiện tại
Để giải quyết bài toán cảnh báo va chạm, nhiều giải pháp thương mại và học thuật đã được đề xuất nhưng bộc lộ các hạn chế lớn:
- **Hạn chế của các giải pháp đo cự ly thuần Camera:** Hầu hết các giải pháp xử lý khoảng cách bằng thị giác máy tính dựa vào kích thước bounding box ước lượng (Perspective Geometry) hoặc mô hình mạng nơ-ron Monocular Depth Estimation. Các phương pháp này đòi hỏi tải tính toán GPU khổng lồ, độ trễ suy luận lớn (> 60ms) và sai số đo đạc cự ly lên tới 15% - 25% khi kích thước đối tượng thay đổi bất thường.
- **Hạn chế về báo động giả của cảm biến Radar:** Cảm biến Radar trong nhà hoặc môi trường hẹp thường xuyên bắt phải các vật phản xạ tĩnh (tường phòng lab, cột mốc, tủ sắt, dải phân cách). Nếu không có thuật toán lọc nền tĩnh thông minh, hệ thống sẽ phát sinh hàng loạt cảnh báo giả (False Alarms), khiến người vận hành mất niềm tin vào hệ thống hỗ trợ lái xe.
- **Hạn chế về mặt công cụ kiểm thử:** Nhiều công trình nghiên cứu sử dụng các bộ mô phỏng đóng gói sẵn, không cho phép can thiệp vào tầng gói tin phần cứng hoặc không hỗ trợ giao diện HMI thân thiện cho người vận hành thực tế tại cabin.

### 1.4. Mục tiêu của đề tài
Đề tài tập trung hoàn thành các mục tiêu kỹ nghệ phần mềm và công nghệ cốt lõi sau:
1. **Nền tảng ứng dụng:** Phát triển phần mềm Desktop hoàn chỉnh bằng Python 3.11/3.13 và thư viện giao diện công nghiệp PyQt6.
2. **Đa luồng thời gian thực:** Thu thập và giải mã luồng UART nhị phân tốc độ cao 256000 bps từ Radar HLK-LD2450 song song luồng video HD 30 FPS.
3. **Thị giác máy tính AI:** Tích hợp mô hình AI YOLOv8n tối ưu qua ONNX Runtime kết hợp bộ bám vết Kalman Filter và thuật toán Hungarian.
4. **Dung hợp cảm biến (Sensor Fusion):** Ánh xạ không gian 3D sang 2D bằng mô hình Pin-hole Camera, ghép cặp Greedy 1-1, gán cự ly chính xác cho Bounding Box.
5. **Động cơ cảnh báo thông minh:** Máy trạng thái cảnh báo 3 mức (An toàn, Cảnh báo, Báo động) dựa trên chỉ số TTC = d / v_close và độ trễ Hysteresis.
6. **Triệt tiêu nhiễu nền tĩnh:** Triệt tiêu hoàn toàn báo động giả do vật cản tĩnh thông qua thuật toán học nền tĩnh 5 giây (background.json).
7. **Giao diện & Đóng gói:** Tái cấu trúc toàn diện HMI cho Người vận hành qua 5 bước chuẩn hóa, bảo mật RBAC và đóng gói độc lập GiamSatGiaoThong.exe.

### 1.5. Ý nghĩa ứng dụng và nghiên cứu
- **Ý nghĩa thực tiễn:** Hệ thống cung cấp giải pháp cảnh báo va chạm đáng tin cậy với chi phí phần cứng thương mại thấp, dễ dàng lắp đặt trên xe ô tô tải, xe buýt đô thị hoặc điểm giao cắt giao thông thông minh. Khả năng phát hiện sớm và tính toán thời gian va chạm TTC giúp người vận hành có đủ thời gian phản xạ (từ 1.5 đến 3.0 giây) để phanh hoặc đánh lái an toàn.
- **Ý nghĩa học thuật:** Đề tài xây dựng một quy trình kỹ nghệ phần mềm hoàn chỉnh từ khâu khảo sát đặc tả yêu cầu IEEE 830, thiết kế 10 biểu đồ UML chuẩn mực, lập trình đa luồng bất đồng bộ, kiểm thử tự động 52 bài test PyTest và đóng gói ứng dụng thực thi độc lập.

---

## CHƯƠNG 2: SƠ ĐỒ KIẾN TRÚC VÀ THIẾT KẾ HỆ THỐNG

### 2.1. Sơ đồ kiến trúc tổng thể của hệ thống phần mềm (5 tầng phân lập)
Hệ thống được thiết kế theo kiến trúc phân tầng (Layered Architecture) 5 tầng phân lập rõ ràng, tuân thủ nguyên lý Loose-Coupling (Kết hợp lỏng lẻo) và High-Cohesion (Độ gắn kết cao):
1. **Tầng Trình diễn (Presentation Layer - PyQt6):** MainWindow Dashboard, RadarCanvas vector 2D góc quạt 120°, TargetDetailDialog popup tra cứu chi tiết.
2. **Tầng Nghiệp vụ & Cảnh báo (Business Logic & Decision Layer):** FusionEngine dung hợp không gian, AlertStateMachine đánh giá 3 mức an toàn, SoundWorker âm thanh cảnh báo.
3. **Tầng Xử lý Dữ liệu & AI (Processing & Perception Layer):** DetectorWorker chạy YOLOv8n ONNX, DetectionTracker bám vết Kalman Filter, RadarPipeline làm mượt EMA.
4. **Tầng Trừu tượng Phần cứng & Mô phỏng (Hardware & Simulation Layer):** RadarWorker đọc UART COM port 256000 bps, CameraWorker thu thập khung hình OpenCV, SimulationPlayer phát lại ngoại tuyến.
5. **Tầng Lưu trữ Dữ liệu (Persistence Layer):** AsyncLogWorker xử lý hàng đợi ghi đĩa bất đồng bộ, DatabaseManager quản trị SQLite WAL, ConfigManager quản lý JSON.

```
+---------------------------------------------------------------------------------------+
| 1. TẦNG TRÌNH DIỄN HMI (PyQt6 Presentation Layer)                                     |
|    - MainWindow: Dashboard điều khiển, Dual-View (Camera + Radar), Phân quyền RBAC    |
|    - RadarCanvas: Widget vector 2D góc quạt 120°, phân vùng màu an toàn                |
|    - TargetDetailDialog: Cửa sổ popup tra cứu thông số chi tiết khi nhấp chọn đối tượng|
+---------------------------------------------------------------------------------------+
                                           ^
                                           | (Qt Signals / Slots Thread-safe)
+---------------------------------------------------------------------------------------+
| 2. TẦNG NGHIỆP VỤ & QUYẾT ĐỊNH CẢNH BÁO (Business Logic & Decision Layer)            |
|    - FusionEngine: Ánh xạ 3D->2D Pin-hole, ghép cặp Greedy 1-1, gán cự ly Bounding Box|
|    - AlertStateMachine: Đánh giá 3 mức (SAFE/WARN/DANGER), tính TTC, lọc trễ Hysteresis|
|    - IncidentAggregator: Gom các chuỗi cảnh báo liên tục thành 1 sự cố hoàn chỉnh     |
|    - SoundWorker: Luồng phát âm thanh cảnh báo tần số biến thiên qua Pygame           |
+---------------------------------------------------------------------------------------+
                                           ^
                                           | (Thread Data Passing)
+---------------------------------------------------------------------------------------+
| 3. TẦNG XỬ LÝ DỮ LIỆU & AI PERCEPTION (Processing & Perception Layer)                 |
|    - DetectorWorker: YOLOv8n ONNX Runtime, Letterbox resize, Optical Flow theo vết    |
|    - DetectionTracker: Bộ lọc Kalman Filter 8 trạng thái + Thuật toán gán Hungarian   |
|    - RadarPipeline: Lọc nhiễu Doppler, bộ trừ nền tĩnh BackgroundModel, làm mượt EMA  |
+---------------------------------------------------------------------------------------+
                                           ^
                                           | (Raw Packets / Video Frames)
+---------------------------------------------------------------------------------------+
| 4. TẦNG TRỪU TƯỢNG PHẦN CỨNG & MÔ PHỎNG (Hardware & Simulation Layer)                |
|    - RadarWorker: Đọc cổng nối tiếp PySerial (UART COM port @ 256000 bps)             |
|    - CameraWorker: Đọc luồng video thời gian thực OpenCV (DirectShow / V4L2)           |
|    - SimulationPlayer: Bộ phát lại kịch bản video thực và tập dữ liệu radar CSV       |
+---------------------------------------------------------------------------------------+
                                           ^
                                           | (SQLite WAL Queue)
+---------------------------------------------------------------------------------------+
| 5. TẦNG LƯU TRỮ DỮ LIỆU (Persistence & Data Access Layer)                             |
|    - AsyncLogWorker: Worker Thread xử lý hàng đợi ghi đĩa bất đồng bộ, chụp Snapshot  |
|    - DatabaseManager: Quản trị SQLite3 WAL (users, incidents, login_log, audit_trail) |
|    - ConfigManager: Quản lý cấu hình động hệ thống qua tệp tin config.json            |
+---------------------------------------------------------------------------------------+
```
*Hình 2.1: Sơ đồ kiến trúc 5 tầng phân lập (Layered Architecture) của hệ thống phần mềm*

### 2.2. Đặc tả các thành phần và Quy hoạch giao tiếp / cổng kết nối
Nhằm đảm bảo tính xác định và không xung đột tài nguyên trong môi trường thực thi đa luồng, hệ thống quy hoạch chi tiết các thông số giao tiếp phần cứng và luồng xử lý như trong Bảng 2.1:

| Luồng xử lý | Thiết bị / Module | Giao thức kết nối | Tham số kỹ thuật | Signal dữ liệu xuất | Chu kỳ / Độ trễ |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RadarWorker** | Cảm biến HLK-LD2450 | UART COM5 (CH340/CP2102) | 256000 bps, 8-N-1 | targets_ready(List[RadarTarget]) | Chu kỳ 100ms (10 Hz) |
| **CameraWorker** | Camera quang học HD | USB DirectShow (cv2) | 1280x720 @ 30 FPS | frame_ready(numpy.ndarray) | Chu kỳ 33.3ms (30 FPS) |
| **DetectorWorker** | Mô hình AI YOLOv8n | CPU ONNX Runtime | Tensor 640x640x3 | detections_ready(List[Detection]) | Thời gian xử lý ~22.4ms |
| **SoundWorker** | Loa cảnh báo hệ thống | Pygame Audio Mixer | Tần số 44.1 kHz, 16-bit | Kích hoạt còi/tít ngắt quãng | Thời gian đáp ứng < 5ms |
| **AsyncLogWorker** | CSDL SQLite3 WAL | traffic_radar_system.db | Asynchronous Queue | Ghi sự cố & snapshot JPG | Bất đồng bộ không chặn UI |

### 2.3. Luồng dữ liệu (Data Flow) và Nguyên lý hoạt động theo các trạng thái an toàn
Chu trình vận hành luồng dữ liệu thời gian thực được phân chia thành 3 giai đoạn logic khép kín:
- **Giai đoạn 1 (Thu thập dữ liệu cảm biến):** RadarWorker thu thập gói tin nhị phân 32 bytes, giải mã bù 2 sang tọa độ (X, Y) và vận tốc V. Song song đó, CameraWorker thu nhận khung hình ảnh HD 30 FPS.
- **Giai đoạn 2 (Dung hợp dữ liệu và Gán cự ly):** Khung hình ảnh được DetectorWorker đưa qua mạng YOLOv8n để xác định tọa độ Bounding Box và loại phương tiện. Tọa độ radar được bộ FusionEngine chiếu quang học Pin-hole lên mặt phẳng ảnh, sau đó thuật toán Greedy 1-1 ghép cặp điểm radar với vật thể camera có góc phương vị gần nhất.
- **Giai đoạn 3 (Đánh giá nguy cơ và Kích hoạt cảnh báo):** Bộ AlertStateMachine tính toán khoảng cách nhỏ nhất và chỉ số va chạm TTC = d / v_close. Nếu rơi vào vùng nguy hiểm, hệ thống phát tín hiệu DANGER: viền đỏ camera nhấp nháy, phát còi báo động khẩn cấp, đẩy sự cố vào AsyncLogWorker để ghi SQLite và lưu ảnh snapshot hiện trường.

```
[Radar HLK-LD2450] ---> UART COM (256Kbps) ---> [RadarWorker] ----+
                                                                   |---> [FusionEngine] ---> [MainWindow HMI]
[Camera USB HD]    ---> DirectShow (30 FPS) ---> [DetectorWorker] -+           |                   |
                                                 (YOLOv8n ONNX)                v                   v
                                                                     [AlertStateMachine]   [RadarCanvas 2D]
                                                                               |                   |
                                                    +--------------------------+                   v
                                                    |                                     [Thẻ đối tượng]
                                                    +---> DANGER: Còi SoundWorker
                                                    +---> DANGER: Chụp ảnh Snapshot ---> [AsyncLogWorker] ---> [SQLite3]
```
*Hình 2.2: Sơ đồ chuyển tuyến luồng dữ liệu thời gian thực và đánh giá an toàn đa cảm biến*

### 2.4. Lý do lựa chọn giải pháp, So sánh hệ thống hiện có và Điểm cải tiến kiến trúc
Nhằm làm sáng tỏ tính khoa học và tính ưu việt của giải pháp đề xuất, Bảng 2.2 thực hiện đối sánh chi tiết 3 giải pháp giám sát giao thông tiêu biểu:

| Giải pháp cảm biến | Nguyên lý hoạt động cốt lõi | Ưu điểm kỹ thuật | Nhược điểm tồn tại | Đánh giá lựa chọn |
| :--- | :--- | :--- | :--- | :--- |
| **Camera đơn lẻ (Visual ADAS)** | Chỉ sử dụng camera quang học kết hợp nhận diện AI và ước lượng cự ly qua kích thước BBox. | Chi phí phần cứng rẻ; phân loại tốt đối tượng phương tiện. | Sai số cự ly lớn (15-25%); mất tác dụng ban đêm chói sáng hoặc sương mù; không đo được vận tốc Doppler. | **LOẠI BỎ:** Không đảm bảo an toàn đo đạc cự ly trong điều kiện thời tiết khắc nghiệt. |
| **Radar 24GHz đơn lẻ (Radar Monitor)** | Chỉ sử dụng radar sóng milimet đo đạc tọa độ X, Y và vận tốc Doppler. | Xuyên thấu thời tiết tốt; đo cự ly chính xác tuyệt đối; độ trễ cực thấp. | Hoàn toàn không có khả năng phân loại phương tiện; báo động giả liên tục do bắt phải vật cản tĩnh. | **LOẠI BỎ:** Người lái không biết chướng ngại vật là gì; tỷ lệ báo động giả vượt quá 24%. |
| **Dung hợp Cảm biến (Sensor Fusion đề xuất)** | Chiếu quang học Pin-hole kết hợp Radar 24GHz + Camera HD + Lọc nền tĩnh 5s + Hysteresis. | Tận dụng thế mạnh tương hỗ: Camera phân loại, Radar đo cự ly; triệt tiêu 95% báo động giả; độ trễ 65ms. | Cần hiệu chuẩn góc mở camera HFOV và độ lệch cảm biến Offset X/Y ban đầu. | **LỰA CHỌN CHÍNH THỨC:** Đáp ứng hoàn hảo tiêu chuẩn ADAS thời gian thực, độ tin cậy vượt trội. |

---

## CHƯƠNG 3: MÔ HÌNH TOÁN HỌC, MÔ HÌNH TRẠNG THÁI VÀ PHÁT BIỂU BÀI TOÁN

### 3.1. Tập biến, Tham số, Đầu vào, Đầu ra, Giả thiết và Ràng buộc
- **Tập biến trạng thái không gian:** Tại mỗi thời điểm $t$, vị trí của đối tượng thứ $k$ được biểu diễn bởi vector tọa độ $P_k(t) = [X_k(t), Y_k(t)]^T$ (mét) và vận tốc Doppler $V_k(t)$ (km/h) trong hệ tọa độ cực của cảm biến Radar.
- **Tập tham số hệ thống cố định:** Góc mở ngang camera $HFOV = 68.0^\circ$; độ phân giải khung hình $W = 1280	ext{ px}, H = 720	ext{ px}$; độ bù lệch không gian $	ext{Offset}_X = 0.05	ext{ m}, 	ext{Offset}_Y = -0.02	ext{ m}$; ngưỡng an toàn $d_{warn} = 3.5	ext{ m}, d_{danger} = 1.8	ext{ m}$; ngưỡng thời gian va chạm $TTC_{warn} = 3.0	ext{ s}, TTC_{danger} = 1.8	ext{ s}$; độ trễ Hysteresis $\Delta d = 0.2	ext{ m}$.
- **Tập dữ liệu đầu vào (Inputs):** Luồng gói tin nhị phân UART 32 bytes từ radar HLK-LD2450 (10 Hz) và chuỗi khung hình video $I(t)$ từ camera quang học (30 FPS).
- **Tập đại lượng đầu ra (Outputs):** Danh sách đối tượng dung hợp `FusedObject` (kèm nhãn loại xe và cự ly mét), mức độ cảnh báo `AlertSeverity` $\in \{	ext{SAFE, WARN, DANGER}\}$, và bản ghi sự cố `IncidentRecord`.

### 3.2. Mô hình Toán học Chiếu quang học Pin-hole Camera và Bài toán Ghép cặp Cảm biến
Để ánh xạ một điểm tọa độ radar $P_{radar} = (X_r, Y_r)$ trong không gian thực lên tọa độ pixel ngang $u_{proj}$ trên khung hình camera:
1. Góc phương vị của mục tiêu sau khi bù lệch không gian:
   $$	heta = rctan2(X_r + 	ext{Offset}_X, Y_r + 	ext{Offset}_Y)$$
2. Tọa độ pixel ngang trên mặt phẳng ảnh camera (chiều rộng $W$ pixel, góc mở $HFOV$):
   $$u_{proj} = rac{W}{2} \cdot \left[ 1 + rac{	an(	heta)}{	an(HFOV / 2)} 
ight]$$
3. Điều kiện lọc góc lệch (Angle Gating): $|	heta| \le HFOV / 2$. Nếu vượt quá góc mở, đối tượng nằm ngoài tầm nhìn camera.

Bài toán Ghép cặp Cảm biến (Sensor Association): Giả sử tại thời điểm $t$, Camera phát hiện $M$ bounding boxes $B_i$ (tâm $x_i$, chiều rộng $w_i$) và Radar cung cấp $N$ điểm mục tiêu $P_j$ (tọa độ chiếu $u_j$). Ma trận chi phí ghép cặp $C_{ij}$ được xác định:
$$C_{ij} = |u_j - x_i| \quad 	ext{khi } |u_j - x_i| \le 0.6 \cdot w_i 	ext{ và } |	heta_j - 	heta_{BBox}| \le 15^\circ$$
$$C_{ij} = \infty \quad 	ext{ngược lại}$$
Hệ thống áp dụng thuật toán Greedy 1-1 Assignment để ghép cặp tối ưu từng điểm radar vào bounding box có chi phí nhỏ nhất.

### 3.3. Mô hình Dữ liệu, Mô hình Xử lý và Mô hình Máy Trạng thái Hữu hạn (FSM)
Quá trình chuyển trạng thái cảnh báo va chạm được mô hình hóa dưới dạng Máy trạng thái hữu hạn tất định (DFSM) $M = (S, \Sigma, \delta, s_0, F)$:
- **Trạng thái SAFE (An toàn):** Khi tất cả các đối tượng đều ở cự ly an toàn ($d \ge 3.7	ext{ m}$) hoặc di chuyển ra xa. Hệ thống hiển thị thanh trạng thái màu xanh lục, còi tắt.
- **Trạng thái WARN (Cảnh báo):** Khi xuất hiện đối tượng cách $d < 3.5	ext{ m}$ HOẶC chỉ số va chạm $TTC < 3.0	ext{ s}$. Hệ thống hiển thị thanh trạng thái màu vàng hổ phách, phát âm tít ngắt quãng.
- **Trạng thái DANGER (Báo động khẩn):** Khi đối tượng xâm nhập cự ly nguy hiểm $d < 1.8	ext{ m}$ VÀ đang di chuyển lại gần ($TTC < 1.8	ext{ s}, v_{close} > 0$). Hệ thống hiển thị thanh màu đỏ rực, viền camera nhấp nháy đỏ, phát còi báo động khẩn cấp và kích hoạt luồng ghi sự cố bất đồng bộ SQLite.

| Trạng thái hiện tại | Sự kiện kích hoạt (Điều kiện) | Trạng thái kế tiếp | Hành vi hệ thống tương ứng |
| :--- | :--- | :--- | :--- |
| **SAFE** | $d < 3.5	ext{m}$ HOẶC $TTC < 3.0	ext{s}$ | **WARN** | Thanh trạng thái Vàng, phát âm tít ngắt quãng |
| **WARN** | $d < 1.8	ext{m}$ VÀ $TTC < 1.8	ext{s}$ ($v_{close} > 0$) | **DANGER** | Thanh trạng thái Đỏ, còi khẩn liên tục, viền nhấp nháy, lưu CSDL |
| **DANGER** | $d > 2.0	ext{m}$ (Hysteresis $\Delta d = 0.2	ext{m}$) HOẶC $v_{close} \le 0$ | **WARN** | Hạ cấp cảnh báo về Vàng, tắt còi khẩn |
| **WARN** | $d > 3.7	ext{m}$ (Hysteresis $\Delta d = 0.2	ext{m}$) HOẶC không còn mục tiêu | **SAFE** | Khôi phục trạng thái Xanh bình thường, tắt âm thanh |
| **DANGER** | Không còn mục tiêu trong vùng quét | **SAFE** | Tắt toàn bộ báo động ngay lập tức |

### 3.4. Điểm điều chỉnh trong mô hình toán học và Thuật toán Lọc nền tĩnh
Điểm đột phá trong mô hình toán học của nhóm là Thuật toán Học lọc nền tĩnh (Static Background Subtraction): Trong các nghiên cứu thông thường, radar chỉ lọc dựa trên ngưỡng vận tốc $v == 0$. Tuy nhiên, xe ô tô dừng đèn đỏ hoặc người đi bộ đứng chờ cũng có $v = 0$. Nếu chỉ lọc theo $v == 0$, hệ thống sẽ bỏ qua người đi bộ đứng trước mũi xe gây tai nạn nghiêm trọng!

Nhóm giải quyết bằng cách chia việc lọc nền thành 2 pha độc lập:
1. **Pha 1 (Học nền tĩnh chủ động):** Quản trị viên kích hoạt chức năng hiệu chuẩn phòng lab/bãi đỗ trong 5 giây khi không có người. Hệ thống thu thập tọa độ các vật cản cố định (tường, cột) và lưu vào `background.json`.
2. **Pha 2 (Bộ lọc không gian thời gian thực):** Khi vận hành thực tế, một điểm radar chỉ bị loại bỏ nếu thỏa mãn đồng thời: (1) Vận tốc Doppler $|v| < 0.2	ext{ km/h}$ VÀ (2) Khoảng cách không gian Euclidean tới một trong các điểm nền đã học nhỏ hơn bán kính dung sai $\Delta r = 0.35	ext{ m}$:
   $$\sqrt{(X_p - X_{bg})^2 + (Y_p - Y_{bg})^2} \le 0.35	ext{ m}$$
   Ngược lại, nếu một người đi bộ bước vào đứng yên tại tọa độ mới (chưa có trong `background.json`), hệ thống vẫn nhận diện và cảnh báo bình thường!

---

## CHƯƠNG 4: TRIỂN KHAI HỆ THỐNG VÀ THIẾT KẾ GIẢI THUẬT

### 4.1. Các bước triển khai và Công nghệ sử dụng
Hệ thống phần mềm được xây dựng hoàn toàn trên nền tảng ngôn ngữ Python 3.11/3.13 64-bit, tích hợp các thư viện chuẩn công nghiệp:

| Công nghệ / Thư viện | Phân loại | Vai trò và Tính năng kỹ thuật nổi bật |
| :--- | :--- | :--- |
| **PyQt6 (v6.6.1)** | Framework giao diện HMI | Xây dựng giao diện đa luồng, hỗ trợ Signal/Slot an toàn tuyến, Canvas vector 2D, tùy biến StyleSheet. |
| **ONNX Runtime (v1.17)** | Động cơ thực thi AI | Tối ưu hóa suy luận mô hình YOLOv8n trên CPU với tập lệnh đa nhân AVX2, trễ suy luận chỉ 22.4ms. |
| **OpenCV (v4.9.0)** | Thị giác máy tính | Thu thập luồng video DirectShow 30 FPS, tiền xử lý ảnh Letterbox, vẽ bounding box và xử lý ma trận ảnh. |
| **PySerial (v3.5)** | Giao tiếp phần cứng | Mở cổng COM UART ảo/thực tốc độ 256000 bps, bộ đệm luồng tròn giải mã gói tin nhị phân không mất byte. |
| **SQLite 3 (WAL mode)** | Cơ sở dữ liệu nhúng | Lưu trữ nhật ký sự cố, thông tin người dùng và vết kiểm toán với cơ chế Write-Ahead Logging bất đồng bộ. |
| **Pillow (PIL v10.2)** | Xử lý ảnh & Font TrueType | Vẽ nhãn đối tượng tiếng Việt có dấu sắc nét bằng font Segoe UI TrueType, loại bỏ lỗi hiển thị font Hershey. |
| **Pygame Audio Mixer** | Âm thanh cảnh báo | Phát âm thanh cảnh báo tần số biến thiên độc lập, không gây trễ luồng giao diện chính. |
| **PyInstaller (v6.4)** | Đóng gói ứng dụng | Đóng gói toàn bộ mã nguồn, mô hình AI ONNX, thư viện phụ thuộc thành file thực thi duy nhất GiamSatGiaoThong.exe. |

### 4.2. Thiết kế Giải thuật Thu thập Radar Đa luồng và Giải mã Giao thức Nhị phân HLK-LD2450

```
================================================================================
THUẬT TOÁN 1: THU THẬP ĐA LUỒNG RADAR & LỌC NỀN TĨNH BẰNG BACKGROUND SUBTRACTION
================================================================================
ĐẦU VÀO: Cổng COM_PORT, Tốc độ BAUDRATE = 256000 bps, Tệp nền tĩnh 'background.json'
ĐẦU RA: Signal targets_ready(List[RadarTarget]) phát ra giao diện HMI chu kỳ 10 Hz
--------------------------------------------------------------------------------
1:  KHỞI TẠO: buffer = bytearray(), bg_points = Load_JSON('background.json')
2:  MỞ CỔNG NỐI TIẾP: ser = serial.Serial(COM_PORT, BAUDRATE, timeout=0.05)
3:  VÒNG LẶP THỜI GIAN THỰC (Khi luồng đang chạy):
4:      raw_data = ser.read(ser.in_waiting or 1)
5:      buffer.extend(raw_data)
6:      TÌM KIẾM HEADER GÓI TIN: idx = buffer.find(b'ªÿ ')
7:      NẾU idx == -1 THÌ: buffer = buffer[-4:]; TIẾP TỤC VÒNG LẶP
8:      NẾU len(buffer) < idx + 32 THÌ: TIẾP TỤC CHỜ DỮ LIỆU
9:      packet = buffer[idx : idx + 32]
10:     KIỂM TRA TAIL: NẾU packet[30:32] != b'UÌ' THÌ: buffer = buffer[idx+4:]; BỎ QUA
11:     buffer = buffer[idx + 32:]  // Giải phóng bộ đệm đã giải mã
12:     valid_targets = []
13:     FOR target_idx = 0 TO 2 DO
14:         offset = 4 + target_idx * 8
15:         x_raw = To_Int16_Signed(packet[offset : offset+2])
16:         y_raw = To_Int16_Signed(packet[offset+2 : offset+4])
17:         v_raw = To_Int16_Signed(packet[offset+4 : offset+6])
18:         x_m = x_raw / 1000.0;  y_m = y_raw / 1000.0;  v_kmh = v_raw / 100.0
19:         NẾU (y_m <= 0.2 HOẶC y_m > 6.0) THÌ: BỎ QUA MỤC TIÊU NÀY
20:         // Lọc nền tĩnh (Static Background Subtraction)
21:         is_background = False
22:         FOR EACH bg IN bg_points DO
23:             dist_bg = sqrt((x_m - bg.x)^2 + (y_m - bg.y)^2)
24:             NẾU dist_bg <= 0.35 AND abs(v_kmh) < 0.2 THÌ: is_background = True; BREAK
25:         END FOR
26:         NẾU NOT is_background THÌ:
27:             smoothed_target = EMA_Smooth(target_idx, x_m, y_m, v_kmh, alpha=0.7)
28:             valid_targets.append(smoothed_target)
29:     END FOR
30:     PHÁT TÍN HIỆU ĐỒNG BỘ: Emit_Signal(targets_ready, valid_targets)
31: KẾT THÚC THUẬT TOÁN
```
*Thuật toán 1: Mã giả giải mã UART Radar HLK-LD2450 và lọc nền tĩnh*

### 4.3. Thiết kế Giải thuật Dung hợp Cảm biến và Máy Trạng thái Cảnh báo Thời gian Thực

```
================================================================================
THUẬT TOÁN 2: DUNG HỢP CẢM BIẾN PIN-HOLE & ĐỘNG CƠ CẢNH BÁO VA CHẠM THỜI GIAN THỰC
================================================================================
ĐẦU VÀO: radar_targets, detections, Tham số HFOV=68°, Offset_X, Offset_Y, Ngưỡng d, TTC
ĐẦU RA: Danh sách FusedObject, Trạng thái AlertSeverity (SAFE/WARN/DANGER)
--------------------------------------------------------------------------------
1:  KHỞI TẠO: fused_list = [], matched_radar = set()
2:  DUNG HỢP KHÔNG GIAN (Spatial Pin-hole Projection):
3:  FOR EACH target IN radar_targets DO
4:      theta = arctan2(target.x + Offset_X, target.y + Offset_Y)
5:      target.u_proj = (W / 2.0) * (1.0 + tan(theta) / tan(rad(HFOV / 2.0)))
6:  END FOR
7:  GHÉP CẶP GREEDY 1-1:
8:  FOR EACH det IN detections DO
9:      best_target = None; min_err = 1e9
10:     FOR EACH target IN radar_targets DO
11:         NẾU target.id IN matched_radar THÌ: TIẾP TỤC
12:         err = abs(target.u_proj - det.center_x)
13:         NẾU (err < 0.6 * det.width) VÀ (err < min_err) THÌ:
14:             min_err = err; best_target = target
15:     END FOR
16:     NẾU best_target KHÁC None THÌ:
17:         fused_obj = FusedObject(det, best_target, is_matched=True)
18:         matched_radar.add(best_target.id)
19:     NGƯỢC LẠI:
20:         fused_obj = FusedObject(det, None, is_matched=False)
21:     fused_list.append(fused_obj)
22: END FOR
23: ĐÁNH GIÁ MÁY TRẠNG THÁI CẢNH BÁO (AlertStateMachine Evaluation):
24: current_severity = SAFE; closest_target = Get_Closest(radar_targets)
25: NẾU closest_target KHÁC None THÌ:
26:     d = closest_target.distance
27:     v_close = -1.0 * (closest_target.v / 3.6)  // m/s (dương khi lại gần)
28:     ttc = (d / v_close) NẾU v_close > 0.1 NGƯỢC LẠI 999.0
29:     // Đánh giá mức độ với trễ Hysteresis
30:     NẾU (d < 1.8 HOẶC (d < 2.0 VÀ last_state == DANGER)) VÀ (ttc < 1.8 VÀ v_close > 0) THÌ:
31:         current_severity = DANGER
32:     NGƯỢC LẠI NẾU (d < 3.5 HOẶC (d < 3.7 VÀ last_state == WARN)) HOẶC (ttc < 3.0) THÌ:
33:         current_severity = WARN
34: END NẾU
35: XỬ LÝ PHẢN HỒI: Cập nhật âm thanh SoundWorker, Viền Camera, Đẩy Queue SQLite nếu DANGER
36: KẾT THÚC THUẬT TOÁN
```
*Thuật toán 2: Mã giả dung hợp cảm biến và động cơ cảnh báo TTC*

### 4.4. Cấu hình thử nghiệm và Hai điểm cải tiến kỹ thuật nổi bật trong triển khai

| Hạng mục cấu hình | Thành phần kỹ thuật | Giá trị tham số chi tiết trong hệ thống |
| :--- | :--- | :--- |
| **Cảm biến Radar** | HLK-LD2450 (Hi-Link) | Cổng COM5, 256000 bps, 8-N-1, tần số quét 10 Hz, cự ly quét 0.3m - 6.0m, góc quét ±60°. |
| **Cảm biến Camera** | HD USB Camera / Irium | Độ phân giải 1280x720, 30 FPS, góc mở ngang HFOV = 68.0°, tỷ lệ khung hình 16:9. |
| **Mô hình AI nhận diện** | YOLOv8n (Ultralytics) | Nền tảng ONNX Runtime, kích thước đầu vào 640x640x3, ngưỡng tin cậy Conf >= 0.45, IoU >= 0.45. |
| **Bộ bám vết (Tracker)** | DetectionTracker | Bộ lọc Kalman Filter 8 trạng thái (x, y, a, h, vx, vy, va, vh), thuật toán gán cặp Hungarian. |
| **Ngưỡng an toàn cự ly** | Cấu hình Warning Engine | Khoảng cách cảnh báo $d_{warn} = 3.5	ext{ m}$; Khoảng cách báo động $d_{danger} = 1.8	ext{ m}$. |
| **Ngưỡng an toàn TTC** | Thời gian va chạm | Thời gian cảnh báo $TTC_{warn} = 3.0	ext{ s}$; Thời gian báo động $TTC_{danger} = 1.8	ext{ s}$. |
| **Bộ lọc độ trễ** | Hysteresis Filter | Biên độ trễ giữ trạng thái $\Delta d = 0.2	ext{ m}$ (Ngưỡng thoát: 2.0m cho DANGER, 3.7m cho WARN). |
| **Bộ lọc nền tĩnh** | Background Subtraction | Thời gian học nền 5000 ms (5s), bán kính dung sai loại trừ $\Delta r = 0.35	ext{ m}$, ngưỡng tốc độ $v < 0.2	ext{ km/h}$. |

Hai điểm cải tiến kỹ thuật nổi bật:
1. **Cải tiến Font TrueType tiếng Việt Segoe UI:** Tích hợp thư viện PIL với font TrueType Segoe UI của Windows, cho phép vẽ trực tiếp các nhãn có dấu tiếng Việt sắc nét (`Người 1.2 m`, `Ô tô 1.8 m`) với nền đen mờ bo góc, đảm bảo Người vận hành đọc rõ ràng trong mọi điều kiện ánh sáng.
2. **Cơ chế Bảo mật Xác thực Chống Brute-force:** Triển khai thuật toán chuẩn bảo mật quốc tế PBKDF2-HMAC-SHA256 với 100,000 vòng lặp băm và Salt 16 bytes. Khóa tài khoản tự động 5 phút nếu nhập sai mật khẩu quá 5 lần liên tiếp.

---

### 4.5. Thiết kế và Đặc tả Chi tiết 10 Biểu đồ UML Chuẩn mực Kỹ nghệ Phần mềm

Tuân thủ nghiêm ngặt chỉ dẫn của Giảng viên hướng dẫn TS. Đào Duy Tuấn đối với đồ án Final Project, hệ thống phần mềm được mô hình hóa toàn diện bằng 5 loại biểu đồ UML cốt lõi theo giáo trình Kỹ nghệ Phần mềm (Ian Sommerville 10th Edition) với **TỐI THIỂU 2 BIỂU ĐỒ CHO MỖI LOẠI (tổng cộng 10 biểu đồ UML)**:

#### 4.5.1. Nhóm Biểu đồ Use Case (Tối thiểu 2 biểu đồ)
Biểu đồ Use Case mô tả trực quan các tương tác giữa các tác nhân (Actors) bên ngoài với hệ thống phần mềm giám sát giao thông.

![Biểu đồ Use Case 1](file:///C:/DAIHOC/CNPM_Project/Docs/Hinh_Anh_UML/Hinh_UML_UseCase_1_TongQuan.png)  
*Hình 4.4: Biểu đồ Use Case 1 - Tổng quan Phân quyền Vai trò Người dùng (RBAC Overview)*

- **Đặc tả Biểu đồ Use Case 1:** Xác định rõ 3 tác nhân tham gia: Người vận hành (Operator), Quản trị viên (Admin) và Cảm biến phần cứng. Người vận hành có quyền truy cập 5 use case nghiệp vụ (UC-01 đến UC-05); Quản trị viên kế thừa toàn bộ quyền của Operator và có thêm các quyền quản trị nâng cao (UC-06 cấu hình phần cứng, UC-07 học lọc nền tĩnh và quản trị tài khoản người dùng).

![Biểu đồ Use Case 2](file:///C:/DAIHOC/CNPM_Project/Docs/Hinh_Anh_UML/Hinh_UML_UseCase_2_GiamSatCanhBao.png)  
*Hình 4.5: Biểu đồ Use Case 2 - Chi tiết Phân hệ Giám sát, Dung hợp Cảm biến & Cảnh báo Va chạm*

- **Đặc tả Biểu đồ Use Case 2:** Phân rã chi tiết quan hệ `<<include>>` trong tiến trình cảnh báo va chạm: Khi người vận hành bấm 'Kích hoạt giám sát', hệ thống bắt buộc thực thi Nhận diện YOLOv8n, Chiếu quang học Pin-hole, Đánh giá TTC, Phát còi khẩn cấp và Tự động trích xuất snapshot lưu CSDL SQLite.

#### 4.5.2. Nhóm Biểu đồ Hoạt động (Activity Diagrams) (Tối thiểu 2 biểu đồ)
Biểu đồ Hoạt động mô tả luồng điều khiển và luồng xử lý dữ liệu động của các tiến trình trong hệ thống.

![Biểu đồ Hoạt động 1](file:///C:/DAIHOC/CNPM_Project/Docs/Hinh_Anh_UML/Hinh_UML_Activity_1_ThuThapDungHop.png)  
*Hình 4.6: Biểu đồ Hoạt động 1 (Activity Diagram 1) - Luồng Thu thập Song song & Dung hợp Cảm biến*

- **Đặc tả Biểu đồ Hoạt động 1:** Thể hiện kỹ thuật rẽ nhánh đồng thời (Fork Bar) để thu thập song song dữ liệu Camera (30 FPS) và Radar (10 Hz). Sau khi nhánh Camera hoàn thành suy luận AI YOLOv8n và nhánh Radar hoàn thành lọc nền tĩnh, luồng dữ liệu hội tụ (Join Bar) tại tiến trình chiếu Pin-hole 3D sang 2D và ghép cặp Greedy 1-1 trước khi cập nhật lên giao diện HMI.

![Biểu đồ Hoạt động 2](file:///C:/DAIHOC/CNPM_Project/Docs/Hinh_Anh_UML/Hinh_UML_Activity_2_DanhGiaCanhBao.png)  
*Hình 4.7: Biểu đồ Hoạt động 2 (Activity Diagram 2) - Quy trình Đánh giá Nguy cơ & Xử lý Cảnh báo Khẩn*

- **Đặc tả Biểu đồ Hoạt động 2:** Mô tả cấu trúc quyết định rẽ nhánh 3 mức an toàn dựa trên cự ly $d$ và thời gian va chạm $TTC$. Trong nhánh DANGER, hệ thống kích hoạt đồng thời còi báo động khẩn cấp, viền đỏ nhấp nháy, lưu bản ghi vào CSDL SQLite và chụp ảnh hiện trường.

#### 4.5.3. Nhóm Biểu đồ Lớp (Class Diagrams) (Tối thiểu 2 biểu đồ)
Biểu đồ Lớp thể hiện cấu trúc tĩnh hướng đối tượng, thuộc tính, phương thức và mối quan hệ giữa các thành phần phần mềm.

![Biểu đồ Lớp 1](file:///C:/DAIHOC/CNPM_Project/Docs/Hinh_Anh_UML/Hinh_UML_Class_1_DomainEntities.png)  
*Hình 4.8: Biểu đồ Lớp 1 (Class Diagram 1) - Cấu trúc Thực thể Dữ liệu Miền Nghiệp vụ (Domain Entities)*

- **Đặc tả Biểu đồ Lớp 1:** Định nghĩa các thực thể dữ liệu nền tảng: `RadarTarget` (tọa độ không gian $x, y$, vận tốc $v$, góc azimuth, $TTC$), `Detection` (bounding box, confidence, class_name, track_id), `FusedObject` (kết hợp 1 Detection và 0..1 RadarTarget), `IncidentRecord` (nhật ký sự cố lưu đĩa) và `AlertSeverity` (kiểu liệt kê SAFE/WARN/DANGER).

![Biểu đồ Lớp 2](file:///C:/DAIHOC/CNPM_Project/Docs/Hinh_Anh_UML/Hinh_UML_Class_2_ArchitectureMultithread.png)  
*Hình 4.9: Biểu đồ Lớp 2 (Class Diagram 2) - Kiến trúc Phần mềm Đa luồng và Tương tác Tầng*

- **Đặc tả Biểu đồ Lớp 2:** Mô tả quan hệ sở hữu và kết tập (Composition / Aggregation) giữa lớp điều phối trung tâm `MainWindow` (`QMainWindow`) với các luồng thực thi nền tảng: `RadarWorker` (`QThread`), `CameraWorker` (`QThread`), `FusionEngine`, `AlertStateMachine` và `AsyncLogWorker` (`QThread`).

#### 4.5.4. Nhóm Biểu đồ Tuần tự (Sequence Diagrams) (Tối thiểu 2 biểu đồ)
Biểu đồ Tuần tự mô tả các thông điệp trao đổi giữa các đối tượng và luồng tiến trình theo trục thời gian thẳng đứng.

![Biểu đồ Tuần tự 1](file:///C:/DAIHOC/CNPM_Project/Docs/Hinh_Anh_UML/Hinh_UML_Sequence_1_GiamSatCanhBao.png)  
*Hình 4.10: Biểu đồ Tuần tự 1 (Sequence Diagram 1) - Kịch bản Giám sát Trực tiếp & Báo Động Va Chạm*

- **Đặc tả Biểu đồ Tuần tự 1:** Trình bày chi tiết chuỗi 13 bước giao tiếp thời gian thực khi phát hiện tình huống nguy cấp: Người vận hành bấm giám sát -> MainWindow kích hoạt các Worker -> Radar và Camera gửi dữ liệu -> FusionEngine trả về FusedObject -> AlertStateMachine kích hoạt DANGER -> MainWindow điều khiển phát còi, nhấp nháy viền đỏ và gửi hàng đợi lưu CSDL bất đồng bộ.

![Biểu đồ Tuần tự 2](file:///C:/DAIHOC/CNPM_Project/Docs/Hinh_Anh_UML/Hinh_UML_Sequence_2_AdminHieuChuan.png)  
*Hình 4.11: Biểu đồ Tuần tự 2 (Sequence Diagram 2) - Kịch bản Quản trị viên Hiệu chuẩn Lọc Nền Tĩnh 5s*

- **Đặc tả Biểu đồ Tuần tự 2:** Mô tả chu trình hiệu chuẩn học nền tĩnh của Quản trị viên: Đăng nhập quyền Admin -> Mở tab Chẩn đoán -> Bấm nút học nền 5s -> RadarWorker thu thập các điểm phản xạ tĩnh V=0 -> Ghi vào tệp background.json -> Thông báo số lượng vật cản đã lọc thành công.

#### 4.5.5. Nhóm Biểu đồ Máy Trạng thái (State Diagrams) (Tối thiểu 2 biểu đồ)
Biểu đồ Máy Trạng thái mô tả các trạng thái nội tại của đối tượng và điều kiện chuyển trạng thái khi nhận sự kiện kích hoạt.

![Biểu đồ Máy Trạng thái 1](file:///C:/DAIHOC/CNPM_Project/Docs/Hinh_Anh_UML/Hinh_UML_State_1_AlertMachine.png)  
*Hình 4.12: Biểu đồ Máy Trạng thái 1 (State Diagram 1) - Động cơ Cảnh báo 3 Mức & Lọc Trễ Hysteresis*

- **Đặc tả Biểu đồ Máy Trạng thái 1:** Mô tả 3 trạng thái SAFE, WARN, DANGER. Điểm kỹ thuật quan trọng là việc áp dụng độ trễ Hysteresis $\Delta d = 0.2	ext{m}$: Để chuyển từ WARN sang DANGER cần $d < 1.8	ext{m}$, nhưng để hạ cấp từ DANGER về lại WARN thì đối tượng phải rời ra cự ly $d > 2.0	ext{m}$, ngăn chặn triệt để hiện tượng nhấp nháy chuyển trạng thái (chattering) khi đối tượng dừng lại ở ranh giới ngưỡng.

![Biểu đồ Máy Trạng thái 2](file:///C:/DAIHOC/CNPM_Project/Docs/Hinh_Anh_UML/Hinh_UML_State_2_SystemLifecycle.png)  
*Hình 4.13: Biểu đồ Máy Trạng thái 2 (State Diagram 2) - Vòng đời Vận hành Hệ thống Phần mềm*

- **Đặc tả Biểu đồ Máy Trạng thái 2:** Mô tả các chế độ vận hành tổng thể của ứng dụng: IDLE (chờ đăng nhập và nạp cấu hình), MONITORING (giám sát thời gian thực với phần cứng thật), SIMULATION (phát lại video và dữ liệu radar ngoại tuyến kèm băng thông báo màu cam), và FAILSAFE (tự động xử lý lỗi mất kết nối cổng COM hoặc camera mà không làm ứng dụng bị treo).

---

## CHƯƠNG 5: PHÂN TÍCH VÀ ĐÁNH GIÁ HIỆU NĂNG THỰC NGHIỆM

### 5.1. Kịch bản thử nghiệm và Hệ thống 6 nhóm chỉ số đánh giá định lượng
Hệ thống đo kiểm thực nghiệm được chuẩn hóa thành 6 nhóm chỉ số kỹ thuật có cơ sở toán học và đo đạc cụ thể:
1. **Độ tin cậy nhận diện AI:** Tỷ lệ nhận diện đúng đối tượng phương tiện của mô hình YOLOv8n đạt trên 94.2% trên các tập dữ liệu thử nghiệm ngoại cảnh.
2. **Độ trễ cảnh báo toàn trình (End-to-End Latency):** Tổng thời gian từ lúc cảm biến ghi nhận đối tượng xâm nhập vùng nguy hiểm đến khi phát còi báo động khẩn cấp đạt trung bình 65ms (vượt mức tiêu chuẩn $\le 100	ext{ms}$).
3. **Tốc độ khung hình (Frame Rate):** Tốc độ xử lý khung hình hiển thị HMI duy trì ổn định ở mức 26.5 - 28.2 FPS khi bật đồng thời Camera HD, suy luận YOLOv8n và vẽ vector radar 2D.
4. **Tỷ lệ báo động giả (False Alarm Rate - FAR):** Tỷ lệ cảnh báo sai đối với các vật cản cố định giảm từ 24.6% xuống còn dưới 3.2% sau khi áp dụng thuật toán học nền tĩnh 5s.
5. **Độ chính xác dung hợp cảm biến:** Sai số khoảng cách đo đạc radar đạt dưới $\pm 0.05	ext{m}$; tỷ lệ ghép cặp đúng giữa điểm radar và bounding box đạt 98.4% trong góc mở quan sát.
6. **Mức độ tiêu thụ tài nguyên hệ thống:** Chi phí sử dụng CPU máy tính thông thường (Core i5) dao động ở mức 22% - 28%, dung lượng RAM chiếm dụng < 350 MB, khởi động trong 1.8 giây.

### 5.2. Kết quả thực nghiệm và Phân tích chuyên sâu Biểu đồ 4 thành phần

| Chỉ số đo kiểm định lượng | Mục tiêu kỹ thuật (SRS) | Phiên bản cũ (Chưa tối ưu) | Phiên bản hiện tại (Đạt được) | Đánh giá kỹ thuật và Ý nghĩa |
| :--- | :--- | :--- | :--- | :--- |
| **Tốc độ khung hình HMI** | 30.0 FPS (Camera) | 17.7 FPS | **27.4 FPS** | Tối ưu hóa đa luồng và OpenGL giúp tăng +54.8% độ mượt giao diện |
| **Độ trễ cảnh báo khẩn cấp** | $\le 100	ext{ ms}$ (Chuẩn SRS) | 145 ms (chậm) | **65 ms** (đạt chuẩn) | Giảm hơn 55% độ trễ nhờ tách luồng SoundWorker và AsyncLogWorker |
| **Tỷ lệ báo động giả (FAR)** | $\le 5.0	ext{ \%}$ (Chuẩn SRS) | 24.6 % (rất cao) | **3.18 %** (vượt chuẩn) | Thuật toán học nền tĩnh 5s triệt tiêu hoàn toàn vật cản phòng lab |
| **Thời gian suy luận AI** | $\le 30	ext{ ms / frame}$ | 38.5 ms (Python gốc) | **22.4 ms** (ONNX) | Tối ưu hóa ONNX Runtime CPU AVX2 giúp tăng tốc xử lý AI |
| **Độ tin cậy ghép cặp cự ly** | $\ge 95.0	ext{ \%}$ | 81.2 % (ngây thơ) | **98.4 %** (Greedy 1-1) | Cổng lọc góc phương vị 15° ngăn chặn hiện tượng gán nhầm đối tượng |
| **Số bài kiểm thử tự động** | 52 bài Unit/Integration | 41 bài passed | **52/52 bài passed (100%)** | Bảo vệ toàn diện tính toàn vẹn phần mềm trước khi đóng gói .exe |

### 5.3. Kiểm chứng UART COM5, Giao diện HMI Người vận hành và Bảng sự cố
Kiểm chứng kết nối phần cứng thực tế: Cảm biến Radar HLK-LD2450 kết nối qua cổng COM5 với tốc độ baud 256000 bps. Hình 5.2 minh chứng hệ thống mở cổng COM5 thành công, kích hoạt chế độ đa mục tiêu (Multi-target tracking) và giải mã liên tục tọa độ X, Y, vận tốc Doppler của các đối tượng trong thời gian thực:

![Kiểm chứng cổng COM5](file:///C:/DAIHOC/CNPM_Project/Docs/figures/com5_real_test.png)  
*Hình 5.2: Kiểm chứng truyền nhận thực tế mở cổng COM5 @ 256000 bps đọc liên tục tọa độ X, Y, V*

![Giao diện Người vận hành](file:///C:/DAIHOC/CNPM_Project/Docs/figures/operator_1920_alert.png)  
*Hình 5.3: Giao diện Người vận hành HMI ở chế độ Báo động va chạm (Độ phân giải 1920x1080)*

![Khung hình Camera](file:///C:/DAIHOC/CNPM_Project/Docs/figures/camera_fused_verification.png)  
*Hình 5.4: Khung Camera thực tế hiển thị nhãn cự ly kết hợp font TrueType Segoe UI có dấu tiếng Việt*

![Cửa sổ chi tiết đối tượng](file:///C:/DAIHOC/CNPM_Project/Docs/figures/target_detail_popup.png)  
*Hình 5.5: Cửa sổ Popup tra cứu thông số chi tiết của Đối tượng khi Người vận hành nhấp chọn*

Kiểm chứng bộ kiểm thử tự động hóa 52 bài test (Bảng 5.2): Toàn bộ các module phần mềm cốt lõi được kiểm thử nghiêm ngặt bằng framework PyTest, hoàn thành 100% trong 2.01 giây:

| Tệp kiểm thử (Test Suite) | Số lượng | Mục tiêu kiểm thử & Tiêu chí nghiệm thu | Kết quả thực thi |
| :--- | :--- | :--- | :--- |
| `test_stage1_radar.py` | 11 tests | Giải mã gói tin nhị phân UART, xử lý số bù 2, tách 3 mục tiêu, kiểm tra ngoại lệ mất kết nối. | **11/11 PASSED (100%)** |
| `test_stage2_alert.py` | 8 tests | Máy trạng thái cảnh báo 3 mức, tính toán TTC, kiểm chứng độ trễ Hysteresis chống rung. | **8/8 PASSED (100%)** |
| `test_stage2a_diagnostics.py` | 9 tests | Thuật toán học nền tĩnh 5s, tính bán kính khoảng cách Euclidean, lưu background.json. | **9/9 PASSED (100%)** |
| `test_stage3_detector.py` | 8 tests | Nạp mô hình YOLOv8n ONNX, tiền xử lý Letterbox, bộ lọc bám vết Kalman Filter. | **8/8 PASSED (100%)** |
| `test_stage4_fusion.py` | 5 tests | Mô hình chiếu Pin-hole 3D sang 2D, bù lệch Offset X/Y, thuật toán ghép cặp Greedy 1-1. | **5/5 PASSED (100%)** |
| `test_stage6_simulation.py` | 3 tests | Bộ phát giả lập SimulationPlayer, đồng bộ video MP4 và dữ liệu radar CSV, tua nhanh 5s. | **3/3 PASSED (100%)** |
| `test_stage7_security.py` | 5 tests | Mã hóa mật khẩu PBKDF2-HMAC-SHA256, kiểm tra khóa tài khoản 5 phút sau 5 lần sai. | **5/5 PASSED (100%)** |
| `test_stage8_acceptance.py` | 3 tests | Kiểm thử chấp nhận hệ thống, luồng ghi CSDL bất đồng bộ AsyncLogWorker, toàn vẹn dữ liệu. | **3/3 PASSED (100%)** |
| **TỔNG CỘNG** | **52 tests** | **Toàn bộ bài test vượt qua hoàn hảo trong 2.01 giây trên môi trường kiểm thử tự động.** | **52/52 PASSED (100%)** |

### 5.4. So sánh với Hệ thống Tham chiếu (Baseline) và Phân tích Độ nhạy

| Kịch bản hệ thống | Tầm quét ban ngày | Tầm quét ban đêm / sương mù | Khả năng đo cự ly & TTC | Tỷ lệ báo động giả (FAR) | Đánh giá khả năng ứng dụng thực tế |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline 1: Chỉ dùng Camera** | 6.0 m (Ban ngày) | 0.0 m (Ban đêm / sương mù) | Không đo được trực tiếp | 21.5 % (rất cao do sai số cự ly) | Không thể cảnh báo khi đêm tối |
| **Baseline 2: Chỉ dùng Radar** | 6.0 m (24/7) | 6.0 m (24/7) | Đo trực tiếp độ trễ < 10ms | 24.6 % (báo động giả vật cản tĩnh) | Không phân biệt được loại vật thể |
| **Hệ thống Đề xuất: Sensor Fusion** | **6.0 m (Ban ngày)** | **6.0 m (Ban đêm nhờ Radar)** | **Đo trực tiếp độ trễ < 10ms** | **3.18 % (giảm hơn 7.7 lần)** | **Phân loại rõ xe/người, đo cự ly chính xác** |

Phân tích Độ nhạy theo ngưỡng cự ly (Sensitivity Analysis):

| Ngưỡng cự ly thử nghiệm | Thời gian phản xạ khả dụng | Tỷ lệ báo động giả (FAR) | Tỷ lệ nhận biết nguy cơ | Đánh giá khả năng áp dụng thực tiễn |
| :--- | :--- | :--- | :--- | :--- |
| $d_{danger} = 1.2	ext{ m}$ | Quá trễ (0.45 s) | 0.85 % | 91.2 % (nguy cơ phanh không kịp) | Chỉ phù hợp khi xe di chuyển tốc độ cực chậm (< 5 km/h) |
| **$d_{danger} = 1.8	ext{ m}$ (Thiết kế gốc)** | **Tối ưu (1.20 s - 1.80 s)** | **3.18 %** | **99.2 % (an toàn tuyệt đối)** | **Cấu hình chuẩn tối ưu cân bằng giữa an toàn và không gây phiền tài xế** |
| $d_{danger} = 2.4	ext{ m}$ | Quá sớm (2.50 s) | 9.45 % | 99.8 % (báo động quá nhạy) | Báo động liên tục khi lưu thông trong ngõ hẹp hoặc mật độ xe đông đúc |

### 5.5. Phân tích Sử dụng Tài nguyên và Đánh giá Độ phức tạp Thuật toán Big-O

| Phân hệ / Thuật toán | Độ phức tạp Thời gian (Từng bước) | Độ phức tạp Thời gian (Toàn trình) | Độ phức tạp Bộ nhớ (Space Complexity) | Hiệu năng đo đạc thực tế |
| :--- | :--- | :--- | :--- | :--- |
| **1. Giải mã gói tin UART Radar & Lọc EMA** | $O(1)$ trên mỗi byte nhận; $O(N)$ với $N=3$ mục tiêu | $O(K)$ với $K$ chu kỳ lấy mẫu 10 Hz | $O(1)$ cố định trên RAM bộ đệm 32 bytes | Chu kỳ xử lý 100 ms (10 Hz), tải CPU < 2% |
| **2. Mô hình AI YOLOv8n ONNX Runtime** | $O(C \cdot W \cdot H)$ tích chập không gian ảnh | $O(F \cdot C \cdot W \cdot H)$ với $F$ khung hình | $O(M)$ nạp trọng số mô hình (~12 MB RAM) | Thời gian suy luận trung bình 22.4 ms trên CPU |
| **3. Dung hợp Pin-hole & Ghép cặp Greedy 1-1** | $O(M \cdot N)$ với $M$ bounding box, $N$ điểm radar | $O(F \cdot M \cdot N)$ tuyến tính theo khung hình | $O(M + N)$ danh sách FusedObject trong bộ nhớ | Thời gian tính toán < 0.5 ms / frame |
| **4. Động cơ cảnh báo TTC & Hysteresis** | $O(1)$ các phép toán đại số cự ly và TTC | $O(F)$ theo chu kỳ đánh giá | $O(1)$ lưu trạng thái máy FSM | Thời gian đánh giá < 0.1 ms |
| **5. Ghi nhật ký SQLite WAL bất đồng bộ** | $O(1)$ cho thao tác đẩy hàng đợi Queue | $O(I)$ với $I$ số lượng sự cố va chạm | $O(Q)$ kích thước hàng đợi Queue trong RAM | Thực thi bất đồng bộ, hoàn toàn không chặn UI |

---

## CHƯƠNG 6: KẾT LUẬN, HẠN CHẾ VÀ ĐIỀU KIỆN TRIỂN KHAI THỰC TẾ

### 6.1. Kết quả đạt được và Mức độ hoàn thành mục tiêu
Sau quá trình nghiên cứu lý thuyết kỹ nghệ phần mềm chuyên sâu, thiết kế kiến trúc phân tầng chuẩn mực và thực hiện đo kiểm thực nghiệm, đề tài *"Hệ thống phần mềm giám sát giao thông và cảnh báo va chạm thời gian thực (Radar 24GHz & Camera Sensor Fusion)"* của Nhóm 5 đã hoàn thành toàn diện 100% các mục tiêu nghiên cứu và phát triển đề ra:
1. **Nền tảng phần mềm hoàn chỉnh:** Xây dựng thành công ứng dụng Desktop hoàn chỉnh bằng Python 3.11 và PyQt6, kết hợp giao diện đồ họa vector 2D và khung camera thời gian thực.
2. **Dung hợp đa cảm biến đột phá:** Hiện thực hóa thuật toán Sensor Fusion Pin-hole 3D sang 2D và ghép cặp Greedy 1-1, gán cự ly chính xác cho Bounding Box AI.
3. **Triệt tiêu báo động giả:** Giải quyết triệt để bài toán báo động giả qua thuật toán học nền tĩnh 5s và bộ lọc trễ Hysteresis, giảm tỷ lệ FAR xuống dưới 3.2%.
4. **Hệ thống 10 Biểu đồ UML chuẩn IEEE:** Hoàn thành đầy đủ 10 biểu đồ UML chuẩn mực (2 Use Case, 2 Activity, 2 Class, 2 Sequence, 2 State) theo đúng yêu cầu Final Project của Giảng viên.
5. **Kiểm thử & Đóng gói Executable:** Vượt qua 52/52 bài kiểm thử tự động hóa PyTest, bảo mật mật khẩu PBKDF2-HMAC-SHA256 và đóng gói thành công file thực thi duy nhất `GiamSatGiaoThong.exe`.

### 6.2. Các hạn chế của mô hình hiện tại
Dưới góc nhìn khoa học khách quan, nhóm thẳng thắn chỉ ra các hạn chế của phiên bản hiện tại:
1. **Giới hạn cự ly cảm biến 24GHz:** Cảm biến HLK-LD2450 sử dụng trong đồ án có cự ly quét hiệu dụng tối đa 6 mét và góc quét 120°, phù hợp với cảnh báo điểm mù đô thị và hỗ trợ lùi xe, nhưng chưa đủ tầm quan sát cho xe chạy tốc độ cao trên đường cao tốc (> 80 km/h).
2. **Chưa tích hợp phanh khẩn cấp AEB:** Hệ thống hiện tại dừng lại ở tầng cảnh báo bằng âm thanh và hình ảnh cho người lái (Driver Advisory), chưa có cơ cấu chấp hành can thiệp phanh tự động khẩn cấp (AEB).
3. **Thị giác đêm phụ thuộc đèn chiếu:** Camera quang học thông thường vẫn phụ thuộc vào ánh sáng đèn pha xe vào ban đêm, chưa tích hợp camera hồng ngoại nhiệt chuyên dụng.

### 6.3. Các điều kiện kỹ thuật để triển khai trên phương tiện giao thông thực tế
Để chuyển giao và triển khai hệ thống trên các dòng xe ô tô thương mại ngoài thực tế, hệ thống đòi hỏi các điều kiện kỹ thuật sau:
1. **Nâng cấp cảm biến Radar 77GHz tầm xa:** Nâng cấp từ mô đun radar 24GHz tầm ngắn lên cụm cảm biến Radar 77GHz ô tô chuyên dụng (chuẩn Automotive Radar) để nâng cự ly quét từ 6m lên 150m - 200m, mở rộng khả năng cảnh báo sớm khi xe chạy tốc độ cao.
2. **Tích hợp mạng CAN-Bus và hệ thống phanh AEB:** Tích hợp bo mạch giao tiếp CAN-Bus (như CANable / PCAN) kết nối trực tiếp vào mạng điều khiển ô tô để gửi lệnh phanh khẩn cấp tự động (AEB) tới bộ chấp hành ECU phanh ABS khi người lái không có phản xạ sau 1.5 giây báo động DANGER.
3. **Bổ sung Camera hồng ngoại nhiệt ban đêm:** Bổ sung mô đun Camera hồng ngoại nhiệt (FLIR Thermal Camera) kết hợp cùng camera quang học để đảm bảo nhận diện người đi bộ và động vật băng qua đường trong đêm tối hoàn toàn không có ánh đèn đường.
4. **Phần cứng máy tính nhúng trên ô tô:** Triển khai phần mềm lên máy tính nhúng chuyên dụng trên xe (NVIDIA Jetson Orin Nano / Orin AGX) chạy hệ điều hành Linux RTOS, tích hợp nguồn điện 12V/24V chuẩn ô tô và vỏ hộp bảo vệ đạt chuẩn chống nước bụi IP67.

---

## PHẦN PHỤ LỤC: TÀI LIỆU THAM KHẢO & LIÊN KẾT MÃ NGUỒN

### 1. Tài liệu tham khảo (Định dạng chuẩn IEEE)
- [1] Ian Sommerville, *Software Engineering*, 10th Edition, Pearson Education, 2016.
- [2] IEEE Computer Society, *IEEE Recommended Practice for Software Requirements Specifications*, IEEE Std 830-1998.
- [3] Object Management Group (OMG), *Unified Modeling Language (OMG UML) Specification*, Version 2.5.1, Dec. 2017.
- [4] Hi-Link Electronics, *HLK-LD2450 24GHz Millimeter-Wave Radar Sensor Module User Manual & Communication Protocol*, 2023.
- [5] Glenn Jocher, Ayush Chaurasia, and Jing Qiu, *Ultralytics YOLOv8 Architecture and Real-Time Object Detection*, 2023.
- [6] National Highway Traffic Safety Administration (NHTSA), *Forward Collision Warning and Autonomous Emergency Braking System Performance Guidelines*, U.S. Department of Transportation, 2021.
- [7] Greg Welch and Gary Bishop, *An Introduction to the Kalman Filter*, University of North Carolina at Chapel Hill, Tech. Rep. TR 95-041.

### 2. Liên kết Kho lưu trữ Mã nguồn và Dữ liệu Thực nghiệm (GitHub Repository)
Nhằm phục vụ công tác kiểm tra, thẩm định và tái lập kết quả khoa học của Hội đồng chấm điểm, toàn bộ mã nguồn chương trình, bộ kiểm thử tự động 52 bài test, tệp cấu hình đóng gói PyInstaller, bộ dữ liệu đo kiểm thực nghiệm gốc (`traffic_radar_system.db`, `background.json`, `captures/`) và 10 tệp ảnh biểu đồ UML được lưu trữ công khai hoàn toàn trên kho lưu trữ trực tuyến:

> **LIÊN KẾT KHO MÃ NGUỒN VÀ DỮ LIỆU ĐỒ ÁN:**  
> • **Kho lưu trữ GitHub:** https://github.com/Thequydo/CNPM_Radar_Camera_Sensor_Fusion  
> • **Đường dẫn tệp thực thi cục bộ:** [GiamSatGiaoThong.exe](file:///C:/DAIHOC/CNPM_Project/GiamSatGiaoThong.exe)  
> • **Đường dẫn tệp báo cáo Word:** [Bao_Cao_Tong_Hop_Do_An_CNPM_Radar_Camera.docx](file:///C:/DAIHOC/CNPM_Project/Docs/Bao_Cao_Tong_Hop_Do_An_CNPM_Radar_Camera.docx)  
> • **Đường dẫn tệp báo cáo Markdown:** [Bao_Cao_Tong_Hop_Do_An_CNPM_Radar_Camera.md](file:///C:/DAIHOC/CNPM_Project/Docs/Bao_Cao_Tong_Hop_Do_An_CNPM_Radar_Camera.md)
