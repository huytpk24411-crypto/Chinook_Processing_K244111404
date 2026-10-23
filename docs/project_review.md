# Rà soát nguồn dữ liệu và mức độ hoàn thiện — 23/10/2026

## Kết luận

Ứng dụng đọc dữ liệu thật từ MySQL Server `localhost:3306/chinook`, phiên bản
8.0.46. Workbench là công cụ quản lý/kết nối server, không phải kho dữ liệu riêng.
Đã chạy SQL độc lập và đối chiếu với service, API mà HTML sử dụng; không chỉ dựa
vào số liệu đối chiếu trong yêu cầu. Không in/lưu mật khẩu vào biên bản.

| Nội dung truy vấn thực | Kết quả |
|---|---:|
| Số bảng | 11 |
| Hóa đơn / dòng hóa đơn | 412 / 2.240 |
| Track / album | 3.503 / 347 |
| Tổng `invoice.Total` | 2.328,60 |
| Tổng `invoiceline.UnitPrice * Quantity` | 2.328,60 |
| Hóa đơn lệch trên 0,005 | 0 |
| Khoảng ngày bán | 01/01/2009–22/12/2013 |
| Tháng có hóa đơn / tháng lịch | 60 / 60 |
| Track / album chưa có doanh thu dương | 1.519 / 43 |

Không phát hiện null ở cột được sử dụng, trùng khóa chính, khóa ngoại thiếu hoặc
giá trị âm. Schema/kiểu cột/quan hệ thật được ghi trong [data_audit.md](data_audit.md).

Mặc định bỏ hai tháng biên vì chưa xác minh độ bao phủ, dùng 02/2009–11/2013:
58 tháng và 2.254,34 doanh thu. Khác biệt này do bộ lọc, không phải số giả hay mất
tiền khi join. Ngày bán cuối là 22 không chứng minh tháng thiếu. Tiền tệ chưa xác minh.

## Đường đi dữ liệu

1. `config/settings.py` đọc `.env` cục bộ; password không có trong repr/JSON API.
2. `connectors/mysql.py` mở transaction chỉ đọc, snapshot nhất quán, rollback và đóng.
3. `repositories/chinook.py` đọc schema thực, invoice tách riêng invoiceline,
   track và album; nhận diện tên bảng/cột không phân biệt hoa thường.
4. `services/data.py` kiểm tra chất lượng và tổng hợp. Track dùng giá giao dịch;
   album cộng track và giữ nhóm chưa gán nếu có. Không SUM invoice.Total sau join chi tiết.
5. `web/application.py`, `web/views.py` trả service qua HTTP; JavaScript không giữ
   bộ doanh thu mẫu. `ml/forecast.py` tạo dự báo từ lịch sử, không coi dự báo là thực tế.

Không có fallback CSV/SQLite hoặc tự sinh doanh thu, không import `tests.fixtures`
trong ứng dụng. Fixture chỉ dành cho tests. Model JSON không thay thế nguồn nghiệp vụ:
phải kết nối, khớp chữ ký dữ liệu và bộ lọc trước khi tải model.

## Sửa đổi trong lần rà soát

- Ghi thời điểm hoàn tất đọc MySQL vào snapshot, hiển thị nguồn + thời điểm trên web.
  Tính lại bộ lọc/tải model không làm đổi thời điểm đọc nguồn.
- Thêm **Đọc lại MySQL**, thực sự mở connection đọc lại và giữ bộ lọc đã áp dụng;
  tăng revision, xóa kết quả cũ. Không tự nhận là dữ liệu realtime liên tục.
- Chặn tháng rỗng, `NaT`, ngày sai và khoảng ngày đảo ngược bằng lỗi đầu vào rõ ràng.
- Khi gõ tìm kiếm, xóa chi tiết/lựa chọn cũ ngay và bỏ phản hồi đến muộn, kể cả trong
  khoảng debounce; áp dụng cho khám phá và chọn thực thể ở trang đánh giá.
- Tải model JSON kiểm tra đủ hàng test, actual khớp lịch sử MySQL, error, số hữu hạn/
  không âm, quan hệ ba cấp và metric tính lại; từ chối số liệu sửa không nhất quán.
- Chặn hai HTTP server cùng bind một cổng trên Windows. Có bản cũ ở 8765 khi rà soát;
  bản sửa được kiểm tra ở 8766, không dừng tiến trình của người dùng.
