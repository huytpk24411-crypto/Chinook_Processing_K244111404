"""Generate an empirical report only after a successful live MySQL read."""
from datetime import datetime, timezone
import json
from config.settings import ROOT, ARTIFACTS


def write_audit(report):
    ARTIFACTS.mkdir(exist_ok=True)
    (ARTIFACTS/'data_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    text = f'''# Khảo sát dữ liệu MySQL thực

Thời điểm đọc: {report.get('source_read_at') or datetime.now(timezone.utc).isoformat()}. Nguồn: `{report['source']}`.
Đọc trong một transaction chỉ đọc, không import hoặc ghi bảng nghiệp vụ.

## Quy mô và thời gian

{json.dumps(report['table_counts'], ensure_ascii=False, indent=2)}

Ngày đầu: {report.get('date_min', 'N/A')}. Ngày cuối: {report.get('date_max', 'N/A')}.
Số tháng lịch: {report.get('calendar_months', 0)}; tháng có hóa đơn: {report.get('observed_months', 0)}.
Tháng không có hóa đơn: {report.get('months_without_invoices', [])}.
Chưa biết độ bao phủ hai tháng biên. Ngày giao dịch cuối không chứng minh dữ liệu bị cắt.
Mặc định loại cả hai tháng biên một cách thận trọng, không kết luận chúng thiếu.

## Doanh thu và đối chiếu

SUM(invoice.Total): {report['invoice_revenue']:.6f}.
SUM(invoiceline.UnitPrice * invoiceline.Quantity): {report['line_revenue']:.6f}.
Chênh lệch: {report['difference']:.8f}. Số hóa đơn lệch trên 0.005: {report['invoice_mismatches']}.
Không cộng invoice.Total sau join chi tiết. Track dùng giá giao dịch, album cộng track qua AlbumId.
Đơn vị tiền tệ chưa xác minh, không tự gắn VNĐ hoặc quy đổi.

## Độ thưa và lựa chọn phương pháp

Track chưa có tháng doanh thu dương: {report.get('never_sold_tracks', 'N/A')}.
Album chưa có tháng doanh thu dương: {report.get('never_sold_albums', 'N/A')}.
Trung vị số tháng dương của track/album: {report.get('track_positive_months_median', 'N/A')} / {report.get('album_positive_months_median', 'N/A')}.
Tỷ lệ ô track-tháng bằng 0: {report.get('track_zero_fraction', 'N/A')}.
Tỷ lệ ô album-tháng bằng 0: {report.get('album_zero_fraction', 'N/A')}.
Ứng dụng dự báo tổng bằng Linear Regression rồi phân bổ bằng tỷ trọng quá khứ để tránh
huấn luyện hàng nghìn mô hình ít quan sát và bảo đảm ba cấp khớp. Track/album là dự báo
phân bổ, không phải mô hình hồi quy riêng. Cần xem kết quả test để đánh giá hạn chế tỷ trọng.

## Chất lượng và giả định

Track không có album: {report['tracks_without_album']}; AlbumId không tồn tại: {report['missing_track_album']}.
Cả hai thuộc nhóm rõ ràng “Chưa gán album”, giữ nguyên doanh thu.
Mỗi hàng train là một tháng toàn cửa hàng, đầu vào chỉ biết trước tháng mục tiêu.
Mỗi hàng đánh giá track/album là một thực thể trong một tháng test cùng mốc thời gian.
Không biết ngày ra mắt track. Ô 0 chỉ là doanh thu ghi nhận 0, không chứng minh có bán cả tháng.
Tháng hoàn toàn không có hóa đơn chỉ điền 0 nếu người dùng xác nhận nguồn liên tục.
Kết quả kiểm tra đầy đủ (null, trùng khóa, khóa ngoại, schema) ở bên dưới và artifacts/data_audit.json.

```json
{json.dumps(report, ensure_ascii=False, indent=2, default=str)}
```
'''
    (ROOT/'docs'/'data_audit.md').write_text(text, encoding='utf-8')
