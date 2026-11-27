# ĐỀ CƯƠNG ÔN TẬP VÀ NGÂN HÀNG CÂU HỎI TRẮC NGHIỆM CÔNG NGHỆ PHẦN MỀM
**Tài liệu học tập dựa trên giáo trình Software Engineering - Ian Sommerville**
**Chương 5: System Modeling (Mô hình hóa hệ thống)**
**Chương 6: Architectural Design (Thiết kế kiến trúc)**

---

# MỤC LỤC
1. [PHẦN 1: TỔNG HỢP LÝ THUYẾT TRỌNG TÂM](#phần-1-tổng-hợp-lý-thuyết-trọng-tâm)
   - [A. CHƯƠNG 5: SYSTEM MODELING (MÔ HÌNH HÓA HỆ THỐNG)](#a-chương-5-system-modeling)
     - 1. Khái niệm và các góc nhìn mô hình hóa (Perspectives)
     - 2. Mô hình ngữ cảnh (Context Models)
     - 3. Mô hình tương tác (Interaction Models: Use Case & Sequence Diagram)
     - 4. Mô hình cấu trúc (Structural Models: Class Diagram, Generalization, Aggregation)
     - 5. Mô hình hành vi (Behavioral Models: Data-driven & Event-driven / State Machine)
     - 6. Kỹ nghệ điều khiển theo mô hình (Model-Driven Engineering - MDE / MDA)
   - [B. CHƯƠNG 6: ARCHITECTURAL DESIGN (THIẾT KẾ KIẾN TRÚC)](#b-chương-6-architectural-design)
     - 1. Bản chất, vai trò và các cấp độ thiết kế kiến trúc
     - 2. Quyết định kiến trúc và các thuộc tính phi chức năng (NFRs)
     - 3. Mô hình 4+1 góc nhìn kiến trúc (Kruchten's 4+1 View Model)
     - 4. Bảng tổng hợp 5 Mẫu kiến trúc kinh điển (Architectural Patterns)
     - 5. Bộ kết nối phần mềm (Software Connectors) & 4 vai trò cốt lõi
     - 6. Kiến trúc ứng dụng phổ biến (Application Architectures: Transaction & Language Processing)
2. [PHẦN 2: BỘ NGÂN HÀNG CÂU HỎI TRẮC NGHIỆM CHUẨN THI (40 CÂU CÓ ĐÁP ÁN & GIẢI THÍCH)](#phần-2-ngân-hàng-câu-hỏi-trắc-nghiệm)
   - [Bộ 20 câu trắc nghiệm Chương 5 (System Modeling)](#bộ-20-câu-trắc-nghiệm-chương-5)
   - [Bộ 20 câu trắc nghiệm Chương 6 (Architectural Design)](#bộ-20-câu-trắc-nghiệm-chương-6)
   - [Bảng tổng hợp đáp án nhanh](#bảng-tổng-hợp-đáp-án-nhanh)

---

# PHẦN 1: TỔNG HỢP LÝ THUYẾT TRỌNG TÂM

---

## A. CHƯƠNG 5: SYSTEM MODELING

### 1. Khái niệm và Các góc nhìn mô hình hóa (Perspectives)
- **Mô hình hóa hệ thống (System Modeling)** là quá trình phát triển các mô hình trừu tượng của một hệ thống, trong đó mỗi mô hình biểu diễn một góc nhìn hoặc khía cạnh khác nhau của hệ thống đó.
- Ngôn ngữ mô hình hóa tiêu chuẩn được sử dụng rộng rãi nhất hiện nay là **UML (Unified Modeling Language)**.
- **4 góc nhìn mô hình hóa chính:**
  1. **External perspective (Góc nhìn bên ngoài):** Mô hình hóa ngữ cảnh hoặc môi trường xung quanh hệ thống (hệ thống nằm ở đâu, tương tác với thực thể ngoài nào).
  2. **Interaction perspective (Góc nhìn tương tác):** Mô hình hóa các tương tác giữa hệ thống với môi trường của nó, hoặc tương tác qua lại giữa các thành phần bên trong hệ thống.
  3. **Structural perspective (Góc nhìn cấu trúc):** Mô hình hóa tổ chức của hệ thống hoặc cấu trúc của dữ liệu mà hệ thống xử lý.
  4. **Behavioral perspective (Góc nhìn hành vi):** Mô hình hóa hành vi động của hệ thống và cách nó phản ứng trước các kích thích (stimuli) hoặc sự kiện.

- **5 loại biểu đồ UML cốt lõi:**
  - *Activity diagrams:* Thể hiện các hoạt động xử lý dữ liệu và luồng điều khiển (Data-driven).
  - *Use case diagrams:* Thể hiện tương tác giữa hệ thống và các tác nhân bên ngoài (Actors).
  - *Sequence diagrams:* Thể hiện chuỗi tương tác giữa các tác nhân và đối tượng theo thứ tự thời gian.
  - *Class diagrams:* Thể hiện cấu trúc tĩnh của các lớp đối tượng và quan hệ giữa chúng.
  - *State machine diagrams:* Thể hiện các trạng thái của hệ thống và phản ứng trước sự kiện (Event-driven).

---

### 2. Mô hình ngữ cảnh (Context Models)
- Được sử dụng để minh họa các ranh giới hoạt động của hệ thống (Operational context).
- **Ranh giới hệ thống (System Boundaries):**
  - Xác định cái gì nằm bên trong hệ thống và cái gì nằm bên ngoài hệ thống.
  - Việc xác định ranh giới không chỉ là một quyết định kỹ thuật đơn thuần mà phụ thuộc rất lớn vào **đánh giá tổ chức / xã hội (social and organizational judgment)**.
- **Context architectural diagram:** Thể hiện hệ thống đang phát triển được đặt trong mối quan hệ với các hệ thống hiện có khác (ví dụ: Hệ thống Mentcare liên kết với Hệ thống hẹn khám, Cơ sở dữ liệu bệnh nhân, Hệ thống thanh toán...).
- **Process models (Mô hình quy trình):** Bổ sung cho mô hình ngữ cảnh bằng cách sử dụng biểu đồ hoạt động (Activity diagram) để mô tả cách hệ thống được sử dụng trong các quy trình nghiệp vụ tổng thể của con người.

---

### 3. Mô hình tương tác (Interaction Models)
Mô hình hóa tương tác giúp làm rõ yêu cầu của người dùng và thiết kế luồng thông tin liên lạc.

#### 3.1. Use Case Modeling (Mô hình hóa trường hợp sử dụng)
- Ban đầu được phát triển bởi Ivar Jacobson, sau này trở thành nền tảng của UML.
- **Actor (Tác nhân):** Con người hoặc hệ thống bên ngoài tương tác với hệ thống.
- **Use Case:** Đại diện cho một tác vụ riêng biệt, mang lại giá trị trọn vẹn cho tác nhân.
- Biểu đồ Use Case thường đi kèm với **bảng mô tả dạng bảng (tabular description)** nêu rõ: Tác nhân, Mô tả, Dữ liệu đầu vào, Dữ liệu đầu ra, Luồng sự kiện chính, Luồng sự kiện nhánh / ngoại lệ.

#### 3.2. Sequence Diagrams (Biểu đồ tuần tự)
- Mô tả chi tiết sự tương tác giữa các đối tượng để thực hiện một Use Case cụ thể.
- **Các thành phần chính:**
  - Các đối tượng / tác nhân được sắp xếp theo hàng ngang ở trên cùng.
  - **Đường sinh mệnh (Lifeline):** Đường nét đứt thẳng đứng thể hiện sự tồn tại của đối tượng theo thời gian.
  - **Thanh kích hoạt (Activation box):** Hình chữ nhật hẹp trên đường sinh mệnh, biểu thị khoảng thời gian đối tượng nắm giữ quyền điều khiển.
  - **Thông điệp (Messages):** Mũi tên nằm ngang giữa các đường sinh mệnh, kèm tên phương thức và tham số.
  - **Khung tương tác (Combined fragments):** Như khung `alt` (rẽ nhánh có điều kiện if-else), `loop` (vòng lặp), `opt` (tùy chọn).

---

### 4. Mô hình cấu trúc (Structural Models)
Mô hình hóa cách hệ thống được tổ chức thành các thành phần tĩnh và mối liên kết dữ liệu.

#### 4.1. Class Diagrams (Biểu đồ lớp)
- Được dùng khi phát triển mô hình hướng đối tượng tĩnh.
- Mỗi lớp gồm 3 ngăn: Tên lớp (Class Name), Thuộc tính (Attributes), Thao tác/Phương thức (Operations).
- **Độ bội (Multiplicity):** Thể hiện số lượng thể hiện liên kết (ví dụ: `1`, `0..*`, `1..*`).

#### 4.2. Quan hệ Kế thừa / Tổng quát hóa (Generalization / Inheritance)
- Là kỹ thuật quản lý sự phức tạp thông qua việc trừu tượng hóa các đặc điểm chung lên lớp cha (Superclass).
- Các lớp con (Subclasses) kế thừa toàn bộ thuộc tính và phương thức từ lớp cha, đồng thời có thể bổ sung các đặc tính riêng.
- **Ký hiệu trong UML:** Mũi tên tam giác rỗng trỏ từ lớp con về phía lớp cha.

#### 4.3. Quan hệ Thu gom / Cấu thành (Aggregation & Composition)
- Biểu diễn mối quan hệ "part-of" (một phần của): Một đối tượng lớn được cấu thành từ nhiều đối tượng nhỏ hơn.
- **Ký hiệu trong UML:**
  - *Aggregation (Thu gom lỏng lẻo):* Hình thoi rỗng nằm ở phía lớp chứa (container). Vòng đời của lớp thành phần độc lập với lớp chứa.
  - *Composition (Hợp thành chặt chẽ):* Hình thoi đặc (tô đen). Vòng đời của lớp thành phần phụ thuộc hoàn toàn vào lớp chứa.

---

### 5. Mô hình hành vi (Behavioral Models)
Mô hình hóa hành vi động của hệ thống khi nó đang thực thi.

#### 5.1. Data-Driven Modeling (Mô hình định hướng dữ liệu)
- Tập trung vào cách dữ liệu được luân chuyển và biến đổi qua các bước xử lý liên tiếp.
- Thường được biểu diễn bằng **Activity Diagrams** (Biểu đồ hoạt động).
- Phù hợp với các hệ thống xử lý hàng loạt (batch processing systems), hệ thống xử lý đường ống dữ liệu (data pipelines).

#### 5.2. Event-Driven Modeling (Mô hình định hướng sự kiện)
- Mô hình hóa cách hệ thống phản ứng lại các sự kiện (kích thích bên ngoài hoặc bên trong).
- Hệ thống được giả định có một số lượng hữu hạn các **trạng thái (states)**. Khi có sự kiện kích thích (stimulus/event), hệ thống chuyển từ trạng thái này sang trạng thái khác (**transition**).
- Thường được biểu diễn bằng **State Machine Diagrams** (Biểu đồ trạng thái).
- **Thành phần:**
  - *State:* Trạng thái của hệ thống (ví dụ: Chờ, Đang nấu, Tạm dừng).
  - *Transition:* Cung tên thể hiện sự chuyển đổi trạng thái khi có sự kiện kích hoạt.
  - *Action:* Hành động được thực thi tại thời điểm chuyển tiếp hoặc khi đang ở trong một trạng thái.
- *Ví dụ kinh điển:* Hệ thống điều khiển lò vi sóng (Microwave Oven) với các trạng thái: Waiting, Set time, Half power, Full power, Operation, Disabled.

---

### 6. Kỹ nghệ điều khiển theo mô hình (Model-Driven Engineering - MDE / MDA)
- **Khái niệm:** MDE là một phương pháp tiếp cận phát triển phần mềm trong đó **các mô hình (models)** là sản phẩm chính của tiến trình phát triển, thay vì viết mã nguồn trực tiếp. Mã nguồn được sinh ra tự động từ các mô hình bằng các công cụ chuyển đổi (translators/code generators).
- **Model-Driven Architecture (MDA):** Là chuẩn MDE được đề xuất bởi tổ chức OMG (Object Management Group), chia thành 3 cấp độ mô hình:
  1. **CIM (Computation Independent Model):** Mô hình độc lập tính toán. Mô tả các khái niệm nghiệp vụ và miền ứng dụng mà không cần biết đến sự tồn tại của hệ thống máy tính.
  2. **PIM (Platform Independent Model):** Mô hình độc lập nền tảng. Mô tả cấu trúc và hoạt động của phần mềm mà không tham chiếu đến bất kỳ nền tảng công nghệ cụ thể nào (thường dùng UML).
  3. **PSM (Platform Specific Model):** Mô hình phụ thuộc nền tảng. Là kết quả chuyển đổi từ PIM kết hợp với các đặc thù của nền tảng đích (như Java/J2EE, Microsoft .NET, RESTful API, quan hệ CSDL).
- **Đánh giá MDE/MDA:**
  - *Ưu điểm:* Khả năng trừu tượng hóa cao, độc lập công nghệ, tự động sinh mã, dễ thích nghi khi đổi nền tảng phần cứng/hệ điều hành.
  - *Nhược điểm & Tranh cãi:* Bộ sinh mã phức tạp và tốn kém; khó debug và tối ưu hóa hiệu năng; **mâu thuẫn với tư duy phát triển Agile** (Agile đề cao việc có phần mềm chạy được thay vì dành quá nhiều thời gian xây dựng mô hình tĩnh ban đầu).

---

## B. CHƯƠNG 6: ARCHITECTURAL DESIGN

### 1. Bản chất, vai trò và các cấp độ thiết kế kiến trúc
- **Thiết kế kiến trúc (Architectural Design)** là tiến trình xác định cấu trúc tổng thể của hệ thống, bao gồm việc phân chia hệ thống thành các hệ thống con (sub-systems) và thiết lập cơ chế liên lạc, điều khiển giữa chúng.
- Đây là **cầu nối quan trọng** giữa khâu Đặc tả yêu cầu phần mềm (Requirements Engineering) và khâu Thiết kế chi tiết / Lập trình (Detailed Design & Implementation).
- **Hai cấp độ kiến trúc:**
  - *Architecture in the small (Kiến trúc vi mô):* Thiết kế kiến trúc của từng chương trình hoặc hệ thống riêng lẻ.
  - *Architecture in the large (Kiến trúc vĩ mô):* Thiết kế kiến trúc cho các hệ thống doanh nghiệp phức tạp bao gồm nhiều chương trình, máy tính và các tổ chức khác nhau.
- **3 Lợi ích cốt lõi của việc thiết kế kiến trúc rõ ràng (Explicit Architecture):**
  1. **Stakeholder communication (Giao tiếp với các bên liên quan):** Cung cấp một bức tranh toàn cảnh cấp cao dễ hiểu để thảo luận với khách hàng, nhà đầu tư và người dùng.
  2. **System analysis (Phân tích hệ thống):** Cho phép đánh giá sớm xem hệ thống có đáp ứng được các yêu cầu phi chức năng then chốt hay không.
  3. **Large-scale reuse (Tái sử dụng quy mô lớn):** Cho phép tái sử dụng các mẫu kiến trúc và thành phần ở cấp độ toàn hệ thống.

---

### 2. Quyết định kiến trúc và các thuộc tính phi chức năng (NFRs)
Thiết kế kiến trúc là quá trình đánh đổi (trade-offs) giữa các yêu cầu phi chức năng:

| Thuộc tính phi chức năng (NFR) | Chiến lược thiết kế kiến trúc tương ứng |
| :--- | :--- |
| **Performance (Hiệu năng)** | - Gom cụm các tác vụ then chốt (localize critical operations).<br>- Giảm thiểu tối đa giao tiếp nội bộ giữa các thành phần.<br>- Sử dụng các thành phần có kích thước hạt lớn (large-grain components). |
| **Security (An ninh bảo mật)** | - Sử dụng kiến trúc phân lớp (layered architecture).<br>- Đặt các tài nguyên và thông tin cốt lõi nhất ở các tầng trong cùng (innermost layers) có xác thực nghiêm ngặt. |
| **Safety (An toàn vận hành)** | - Cô lập các tính năng liên quan đến an toàn trong một số ít hệ thống con độc lập.<br>- Tránh phụ thuộc lan truyền để dễ dàng kiểm định (validation). |
| **Availability (Độ sẵn sàng)** | - Bổ sung các thành phần dự phòng (redundant components).<br>- Thiết kế cơ chế chịu lỗi và phục hồi tự động (fault tolerance). |
| **Maintainability (Khả năng bảo trì)** | - Sử dụng các thành phần độc lập, hạt nhỏ (fine-grain, loosely-coupled components).<br>- Tách biệt rõ ràng giao diện và cài đặt để dễ thay thế. |

---

### 3. Mô hình 4+1 góc nhìn kiến trúc (Kruchten's 4+1 View Model)
Philippe Kruchten đề xuất mô hình 4+1 góc nhìn để mô tả toàn diện một kiến trúc phần mềm:
1. **Logical view (Góc nhìn logic):** Thể hiện các trừu tượng hóa của hệ thống dưới dạng các lớp (classes) và đối tượng (objects).
2. **Process view (Góc nhìn tiến trình):** Thể hiện hệ thống tại thời điểm chạy (runtime), cách các tiến trình tương tác, luồng (threads), cơ chế đồng bộ và hiệu năng.
3. **Development view (Góc nhìn phát triển):** Thể hiện cách phần mềm được phân rã thành các module, gói (packages), thư viện để phân chia công việc cho lập trình viên.
4. **Physical view (Góc nhìn vật lý):** Thể hiện cách các thành phần phần mềm được phân bổ lên phần cứng và cấu hình mạng máy tính.
- **+1 (Use Cases / Scenarios):** Các kịch bản ca sử dụng được dùng làm cầu nối để kiểm chứng và chứng minh rằng 4 góc nhìn trên phối hợp nhịp nhàng với nhau.

---

### 4. Bảng tổng hợp 5 Mẫu kiến trúc kinh điển (Architectural Patterns)

| Tên mẫu kiến trúc | Mô tả nguyên lý hoạt động | Khi nào nên sử dụng? | Ưu điểm chính | Nhược điểm / Hạn chế |
| :--- | :--- | :--- | :--- | :--- |
| **MVC (Model - View - Controller)** | Tách hệ thống làm 3 phần: **Model** (dữ liệu & logic nghiệp vụ), **View** (giao diện hiển thị), **Controller** (xử lý tương tác người dùng). | Khi hệ thống có nhiều cách hiển thị dữ liệu hoặc giao diện thường xuyên thay đổi. | Cho phép dữ liệu thay đổi độc lập với giao diện; hỗ trợ nhiều giao diện cùng lúc cho một Model. | Tăng độ phức tạp mã nguồn và chi phí bảo trì khi ứng dụng có giao diện quá đơn giản. |
| **Layered Architecture (Phân tầng)** | Tổ chức thành các tầng phân cấp trừu tượng. Tầng trên chỉ gọi dịch vụ của tầng dưới liền kề. Tầng đáy là core/OS/DB. | Khi xây dựng hệ thống trên nền tảng sẵn có; hệ thống yêu cầu bảo mật đa lớp hoặc nhóm phát triển theo chuyên môn. | Dễ phát triển độc lập; có thể thay thế toàn bộ một tầng mà không ảnh hưởng tầng khác nếu giữ nguyên giao diện. | Khó phân định ranh giới tầng rõ ràng; hiệu năng giảm do dữ liệu phải trung chuyển qua nhiều tầng. |
| **Repository (Kho lưu trữ tập trung)** | Mọi dữ liệu được chia sẻ và lưu trữ tại một cơ sở dữ liệu trung tâm. Các thành phần độc lập truy cập vào kho này. | Các hệ thống quản lý dữ liệu lớn, vận hành lâu dài và nhiều công cụ cùng truy xuất (IDE, Bệnh viện). | Chia sẻ dữ liệu lớn hiệu quả; cơ chế sao lưu, phục hồi và kiểm soát an ninh dữ liệu tập trung, nhất quán. | **Điểm lỗi đơn lẻ (Single Point of Failure - SPOF)**; nguy cơ nghẽn cổ chai hiệu năng khi truy cập đồng thời; khó đổi schema. |
| **Client - Server (Khách - Chủ)** | Hệ thống phân tán gồm tập hợp các máy chủ cung cấp dịch vụ và các máy khách gửi yêu cầu qua mạng. | Khi dữ liệu và dịch vụ cần được chia sẻ cho người dùng phân tán trên diện rộng qua Internet. | Máy chủ có thể phân tán trên mạng; dễ mở rộng phần cứng server; khách hàng truy cập từ mọi nơi. | Phụ thuộc hoàn toàn vào đường truyền mạng; máy chủ dễ bị nghẽn (overload); quản lý bảo mật phân tán phức tạp. |
| **Pipe and Filter (Ống dẫn & Bộ lọc)** | Dữ liệu đầu vào chảy tuần tự qua một chuỗi các bộ lọc độc lập (Filters) thông qua các ống dẫn (Pipes). | Các hệ thống xử lý dữ liệu hàng loạt (batch), xử lý tín hiệu, trình biên dịch (Compilers). | Rất trực quan; dễ tái sử dụng bộ lọc; dễ dàng hỗ trợ tính toán song song (concurrency). | Yêu cầu định dạng dữ liệu chung giữa các pipe; độ trễ do chuyển đổi dữ liệu; **không phù hợp cho hệ thống tương tác người dùng**. |

---

### 5. Bộ kết nối phần mềm (Software Connectors) & 4 vai trò cốt lõi
- **Khái niệm:** Connector là một thực thể kiến trúc dùng để mô hình hóa và điều phối các tương tác giữa các thành phần phần mềm (Components). Nó giúp tách rời chức năng tính toán (Computation) khỏi chức năng giao tiếp (Communication).
- **Các loại Connector phổ biến:** Procedure Call (Gọi hàm), Event/Message, Pipe, Socket, Shared Memory, File.
- **4 vai trò (Roles) chính của Connector:**
  1. **Coordinator (Điều phối):** Điều khiển luồng thực thi và kích hoạt các component (ví dụ: bộ lập lịch Scheduler, cơ chế gọi hàm RPC, điều phối luồng).
  2. **Wrapper (Đóng gói):** Bao bọc thành phần để ẩn giấu chi tiết cài đặt, cung cấp giao diện chuẩn hoặc bổ sung tính năng phụ trợ (ví dụ: Logging wrapper, Security wrapper).
  3. **Adaptor (Thích ứng / Chuyển đổi):** Chuyển đổi giao diện hoặc định dạng dữ liệu giữa hai thành phần không tương thích để chúng có thể làm việc được với nhau (ví dụ: chuyển dòng byte từ Pipe thành file).
  4. **Monitor (Giám sát):** Quan sát, ghi nhật ký (log) thông điệp, đo đạc thời gian đáp ứng, kiểm tra tải và hỗ trợ cân bằng tải giữa các thành phần.

---

### 6. Kiến trúc ứng dụng phổ biến (Application Architectures)

#### 6.1. Transaction Processing Systems (Hệ thống xử lý giao dịch)
- Thiết kế để xử lý các yêu cầu của người dùng nhằm truy cập và cập nhật thông tin trong cơ sở dữ liệu.
- Đảm bảo tính toàn vẹn dữ liệu (tính chất ACID: Atomicity, Consistency, Isolation, Durability).
- *Ví dụ:* Hệ thống ATM ngân hàng, hệ thống đặt vé máy bay trực tuyến, giỏ hàng thương mại điện tử.
- *Cấu trúc luồng xử lý:* Nhận yêu cầu I/O $\rightarrow$ Xử lý logic nghiệp vụ ứng dụng $\rightarrow$ Transaction Manager $\rightarrow$ Lưu trữ Cơ sở dữ liệu.

#### 6.2. Language Processing Systems (Hệ thống xử lý ngôn ngữ)
- Tiếp nhận chuỗi ký tự tự nhiên hoặc ngôn ngữ lập trình và chuyển đổi sang một dạng biểu diễn khác (trình biên dịch Compiler, trình thông dịch Interpreter).
- Thường áp dụng kết hợp kiến trúc **Pipe and Filter** (chuỗi xử lý tuần tự) và **Repository** (Bảng ký hiệu - Symbol Table):
  1. *Lexical Analysis (Phân tích từ vựng):* Chuyển chuỗi ký tự thành các Token.
  2. *Syntactic Analysis (Phân tích cú pháp):* Xây dựng cây cú pháp (Parse Tree).
  3. *Semantic Analysis (Phân tích ngữ nghĩa):* Kiểm tra kiểu dữ liệu và tính hợp lệ.
  4. *Code Generation (Sinh mã):* Tạo mã máy hoặc mã trung gian (Bytecode).

---

# PHẦN 2: BỘ NGÂN HÀNG CÂU HỎI TRẮC NGHIỆM CHUẨN THI

---

## BỘ 20 CÂU TRẮC NGHIỆM CHƯƠNG 5 (SYSTEM MODELING)

#### Câu 1: Mục đích chính của việc xây dựng mô hình hệ thống (System Modeling) trong giai đoạn công nghệ phần mềm là gì?
A. Để trình biên dịch có thể tự động thực thi chương trình mà không cần viết mã.  
B. Giúp các kỹ sư phần mềm và các bên liên quan (stakeholders) hiểu rõ và thảo luận về hệ thống qua các biểu diễn trừu tượng.  
C. Để thay thế hoàn toàn tài liệu đặc tả yêu cầu phần mềm (SRS).  
D. Để kiểm thử tự động toàn bộ mã nguồn của hệ thống.  
> **Đáp án:** **B**  
> *Giải thích:* Mô hình hệ thống là các biểu diễn trừu tượng giúp kỹ sư và khách hàng thảo luận, làm rõ yêu cầu và hiểu về cấu trúc, hành vi của hệ thống trước khi hiện thực hóa.

#### Câu 2: Trong UML, góc nhìn nào mô tả hành vi động của hệ thống và cách hệ thống phản ứng với các kích thích (stimuli)?
A. External perspective  
B. Interaction perspective  
C. Structural perspective  
D. Behavioral perspective  
> **Đáp án:** **D**  
> *Giải thích:* Behavioral perspective (Góc nhìn hành vi) mô tả hành vi động của hệ thống khi phản ứng lại các sự kiện bên trong hoặc kích thích từ bên ngoài.

#### Câu 3: Khi xác định biên giới hệ thống (System Boundaries) trong Context Model, quyết định này phụ thuộc chủ yếu vào yếu tố nào?
A. Thuật toán tối ưu hóa phần cứng máy chủ.  
B. Đánh giá mang tính xã hội và tổ chức (Social and organizational judgment).  
C. Tốc độ truyền tải của mạng máy tính.  
D. Số lượng dòng mã của chương trình.  
> **Đáp án:** **B**  
> *Giải thích:* Ranh giới hệ thống không phải là ranh giới kỹ thuật cứng nhắc mà phụ thuộc vào chính sách, cách tổ chức công việc và sự phân định trách nhiệm của con người trong tổ chức.

#### Câu 4: Một Actor trong Use Case Diagram của UML có thể là đối tượng nào sau đây?
A. Chỉ có thể là người dùng cuối (End-user) của hệ thống.  
B. Một bảng trong cơ sở dữ liệu quan hệ.  
C. Một con người, một nhóm người hoặc một hệ thống bên ngoài tương tác với hệ thống.  
D. Một phương thức private trong một lớp.  
> **Đáp án:** **C**  
> *Giải thích:* Actor đại diện cho một vai trò của người dùng hoặc một hệ thống phần mềm/phần cứng bên ngoài có tương tác trực tiếp với hệ thống.

#### Câu 5: Trong Sequence Diagram, đường nét đứt thẳng đứng kéo dài từ trên xuống dưới biểu diễn cho thành phần nào?
A. Thông điệp đồng bộ (Synchronous message).  
B. Đường sinh mệnh của đối tượng (Lifeline).  
C. Thanh thời gian thực thi (Activation box).  
D. Điều kiện rẽ nhánh (Guard condition).  
> **Đáp án:** **B**  
> *Giải thích:* Đường nét đứt thẳng đứng gọi là Lifeline, biểu thị sự tồn tại của đối tượng đó trong suốt tiến trình tương tác theo thời gian.

#### Câu 6: Trong Sequence Diagram, khung tương tác có nhãn `alt` được sử dụng để làm gì?
A. Lặp lại một tập hợp các thông điệp nhiều lần.  
B. Thực thi các thông điệp một cách song song.  
C. Biểu thị sự lựa chọn rẽ nhánh có điều kiện (tương đương if-else).  
D. Đánh dấu một bước xử lý bị lỗi cần bỏ qua.  
> **Đáp án:** **C**  
> *Giải thích:* Khung `alt` (alternative) trong UML sequence diagram biểu thị nhiều nhánh thực thi loại trừ lẫn nhau tùy thuộc vào điều kiện (tương đương cấu trúc if-then-else).

#### Câu 7: Mối quan hệ Generalization (Tổng quát hóa / Kế thừa) trong Class Diagram được thể hiện bằng ký hiệu nào?
A. Đường nét đứt có mũi tên mở.  
B. Đường nét liền có hình thoi rỗng ở đầu.  
C. Đường nét liền có hình thoi tô đặc ở đầu.  
D. Đường nét liền có mũi tên hình tam giác rỗng trỏ về lớp cha.  
> **Đáp án:** **D**  
> *Giải thích:* Generalization trong UML được ký hiệu bằng đường nét liền kết thúc bằng một hình tam giác rỗng trỏ về lớp cha (Superclass).

#### Câu 8: Sự khác biệt cơ bản giữa Aggregation (Thu gom) và Composition (Hợp thành) trong UML là gì?
A. Aggregation là quan hệ lỏng lẻo (vòng đời độc lập), trong khi Composition là quan hệ chặt chẽ (vòng đời lớp con phụ thuộc vào lớp cha).  
B. Aggregation dùng hình thoi đặc, Composition dùng hình thoi rỗng.  
C. Aggregation chỉ áp dụng cho giao diện (Interface), Composition chỉ áp dụng cho lớp trừu tượng (Abstract class).  
D. Không có sự khác biệt, hai khái niệm này là một.  
> **Đáp án:** **A**  
> *Giải thích:* Trong Composition (hình thoi đặc), các bộ phận cấu thành không thể tồn tại độc lập nếu đối tượng chứa bị hủy. Trong Aggregation (hình thoi rỗng), các bộ phận có thể tồn tại độc lập.

#### Câu 9: Mô hình nào sau đây là đại diện tiêu biểu cho phương pháp tiếp cận định hướng dữ liệu (Data-driven modeling)?
A. State Machine Diagram  
B. Activity Diagram  
C. Class Diagram  
D. Deployment Diagram  
> **Đáp án:** **B**  
> *Giải thích:* Activity Diagram biểu diễn luồng điều khiển và quá trình biến đổi dữ liệu tuần tự qua các hoạt động (Data-driven processing).

#### Câu 10: State Machine Diagram (Biểu đồ trạng thái) phù hợp nhất để mô hình hóa loại hệ thống nào sau đây?
A. Hệ thống báo cáo tài chính hàng quý chạy ngầm.  
B. Hệ thống thời gian thực, nhúng hoặc điều khiển dựa trên sự kiện (Event-driven systems).  
C. Cơ sở dữ liệu lưu trữ hồ sơ nhân viên tĩnh.  
D. Một trang web đọc tin tức tĩnh chỉ gồm HTML.  
> **Đáp án:** **B**  
> *Giải thích:* State machine mô hình hóa các trạng thái hữu hạn và chuyển đổi trạng thái khi nhận kích thích (stimuli), rất thích hợp cho hệ thống nhúng (như lò vi sóng, thang máy, xe tự hành).

#### Câu 11: Trong ví dụ về lò vi sóng (Microwave Oven) ở giáo trình Sommerville, nếu lò đang ở trạng thái `Operation` mà người dùng bấm nút `Door open`, hệ thống sẽ chuyển về trạng thái nào?
A. Full power  
B. Half power  
C. Waiting / Disabled  
D. Cooking complete  
> **Đáp án:** **C**  
> *Giải thích:* Khi cửa mở trong lúc đang hoạt động, để đảm bảo an toàn, lò vi sóng lập tức ngắt phát sóng vi ba và chuyển sang trạng thái chờ/vô hiệu hóa (Waiting/Disabled).

#### Câu 12: Kỹ nghệ điều khiển theo mô hình (Model-Driven Engineering - MDE) xem yếu tố nào là sản phẩm phát triển chính (primary artifacts)?
A. Các dòng mã nguồn viết bằng C++ hoặc Java.  
B. Các mô hình phần mềm ở các mức trừu tượng khác nhau.  
C. Các kịch bản kiểm thử tự động (Unit tests).  
D. Biên bản họp với khách hàng.  
> **Đáp án:** **B**  
> *Giải thích:* Trong MDE, mô hình là sản phẩm cốt lõi, mã nguồn chỉ là sản phẩm phái sinh được sinh tự động từ mô hình thông qua bộ dịch.

#### Câu 13: Trong chuẩn MDA của OMG, mô hình nào mô tả nghiệp vụ và miền ứng dụng mà hoàn toàn không phụ thuộc vào công nghệ hay hệ thống máy tính?
A. PIM (Platform Independent Model)  
B. PSM (Platform Specific Model)  
C. CIM (Computation Independent Model)  
D. PDM (Platform Dependent Model)  
> **Đáp án:** **C**  
> *Giải thích:* CIM (Computation Independent Model) là mô hình độc lập tính toán, tập trung vào tri thức nghiệp vụ và môi trường hoạt động mà không quan tâm hệ thống máy tính được xây dựng ra sao.

#### Câu 14: Mô hình PIM (Platform Independent Model) trong MDA có đặc điểm gì?
A. Chứa các mã lệnh SQL và thư viện cụ thể của Microsoft .NET.  
B. Mô tả hoạt động của hệ thống mà không tham chiếu đến các chi tiết của nền tảng triển khai cụ thể.  
C. Chỉ được vẽ trên giấy và không thể chuyển đổi tự động.  
D. Phụ thuộc vào phần cứng của vi điều khiển cụ thể.  
> **Đáp án:** **B**  
> *Giải thích:* PIM mô tả cấu trúc và hoạt động của hệ thống phần mềm độc lập với công nghệ (dùng chuẩn UML), sau đó được chuyển đổi sang PSM.

#### Câu 15: Mô hình PSM (Platform Specific Model) trong MDA được tạo ra như thế nào?
A. Do người dùng cuối tự viết mã nguồn bằng tay.  
B. Được chuyển đổi từ PIM bằng cách áp dụng các quy tắc chuyển đổi tương ứng với nền tảng công nghệ đích (J2EE, .NET...).  
C. Được tạo ra trước CIM trong tiến trình phát triển.  
D. Tự động sinh ra tài liệu hướng dẫn sử dụng.  
> **Đáp án:** **B**  
> *Giải thích:* PSM là kết quả của việc kết hợp PIM với các thông tin đặc thù của một nền tảng thực thi cụ thể.

#### Câu 16: Một trong những lý do khiến MDA ít được áp dụng phổ biến trong các dự án phát triển phần mềm Agile là gì?
A. Agile yêu cầu không được dùng máy tính để mô hình hóa.  
B. Chi phí xây dựng các bộ chuyển đổi (translators) cao và Agile ưu tiên phần mềm chạy được hơn tài liệu/mô hình tĩnh toàn diện.  
C. MDA không hỗ trợ ngôn ngữ lập trình hướng đối tượng.  
D. Các mô hình MDA quá dễ hiểu nên khách hàng không cần lập trình viên.  
> **Đáp án:** **B**  
> *Giải thích:* Agile tập trung vào mã nguồn chạy được và phản ứng nhanh với thay đổi, trong khi MDA đòi hỏi đầu tư lớn để xây dựng mô hình hoàn chỉnh và công cụ sinh mã phức tạp.

#### Câu 17: Trong biểu đồ lớp UML, ký hiệu `1..*` biểu thị độ bội (multiplicity) như thế nào?
A. Không có đối tượng nào hoặc có đúng một đối tượng.  
B. Chính xác một đối tượng.  
C. Ít nhất một đối tượng và có thể có nhiều đối tượng.  
D. Không giới hạn số lượng nhưng không được có giá trị 1.  
> **Đáp án:** **C**  
> *Giải thích:* `1..*` nghĩa là từ 1 đến nhiều (ít nhất là 1 thể hiện).

#### Câu 18: Khi vẽ biểu đồ Use Case cho hệ thống quản lý bệnh nhân tâm thần Mentcare, Use Case "Xem bệnh án" có tác nhân chính là ai?
A. Bệnh nhân  
B. Bác sĩ / Nhân viên y tế (Medical Receptionist / Doctor)  
C. Người bảo trì máy chủ  
D. Trình biên dịch mã nguồn  
> **Đáp án:** **B**  
> *Giải thích:* Nhân viên y tế và bác sĩ là những người có thẩm quyền thực hiện Use Case xem thông tin và hồ sơ điều trị của bệnh nhân.

#### Câu 19: Sự khác biệt chính giữa Context Model và Interaction Model là gì?
A. Context Model chỉ quan tâm đến dữ liệu, Interaction Model chỉ quan tâm đến phần cứng.  
B. Context Model mô tả môi trường bao quanh hệ thống, Interaction Model mô tả chi tiết cách hệ thống tương tác với môi trường và giữa các thành phần bên trong.  
C. Context Model dùng biểu đồ tuần tự, Interaction Model dùng biểu đồ triển khai.  
D. Cả hai mô hình này hoàn toàn giống nhau.  
> **Đáp án:** **B**  
> *Giải thích:* Context model cho biết hệ thống đặt trong ngữ cảnh nào và ranh giới ở đâu; Interaction model đi sâu vào các bước trao đổi thông tin, thông điệp cụ thể.

#### Câu 20: Trong State Machine Diagram, một "Transition" (Chuyển trạng thái) được kích hoạt bởi yếu tố nào?
A. Một Event / Stimulus (Sự kiện hoặc kích thích bên ngoài/nội bộ).  
B. Việc tắt nguồn máy tính.  
C. Thay đổi kích thước cửa sổ phần mềm.  
D. Sự biên dịch lại mã nguồn của lập trình viên.  
> **Đáp án:** **A**  
> *Giải thích:* Trạng thái thay đổi khi và chỉ khi có một sự kiện (event) hoặc điều kiện kích hoạt (stimulus) xảy ra.

---

## BỘ 20 CÂU TRẮC NGHIỆM CHƯƠNG 6 (ARCHITECTURAL DESIGN)

#### Câu 21: Thiết kế kiến trúc (Architectural Design) đóng vai trò là cầu nối giữa hai giai đoạn nào trong quy trình phát triển phần mềm?
A. Kiểm thử phần mềm (Testing) và Bảo trì (Maintenance).  
B. Đặc tả yêu cầu phần mềm (Requirements Engineering) và Thiết kế chi tiết / Hiện thực hóa (Detailed Design & Implementation).  
C. Triển khai phần mềm và Khảo sát người dùng.  
D. Đóng gói sản phẩm và Bán hàng.  
> **Đáp án:** **B**  
> *Giải thích:* Thiết kế kiến trúc chuyển đổi các yêu cầu phần mềm thành cấu trúc tổng thể làm nền tảng cho việc thiết kế chi tiết và viết mã.

#### Câu 22: Thuật ngữ "Architecture in the large" trong giáo trình của Sommerville đề cập đến vấn đề gì?
A. Kiến trúc của một hàm tính toán có trên 1000 dòng mã.  
B. Kiến trúc của các hệ thống doanh nghiệp phức tạp bao gồm nhiều hệ thống thành phần, máy tính và tổ chức khác nhau.  
C. Dung lượng bộ nhớ RAM mà kiến trúc đó chiếm dụng.  
D. Kích thước file thiết kế đồ họa lớn hơn 1 GB.  
> **Đáp án:** **B**  
> *Giải thích:* "In the large" nói về các hệ thống cấp doanh nghiệp lớn, phân tán, liên kết giữa nhiều tổ chức; khác với "in the small" là kiến trúc một chương trình đơn lẻ.

#### Câu 23: Lợi ích nào sau đây KHÔNG PHẢI là ưu điểm chính của việc thiết kế kiến trúc rõ ràng (Explicit Architecture)?
A. Giúp giao tiếp hiệu quả với các bên liên quan (Stakeholder communication).  
B. Cho phép phân tích sớm các thuộc tính phi chức năng của hệ thống (System analysis).  
C. Tái sử dụng quy mô lớn các cấu trúc và thành phần (Large-scale reuse).  
D. Đảm bảo chương trình chạy hoàn toàn không còn bất kỳ lỗi cú pháp nào.  
> **Đáp án:** **D**  
> *Giải thích:* Thiết kế kiến trúc định hình cấu trúc cấp cao và đánh giá rủi ro/NFRs, không liên quan đến việc ngăn chặn lỗi cú pháp khi lập trình viên viết code.

#### Câu 24: Nhược điểm lớn nhất của việc biểu diễn kiến trúc bằng Sơ đồ khối (Block Diagrams) đơn giản là gì?
A. Quá khó vẽ và khó hiểu đối với khách hàng.  
B. Thiếu các thông tin ngữ nghĩa chính xác về bản chất mối quan hệ và cách thức giao tiếp giữa các thành phần.  
C. Tốn quá nhiều tài nguyên tính toán của CPU khi mở file.  
D. Không thể in ra giấy được.  
> **Đáp án:** **B**  
> *Giải thích:* Sơ đồ khối trực quan và dễ tiếp cận nhưng mang tính phi hình thức (informal), không chỉ rõ các thực thể giao tiếp với nhau bằng giao thức gì, dữ liệu truyền tải như thế nào.

#### Câu 25: Để tối ưu hóa thuộc tính Hiệu năng (Performance) của hệ thống, chiến lược thiết kế kiến trúc nào sau đây là phù hợp nhất?
A. Chia nhỏ hệ thống thành hàng ngàn thành phần vi mô và phân tán trên nhiều máy chủ khác nhau.  
B. Gom cụm các tác vụ then chốt (localize critical operations), giảm thiểu giao tiếp giữa các thành phần và dùng thành phần hạt lớn.  
C. Đưa toàn bộ dữ liệu lên một cơ sở dữ liệu dùng chung duy nhất qua mạng Internet tốc độ thấp.  
D. Bắt buộc mọi yêu cầu đều phải đi qua 10 lớp bảo mật trung gian.  
> **Đáp án:** **B**  
> *Giải thích:* Giảm giao tiếp mạng/nội bộ và gom các phép tính quan trọng lại một chỗ giúp giảm độ trễ, tối ưu hóa hiệu năng xử lý.

#### Câu 26: Theo hướng tiếp cận của Sommerville, để đáp ứng yêu cầu An ninh bảo mật (Security), mẫu kiến trúc nào là lựa chọn hàng đầu?
A. Pipe and Filter Architecture  
B. Layered Architecture (Kiến trúc phân lớp với tài nguyên quan trọng nằm ở lớp trong cùng)  
C. Client-Server Architecture không mã hóa  
D. Repository Architecture với toàn quyền truy cập mở  
> **Đáp án:** **B**  
> *Giải thích:* Kiến trúc phân lớp cho phép đặt các tài nguyên cốt lõi vào tầng sâu nhất, buộc mọi truy cập phải vượt qua các lớp xác thực và ủy quyền bên ngoài.

#### Câu 27: Khi hệ thống đòi hỏi thuộc tính Khả năng bảo trì (Maintainability) cao, kiến trúc sư nên ưu tiên điều gì?
A. Dùng các thành phần hạt mịn, độc lập, ghép nối lỏng (loosely-coupled, fine-grain components).  
B. Viết tất cả logic chương trình vào một file duy nhất để dễ tìm kiếm.  
C. Triển khai các thành phần dự phòng phần cứng đắt tiền.  
D. Đóng gói mã nguồn thành tệp nhị phân không thể giải mã.  
> **Đáp án:** **A**  
> *Giải thích:* Ghép nối lỏng và chia nhỏ thành phần giúp việc sửa đổi, thay thế hoặc nâng cấp một module không gây ảnh hưởng dây chuyền đến các module khác.

#### Câu 28: Trong mô hình 4+1 View của Philippe Kruchten, góc nhìn nào thể hiện cấu trúc mã nguồn, các gói (packages) và sự phân chia công việc cho lập trình viên?
A. Logical view  
B. Process view  
C. Development view  
D. Physical view  
> **Đáp án:** **C**  
> *Giải thích:* Development view (Góc nhìn phát triển) tập trung vào tổ chức module, thư viện và mã nguồn từ lăng kính của nhà phát triển phần mềm.

#### Câu 29: Trong mô hình Kruchten 4+1, yếu tố "+1" đại diện cho điều gì và có vai trò như thế nào?
A. Một máy chủ vật lý dự phòng.  
B. Các ca sử dụng / kịch bản (Use Cases / Scenarios) dùng để minh họa và kiểm chứng sự phối hợp của 4 góc nhìn.  
C. Một ngôn ngữ lập trình bổ sung.  
D. Một kỹ sư kiến trúc trưởng giám sát dự án.  
> **Đáp án:** **B**  
> *Giải thích:* "+1" là Use Cases hoặc Scenarios, liên kết 4 góc nhìn lại với nhau để chứng minh kiến trúc giải quyết được các bài toán thực tế của người dùng.

#### Câu 30: Thành phần "Controller" trong mẫu kiến trúc MVC có nhiệm vụ chính là gì?
A. Trực tiếp hiển thị đồ họa và nút bấm cho người dùng.  
B. Quản lý dữ liệu và các quy tắc nghiệp vụ cốt lõi của ứng dụng.  
C. Tiếp nhận các tương tác/sự kiện từ người dùng (click chuột, gõ phím), xử lý và yêu cầu Model hoặc View cập nhật tương ứng.  
D. Kết nối trực tiếp dây mạng giữa máy khách và máy chủ.  
> **Đáp án:** **C**  
> *Giải thích:* Controller tiếp nhận đầu vào của người dùng, dịch chúng thành các thao tác cập nhật trạng thái của Model hoặc chuyển đổi View hiển thị.

#### Câu 31: Mẫu kiến trúc nào phù hợp nhất khi một hệ thống phần mềm cần cung cấp nhiều giao diện khác nhau (như Web, Mobile App, Bảng điều khiển Desktop) cho cùng một nguồn dữ liệu?
A. Pipe and Filter  
B. MVC (Model - View - Controller)  
C. Monolithic Batch  
D. Master - Slave phần cứng  
> **Đáp án:** **B**  
> *Giải thích:* MVC tách rời Model (dữ liệu) khỏi View, do đó một Model có thể liên kết đồng thời với nhiều View khác nhau mà không cần sửa đổi logic cốt lõi.

#### Câu 32: Hạn chế lớn nhất của Kiến trúc phân tầng (Layered Architecture) là gì?
A. Không thể phân chia công việc cho các nhóm phát triển khác nhau.  
B. Khó phân chia ranh giới rõ ràng trong thực tế và hiệu năng có thể suy giảm do dữ liệu phải đi qua nhiều tầng trung gian.  
C. Chỉ có thể chạy được trên hệ điều hành Linux.  
D. Không thể áp dụng cho các ứng dụng web.  
> **Đáp án:** **B**  
> *Giải thích:* Việc đi qua nhiều tầng trừu tượng làm tăng chi phí truyền thông nội bộ, đồng thời đôi khi một yêu cầu cấp cao cần chọc thẳng xuống tầng dưới gây phá vỡ cấu trúc phân tầng thuần túy.

#### Câu 33: Trong Kiến trúc Kho lưu trữ tập trung (Repository Architecture), nhược điểm nguy hiểm nhất liên quan đến độ tin cậy là gì?
A. Không hỗ trợ lưu trữ dữ liệu dạng văn bản.  
B. Điểm lỗi đơn lẻ (Single Point of Failure - SPOF): nếu kho dữ liệu trung tâm gặp sự cố, toàn bộ hệ thống sẽ ngừng hoạt động.  
C. Quá dễ dàng mở rộng sang các công nghệ khác.  
D. Tốn quá ít tài nguyên lưu trữ.  
> **Đáp án:** **B**  
> *Giải thích:* Vì tất cả các hệ thống con đều phụ thuộc vào kho dữ liệu trung tâm, nếu Repository bị treo, hỏng hóc hoặc mất mạng, toàn bộ hệ thống con đều tê liệt.

#### Câu 34: Một môi trường phát triển tích hợp (IDE) như Visual Studio hoặc Eclipse, nơi các công cụ soạn thảo, biên dịch, gỡ lỗi và phân tích cú pháp cùng chia sẻ một kho thông tin chung của dự án, là ví dụ điển hình của mẫu kiến trúc nào?
A. Client - Server  
B. Pipe and Filter  
C. Repository Architecture  
D. Microservices  
> **Đáp án:** **C**  
> *Giải thích:* IDE sử dụng Repository Architecture để chia sẻ bảng ký hiệu, cây cú pháp trừu tượng (AST) và file dự án giữa các công cụ biên dịch, highlight và debugger.

#### Câu 35: Lệnh Unix sau đây: `cat access.log | grep "404" | wc -l` là minh chứng rõ nét nhất cho mẫu kiến trúc nào?
A. Layered Architecture  
B. Model - View - Controller  
C. Pipe and Filter  
D. Repository Architecture  
> **Đáp án:** **C**  
> *Giải thích:* Dữ liệu xuất ra từ lệnh trước (`cat`) làm đầu vào cho lệnh sau (`grep`), rồi lại làm đầu vào cho `wc` qua cơ chế đường ống (`|`). Đây là nguyên mẫu của Pipe and Filter.

#### Câu 36: Tại sao mẫu kiến trúc Pipe and Filter KHÔNG PHÙ HỢP cho các ứng dụng tương tác thời gian thực với người dùng (Interactive Systems)?
A. Vì nó không thể chạy trên máy tính cá nhân.  
B. Vì các bộ lọc xử lý theo luồng dữ liệu hoặc khối (batch/stream) và khó có thể duy trì trạng thái tương tác phản hồi tức thì hai chiều với người dùng.  
C. Vì nó yêu cầu quá nhiều card đồ họa đắt tiền.  
D. Vì ngôn ngữ Java không hỗ trợ Pipe and Filter.  
> **Đáp án:** **B**  
> *Giải thích:* Pipe & filter chuyển đổi dữ liệu một chiều qua các bộ lọc, không có cơ chế quản lý trạng thái phiên làm việc (session state) hoặc phản hồi các thao tác ngẫu nhiên của người dùng theo thời gian thực.

#### Câu 37: Trong thiết kế phần mềm, "Software Connector" có vai trò gì quan trọng nhất?
A. Tách rời chức năng tính toán (Computation) của các thành phần khỏi chức năng giao tiếp/điều phối (Communication).  
B. Thay thế hoàn toàn cáp mạng vật lý giữa các máy tính.  
C. Tự động viết mã lệnh thay cho lập trình viên.  
D. Làm mát các chip xử lý trên bo mạch chủ.  
> **Đáp án:** **A**  
> *Giải thích:* Software Connectors là các cầu nối trừu tượng giúp các component giao tiếp mà không cần phụ thuộc cứng vào cách thức truyền tải dữ liệu của nhau.

#### Câu 38: Một Software Connector đóng vai trò "Adaptor" khi nào?
A. Khi nó ghi nhật ký thời gian phản hồi của thông điệp để cân bằng tải.  
B. Khi nó chuyển đổi giao diện hoặc định dạng dữ liệu không tương thích giữa hai thành phần để chúng có thể kết nối được với nhau.  
C. Khi nó kích hoạt một tiến trình mới chạy ngầm.  
D. Khi nó mã hóa toàn bộ ổ cứng máy chủ.  
> **Đáp án:** **B**  
> *Giải thích:* Adaptor (bộ chuyển đổi) đóng vai trò làm cầu nối giữa hai giao diện hoặc định dạng khác biệt (ví dụ: chuyển đổi giữa XML và JSON, hoặc chuyển stream thành buffer).

#### Câu 39: Hệ thống máy ATM ngân hàng hoặc hệ thống đặt vé xem phim trực tuyến là ví dụ tiêu biểu của loại kiến trúc ứng dụng nào?
A. Language Processing System  
B. Transaction Processing System (Hệ thống xử lý giao dịch)  
C. Standalone Batch Image Renderer  
D. Single-user Text Editor  
> **Đáp án:** **B**  
> *Giải thích:* ATM và đặt vé xử lý các giao dịch cơ sở dữ liệu đồng thời từ người dùng, đòi hỏi tính toàn vẹn (ACID transactions) để tránh việc một vé bị đặt hai lần hoặc rút tiền sai lệch.

#### Câu 40: Một trình biên dịch (Compiler) hiện đại thường kết hợp hai mẫu kiến trúc nào để xử lý mã nguồn và quản lý bảng ký hiệu (Symbol Table)?
A. MVC và Client-Server  
B. Pipe and Filter (cho các pha xử lý từ vựng, cú pháp, sinh mã) và Repository (cho bảng ký hiệu dùng chung).  
C. Layered và Peer-to-Peer  
D. Microservices và Event Bus  
> **Đáp án:** **B**  
> *Giải thích:* Các pha biên dịch (Lexical -> Syntactic -> Semantic -> Code Gen) tạo thành chuỗi Pipe and Filter, trong khi Symbol Table được lưu trữ tập trung theo dạng Repository để mọi pha đều có thể đọc/ghi thông tin biến và hàm.

---

## BẢNG TỔNG HỢP ĐÁP ÁN NHANH

| Câu | Đáp án | Câu | Đáp án | Câu | Đáp án | Câu | Đáp án |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | B | **11** | C | **21** | B | **31** | B |
| **2** | D | **12** | B | **22** | B | **32** | B |
| **3** | B | **13** | C | **23** | D | **33** | B |
| **4** | C | **14** | B | **24** | B | **34** | C |
| **5** | B | **15** | B | **25** | B | **35** | C |
| **6** | C | **16** | B | **26** | B | **36** | B |
| **7** | D | **17** | C | **27** | A | **37** | A |
| **8** | A | **18** | B | **28** | C | **38** | B |
| **9** | B | **19** | B | **29** | B | **39** | B |
| **10**| B | **20** | A | **30** | C | **40** | B |

---
*Tài liệu được biên soạn và lưu trữ tự động tại:* `C:\DAIHOC\CNPM_Project\Docs\De_Cuong_On_Tap_Va_Trac_Nghiem_Sommerville_Ch05_Ch06.md`