- Thêm `scripts/verify_data_origin.py` để lặp lại đối chiếu SQL độc lập.

## Kiểm chứng

- **45/45 tests Python đạt**, gồm không fallback khi kết nối lỗi, rò rỉ tương lai,
  chia thời gian, save/load, stale result, refresh nguồn và trùng cổng. Fixture riêng.
- `node tests/web_frontend.test.mjs`: đạt kiểm tra dịch, selector và SVG.
- `tests/web_client.test.mjs` gọi HTTP/MySQL thật: đạt cả tình huống tìm kiếm/chi tiết
  trả chậm. DOM tối thiểu của test không thay thế trình duyệt thật.
- `scripts.web_integration_check --port 8766`: train thật, 27 tổ hợp phạm vi/phương
  pháp/kỳ 1–3–6 tháng, CSV, model JSON, refresh và bộ lọc đều đạt.
- `scripts.verify_data_origin --port 8766`: SQL khớp service từng ô tháng–track/album;
  HTTP khớp lịch sử từng tháng và CSV khớp mọi ID, gồm chưa bán. Chênh lệch đối chiếu
  tháng lớn nhất khoảng `2,13e-14` do số thực.
- Đã mở/quan sát tổng quan Chrome thật ở cửa sổ rộng 720 và 1.440 pixel: thấy nguồn,
  thời điểm đọc và doanh thu 2.254,34. Ảnh: `artifacts/verification/web_live_overview.jpg`.
  Chưa xác nhận tải PNG/file-picker bằng chuột trên Chrome; các flow khác chủ yếu
  được kiểm bằng HTTP/client. Ảnh desktop PySide6 không phải bằng chứng web.
- `pip check` đạt. Python 3.14 vẫn phát một ResourceWarning Qt/garbage collector lúc
  thoát bộ test, không có test thất bại.

Bằng chứng có timestamp: `artifacts/verification/data_origin.json` và
`artifacts/verification/web_live_checks.json`. Số liệu trên phản ánh snapshot lúc
kiểm tra; khi nguồn thay đổi cần đọc lại và kiểm chứng lại.

## Giới hạn và phần nên bổ sung

Ba phạm vi dự báo hoạt động. Track/album là **phân bổ dự báo tổng**, không phải ML
riêng. Trung vị track chỉ có một tháng doanh thu dương, khoảng 98,93% ô track–tháng
bằng 0; cần xem positive_actual/macro, không chỉ MAE toàn bộ rất nhỏ. Phương pháp
tỷ trọng khó xử lý nhu cầu mới của track chưa bán.

MAE tổng trên 6 tháng test: LR 3,887679; tháng trước 2,000000; mean3 2,440000.
Không kết luận LR tốt nhất. Test một bước không chứng minh chất lượng đệ quy 3/6 bước.
Nếu mở rộng nghiên cứu, ưu tiên backtest nhiều mốc cho chế độ nhiều bước; vẫn giữ
test cuối độc lập, không chọn tham số bằng test.

Bản web chạy cục bộ, chưa triển khai Internet. Nên kiểm thủ công tải PNG/file-picker,
Edge và scaling trên máy nộp bài. Chưa xác minh tiền tệ, độ đầy đủ hai tháng biên,
ngày bắt đầu bán; không tự bổ sung giả định thành dữ liệu.

Tại lần rà soát này `references/` chỉ còn README, không thấy slide/ZIP ở gốc project.
Ghi chú lần triển khai trước ở `implementation_plan.md`; không thể đọc lại bản gốc
đã vắng mặt. Nên bổ sung tài liệu môn học vào `references/` cho bộ bàn giao.

## Chạy lại

Chạy `main.py` hoặc `run_web.cmd`. Nếu 8765 đang có bản cũ, dừng bản đó trong terminal
của mình rồi chạy lại; hoặc dùng cổng riêng:

```bat
cd /d D:\Project_Processing
.venv\Scripts\python.exe main.py --port 8766
```

Khi server đã kết nối:

```bat
.venv\Scripts\python.exe -m scripts.verify_data_origin --port 8766
.venv\Scripts\python.exe -m scripts.web_integration_check --port 8766
```

Script integration thay bộ lọc/model/dự báo của workspace đang kiểm tra (không ghi
MySQL), nên chạy với server kiểm tra riêng. Không cần điền mật khẩu vào source.
