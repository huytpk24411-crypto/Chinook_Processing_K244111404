# Hướng dẫn sử dụng

Bản mặc định hiện là web: chạy `main.py` hoặc `run_web.cmd`, ứng dụng tự tải Chinook
bằng cấu hình `.env` đã lưu. Không có màn hình kết nối hoặc nhập mật khẩu trên web.
Nhấn **Làm mới** để đọc lại MySQL, **Thử lại** khi nguồn lỗi. Các thao tác web chi tiết
ở [web_guide.md](web_guide.md). Nội dung phía dưới mô tả bản desktop PySide6 cũ,
chỉ dùng khi chạy `main.py --desktop`.


## Bản desktop cũ: Kết nối và ngôn ngữ

Chạy `main.py --desktop` bằng `.venv`. Chọn ngôn ngữ ở cuối sidebar. Menu, trạng thái,
nhãn và biểu đồ đổi ngay. Lựa chọn lưu trong `config/preferences.json`; tên track/album
không dịch. Định dạng số dùng dấu phân cách theo ngôn ngữ, CSV giữ giá trị số gốc.

Ở Kết nối / Cài đặt, mở hộp thoại và nhập host, cổng, user, database, mật khẩu. Mật khẩu
được che và không lưu mặc định. Khi lỗi đăng nhập, chỉnh và thử lại; khi lỗi dịch vụ,
kiểm tra MySQL Server. Không cần và không nên gửi mật khẩu qua chat.

Kết nối tải snapshot mới và tự chạy khảo sát. Trong lúc chạy, thanh tiến trình hoạt động,
nút thao tác phụ thuộc bị khóa; widget chỉ cập nhật trên thread giao diện. Sau lỗi không
hiện dữ liệu thay thế. Nhập lại cấu hình và thử kết nối.

## Bộ lọc tháng dùng chung

Từ tháng/Đến tháng chọn lịch sử dùng cho tổng, track và album. Bấm Áp dụng phạm vi.
Thay tháng sẽ xóa dataset/model/kết quả cũ ngay và yêu cầu áp dụng lại. Có thể chọn
phạm vi ngắn để khảo sát, nhưng ML cần ≥30 tháng và ≥12 tháng tổng dương.

Mặc định bỏ hai tháng biên của toàn nguồn. Chỉ tick gồm biên khi xác nhận nguồn trọn
tháng. Không kết luận thiếu tháng chỉ vì lần bán cuối không phải cuối tháng. Checkbox
nguồn liên tục chỉ dùng khi có căn cứ rằng tháng không hóa đơn là doanh thu 0.

Dự báo bắt đầu sau tháng cuối **đã dùng trong lịch sử**. Đọc khoảng ngày tổng quan
để biết mốc thật, nhất là khi mặc định loại tháng biên.

## Tổng quan, khám phá và chất lượng

Tổng quan hiện tổng doanh thu, số tháng, catalog và đối chiếu tháng giữa hóa đơn,
track, album. Khám phá hiện xếp hạng doanh thu quá khứ và lịch sử của lựa chọn.
Chọn track/album trong bộ lọc, tìm bằng một phần tên hoặc ID; combo hiện cả tên và ID.
Track/album chưa bán vẫn trong danh sách. Nhóm chưa gán album giữ doanh thu còn thiếu ánh xạ.

Chất lượng hiện số dòng bảng, ngày, null, trùng, khóa ngoại và độ thưa. Hai tab kỹ
thuật cho schema và quan hệ thật. Báo cáo đầy đủ tự ghi vào docs/data_audit.md. Nếu có
chênh từng hóa đơn >0,005, thiếu khóa chi tiết, trùng khóa hoặc giá trị không hợp lệ,
ứng dụng chặn dự báo. File nguồn phải được người quản lý xem xét, ứng dụng không sửa DB.

## Huấn luyện và đánh giá

