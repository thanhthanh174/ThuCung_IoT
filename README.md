# Smart Pet Station – Trạm chăm sóc thú cưng thông minh (IoT)

Đồ án cuối kỳ học phần **Thương mại điện tử** – Hướng 2: Thiết kế sản phẩm IoT (không cần mua thiết bị).

> Hệ thống gồm thiết bị cho thú cưng ăn (mô phỏng bằng phần mềm), máy chủ API và ứng dụng web để chủ nuôi theo dõi, đặt lịch và cho ăn từ xa.

## 1. Bài toán và người dùng

- **Vấn đề:** người nuôi thú cưng đi làm/đi xa khó cho ăn đúng giờ, không biết thức ăn và nước còn bao nhiêu.
- **Người dùng mục tiêu:** [điền: ví dụ người nuôi chó mèo ở đô thị, thường xuyên vắng nhà]
- **Giá trị mang lại:** cho ăn theo lịch hoặc từ xa, theo dõi mức thức ăn/nước, nhận cảnh báo khi sắp hết hoặc thiết bị mất kết nối.
- **Mô hình bán / giá dự kiến:** xem báo cáo (mục phân tích khách hàng, chi phí).

## 2. Kiến trúc

```
 ┌──────────────┐   HTTP + JWT    ┌────────────────────┐   SQL    ┌────────────┐
 │  Web (HTML/  │ ──────────────► │  Backend FastAPI   │ ───────► │ PostgreSQL │
 │  JS) :5500   │ ◄────────────── │  :8000             │ ◄─────── │            │
 └──────────────┘                 │  + APScheduler     │          └────────────┘
                                  └─────────▲──────────┘
                                            │ HTTP polling
                                            │ + header X-Khoa-Thiet-Bi
                                  ┌─────────┴──────────┐
                                  │ Thiết bị IoT (mô   │
                                  │ phỏng, Python)     │
                                  └────────────────────┘
```

Luồng chính (cho ăn thủ công):
1. Chủ nuôi bấm "Cho ăn" trên web → backend tạo lệnh trạng thái `CHO_XU_LY`.
2. Thiết bị hỏi lệnh định kỳ (đồng thời là nhịp tim báo còn sống).
3. Thiết bị nhả thức ăn (mô phỏng motor) → báo `hoan-thanh` hoặc `that-bai`.
4. Backend trừ lượng thức ăn, ghi lịch sử, sinh cảnh báo nếu thức ăn thấp.

Lệnh không được xử lý sau 30 giây sẽ chuyển sang `HET_HAN`. Thiết bị im lặng quá 30 giây bị đánh dấu `NGAT_KET_NOI` và sinh cảnh báo.

## 3. Chức năng

- Đăng ký, đăng nhập (JWT), mỗi người chỉ thấy dữ liệu của mình.
- Quản lý hồ sơ thú cưng (thêm, sửa, xóa) và thiết bị.
- Cho ăn ngay từ xa; đặt lịch cho ăn tự động theo giờ `HH:MM`.
- Lịch sử cho ăn; dữ liệu cảm biến (mức thức ăn, mức nước).
- Cảnh báo: thức ăn thấp, hết thức ăn, nước thấp, mất kết nối (không tạo trùng, tự đóng khi hết vấn đề).

## 4. Công nghệ

| Thành phần | Công nghệ |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy, APScheduler |
| CSDL | PostgreSQL |
| Xác thực | bcrypt, JWT (PyJWT), khóa HMAC riêng cho từng thiết bị |
| Frontend | HTML, CSS, JavaScript thuần |
| Thiết bị | Script Python mô phỏng cảm biến và motor |

## 5. Cấu trúc thư mục

```
ThuCung_IoT/
├── backend/            # API, mô hình dữ liệu, bảo mật, cảnh báo, lịch tự động
├── frontend/           # Giao diện web (index.html, app.js, style.css)
├── iot/                # Thiết bị mô phỏng (thiet_bi.py)
├── image/              # Ảnh thú cưng
├── chay_he_thong.bat   # Chạy cả 3 thành phần (Windows)
├── requirements.txt
└── .env.example
```

## 6. Cài đặt

Yêu cầu: Python 3.11+, PostgreSQL.

```bash
# 1. Tạo môi trường ảo và cài thư viện
python -m venv venv
venv\Scripts\activate            # Windows
pip install -r requirements.txt

# 2. Tạo database trong PostgreSQL (tên mặc định: ThuCungIoT_DB)

# 3. Tạo file cấu hình
copy .env.example .env           # rồi điền giá trị thật
```

