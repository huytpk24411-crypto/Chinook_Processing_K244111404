# Tài liệu nguồn

Lúc triển khai, 13 file slide `.pptx` và `ML on Class.zip` nằm trực tiếp ở gốc project,
không có thư mục references. Các bản gốc được giữ nguyên ở đó, không giải nén database
để thay dữ liệu nghiệp vụ. Nội dung liên quan đã đọc và ghi nhận trong
[implementation_plan.md](../docs/implementation_plan.md).

Các phần áp dụng chính: Python/pandas/NumPy, MySQL interaction, Linear Regression,
chuẩn bị dữ liệu, huấn luyện và MAE/MSE/RMSE, lưu/tải, tích hợp GUI. Các phần khác với
ví dụ giá nhà: chia thời gian thay random split, PySide6 thống nhất, JSON có metadata,
dự báo phân cấp nhất quán, không dùng CSV/SQLite làm fallback.