Chọn Huấn luyện và đánh giá → Huấn luyện. Xem số tháng train/validation/test, khoảng
ngày, feature và cửa sổ tỷ trọng được chọn. Bảng metric cho phạm vi đang chọn là đánh
giá **toàn catalog của phạm vi**, không phải metric riêng của track đang chọn.
Tab actual/predicted/error là các hàng test của thực thể đang chọn, gồm ba phương pháp.
Biểu đồ dùng phương pháp được chọn ở bộ lọc chung và vạch đứt đánh dấu bắt đầu test.

MAE là độ lệch tuyệt đối trung bình. RMSE phạt lỗi lớn mạnh hơn. MSE là lỗi bình phương.
Càng nhỏ càng tốt. Xem thêm nhóm thực tế dương và đã từng bán; nhiều ô 0 có thể khiến
metric toàn bộ trông tốt. ML có thể kém baseline, ứng dụng vẫn hiện kết quả thật.

## Dự báo tổng / track / album

Chọn phạm vi, tìm tên/ID, chọn phương pháp và kỳ 1/3/6 tháng, rồi Chạy dự báo.
LR cần train/tải trước. Chọn baseline để dùng khi chưa đủ lịch sử. Ứng dụng không tự
đổi baseline thành LR hoặc gọi baseline là mô hình đã huấn luyện.

Track/album dùng phân bổ tổng theo tỷ trọng quá khứ, không có hồi quy riêng từng thực
thể. Track chưa bán có thể nhận 0 vì không có tỷ trọng, không phải dự báo “chắc chắn
không có nhu cầu”. Album cộng track. Tab đối chiếu cộng toàn bộ thực thể cho mỗi tháng,
giúp so với tổng. Số hiển thị làm tròn 2 chữ số, CSV lưu số đầy đủ.

Biểu đồ xám là thực tế ghi nhận, xanh là dự báo. Vạch đứt là ranh giới bắt đầu dự báo.
3/6 tháng dùng kết quả trước để tạo lag cho kết quả sau và giữ tỷ trọng ở mốc đầu.
Sai số có thể tích lũy, metric test một bước không phải metric forecast 6 bước.

Đổi phạm vi, tên/ID, tìm kiếm, phương pháp hoặc horizon sẽ xóa dự báo cũ. Bấm chạy lại.
Đổi ngôn ngữ giữ kết quả và chỉ đổi cách trình bày. Tìm không khớp không giữ track cũ.

## Lưu, tải và xuất

Lưu mô hình JSON lưu cả estimator state, feature, metadata và báo cáo test. Tải chỉ
chấp nhận cùng snapshot, catalog, bộ lọc và phiên bản sklearn. Nếu bị từ chối hãy áp
dụng lại đúng bộ lọc hoặc train lại trên dữ liệu hiện tại. Không có mật khẩu trong model.

CSV ở tổng quan xuất đối chiếu; ở khám phá có hai nút tương ứng xếp hạng/lịch sử;
ở huấn luyện xuất bảng metric hoặc chi tiết theo tab; ở dự báo xuất kết quả hoặc đối
chiếu theo tab. PNG xuất biểu đồ của trang. CSV UTF-8 BOM để Excel đọc tiếng Việt.
Tất cả là file cục bộ, không đẩy cloud hay gửi cho người khác.

## Trạng thái cần chú ý

- Chưa kết nối: chưa có dữ liệu, vào trang kết nối.
- Đang xử lý: chờ worker, không mở kết nối dùng chung ở thread khác.
- Không có dữ liệu: đổi phạm vi hoặc kiểm tra nguồn.
- Không đủ lịch sử: dùng baseline hoặc mở rộng lịch sử có căn cứ.
- Chưa huấn luyện: train/tải hoặc chọn baseline.
- Đầu vào đã thay đổi: dữ liệu/kết quả cũ đã xóa, áp dụng/chạy lại.
- Lỗi: đọc nội dung, chỉnh cấu hình/bộ lọc rồi thử lại.
