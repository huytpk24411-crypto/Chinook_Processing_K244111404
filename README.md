# Chinook Revenue Forecast

Ứng dụng phân tích doanh thu cho bài giữa kỳ **Học máy trong phân tích kinh doanh**.
Giao diện mặc định chạy trên trình duyệt bằng **HTML/CSS/JavaScript**, với máy chủ Python
cục bộ. Bản desktop PySide6 vẫn có thể chạy bằng `main.py --desktop`.
Dữ liệu nghiệp vụ chỉ đọc từ MySQL. Có dự báo tổng, track và album, lịch sử,
kiểm tra chất lượng, đánh giá theo thời gian, lưu/tải mô hình, xuất CSV/PNG và Việt–Anh.

Bản GitHub không chứa `.env`, môi trường ảo, mô hình sinh ra hoặc ảnh chụp màn hình
cục bộ. Trên máy mới, tạo `.venv`, cài requirements và sao chép `.env.example` thành
`.env` để cấu hình MySQL riêng. Các báo cáo kiểm chứng dạng JSON/CSV/text được giữ lại;
những ảnh được tài liệu nhắc tới nằm trong bản làm việc cục bộ.

## Trạng thái kiểm chứng

Rà soát ngày 23/10/2026: dữ liệu MySQL thật đã đối chiếu độc lập với API/CSV theo
từng tháng và mọi track/album; **49/49 tests Python đạt**. Nguồn/thời điểm đọc và nút
**Làm mới** hiện trên web. Xem [biên bản rà soát](docs/project_review.md).

Đã chạy bằng `.venv` trên Python 3.14.7, đọc MySQL thật thành công, khảo sát schema,
huấn luyện/đánh giá và kiểm tra dự báo đủ ba cấp ở kỳ 1/3/6 tháng. Đã kiểm tra JSON
roundtrip trên dữ liệu thật. Mật khẩu được đọc từ `.env` cục bộ đã gitignore theo yêu
cầu cấu hình của người dùng; không đưa vào HTML, JSON API, metadata hoặc log.

Database có 11 bảng, 412 hóa đơn, 2.240 dòng chi tiết, 3.503 track. Tổng hóa đơn và
chi tiết đều 2.328,60 đơn vị tiền tệ dữ liệu. 60 tháng 01/2009–12/2013. Với mặc định
bỏ hai tháng biên, lịch sử dùng 02/2009–11/2013 và test 06–11/2013: MAE tổng LR
**3,8877**, baseline tháng trước **2,0000**, baseline mean3 **2,4400**. LR không thắng
baseline trên chỉ số này. Xem `docs/model_results.md` cho các phạm vi và nhóm sparse.

`artifacts/revenue_model.json` là mô hình đã train từ MySQL thật, chỉ tải khi snapshot
và bộ lọc khớp. Ảnh `*test_fixture.png` dùng fixture riêng; ảnh `live_*.png` dùng MySQL thật.
Báo cáo khảo sát thực nằm ở `docs/data_audit.md` và được cập nhật sau mỗi lần kết nối.

## Chạy ngay trên máy hiện tại

Trong CMD:

```bat
cd /d D:\Project_Processing
.venv\Scripts\python.exe main.py
```

Hoặc nhấp đúp **`run_web.cmd`** / `run.cmd`. Trình duyệt tự mở tại:

**http://127.0.0.1:8765/**

Giữ cửa sổ terminal đang chạy. `main.py` tự đọc `.env`, tải MySQL và tải mô hình đã lưu
nếu tương thích. Không mở trực tiếp `web/static/index.html` bằng `file://`, vì trang
cần API của máy chủ Python. Không cần cài Node/npm hoặc thêm thư viện Python để chạy web.

Không cần mở trang cài đặt hoặc nhập lại mật khẩu; bản web tự dùng cấu hình MySQL đã lưu.

Chạy bản desktop cũ hoặc đổi cổng khi cần:

```bat
.venv\Scripts\python.exe main.py --desktop
.venv\Scripts\python.exe main.py --port 8766
```

Bản web dùng MySQL trên máy này và chỉ bind loopback. Đây là địa chỉ trình duyệt cục
bộ; chưa phải website public trên Internet. Xem [hướng dẫn web](docs/web_guide.md).

Trong PowerShell, dùng `\.venv\Scripts\python.exe` với dấu chấm đầu đường dẫn:

```powershell
.\.venv\Scripts\python.exe main.py
```

### PyCharm