Sinh khóa bí mật (chạy 2 lần, dùng cho `KHOA_BI_MAT` và `KHOA_GOC_THIET_BI`):

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Bảng dữ liệu được tạo tự động khi backend khởi động lần đầu.

**Khóa cho thiết bị:** sau khi điền `.env`, chạy lệnh dưới (từ thư mục gốc) rồi dán kết quả vào `iot/.env` với tên `KHOA_THIET_BI`:

```bash
python -m backend.in_khoa_thiet_bi 1
```

## 7. Chạy hệ thống

**Cách nhanh (Windows):** chạy `chay_he_thong.bat`, sẽ mở 3 cửa sổ (backend, giao diện, thiết bị) và trình duyệt.

**Chạy thủ công** (3 terminal, đều từ thư mục gốc, đã kích hoạt venv):

```bash
uvicorn backend.main:app --reload          # API: http://127.0.0.1:8000  (tài liệu: /docs)
cd frontend && python -m http.server 5500  # Web: http://127.0.0.1:5500
python iot/thiet_bi.py                     # Thiết bị mô phỏng
```

## 8. Kịch bản demo

1. Mở web, đăng ký rồi đăng nhập.
2. Tạo thiết bị đầu tiên qua `POST /api/thiet-bi` tại http://127.0.0.1:8000/docs (bấm Authorize, dán token đăng nhập). Thiết bị mô phỏng đang dùng `ma_thiet_bi = 1`.
3. Thêm thú cưng trên web.
4. Bấm **Cho ăn**: terminal thiết bị in "đang cho ăn", web cập nhật mức thức ăn và lịch sử.
5. Dùng menu của thiết bị mô phỏng để giảm mức thức ăn/nước hoặc ngắt kết nối → web hiện cảnh báo (chuông 🔔).
6. Thêm lịch cho ăn vào phút kế tiếp để xem cho ăn tự động.

## 9. API chính

Tài liệu đầy đủ, thử trực tiếp: `http://127.0.0.1:8000/docs`.

| Nhóm | Endpoint | Xác thực |
|---|---|---|
| Tài khoản | `POST /api/dang-ky`, `POST /api/dang-nhap`, `GET /api/toi` | – / JWT |
| Thú cưng | `/api/thu-cung` (GET, POST, PUT, DELETE) | JWT |
| Thiết bị | `/api/thiet-bi` (GET, POST, PUT, DELETE) | JWT |
| Lịch cho ăn | `/api/lich-cho-an` (CRUD) | JWT |
| Cho ăn ngay | `POST /api/cho-an-ngay` | JWT |
| Lịch sử, dữ liệu, cảnh báo | `/api/lich-su-cho-an`, `/api/du-lieu-thiet-bi`, `/api/canh-bao` | JWT |
| Dành cho thiết bị | `GET /api/lenh-cho-an/{ma_thiet_bi}`, `PUT /api/lenh-cho-an/{id}/hoan-thanh`, `PUT .../that-bai`, `POST /api/du-lieu-thiet-bi`, `GET /api/iot/thiet-bi/{id}` | Header `X-Khoa-Thiet-Bi` |

## 10. Bảo mật (tóm tắt)

- Mật khẩu băm bằng bcrypt; JWT hết hạn sau 60 phút.
- Mọi truy vấn dữ liệu đều lọc theo chủ sở hữu (chống truy cập chéo tài khoản).
- Thiết bị xác thực bằng khóa HMAC riêng, so sánh hằng thời gian; khóa gốc nằm ở server.
- CORS chỉ cho phép nguồn khai báo trong `.env`; frontend escape dữ liệu trước khi hiển thị.
- Threat model và các test case bảo mật: xem thư mục tests/, chạy bằng python -m pytest tests -v.

**Lưu ý:** không đưa file `.env` lên Git (đã có trong `.gitignore`).

## 11. Hạn chế và hướng phát triển

- Thiết bị đang mô phỏng bằng phần mềm; bản thật dùng vi điều khiển, cảm biến khối lượng/mực nước và động cơ.
- Giao tiếp đang dùng HTTP polling; có thể chuyển sang MQTT để giảm độ trễ.
- Chưa có giới hạn số lần đăng nhập sai và chưa dùng HTTPS (cần khi triển khai thật).

## 12. Thành viên và phân công

| Thành viên | MSSV | 
|---|---|
| Đoàn Ngọc Phương Thanh | 1250080174 | 
| Nguyễn Thị Kim Thi | 1250080181 | 
| Nhan Anh Thư | 1250080190 |

Giảng viên: ThS. Từ Thanh Trí + ThS. Hà Châu Hoàng – Học phần Thương mại điện tử.
