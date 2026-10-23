# Giao diện web HTML/CSS

## Chạy

Trong PyCharm chạy `main.py` bằng `.venv/Scripts/python.exe`, hoặc nhấp đúp
`D:\Project_Processing\run_web.cmd`. Trình duyệt tự mở **http://127.0.0.1:8765/**.
Giữ terminal mở; Ctrl+C để dừng. Nếu cổng đang dùng, mở tab vào server hiện có hoặc
chạy `main.py --port 8766`. `--no-browser` chạy server mà không tự mở tab.
`main.py --desktop` giữ lại phiên bản PySide6.

Trang không chạy độc lập bằng cách nhấp đúp `index.html`: nó cần API Python để đọc
MySQL và gọi mô hình. Không cần npm, CDN hoặc thư viện web Python bổ sung. Tất cả
HTML/CSS/JavaScript được phục vụ từ project.

## Thiết kế và bố cục

- Sidebar gồm Tổng quan, Khám phá, Dự báo, Mô hình, Chất lượng và Phương pháp;
  dưới cùng là Tiếng Việt/English. Không có trang kết nối hoặc ô nhập mật khẩu.
- Bộ lọc tháng dùng chung trên các trang phân tích, tùy chọn tháng biên và tháng
  trống nằm trong phần mở rộng. Khoảng tháng thực sự sử dụng hiện riêng ở tổng quan.
- Tổng quan dùng một dải 3 số liệu, biểu đồ tháng lớn, xếp hạng 5 track/album và bảng
  đối chiếu cùng phạm vi. Không có số liệu mẫu khi nguồn lỗi.
- Dự báo theo 3 bước: phạm vi → phương pháp → kỳ dự báo. Track/album tìm bằng tên
  hoặc ID, chọn rõ thực thể trước khi chạy. Tên nguồn không dịch.
- Khám phá có tìm kiếm, phân trang, doanh thu và số tháng dương, chọn một dòng để xem
  lịch sử hoặc chuyển thực thể đó sang trang dự báo. Danh mục giữ cả thực thể chưa bán.
- Đánh giá trình bày 3 phương pháp trên cùng hàng, chọn nhóm all/positive/seen/macro,
  có khoảng train/validation/test, feature và bảng actual/predicted/error.
- Chất lượng kiểm tra toàn nguồn, không để bộ lọc tháng che lỗi dữ liệu gốc. Schema
  và khóa ngoại nằm trong phần thu gọn.
- Trang Phương pháp giữ giả định và giới hạn; bỏ nhãn MIDTERM, khẩu hiệu và nội dung
  giới thiệu lặp lại trên màn hình EDA.

Theme nền xám trung tính, bảng trắng và màu nhấn xanh lam, typography Segoe UI.
Sidebar thu thành menu ở 900 px; các cột xếp dọc và bảng cuộn
ngang. Biểu đồ tự điều chỉnh viewBox/số nhãn theo chiều rộng, không thu chữ xuống
quá nhỏ bằng việc co một canvas desktop cố định.

## Dữ liệu và mô hình

Máy chủ Python tự đọc `.env`, kết nối MySQL read-only và chạy khảo sát. Sau đó áp
dụng `services.data.Filters` và `build_data` giống bản desktop. Không viết lại công
thức doanh thu ở JavaScript. Mô hình tương thích được tải từ
`artifacts/web_revenue_model.json` rồi `artifacts/revenue_model.json`. Không khớp thì
thông báo và yêu cầu huấn luyện/tải JSON phù hợp, không gán nhãn ML cho baseline.

Thanh trên hiển thị database và giờ cập nhật; nguồn đầy đủ ở trang Chất lượng,
thời điểm đầy đủ ở tooltip giờ cập nhật. Đổi bộ lọc chỉ tính lại snapshot, không đọc
DB mới hoặc đổi thời điểm này. Nút **Làm mới** lấy snapshot mới, giữ bộ lọc đã áp dụng,
xóa kết quả cũ; model chỉ được tải lại khi dữ liệu/bộ lọc tương thích.

