# Phương pháp dự báo

## Mục tiêu và dữ liệu

Dùng thông tin đã biết đến hết tháng t để dự báo doanh thu t+1. Mặc định một tháng,
mở rộng 3/6 tháng bằng đệ quy. Thống kê lịch sử ở trang tổng quan không phải dự báo.

Tổng thực tế = SUM(invoice.Total), không nhân qua join. Track thực tế = tổng
invoiceline.UnitPrice × Quantity, join invoice chỉ để lấy InvoiceDate. Album là tổng
doanh thu track qua AlbumId, tên lấy album.Title. Không dùng track.UnitPrice. Quan hệ
invoice–line–track là nhiều-một được xác thực trước tổng hợp. Album null hoặc không
tồn tại được đưa vào nhóm chưa gán album. Catalog giữ cả track/album chưa bán.

Mọi màn hình dùng `RevenueData` từ cùng snapshot và `Filters`. Khoảng lọc là lịch sử,
không phải khoảng dự báo. Mặc định loại hai tháng biên toàn nguồn vì chưa có bằng chứng
độ bao phủ. Tháng cuối dự báo nối ngay sau tháng cuối **thực sự được dùng**; nếu bỏ
tháng biên, tháng đó là kỳ chưa dùng trong lịch sử, không gọi đây là tương lai sau toàn
database. Có thể xác nhận biên đầy đủ để đưa vào lịch sử và dự báo sau tháng cuối database.
Không quyết định độ đầy đủ dựa riêng vào ngày bán cuối.

Tháng hoàn toàn không có hóa đơn có thể là thiếu nguồn. Chặn tổng hợp nếu chưa xác
nhận nguồn liên tục, rồi mới điền 0. Trong các tháng được chấp nhận, ô track/album
không phát sinh được điền 0 để đối chiếu tổng. Đây là doanh thu **ghi nhận**, không
phải xác nhận hàng có sẵn. Database không cho biết ngày ra mắt track.

Catalog là snapshot hiện tại, không có lịch sử thêm/xóa danh mục theo tháng. Khi đánh
giá toàn catalog, vẫn giữ track/album chưa bán để không âm thầm loại thực thể; số lượng
ô 0 tăng vì vậy phải đọc thêm nhóm đã từng bán và actual>0. Catalog không được đưa
vào feature hồi quy và không lấy doanh thu tương lai để xác định tỷ trọng.

## Mô hình tổng và feature

Linear Regression (OLS) của scikit-learn, có intercept. Một hàng train ứng với một
tháng mục tiêu m:

| Feature | Định nghĩa, chỉ dùng quá khứ |
|---|---|
| lag1 | y[m−1] |
| mean3 | trung bình y[m−3], y[m−2], y[m−1] |
| mean6 | trung bình y[m−6] … y[m−1] |
| month_sin | sin(2π × tháng(m)/12), biết trước |
| month_cos | cos(2π × tháng(m)/12), biết trước |

Hai tập feature cố định trước test: `[lag1, mean3, mean6]` và tập đó cộng sin/cos tháng.
`shift(1)` trước `rolling`, bỏ 6 tháng warm-up. Không đưa lượng bán, số hóa đơn hay
doanh thu của tháng mục tiêu vào X. Không dùng ID số làm biến liên tục. Không thêm
xu hướng tuyến tính vì chưa có cơ sở thực nghiệm trong dữ liệu thật.

Cần ít nhất 30 tháng lịch được chấp nhận, trong đó ≥12 tháng tổng doanh thu dương.
Với 30 tháng, sau warm-up còn 24 mẫu: 12 train, 6 validation, 6 test. Đây là ngưỡng
tối thiểu minh bạch cho bài sinh viên, không bảo đảm mô hình tốt. Không đủ điều kiện:
hiển thị lý do và cho người dùng chọn baseline, không tự gọi baseline là ML.

## Train / validation / test

Chia theo tháng tăng dần. 6 tháng cuối là test, 6 tháng trước test là validation,
các hàng khả dụng trước đó là train. Không xáo trộn. Chọn tập feature bằng MAE trên
validation, hòa thì ưu tiên tập gọn được liệt kê trước. Sau chọn, fit lại trên
train+validation, **cố định estimator này để đánh giá test**.

