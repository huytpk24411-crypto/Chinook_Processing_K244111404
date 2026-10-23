# Kế hoạch triển khai và trạng thái

1. Đã kiểm tra Python 3.14.7 và Python 3.13.14. Thư viện chính import được trên 3.14.
2. Đã trích nội dung 13 bộ slide và đọc code trong ML on Class.zip. Tài liệu nguồn thực tế
   ở gốc project, không có thư mục references lúc bắt đầu. Không sửa bản gốc.
3. MySQL80 chạy, localhost:3306 phản hồi. Ban đầu root trống trả 1045; sau khi người dùng
   cung cấp thông tin, đã đọc MySQL thật bằng credentials chỉ giữ trong bộ nhớ.
4. Triển khai tổng hợp thống nhất, kiểm tra schema/khóa/đối chiếu trước mô hình.
5. Phương án hiện tại: Linear Regression tổng tháng, phân bổ track bằng tỷ trọng quá khứ,
   album cộng track. Khảo sát thực có 98,93% ô track-tháng bằng 0, trung vị track chỉ có
   1 tháng dương; do đó giữ phương án này thay mô hình riêng. Validation chọn lag1/mean3/mean6
   và tỷ trọng toàn quá khứ. Test cho thấy MAE tổng LR kém baseline tháng trước; báo cáo thật.
6. Đã có các màn hình PySide6, worker nền, Việt–Anh, lưu/tải JSON, CSV/PNG.
7. Kiểm thử bằng fixture tách riêng trong tests; đồng thời kiểm tra MySQL thật, đủ 3 cấp,
   3 phương pháp và horizon 1/3/6; JSON roundtrip và đối chiếu ba cấp đều đạt.

Tham khảo môn học: slide 05 về truy vấn MySQL, slide 06 về hồi quy tuyến tính và MSE/RMSE,
slide 08 (10–19) về chuẩn bị/build/use model, slide 09 về tích hợp giao diện.
Ví dụ Housing_price_prediction dùng pandas, sklearn LinearRegression, MAE/MSE/RMSE,
pickle và Tkinter. Dự án này dùng PySide6 thống nhất, chia thời gian thay chia ngẫu nhiên,
JSON có metadata thay việc chỉ lưu estimator. Ví dụ quản lý sales có code PySide6 và cả
nhánh PyQt6; không sao chép phần trộn hai framework vào ứng dụng mới.
