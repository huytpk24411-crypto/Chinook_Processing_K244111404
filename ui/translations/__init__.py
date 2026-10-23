"""All application-owned visible copy lives here; source catalog names stay intact."""
from PySide6.QtCore import QLocale

COPY = {
 'app': ('Chinook · Dự báo doanh thu', 'Chinook · Revenue forecasting'),
 'subtitle': ('Học máy trong phân tích kinh doanh', 'Machine learning for business analytics'),
 'connection': ('Kết nối / Cài đặt', 'Connection / Settings'),
 'overview': ('Tổng quan doanh thu', 'Revenue overview'),
 'explore': ('Khám phá dữ liệu', 'Explore data'),
 'training': ('Huấn luyện và đánh giá', 'Training and evaluation'),
 'forecast': ('Dự báo doanh thu', 'Revenue forecast'),
 'quality': ('Chất lượng dữ liệu', 'Data quality'),
 'explanation': ('Mô hình và giới hạn', 'Model and limitations'),
 'host': ('Máy chủ', 'Host'), 'port': ('Cổng', 'Port'), 'user': ('Người dùng', 'User'),
 'database': ('Cơ sở dữ liệu', 'Database'), 'password': ('Mật khẩu', 'Password'),
 'connect': ('Kết nối / Thử lại', 'Connect / Retry'),
 'password_note': ('Mật khẩu được che, chỉ giữ trong bộ nhớ phiên này. Không tự lưu mật khẩu.', 'Password is masked and kept in session memory only. It is never saved automatically.'),
 'readonly_note': ('Chỉ đọc MySQL. Hãy kết nối để tải dữ liệu thật và chạy khảo sát.', 'Read-only MySQL. Connect to load real data and run the audit.'),
 'schema_tab': ('Cấu trúc bảng', 'Table schema'), 'relations_tab': ('Quan hệ khóa ngoại', 'Foreign key relations'),
 'TABLE_NAME': ('Tên bảng', 'Table name'), 'COLUMN_NAME': ('Tên cột', 'Column name'),
 'COLUMN_TYPE': ('Kiểu dữ liệu', 'Data type'), 'IS_NULLABLE': ('Cho phép null', 'Nullable'),
 'COLUMN_KEY': ('Khóa', 'Key'), 'REFERENCED_TABLE_NAME': ('Bảng được tham chiếu', 'Referenced table'),
 'REFERENCED_COLUMN_NAME': ('Cột được tham chiếu', 'Referenced column'),
 'export_ranking': ('Xuất xếp hạng CSV', 'Export ranking CSV'),
 'export_history': ('Xuất lịch sử CSV', 'Export history CSV'),
 'not_connected': ('Chưa kết nối MySQL.', 'Not connected to MySQL.'),
 'loading': ('Đang xử lý… Giao diện vẫn sẵn sàng.', 'Working… The interface remains responsive.'),
 'connected': ('Đã tải dữ liệu MySQL. Kiểm tra phạm vi tháng rồi áp dụng.', 'MySQL data loaded. Review the month range and apply.'),
 'ready': ('Dữ liệu đã sẵn sàng.', 'Data is ready.'),
 'no_data': ('Không có dữ liệu trong phạm vi này.', 'No data in this range.'),
 'auth_error': ('MySQL từ chối đăng nhập. Nhập mật khẩu trong ô được che, kiểm tra tài khoản và thử lại.', 'MySQL rejected the login. Enter the password in the masked field, check the account and retry.'),
 'database_error': ('Không tìm thấy database. Kiểm tra tên database và thử lại.', 'Database not found. Check its name and retry.'),
 'connection_error': ('Không đọc được MySQL. Kiểm tra dịch vụ, host, cổng và thử kết nối lại.', 'Could not read MySQL. Check the service, host and port, then reconnect.'),
 'schema_error': ('Cấu trúc bảng/cột chưa phù hợp Chinook. Xem schema trong báo cáo khảo sát.', 'The table/column structure does not match Chinook. Inspect the schema in the audit.'),
 'quality_block': ('Dữ liệu chưa đạt kiểm tra đối chiếu/khóa/giá trị. Xem trang Chất lượng dữ liệu trước khi dự báo.', 'Reconciliation, key or value checks failed. Review Data quality before forecasting.'),
 'coverage_error': ('Có tháng không có hóa đơn. Chưa thể phân biệt thiếu dữ liệu với không bán. Chỉ xác nhận nguồn liên tục khi có bằng chứng.', 'Some months have no invoices. Missing data and no sales cannot be distinguished. Confirm continuous coverage only with evidence.'),
 'insufficient_history': ('Chưa đủ lịch sử cho ML: cần ít nhất 30 tháng và 12 tháng có doanh thu dương. Có thể dùng baseline.', 'Insufficient ML history: at least 30 months and 12 positive-revenue months are required. Baselines remain available.'),
 'not_trained': ('Chưa huấn luyện hoặc tải mô hình phù hợp. Có thể chọn baseline để dự báo.', 'Train or load a compatible model first. You can select a baseline to forecast.'),
 'model_incompatible': ('Không tải/dùng được mô hình: kiểm tra dữ liệu, bộ lọc, feature, phiên bản thư viện và định dạng JSON.', 'Cannot load/use this model: check data, filters, features, library version and JSON format.'),
 'invalid_horizon': ('Chọn kỳ dự báo 1, 3 hoặc 6 tháng.', 'Choose a 1, 3 or 6 month horizon.'),
 'unexpected_error': ('Thao tác thất bại. Kiểm tra quyền truy cập file và thử lại.', 'The operation failed. Check file permissions and retry.'),
 'stale': ('Đầu vào đã thay đổi. Kết quả cũ đã xóa; áp dụng bộ lọc / chạy lại.', 'Inputs changed. Old results cleared; apply filters / run again.'),
 'selection_stale': ('Lựa chọn đã thay đổi. Chạy dự báo để xem kết quả tương ứng.', 'Selection changed. Run the forecast to view matching results.'),
 'start': ('Từ tháng', 'From month'), 'end': ('Đến tháng', 'To month'),
 'apply': ('Áp dụng phạm vi', 'Apply range'),
 'boundaries': ('Gồm tháng biên (xác nhận đầy đủ)', 'Include edges (coverage confirmed)'),
 'coverage': ('Nguồn liên tục: tháng trống = 0', 'Continuous coverage: empty month = 0'),
 'boundary_note': ('Mặc định loại hai tháng biên vì chưa biết độ bao phủ. Ngày bán cuối không chứng minh tháng thiếu. Các bộ lọc tháng dùng chung mọi màn hình.', 'Boundary months are excluded by default because coverage is unknown. The last sale date does not prove an incomplete month. All screens share the month filters.'),
 'scope': ('Phạm vi', 'Scope'), 'total': ('Tổng doanh thu', 'Total revenue'),
 'track': ('Theo track', 'By track'), 'album': ('Theo album', 'By album'),
 'search': ('Tìm tên hoặc ID…', 'Search name or ID…'), 'entity': ('Track / Album', 'Track / Album'),
 'method': ('Phương pháp', 'Method'),
 'linear': ('Linear Regression + phân bổ', 'Linear Regression + allocation'),
 'previous': ('Baseline · tháng trước', 'Baseline · previous month'),
 'mean3': ('Baseline · trung bình 3 tháng', 'Baseline · 3 month mean'),
 'horizon': ('Số tháng tới', 'Months ahead'),
 'run_forecast': ('Chạy dự báo', 'Run forecast'), 'train': ('Huấn luyện và đánh giá', 'Train and evaluate'),
 'save_model': ('Lưu mô hình JSON', 'Save model JSON'), 'load_model': ('Tải mô hình JSON', 'Load model JSON'),
 'export_csv': ('Xuất CSV', 'Export CSV'), 'export_png': ('Xuất biểu đồ PNG', 'Export chart PNG'),
 'exported': ('Đã xuất file.', 'File exported.'), 'model_saved': ('Đã lưu mô hình và metadata.', 'Model and metadata saved.'),
 'trained': ('Đã huấn luyện và đánh giá trên test giữ lại.', 'Training and held-out test evaluation completed.'),
 'model_loaded': ('Đã tải mô hình tương thích dữ liệu và bộ lọc.', 'Model loaded: data and filters are compatible.'),
 'unit': ('Đơn vị tiền tệ của dữ liệu', 'Data currency unit'),
 'unit_note': ('Đơn vị tiền tệ chưa xác minh; không quy đổi. MSE có đơn vị tiền tệ bình phương.', 'Currency is unverified; no conversion is applied. MSE uses squared currency units.'),
 'history': ('Doanh thu ghi nhận', 'Recorded revenue'), 'predicted': ('Dự báo', 'Predicted'),
 'actual': ('Thực tế', 'Actual'), 'error': ('Sai số (dự báo − thực tế)', 'Error (predicted − actual)'),
 'month': ('Tháng', 'Month'), 'name': ('Tên', 'Name'), 'id': ('ID', 'ID'),
 'revenue': ('Doanh thu', 'Revenue'), 'invoice': ('Theo hóa đơn', 'Invoice total'),
 'difference': ('Chênh lệch', 'Difference'), 'unassigned': ('Chưa gán album', 'Unassigned album'),
 'unknown_name': ('Không có tên', 'Unnamed'),
 'ranking': ('Xếp hạng doanh thu quá khứ trong phạm vi tháng', 'Historical revenue ranking in the selected month range'),
 'reconciliation': ('Đối chiếu doanh thu theo tháng', 'Monthly revenue reconciliation'),
 'overview_summary': ('{months} tháng · {start} – {end}\nTổng: {revenue} · Track: {tracks} · Album: {albums}', '{months} months · {start} – {end}\nTotal: {revenue} · Tracks: {tracks} · Albums: {albums}'),
 'metric_note': ('MAE: lệch tuyệt đối trung bình. RMSE: phạt sai số lớn mạnh hơn; cả hai càng nhỏ càng tốt. Không phải phần trăm chính xác. Xem cả tháng có doanh thu dương và thực thể đã từng bán để tránh các số 0 che sai số.', 'MAE is the average absolute error. RMSE penalizes large errors more; lower is better for both. Neither is an accuracy percentage. Check positive-revenue months and previously sold entities so zeros do not hide errors.'),
 'test_note': ('Test một bước: dùng lịch sử thực tế của tháng trước; estimator cố định từ trước test. Mô hình triển khai được fit lại sau báo cáo test. Track/album dùng cùng mốc tháng test.', 'One-step test uses the actual prior-month history and an estimator fixed before test. The deployment model is refitted after test reporting. Track/album share the same test months.'),
 'forecast_note': ('1 tháng: tháng ngay sau lịch sử đã chọn. 3/6 tháng: đệ quy từ một mốc, dùng dự báo trước làm lag; sai số có thể tích lũy. Tỷ trọng track cố định tại mốc. Album cộng các track; cả ba cấp khớp trước làm tròn.', '1 month: the next month after selected history. 3/6 months: recursive from a fixed origin using prior forecasts as lags; errors may accumulate. Track shares are frozen at origin. Albums sum tracks; all levels reconcile before rounding.'),
 'forecast_origin': ('Lịch sử kết thúc {origin}. Dự báo {start} – {end}.', 'History ends {origin}. Forecast: {start} – {end}.'),
 'allocation_note': ('Track/album là dự báo phân bổ từ tổng, không có mô hình ML riêng. Track chưa từng bán vẫn được chọn, tỷ trọng 0 nếu có doanh thu quá khứ ở track khác. Số 0 không chứng minh track chưa ra mắt hoặc không còn bán.', 'Track/album forecasts allocate the total; there is no individual ML estimator. Never-sold tracks remain selectable and receive zero share when other tracks have historical sales. Zero does not establish launch or availability.'),
 'never_sold': ('Thực thể này chưa có doanh thu trong lịch sử đã chọn. Dự báo phân bổ / baseline có thể bằng 0, không phải kết luận về nhu cầu tương lai.', 'This entity has no revenue in the selected history. Its allocation / baseline may be zero; this is not a conclusion about future demand.'),
 'training_summary': ('Train {train} tháng ({ts} – {te}); validation {val} tháng; test {test} tháng ({ss} – {se}).\nFeature: {features}. Tỷ trọng: {window}. Fit triển khai: {deployment} hàng tháng.', 'Train {train} months ({ts} – {te}); validation {val} months; test {test} months ({ss} – {se}).\nFeatures: {features}. Share window: {window}. Deployment fit: {deployment} monthly rows.'),
 'all_history': ('toàn bộ quá khứ', 'all past history'),
 'subset': ('Nhóm đánh giá', 'Evaluation subset'), 'all': ('Tất cả', 'All'),
 'positive_actual': ('Tháng thực tế > 0', 'Positive actual months'),
 'seen_before': ('Đã từng bán trước mốc', 'Sold before origin'),
 'macro_seen_MAE': ('MAE trung bình theo thực thể đã bán', 'Macro MAE for previously sold entities'),
 'n': ('Số quan sát', 'Observations'),
 'quality_intro': ('Khảo sát MySQL thực. Các số đếm được tính tại lúc tải; null/trùng khóa/khóa ngoại được kiểm tra trước khi tổng hợp. Báo cáo đầy đủ: docs/data_audit.md và artifacts/data_audit.json.', 'Live MySQL audit. Counts are computed at load time; nulls, duplicate keys and foreign keys are checked before aggregation. Full report: docs/data_audit.md and artifacts/data_audit.json.'),
 'check': ('Kiểm tra', 'Check'), 'value': ('Giá trị', 'Value'),
 'invoice_revenue': ('Tổng hóa đơn', 'Invoice revenue'), 'line_revenue': ('Tổng chi tiết', 'Line revenue'),
 'invoice_mismatches': ('Hóa đơn lệch > 0,005', 'Invoices differing by > 0.005'),
 'missing_line_invoice': ('Chi tiết thiếu hóa đơn', 'Lines missing invoice'),
 'missing_line_track': ('Chi tiết thiếu track', 'Lines missing track'),
 'tracks_without_album': ('Track không có AlbumId', 'Tracks with no AlbumId'),
 'missing_track_album': ('Track có AlbumId không tồn tại', 'Tracks with missing referenced album'),
 'identical_line_values': ('Dòng giống giá trị (cần xem xét)', 'Identical line values (review needed)'),
 'negative_values': ('Giá trị âm', 'Negative values'), 'safe_for_forecast': ('Đạt kiểm tra để dự báo', 'Passed forecasting checks'),
 'date_min': ('Ngày giao dịch đầu', 'First transaction'), 'date_max': ('Ngày giao dịch cuối', 'Last transaction'),
 'calendar_months': ('Số tháng lịch', 'Calendar months'), 'observed_months': ('Số tháng có hóa đơn', 'Months with invoices'),
 'months_without_invoices': ('Tháng không hóa đơn', 'Months without invoices'),
 'never_sold_tracks': ('Track chưa có doanh thu dương', 'Tracks with no positive revenue'),
 'never_sold_albums': ('Album chưa có doanh thu dương', 'Albums with no positive revenue'),
 'track_positive_months_median': ('Trung vị số tháng dương / track', 'Median positive months / track'),
 'album_positive_months_median': ('Trung vị số tháng dương / album', 'Median positive months / album'),
 'track_zero_fraction': ('Tỷ lệ ô 0 track-tháng', 'Zero track-month fraction'),
 'album_zero_fraction': ('Tỷ lệ ô 0 album-tháng', 'Zero album-month fraction'),
 'nulls': ('Giá trị null theo cột', 'Null values by column'),
 'duplicate_primary_keys': ('Khóa chính trùng', 'Duplicate primary keys'),
 'declared_foreign_keys_missing': ('Vi phạm khóa ngoại khai báo', 'Declared foreign key violations'),
 'table_counts': ('Số dòng từng bảng', 'Table row counts'),
 'yes': ('Có', 'Yes'), 'no': ('Không', 'No'),
 'explanation_text': (
    'Mỗi hàng train là doanh thu một tháng toàn cửa hàng. Mục tiêu: hết tháng t dự báo t+1. Linear Regression học từ lag1, trung bình 3/6 tháng đã shift, có thể thêm sin/cos tháng. Chọn feature bằng MAE validation, giữ 6 tháng cuối cho test. Cần 30 tháng và 12 tháng tổng doanh thu dương.\n\nTrack/album là phân bổ theo tỷ trọng lịch sử (6, 12 tháng hoặc toàn quá khứ), chọn cửa sổ bằng validation. ID chỉ là khóa, không phải số thứ tự đưa vào hồi quy. Không biết ngày ra mắt. Track chưa bán vẫn hiện trong danh mục. Không huấn luyện mô hình riêng cho lịch sử thưa.\n\nDự báo âm được chặn 0 cả khi test lẫn sử dụng. So sánh Linear Regression và hai baseline trên cùng hàng, cùng tháng. ML có thể thua baseline; ứng dụng hiển thị trung thực. Không có khoảng tin cậy tự tạo.\n\nTháng biên chưa biết độ bao phủ, mặc định bỏ cả hai. Khoảng tháng lọc là lịch sử dùng chung; dự báo bắt đầu ngay sau tháng cuối thực sự được dùng. Các ô 0 thực thể là doanh thu ghi nhận, không khẳng định có mặt hàng để bán cả tháng.\n\nTổng lấy từ invoice.Total độc lập với chi tiết. Track lấy UnitPrice × Quantity của invoiceline. Album cộng track, giữ nhóm chưa gán album. Chặn dự báo khi đối chiếu hoặc khóa dữ liệu lỗi. Đơn vị tiền tệ chưa xác minh.\n\nXem docs/methodology.md để biết công thức, cách chia thời gian và giới hạn. Các con số trong giao diện luôn đến từ MySQL, không có dữ liệu demo hoặc fallback.',
    'Each training row represents one month of store-wide revenue. At the end of t, predict t+1. Linear Regression uses lag1 and shifted 3/6 month means, optionally month sine/cosine. Select features by validation MAE and reserve the final 6 months for test. Require 30 months and 12 positive total-revenue months.\n\nTrack/album outputs allocate totals using historical shares (6, 12 months or all past history), with the window selected on validation. IDs are keys, never ordinal regression inputs. Launch dates are unknown. Never-sold tracks stay in the catalog. Sparse entities do not receive individual fitted models.\n\nNegative forecasts are clipped to zero in evaluation and use. Linear Regression and both baselines are compared on identical rows and months. ML may lose to a baseline; results are shown honestly. No invented confidence intervals.\n\nBoundary coverage is unknown, so both edges are excluded by default. The shared month filter defines history; forecasts begin immediately after the last month actually used. Entity zeros mean recorded zero revenue, not proof of full-month availability.\n\nTotals use invoice.Total separately from lines. Tracks use transaction UnitPrice × Quantity in invoiceline. Albums sum tracks and preserve an unassigned group. Forecasting is blocked on reconciliation or key errors. Currency remains unverified.\n\nSee docs/methodology.md for formulas, time splits and limitations. All interface figures come from MySQL, with no demo data or fallback.'),
}


class Translator:
    def __init__(self, language='vi'):
        self.language = language if language in ('vi', 'en') else 'vi'

    def __call__(self, key, **kwargs):
        pair = COPY.get(key)
        text = pair[0 if self.language == 'vi' else 1] if pair else str(key)
        return text.format(**kwargs)

    @property
    def locale(self):
        return QLocale('vi_VN' if self.language == 'vi' else 'en_US')

    def number(self, value, decimals=2):
        return self.locale.toString(float(value), 'f', decimals)

    def month(self, date):
        from PySide6.QtCore import QDate
        return self.locale.toString(QDate(date.year, date.month, 1), 'MM/yyyy' if self.language == 'vi' else 'MMM yyyy')