Settings → Project → Python Interpreter → Add Interpreter → Add Local Interpreter →
Existing environment. Chọn **`D:\Project_Processing\.venv\Scripts\python.exe`**.
Mở `main.py`, đặt Working directory là thư mục project rồi Run. Interpreter project
hiện có trước khi triển khai là Python 3.14 dùng chung; không cần đổi Python hệ thống.
Ứng dụng dùng đường dẫn tương đối theo vị trí source nên có thể di chuyển project.

## Cài lại môi trường riêng

```bat
py -3.14 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip check
```

`requirements.txt` chốt các package trực tiếp đã import thực tế. `requirements.lock.txt`
chốt cả dependency của môi trường bàn giao. Không cài vào Python dùng chung.
Trên máy này, 3.14.7 tương thích các package hiện có. Python 3.13.14 cũng có sẵn nhưng
chưa có đủ sklearn/PySide6. Không cần hạ phiên bản hoặc cài Python toàn hệ thống.

Trong phiên công cụ triển khai, pip tải mạng bị chặn (`PIP_NO_INDEX`, proxy từ chối),
và ensurepip gặp ACL của thư mục tạm. `.venv` hiện tại được tạo cách ly rồi sao chép
đầy đủ 25 distribution và dependency đã cài, đúng Python 3.14 và Windows ABI, từ môi
trường có sẵn. Không bật `system-site-packages`, không sửa package dùng chung. `pip check`
đã đạt và đường dẫn import nằm trong `.venv`. Đây là cách chuẩn bị môi trường offline,
không phải lỗi tương thích của mô hình. Khi cài lại ở môi trường có Internet dùng lệnh trên.

## Kết nối MySQL tự động

Bản web không có màn hình Kết nối & cài đặt hoặc ô nhập mật khẩu. Chạy `main.py`
hay `run_web.cmd` là Python tự đọc cấu hình đã lưu và tải Chinook. Trên máy hiện tại
`.env` đã được cấu hình. Mật khẩu chỉ dùng phía Python, không đưa vào HTML/JSON/log.
Không tắt cơ chế xác thực của MySQL Server.

Trên máy khác, sao chép `.env.example` thành `.env` và cấu hình một lần. Biến môi
trường có ưu tiên cao hơn `.env`; file này đã gitignore, không đưa vào bản nộp công khai.
Khi nguồn lỗi, kiểm tra dịch vụ MySQL và cấu hình cục bộ, rồi nhấn **Thử lại**.
**Làm mới** đọc lại cấu hình và dữ liệu, giữ khoảng lịch sử đã áp dụng, xóa kết quả cũ.
Giờ đọc nguồn hiển thị ở thanh trên; di chuột để xem ngày giờ đầy đủ.

Tên bảng/cột được phát hiện từ `information_schema`, không phụ thuộc hoa/thường.
Mỗi lần tải tạo connection riêng trong worker và transaction `READ ONLY`.
Không ghi/import lại Chinook, không fallback SQLite/CSV và không có dữ liệu demo.
Bản PySide6 cũ (`--desktop`) vẫn giữ hộp thoại kết nối riêng; thay đổi giao diện này
áp dụng cho bản web mặc định.

## Quy trình sử dụng

1. Mở ứng dụng để tự tải dữ liệu, xem **Chất lượng dữ liệu**. Schema, số dòng, khóa, null, ngày và doanh thu
   được đọc/tính thật. Lỗi đối chiếu hoặc khóa chính/chi tiết sẽ chặn dự báo.
2. Chọn khoảng **tháng lịch sử** rồi **Áp dụng phạm vi**. Mặc định bỏ cả hai tháng biên
   vì độ bao phủ chưa biết. Chỉ tick gồm tháng biên nếu xác nhận đầy đủ. Nếu có tháng
   không có hóa đơn, chỉ cho điền 0 khi bạn xác nhận nguồn liên tục.
3. **Huấn luyện và đánh giá**: Linear Regression cần ≥30 tháng, ≥12 tháng tổng dương.
   Train/validation/test theo thời gian; 6 tháng validation, 6 tháng test cuối.
4. **Dự báo doanh thu**: chọn tổng/track/album, tìm bằng tên hoặc ID, chọn phương pháp,
   kỳ 1/3/6 tháng và chạy. Baseline dùng được cả khi lịch sử chưa đủ cho ML.
5. Lưu/tải mô hình JSON ở trang huấn luyện, xuất CSV/PNG ở từng trang tương ứng.