Nút Huấn luyện dùng chính `ml.forecast.train`, ghi báo cáo test và mô hình web. Test
không dùng để chỉnh lại tham số. Track/album vẫn là phân bổ từ tổng theo tỷ trọng
quá khứ và cộng track lên album. Dự báo 3/6 tháng là đệ quy. Không có ML riêng từng
track, không bịa độ chính xác hoặc khoảng tin cậy.

Truy vấn, train, forecast và tải mô hình chạy trên một worker nền. HTTP vẫn trả trạng
thái để JavaScript cập nhật tiến trình. Mỗi lần đọc DB tạo connection trong worker
riêng, đóng sau transaction. Các tab cùng một server dùng chung một workspace và bộ
lọc; đây không phải ứng dụng nhiều tài khoản.

Đổi bộ lọc ẩn kết quả cũ ngay, yêu cầu Áp dụng. Server tăng revision và xóa model/
forecast. Đổi thực thể, phương pháp hoặc horizon xóa forecast client; request_id và
revision ngăn nhận nhầm kết quả cũ. Đổi ngôn ngữ giữ dữ liệu và chỉ đổi trình bày.

## Kết nối và file xuất

Ứng dụng luôn thử kết nối tự động khi chạy `main.py`, lấy cấu hình từ `.env` hoặc
biến môi trường. Mật khẩu chỉ ở phía Python, không trả xuống trình duyệt. Không có
form kết nối. Nút Làm mới/Thử lại đọc lại cấu hình đã lưu; biến môi trường có độ ưu
tiên cao hơn `.env`. Nếu nguồn lỗi, thông báo và thử lại, không tạo dữ liệu thay thế.
API không log body/config. Không tắt xác thực MySQL hoặc ghi mật khẩu vào source.

Nút Xuất dữ liệu tải CSV đúng trang. CSV UTF-8 BOM, số giữ nguyên giá trị, không
chuyển tiền tệ. Lưu JSON tải đầy đủ estimator state, feature, metadata và đánh giá;
Tải JSON kiểm tra tương thích trước khi sử dụng. PNG tạo từ biểu đồ SVG ở trình duyệt.

Server chỉ bind `127.0.0.1`, phục vụ allowlist asset; không cho tải `.env`, source hoặc
file bất kỳ trong project. POST kiểm tra Host, Origin và token của trang. Không có
đường truyền credentials đến cloud. Chưa triển khai Internet: một dịch vụ hosted
không thể dùng `localhost` để truy cập MySQL trên máy Windows này.

## Kiểm chứng bản web

Đã chạy:

```text
python -m unittest tests.test_web -v
node tests/web_frontend.test.mjs
python -m scripts.web_integration_check
node tests/web_client.test.mjs
```

HTTP integration đọc MySQL thật, train thật, kiểm tra đủ 27 tổ hợp (3 phạm vi ×
3 phương pháp × 1/3/6 tháng), đối chiếu ba cấp, track chưa bán, CSV, model JSON
download/upload, revision và request_id. Kết quả trong
`artifacts/verification/web_live_checks.json`.

Kiểm thử JavaScript xác nhận đầy đủ bản dịch, ID/selector, định dạng số/tháng, hình
học SVG; client chạy với DOM tối thiểu của test và gọi HTTP thật để kiểm tra bootstrap,
dự báo, đổi horizon, ngôn ngữ, đánh giá và lọc. Đây là kiểm thử logic, **không phải
chụp hoặc bấm trong trình duyệt thật**.

Ngày 23/10/2026 đã mở/quan sát tổng quan trên Chrome thật, ở cửa sổ 720 và 1.440 pixel.
Ảnh web riêng: `artifacts/verification/web_live_overview.jpg`. Chưa xác nhận tải PNG/
file-picker bằng chuột hoặc mọi màn hình/scaling/Edge. Không dùng ảnh PySide6 làm
bằng chứng web. Xem `project_review.md`; phương pháp vẫn như `methodology.md`.

Lượt kiểm thử Python toàn dự án sau cập nhật giao diện đạt **49/49**, gồm kiểm tra bổ sung về
đầu vào, nguồn/refresh, lỗi kết nối, model JSON và trùng cổng. Python 3.14 vẫn phát một ResourceWarning của garbage
collector khi thoát bộ test Qt như đã ghi trong biên bản desktop; không có test thất bại.
