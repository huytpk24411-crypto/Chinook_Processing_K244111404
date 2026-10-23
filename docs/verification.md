# Biên bản kiểm chứng, 22/10/2026

## Môi trường thực

- Python chạy: 3.14.7, virtual environment `D:\Project_Processing\.venv`.
- Import NumPy 2.4.4, pandas 3.0.2, sklearn 1.9.1, PySide6 6.11.2,
  mysql-connector-python 26.7.0, Matplotlib 3.11.1 thành công.
- `pip check`: No broken requirements found. Import lấy từ `.venv/Lib/site-packages`.
- Python 3.13.14 cũng có trên máy; không cần đổi vì bộ package 3.14 đang chạy được.
- Không sửa hoặc gỡ package dùng chung, không cài Python toàn hệ thống.
- Môi trường công cụ chặn tải pip qua mạng và gặp ACL ensurepip. Đã tạo môi trường
  offline độc lập từ dependency có sẵn; chi tiết README, chốt version trong lock file.

## MySQL thật

Đã đọc `localhost:3306/chinook`, MySQL80 đang chạy. Ban đầu thử mật khẩu trống bị 1045,
sau đó dùng credentials người dùng cung cấp chỉ trong bộ nhớ và kết nối thành công.
Không lưu password. Không import lại DB hoặc chạy lệnh ghi nghiệp vụ.

| Kiểm tra | Kết quả tính thực |
|---|---:|
| Số bảng | 11 |
| invoice | 412 |
| invoiceline | 2.240 |
| track | 3.503 |
| album | 347 |
| Tổng invoice.Total | 2.328,60 |
| Tổng chi tiết UnitPrice × Quantity | 2.328,60 |
| Hóa đơn lệch >0,005 | 0 |
| Trùng khóa chính trong bảng sử dụng | 0 |
| Null trong cột sử dụng | 0 |
| Vi phạm khóa ngoại khai báo | 0 |
| Track thiếu album | 0 |
| Tháng lịch / tháng có hóa đơn | 60 / 60 |

Khoảng giao dịch 01/01/2009–22/12/2013. Không có tháng nội bộ thiếu hóa đơn. Không xác
nhận độ bao phủ hai tháng biên từ ngày giao dịch. Khảo sát đầy đủ ở data_audit.md,
bao gồm kiểu cột và quan hệ thật. Tiền tệ chưa xác minh.

## Mô hình thực và tính nhất quán

Với mặc định loại hai biên: 58 tháng 02/2009–11/2013, doanh thu 2.254,34.
Warm-up 6 tháng. Train 40 hàng (08/2009–11/2012), validation 6 (12/2012–05/2013),
test 6 (06–11/2013). Estimator test fit 46 hàng trước test; estimator triển khai fit
52 hàng khả dụng sau khi đã ghi đánh giá. Validation chọn lag1, mean3, mean6 và tỷ
trọng track toàn quá khứ. Không điều chỉnh theo test.

| Phương pháp tổng | MAE | MSE | RMSE |
|---|---:|---:|---:|
| Linear Regression | 3,887679 | 24,020521 | 4,901074 |
| Baseline tháng trước | 2,000000 | 24,000000 | 4,898979 |
| Baseline mean3 | 2,440000 | 24,580800 | 4,957903 |

ML kém baseline tháng trước trên MAE và hơi kém trên RMSE. Không giấu kết quả này.
Track LR MAE toàn catalog 0,022610, nhưng khi actual>0 là 1,036958, minh họa vì sao
không chỉ xem metric bị các ô 0 chi phối. Bảng đủ track/album và các nhóm ở model_results.md.

Đã chạy 9 lượt dự báo (3 phương pháp × 1/3/6 tháng), mỗi lượt đủ tổng/3.503 track/347
album. Tổng track và album bằng tổng với dung sai số học 1e-10. JSON save/load có dự
báo tương đương chính xác trên dữ liệu thật. Script tích hợp `scripts.integration_check`
đã chạy thành công sau khi sửa chuẩn hóa bộ lọc tháng.

## GUI PySide6 thực

Đã khởi tạo và chạy event loop Qt với platform **windows**, không chỉ kiểm tra import.
Đã kết nối dữ liệu thật qua repository trong worker và nhận kết quả qua slot UI.
Đã bấm các nút huấn luyện, dự báo tổng, track, album; tìm tên/ID; đổi ngôn ngữ; đổi
bộ lọc và xác nhận kết quả cũ bị xóa. Đã thực hiện lưu/tải JSON, CSV và PNG qua callback
giao diện. Hộp chọn đường dẫn trong lượt tự động được trả về đường dẫn test cục bộ;
không tuyên bố đã thao tác chuột vào tất cả hộp thoại hệ điều hành.