Track/album là **dự báo phân bổ** từ tổng bằng tỷ trọng lịch sử; album cộng track.
Không có mô hình riêng cho mỗi track. Ba cấp khớp trước làm tròn. Không khẳng định ML
tốt hơn baseline. Không dùng MAPE hoặc phần trăm “độ chính xác”. Đơn vị tiền tệ chưa
xác minh nên hiển thị “Đơn vị tiền tệ của dữ liệu”, không tự gắn VNĐ.

## Kiểm thử

```bat
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Unit test dùng fixture tối thiểu trong `tests/`. Ứng dụng không import thư mục đó.
Kiểm tra tổng hợp không nhân join, đối chiếu hóa đơn/chi tiết, nhóm chưa gán album,
feature không nhìn tương lai, chia thời gian cùng mốc, selection không dùng test,
đệ quy, ba cấp khớp, JSON roundtrip và xóa kết quả khi đổi đầu vào.
Test Qt mặc định dùng offscreen, không cần thao tác chuột. Ảnh test có tên phân biệt rõ.

Kiểm tra riêng bản web:

```bat
.venv\Scripts\python.exe -m unittest tests.test_web -v
node tests/web_frontend.test.mjs
```

Khi máy chủ web đang chạy, kiểm tra luồng HTTP/MySQL thật và logic JavaScript client:

```bat
.venv\Scripts\python.exe -m scripts.web_integration_check
.venv\Scripts\python.exe -m scripts.verify_data_origin
node tests/web_client.test.mjs
```

Node chỉ dùng cho kiểm thử phát triển, không cần để chạy ứng dụng. Kiểm thử client dùng
DOM tối thiểu trong tests. Đã mở/quan sát tổng quan Chrome thật; ảnh web riêng là
`artifacts/verification/web_live_overview.jpg`. Chưa xác nhận tải PNG/file-picker qua
UI. Ảnh `live_*.png` trước đó là GUI PySide6. Xem `docs/project_review.md`.
Nếu server ở 8766, truyền `--port 8766` cho hai script Python; với test Node đặt
`CHINOOK_TEST_PORT=8766` trong phiên terminal kiểm tra.

Kiểm tra tích hợp thật qua terminal (nhập mật khẩu cục bộ, được che):

```bat
.venv\Scripts\python.exe -m scripts.integration_check --ask-password
```

Lệnh này chỉ đọc MySQL, ghi báo cáo và artifacts trong project. Mặc định không tự
huấn luyện nếu khảo sát lỗi; có thể dùng `--audit-only` để chỉ khảo sát.

## Cấu trúc

```text
main.py                 Điểm chạy web mặc định, --desktop để chạy PySide6
web_app.py              Máy chủ trình duyệt, --port / --no-browser
web/application.py      Trạng thái phiên và tác vụ nền, dùng services/ml hiện có
web/server.py           HTTP cục bộ, API, chỉ phục vụ asset được cho phép
web/views.py            Chuyển dữ liệu thật sang JSON cho giao diện
web/static/             HTML, CSS, JavaScript, bản dịch, biểu đồ SVG
config/                 .env, cấu hình và lựa chọn ngôn ngữ
connectors/             Connection MySQL chỉ đọc, lỗi an toàn
repositories/           Phát hiện schema, SQL có tham số
services/               Kiểm tra dữ liệu, bộ lọc, tổng hợp dùng chung, báo cáo
ml/                     Features, chia thời gian, train, đánh giá, dự báo, JSON
ui/windows/             Các màn hình và hộp thoại kết nối
ui/widgets/             Bảng DataFrame và biểu đồ Matplotlib
ui/styles/              Theme sáng, một màu nhấn
ui/translations/        Toàn bộ chuỗi Việt–Anh
artifacts/              Mô hình, bảng kết quả, biểu đồ xuất
docs/                   Khảo sát, phương pháp, hướng dẫn và ghi chú bảo vệ
tests/                  Fixture và kiểm thử riêng
scripts/                Kiểm tra tích hợp MySQL cục bộ
```

Đọc [phương pháp](docs/methodology.md), [hướng dẫn](docs/user_guide.md),
[khảo sát](docs/data_audit.md), [ghi chú bảo vệ](docs/defense_notes.md) và
[kiểm chứng](docs/verification.md). Tài liệu môn học nguồn nằm ở gốc project lúc triển khai;
nội dung đã đọc được ghi trong `docs/implementation_plan.md`.
