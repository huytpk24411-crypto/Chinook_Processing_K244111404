# Ghi chú bảo vệ giữa kỳ

**Bài toán của em là gì?** Hết tháng t, dùng doanh thu đã biết để dự báo t+1.
Tổng quan là thống kê quá khứ, màn hình dự báo là kết quả cho tháng chưa dùng trong lịch sử.

**Mỗi hàng train là gì?** Một tháng toàn cửa hàng, y là doanh thu tháng đó; X là lag1,
mean3, mean6 của các tháng trước và có thể thêm sin/cos tháng. Track/album trong bảng
đánh giá là một thực thể trong một tháng test. Không dùng ID như số có thứ tự.

**Kế thừa gì từ môn học?** Python, NumPy, pandas, mysql.connector, LinearRegression,
chuẩn bị dữ liệu → train → đánh giá MAE/MSE/RMSE → lưu/tải → tích hợp GUI.
Ví dụ giá nhà dùng Tkinter và chia ngẫu nhiên. Bài này dùng PySide6 thống nhất và chia
theo thời gian vì dữ liệu tháng có thứ tự. Không sao chép SQLite để giả làm MySQL.

**Tính doanh thu có bị nhân không?** Không cộng invoice.Total trên join với chi tiết.
Đọc riêng tổng hóa đơn và tính line.UnitPrice × Quantity cho track. Album cộng track.
Đối chiếu từng hóa đơn và từng tháng trong dung sai 0,005, có nhóm chưa gán album.

**Tại sao không dùng giá trong track?** Đó là giá niêm yết hiện tại. Doanh thu phải
dùng giá giao dịch ở invoiceline. Không tự đổi tiền tệ hay gắn VNĐ khi chưa xác minh.

**Chống nhìn tương lai thế nào?** Shift(1) trước rolling. 6 tháng test cuối không dùng
chọn feature/cửa sổ. Tỷ trọng ở mốc t chỉ lấy dữ liệu trước mốc. Unit test thay mục
tiêu/tương lai và kiểm tra feature của tháng trước không đổi.

**Vì sao không train mỗi track?** Catalog nhiều thực thể có thể rất ít tháng phát sinh.
Thay vì ép hàng nghìn hồi quy không đủ tín hiệu, bài dùng hồi quy tổng rồi phân bổ.
Phải chỉ vào số tháng dương/trung vị/ô 0 trong khảo sát thật để giải thích độ thưa.
Nếu chưa kết nối được MySQL, nói rõ đây là phương án triển khai chưa được chứng minh
phù hợp bằng khảo sát thực, không đọc số fixture thành số Chinook.

**Track/album có phải mô hình riêng không?** Không. Đó là dự báo phân bổ tổng theo
tỷ trọng lịch sử, album cộng track. Nhãn giao diện ghi rõ. Phương pháp có đánh giá
giữ lại ở cả ba cấp, so với baseline từng thực thể. Track chưa bán vẫn hiện nhưng tỷ
trọng 0 khi có bán ở track khác; hạn chế là không dự đoán tốt nhu cầu mới xuất hiện.

**Ba cấp khớp thế nào?** Tổng dự báo nhân trọng số track có tổng bằng 1; album cộng các
track theo AlbumId và nhóm chưa gán. Khớp trước làm tròn, không phải ba mô hình độc lập
tự nhiên luôn bằng nhau. Baseline cũng cộng từ track để giữ tính nhất quán.

**Tại sao không MAPE?** Thực tế nhiều ô 0, MAPE chia cho 0 hoặc thiếu ổn định. Dùng
MAE/MSE/RMSE, thêm nhóm actual>0, đã từng bán và macro MAE để không bị số 0 che lỗi.

**Nếu hồi quy cho số âm?** Chặn 0 nhất quán trong validation, test và dùng thật, ghi
chính sách trong metadata. Không bịa khoảng tin cậy hay phần trăm chính xác.

**Nếu ML thua baseline?** Báo cáo trung thực. Linear Regression là mô hình ML chính
đáp ứng môn học, không có cam kết thắng. Người dùng được chọn baseline có nhãn riêng.

**Test 6 tháng khác forecast 6 tháng thế nào?** Test một bước biết doanh thu thực tế
tháng trước mỗi lần, estimator vẫn cố định. Forecast nhiều bước giữ mốc đầu và dùng
chính dự báo trước làm lag, nên sai số tích lũy. Không dùng thực tế tương lai.

**Tại sao fit lại sau test?** Báo cáo test dùng estimator trước test. Sau báo cáo, fit
cấu hình đã chốt trên toàn lịch sử để triển khai. Không chỉnh cấu hình vì xem test.
Metadata ghi riêng hai khoảng fit.

**Vì sao bỏ tháng biên?** Không biết thời gian export bao phủ trọn tháng không. Ngày
giao dịch cuối không cho kết luận. Bỏ biên là mặc định thận trọng, người dùng có thể
xác nhận đầy đủ để đưa vào. Tháng nội bộ không hóa đơn chỉ điền 0 khi nguồn liên tục.

**Lưu mô hình gồm những gì?** JSON chứa hệ số, intercept, thứ tự feature, window phân
bổ, signature dữ liệu/bộ lọc, phiên bản, khoảng fit, đánh giá, giả định, chính sách âm.
Tải kiểm tra tương thích. Không có password hoặc pickle thực thi mã.

**GUI có treo không?** Truy vấn, chuẩn bị dữ liệu, train, forecast và JSON/CSV dùng
worker. Mỗi lần đọc DB có connection riêng; widget chỉ cập nhật ở slot UI. Revision
loại kết quả quá hạn, đổi thực thể xóa forecast cũ. PNG render ở UI thread vì figure
gắn Qt, có thể mất một khoảng ngắn khi ghi ảnh.

**Đã chứng minh được gì?** Xem docs/verification.md để phân biệt unit/GUI test fixture
với MySQL tích hợp. Chỉ dùng docs/data_audit.md và báo cáo test sinh từ MySQL để nói về
Chinook. Không đưa nhận định kinh doanh khi chưa có số liệu thật.