Đã xem ảnh render và sửa font Qt offscreen, trục ngày/vùng dự báo, chiều cao tóm tắt,
nhãn checkbox và bố cục tiếng Anh. Đã kiểm tra kích thước 1240×850 và 1100×720 pixel
logic trên Windows có scaling. Trang dài có thanh cuộn để truy cập bảng/nút xuất.

Các bằng chứng:

- `artifacts/verification/live_gui_checks.json`: các bước dùng MySQL và worker.
- `artifacts/verification/live_export_checks.json`: load/save, CSV/PNG và đổi ngôn ngữ.
- `artifacts/verification/live_total_vi.png`, `live_total_en.png`, `live_training_vi.png`,
  `live_track_vi.png`, `live_album_vi.png`, `live_laptop_en.png`: ảnh dữ liệu thật.
- `artifacts/verification/live_chart_export.png`: PNG xuất qua UI.
- `artifacts/verification/live_forecast_export.csv`: CSV đã đối chiếu số với bảng UI.

## Kiểm thử tự động riêng

Chạy `python -m unittest discover -s tests -v`. Fixture tối thiểu nằm trong tests;
ứng dụng không dùng fixture. Kiểm tra join không nhân doanh thu, đối chiếu hóa đơn,
null/trùng khóa, album chưa gán, tháng thiếu/biên, chuẩn hóa bộ lọc tháng, đóng cursor,
transaction readonly và che nội dung lỗi server, feature shift, chia thời gian chung,
test không chọn tham số, đệ quy không dùng thực tế tương lai, ba cấp khớp, JSON roundtrip,
ngôn ngữ không dịch tên nguồn, đổi thực thể/bộ lọc không giữ forecast cũ.

Ảnh có hậu tố `test_fixture.png` chỉ thuộc unit/GUI test fixture, tách khỏi ảnh `live_*`.
Lượt cuối của bản desktop trước khi bổ sung web đạt **28/28**, 20,799 giây, exit code 0. Bản ghi kết quả ở
`artifacts/verification/unit_test_results.txt`. Python 3.14 phát ResourceWarning của
garbage collector lúc thoát bộ test Qt (1 đối tượng không thu gom); không có test
thất bại. Phiên GUI Windows và các kiểm tra MySQL/export hoàn tất bình thường.

## Giới hạn còn lại

- Chưa có bằng chứng nguồn bao phủ trọn hai tháng biên. Mặc định bỏ biên là chính sách.
- Không có ngày track bắt đầu bán, biến quảng bá hoặc giá tương lai.
- Chỉ 6 tháng test một bước; không suy diễn thành chất lượng dự báo 6 bước.
- Tỷ trọng quá khứ khó xử lý nhu cầu mới ở track chưa bán. Đây là phân bổ, không phải ML riêng.
- Chưa kiểm thử mọi phiên bản Windows/scaling hoặc máy khác; môi trường bàn giao đã chạy.
- Sau yêu cầu cấu hình tiếp theo, credentials được người dùng cho phép lưu cục bộ
  trong `.env` đã gitignore để tự kết nối; không có trong mã, metadata hoặc log.
  Không tự tạo kết nối bằng password trong tài liệu mẫu ở mã ứng dụng/script bàn giao.

## Bản web bổ sung

`main.py` hiện mặc định mở HTML/CSS qua máy chủ Python cục bộ; `--desktop` giữ PySide6.
Kiểm thử HTTP/JavaScript và giới hạn browser được ghi riêng trong `web_guide.md` và
`artifacts/verification/web_live_checks.json`. Các ảnh `live_*.png` trong biên bản này
chỉ kiểm chứng PySide6, không kiểm chứng giao diện web.
Lượt cũ sau khi thêm web đạt **38/38**; xem `web_test_results.txt`.
Rà soát 23/10/2026 đạt **45/45**. SQL độc lập khớp service/API từng tháng và
track/album; Chrome tổng quan đã quan sát thực. Xem `project_review.md` và
`artifacts/verification/data_origin.json` cho kết quả mới, phạm vi GUI và phần chưa kiểm chứng.