Test là dự đoán một bước: khi dự báo tháng m, được biết doanh thu thực tế đến m−1,
kể cả nếu m−1 thuộc test. Điều này mô phỏng vận hành cập nhật doanh thu hàng tháng,
không phải forecast 6 tháng từ mốc đầu test. Không refit estimator trong test.

Sau khi ghi báo cáo test, fit cấu hình đã chọn trên toàn bộ lịch sử khả dụng cho
triển khai. Metadata phân biệt `frozen_fit` và `deployment_fit`. Test không dùng để
chọn feature/cửa sổ. Không thay đổi cấu hình vì thấy metric test kém. Kết quả test là
của estimator trước test, không phải kết quả in-sample của estimator triển khai.

## Track, album và tính nhất quán

Phương án dùng **dự báo phân bổ**, không phải mô hình riêng từng track/album. Khảo sát
MySQL thật trên toàn 60 tháng cho thấy 1.519/3.503 track chưa có doanh thu dương,
trung vị track có 1 tháng dương và 98,934% ô track-tháng bằng 0. Album có 43/347 chưa
bán, trung vị 4 tháng dương và 94,721% ô album-tháng bằng 0. Vì lịch sử thực thể rất
thưa, không ép mô hình riêng cho từng thực thể. Phân bổ bảo đảm ba cấp khớp nhưng
không tự bảo đảm dự báo tốt, cần đọc kết quả test.

Tại mốc dự báo t, với cửa sổ W thuộc {6, 12, toàn bộ quá khứ}:

```text
w_track(i,t) = doanh thu track i trong W tháng quá khứ / tổng doanh thu track trong W
forecast_track(i,t+1) = max(0, forecast_total(t+1)) × w_track(i,t)
forecast_album(a,t+1) = sum forecast_track(i,t+1) với track i thuộc album a
```

Nếu W không có doanh thu, dùng toàn quá khứ. Nếu toàn quá khứ cũng 0, baseline tổng
và hồi quy trên mục tiêu 0 cho 0; quy tắc phân bổ kỹ thuật là trọng số đều trong catalog.
Không diễn giải trọng số đó thành nhu cầu học được. Khi có doanh thu ở track khác,
track chưa từng bán có tỷ trọng 0 và vẫn chọn được. Album chưa bán vẫn hiện trong catalog.

Chọn W bằng MAE validation trên những track đã có doanh thu dương **trước từng mốc**,
dùng dự báo tổng baseline mean3 chung cho mọi W để tách việc chọn tỷ trọng khỏi feature.
So sánh cùng tháng, cùng tập track tại mỗi mốc; mọi tham số chọn trước test. Đây là
tiêu chí trọng số ngang nhau cho các ô đủ điều kiện, không tối ưu riêng album. Ghi rõ
giới hạn: album có thể hưởng lợi từ cửa sổ khác; track mới bán và biến động danh mục
khó dự báo bằng tỷ trọng lịch sử.

Tỷ trọng thay đổi theo lịch sử đã biết tại từng mốc test. Không dùng tổng năm tương lai
để chia ngược về tháng trước. Album luôn cộng track, gồm nhóm chưa gán. Tổng ba cấp
bằng nhau trước làm tròn vì SUM(weights)=1. Làm tròn từng dòng có thể lệch số hiển thị;
CSV giữ độ chính xác float đầy đủ. Đối chiếu thực tế dùng invoice/line sai lệch ≤0,005
**từng hóa đơn**, và tổng theo tháng ≤0,005, không dùng dung sai tỷ lệ rộng.

Đây là cách kiểm soát nhất quán đơn giản, không phải bằng chứng ML riêng cho từng track.
Hạn chế lớn: khó dự báo doanh thu mới của track chưa bán, tỷ trọng có thể lỗi thời,
không có biến quảng bá/giá tương lai/ngày phát hành. Cần xem test thay vì khẳng định
phương án phân bổ luôn tốt.

## Baseline và đánh giá

Baseline tháng trước lấy doanh thu tháng t. Baseline trung bình gần nhất lấy 3 tháng
trước (hoặc số tháng thực có nếu lịch sử ngắn). Track baseline tính trực tiếp trên
lịch sử track, album cộng track nên tổng baseline ba cấp cũng khớp. Trong test:

- Tổng: LR so với hai baseline tổng.
- Track: phân bổ tổng LR so với baseline track trực tiếp.
- Album: cộng track phân bổ so với cộng track baseline trực tiếp.

Cả ba phương pháp có cùng hàng thực thể/tháng và cùng cutoff. Không khẳng định LR
phải thắng. Người dùng chọn rõ phương pháp thực sự muốn sử dụng. Giao diện giữ nhãn
“Baseline” nếu chọn baseline, cả khi đã huấn luyện LR.

MAE = mean(abs(predicted − actual)). MSE = mean(error²). RMSE = sqrt(MSE). MAE và RMSE
cùng đơn vị tiền tệ dữ liệu, MSE đơn vị bình phương. Không gọi chúng là phần trăm chính xác.
Không dùng MAPE vì thực tế có thể 0. Không bịa khoảng tin cậy.

Mỗi phạm vi báo cáo các nhóm:

1. `all`: mọi ô test, gồm 0.
2. `positive_actual`: chỉ thực tế dương, kèm n, tránh ô 0 che chất lượng khi phát sinh bán.
3. `seen_before`: thực thể từng có doanh thu trước mốc dự đoán, không dùng tương lai
   để xét đủ lịch sử.
4. `macro_seen_MAE`: tính MAE từng thực thể trên các hàng seen_before, rồi trung bình
   ngang nhau giữa thực thể. Chỉ định nghĩa MAE ở hàng này, để trống MSE/RMSE.

`positive_actual` là phân nhóm **sau dự đoán để chẩn đoán**, không dùng chọn thực thể
để dự báo hoặc feature. Các nhóm này không thay thế báo cáo toàn catalog.

## Dự báo 3/6 tháng

Đây là forecast đệ quy từ một mốc cố định, khác test một bước. LR dùng chính tổng dự
báo ở các bước trước để tạo lag và rolling cho bước sau. Không đưa doanh thu tương lai
thực vào lịch sử. Tỷ trọng track được đóng băng tại mốc đầu cho toàn horizon; không
“cập nhật” bằng giao dịch thật tương lai. Baseline cũng đệ quy trên dự báo của chính nó.
Sai số có thể tích lũy. Metric test một bước không chứng minh metric 3/6 bước tốt tương tự.

## Lưu/tải và metadata

JSON lưu hệ số, intercept, feature đúng thứ tự, thuật toán feature, cửa sổ phân bổ,
scope, signature snapshot+catalog+filters+source, ngày tạo, phiên bản thư viện,
khoảng train/validation/test/deployment, kết quả đánh giá, giả định và chính sách âm.
Không có scaler/encoder bị bỏ sót: tất cả feature số được tạo bởi cùng module đã version.
ID là khóa ánh xạ, không encode vào hồi quy. Không dùng pickle thực thi mã khi load.

Chỉ nhận JSON cùng format, scope ba cấp, signature, feature set/thứ tự, window, chính
sách âm và phiên bản sklearn chính xác; kiểm tra hệ số hữu hạn. Đổi bộ lọc/dữ liệu buộc
train hoặc tải bundle khớp. Không lấy kết quả track trước gán cho track mới.

## Giới hạn kết luận

Dữ liệu Chinook ít tháng, giao dịch thưa ở thực thể, không có biến nhu cầu ngoại sinh.
Quan sát chỉ mô tả số liệu đã tính, không chứng minh quan hệ nhân quả. Kết quả thực
với mặc định bỏ hai tháng biên: LR tổng MAE 3,8877, tháng trước 2,0000, mean3 2,4400.
Không chọn lại cấu hình vì xem test, cũng không che việc baseline tốt hơn trên MAE.
Track LR có MAE toàn catalog khoảng 0,02261 nhưng MAE khi thực tế dương khoảng 1,03696,
cho thấy cần đọc metric nhóm thưa. Xem đầy đủ `data_audit.md` và `model_results.md`.
