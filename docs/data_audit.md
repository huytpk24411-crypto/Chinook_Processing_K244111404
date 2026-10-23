# Khảo sát dữ liệu MySQL thực

Thời điểm đọc: 2026-10-23T12:01:03.153357+00:00. Nguồn: `localhost:3306/chinook`.
Đọc trong một transaction chỉ đọc, không import hoặc ghi bảng nghiệp vụ.

## Quy mô và thời gian

{
  "album": 347,
  "artist": 275,
  "customer": 59,
  "employee": 8,
  "genre": 25,
  "invoice": 412,
  "invoiceline": 2240,
  "mediatype": 5,
  "playlist": 18,
  "playlisttrack": 8715,
  "track": 3503
}

Ngày đầu: 2009-01-01 00:00:00. Ngày cuối: 2013-12-22 00:00:00.
Số tháng lịch: 60; tháng có hóa đơn: 60.
Tháng không có hóa đơn: [].
Chưa biết độ bao phủ hai tháng biên. Ngày giao dịch cuối không chứng minh dữ liệu bị cắt.
Mặc định loại cả hai tháng biên một cách thận trọng, không kết luận chúng thiếu.

## Doanh thu và đối chiếu

SUM(invoice.Total): 2328.600000.
SUM(invoiceline.UnitPrice * invoiceline.Quantity): 2328.600000.
Chênh lệch: -0.00000000. Số hóa đơn lệch trên 0.005: 0.
Không cộng invoice.Total sau join chi tiết. Track dùng giá giao dịch, album cộng track qua AlbumId.
Đơn vị tiền tệ chưa xác minh, không tự gắn VNĐ hoặc quy đổi.

## Độ thưa và lựa chọn phương pháp

Track chưa có tháng doanh thu dương: 1519.
Album chưa có tháng doanh thu dương: 43.
Trung vị số tháng dương của track/album: 1.0 / 4.0.
Tỷ lệ ô track-tháng bằng 0: 0.9893424683604529.
Tỷ lệ ô album-tháng bằng 0: 0.9472142170989433.
Ứng dụng dự báo tổng bằng Linear Regression rồi phân bổ bằng tỷ trọng quá khứ để tránh
huấn luyện hàng nghìn mô hình ít quan sát và bảo đảm ba cấp khớp. Track/album là dự báo
phân bổ, không phải mô hình hồi quy riêng. Cần xem kết quả test để đánh giá hạn chế tỷ trọng.

## Chất lượng và giả định

Track không có album: 0; AlbumId không tồn tại: 0.
Cả hai thuộc nhóm rõ ràng “Chưa gán album”, giữ nguyên doanh thu.
Mỗi hàng train là một tháng toàn cửa hàng, đầu vào chỉ biết trước tháng mục tiêu.
Mỗi hàng đánh giá track/album là một thực thể trong một tháng test cùng mốc thời gian.
Không biết ngày ra mắt track. Ô 0 chỉ là doanh thu ghi nhận 0, không chứng minh có bán cả tháng.
Tháng hoàn toàn không có hóa đơn chỉ điền 0 nếu người dùng xác nhận nguồn liên tục.
Kết quả kiểm tra đầy đủ (null, trùng khóa, khóa ngoại, schema) ở bên dưới và artifacts/data_audit.json.

```json
{
  "source": "localhost:3306/chinook",
  "source_read_at": "2026-10-23T12:01:03.153357+00:00",
  "table_counts": {
    "album": 347,
    "artist": 275,
    "customer": 59,
    "employee": 8,
    "genre": 25,
    "invoice": 412,
    "invoiceline": 2240,
    "mediatype": 5,
    "playlist": 18,
    "playlisttrack": 8715,
    "track": 3503
  },
  "schema": [
    {
      "TABLE_NAME": "album",
      "COLUMN_NAME": "AlbumId",
      "COLUMN_TYPE": "int",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": "PRI"
    },
    {
      "TABLE_NAME": "album",
      "COLUMN_NAME": "Title",
      "COLUMN_TYPE": "varchar(160)",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "album",
      "COLUMN_NAME": "ArtistId",
      "COLUMN_TYPE": "int",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": "MUL"
    },
    {
      "TABLE_NAME": "artist",
      "COLUMN_NAME": "ArtistId",
      "COLUMN_TYPE": "int",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": "PRI"
    },
    {
      "TABLE_NAME": "artist",
      "COLUMN_NAME": "Name",
      "COLUMN_TYPE": "varchar(120)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "customer",
      "COLUMN_NAME": "CustomerId",
      "COLUMN_TYPE": "int",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": "PRI"
    },
    {
      "TABLE_NAME": "customer",
      "COLUMN_NAME": "FirstName",
      "COLUMN_TYPE": "varchar(40)",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "customer",
      "COLUMN_NAME": "LastName",
      "COLUMN_TYPE": "varchar(20)",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "customer",
      "COLUMN_NAME": "Company",
      "COLUMN_TYPE": "varchar(80)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "customer",
      "COLUMN_NAME": "Address",
      "COLUMN_TYPE": "varchar(70)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "customer",
      "COLUMN_NAME": "City",
      "COLUMN_TYPE": "varchar(40)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "customer",
      "COLUMN_NAME": "State",
      "COLUMN_TYPE": "varchar(40)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "customer",
      "COLUMN_NAME": "Country",
      "COLUMN_TYPE": "varchar(40)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "customer",
      "COLUMN_NAME": "PostalCode",
      "COLUMN_TYPE": "varchar(10)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "customer",
      "COLUMN_NAME": "Phone",
      "COLUMN_TYPE": "varchar(24)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "customer",
      "COLUMN_NAME": "Fax",
      "COLUMN_TYPE": "varchar(24)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "customer",
      "COLUMN_NAME": "Email",
      "COLUMN_TYPE": "varchar(60)",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "customer",
      "COLUMN_NAME": "SupportRepId",
      "COLUMN_TYPE": "int",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": "MUL"
    },
    {
      "TABLE_NAME": "employee",
      "COLUMN_NAME": "EmployeeId",
      "COLUMN_TYPE": "int",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": "PRI"
    },
    {
      "TABLE_NAME": "employee",
      "COLUMN_NAME": "LastName",
      "COLUMN_TYPE": "varchar(20)",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "employee",
      "COLUMN_NAME": "FirstName",
      "COLUMN_TYPE": "varchar(20)",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "employee",
      "COLUMN_NAME": "Title",
      "COLUMN_TYPE": "varchar(30)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "employee",
      "COLUMN_NAME": "ReportsTo",
      "COLUMN_TYPE": "int",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": "MUL"
    },
    {
      "TABLE_NAME": "employee",
      "COLUMN_NAME": "BirthDate",
      "COLUMN_TYPE": "datetime",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "employee",
      "COLUMN_NAME": "HireDate",
      "COLUMN_TYPE": "datetime",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "employee",
      "COLUMN_NAME": "Address",
      "COLUMN_TYPE": "varchar(70)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "employee",
      "COLUMN_NAME": "City",
      "COLUMN_TYPE": "varchar(40)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "employee",
      "COLUMN_NAME": "State",
      "COLUMN_TYPE": "varchar(40)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "employee",
      "COLUMN_NAME": "Country",
      "COLUMN_TYPE": "varchar(40)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "employee",
      "COLUMN_NAME": "PostalCode",
      "COLUMN_TYPE": "varchar(10)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "employee",
      "COLUMN_NAME": "Phone",
      "COLUMN_TYPE": "varchar(24)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "employee",
      "COLUMN_NAME": "Fax",
      "COLUMN_TYPE": "varchar(24)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "employee",
      "COLUMN_NAME": "Email",
      "COLUMN_TYPE": "varchar(60)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "genre",
      "COLUMN_NAME": "GenreId",
      "COLUMN_TYPE": "int",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": "PRI"
    },
    {
      "TABLE_NAME": "genre",
      "COLUMN_NAME": "Name",
      "COLUMN_TYPE": "varchar(120)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "invoice",
      "COLUMN_NAME": "InvoiceId",
      "COLUMN_TYPE": "int",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": "PRI"
    },
    {
      "TABLE_NAME": "invoice",
      "COLUMN_NAME": "CustomerId",
      "COLUMN_TYPE": "int",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": "MUL"
    },
    {
      "TABLE_NAME": "invoice",
      "COLUMN_NAME": "InvoiceDate",
      "COLUMN_TYPE": "datetime",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "invoice",
      "COLUMN_NAME": "BillingAddress",
      "COLUMN_TYPE": "varchar(70)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "invoice",
      "COLUMN_NAME": "BillingCity",
      "COLUMN_TYPE": "varchar(40)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "invoice",
      "COLUMN_NAME": "BillingState",
      "COLUMN_TYPE": "varchar(40)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "invoice",
      "COLUMN_NAME": "BillingCountry",
      "COLUMN_TYPE": "varchar(40)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "invoice",
      "COLUMN_NAME": "BillingPostalCode",
      "COLUMN_TYPE": "varchar(10)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "invoice",
      "COLUMN_NAME": "Total",
      "COLUMN_TYPE": "decimal(10,2)",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "invoiceline",
      "COLUMN_NAME": "InvoiceLineId",
      "COLUMN_TYPE": "int",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": "PRI"
    },
    {
      "TABLE_NAME": "invoiceline",
      "COLUMN_NAME": "InvoiceId",
      "COLUMN_TYPE": "int",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": "MUL"
    },
    {
      "TABLE_NAME": "invoiceline",
      "COLUMN_NAME": "TrackId",
      "COLUMN_TYPE": "int",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": "MUL"
    },
    {
      "TABLE_NAME": "invoiceline",
      "COLUMN_NAME": "UnitPrice",
      "COLUMN_TYPE": "decimal(10,2)",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "invoiceline",
      "COLUMN_NAME": "Quantity",
      "COLUMN_TYPE": "int",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "mediatype",
      "COLUMN_NAME": "MediaTypeId",
      "COLUMN_TYPE": "int",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": "PRI"
    },
    {
      "TABLE_NAME": "mediatype",
      "COLUMN_NAME": "Name",
      "COLUMN_TYPE": "varchar(120)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "playlist",
      "COLUMN_NAME": "PlaylistId",
      "COLUMN_TYPE": "int",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": "PRI"
    },
    {
      "TABLE_NAME": "playlist",
      "COLUMN_NAME": "Name",
      "COLUMN_TYPE": "varchar(120)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "playlisttrack",
      "COLUMN_NAME": "PlaylistId",
      "COLUMN_TYPE": "int",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": "PRI"
    },
    {
      "TABLE_NAME": "playlisttrack",
      "COLUMN_NAME": "TrackId",
      "COLUMN_TYPE": "int",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": "PRI"
    },
    {
      "TABLE_NAME": "track",
      "COLUMN_NAME": "TrackId",
      "COLUMN_TYPE": "int",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": "PRI"
    },
    {
      "TABLE_NAME": "track",
      "COLUMN_NAME": "Name",
      "COLUMN_TYPE": "varchar(200)",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "track",
      "COLUMN_NAME": "AlbumId",
      "COLUMN_TYPE": "int",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": "MUL"
    },
    {
      "TABLE_NAME": "track",
      "COLUMN_NAME": "MediaTypeId",
      "COLUMN_TYPE": "int",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": "MUL"
    },
    {
      "TABLE_NAME": "track",
      "COLUMN_NAME": "GenreId",
      "COLUMN_TYPE": "int",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": "MUL"
    },
    {
      "TABLE_NAME": "track",
      "COLUMN_NAME": "Composer",
      "COLUMN_TYPE": "varchar(220)",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "track",
      "COLUMN_NAME": "Milliseconds",
      "COLUMN_TYPE": "int",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "track",
      "COLUMN_NAME": "Bytes",
      "COLUMN_TYPE": "int",
      "IS_NULLABLE": "YES",
      "COLUMN_KEY": ""
    },
    {
      "TABLE_NAME": "track",
      "COLUMN_NAME": "UnitPrice",
      "COLUMN_TYPE": "decimal(10,2)",
      "IS_NULLABLE": "NO",
      "COLUMN_KEY": ""
    }
  ],
  "relations": [
    {
      "TABLE_NAME": "album",
      "COLUMN_NAME": "ArtistId",
      "REFERENCED_TABLE_NAME": "artist",
      "REFERENCED_COLUMN_NAME": "ArtistId"
    },
    {
      "TABLE_NAME": "customer",
      "COLUMN_NAME": "SupportRepId",
      "REFERENCED_TABLE_NAME": "employee",
      "REFERENCED_COLUMN_NAME": "EmployeeId"
    },
    {
      "TABLE_NAME": "employee",
      "COLUMN_NAME": "ReportsTo",
      "REFERENCED_TABLE_NAME": "employee",
      "REFERENCED_COLUMN_NAME": "EmployeeId"
    },
    {
      "TABLE_NAME": "invoice",
      "COLUMN_NAME": "CustomerId",
      "REFERENCED_TABLE_NAME": "customer",
      "REFERENCED_COLUMN_NAME": "CustomerId"
    },
    {
      "TABLE_NAME": "invoiceline",
      "COLUMN_NAME": "TrackId",
      "REFERENCED_TABLE_NAME": "track",
      "REFERENCED_COLUMN_NAME": "TrackId"
    },
    {
      "TABLE_NAME": "invoiceline",
      "COLUMN_NAME": "InvoiceId",
      "REFERENCED_TABLE_NAME": "invoice",
      "REFERENCED_COLUMN_NAME": "InvoiceId"
    },
    {
      "TABLE_NAME": "playlisttrack",
      "COLUMN_NAME": "TrackId",
      "REFERENCED_TABLE_NAME": "track",
      "REFERENCED_COLUMN_NAME": "TrackId"
    },
    {
      "TABLE_NAME": "playlisttrack",
      "COLUMN_NAME": "PlaylistId",
      "REFERENCED_TABLE_NAME": "playlist",
      "REFERENCED_COLUMN_NAME": "PlaylistId"
    },
    {
      "TABLE_NAME": "track",
      "COLUMN_NAME": "MediaTypeId",
      "REFERENCED_TABLE_NAME": "mediatype",
      "REFERENCED_COLUMN_NAME": "MediaTypeId"
    },
    {
      "TABLE_NAME": "track",
      "COLUMN_NAME": "GenreId",
      "REFERENCED_TABLE_NAME": "genre",
      "REFERENCED_COLUMN_NAME": "GenreId"
    },
    {
      "TABLE_NAME": "track",
      "COLUMN_NAME": "AlbumId",
      "REFERENCED_TABLE_NAME": "album",
      "REFERENCED_COLUMN_NAME": "AlbumId"
    }
  ],
  "declared_foreign_keys_missing": {
    "album.ArtistId -> artist.ArtistId": 0,
    "customer.SupportRepId -> employee.EmployeeId": 0,
    "employee.ReportsTo -> employee.EmployeeId": 0,
    "invoice.CustomerId -> customer.CustomerId": 0,
    "invoiceline.TrackId -> track.TrackId": 0,
    "invoiceline.InvoiceId -> invoice.InvoiceId": 0,
    "playlisttrack.TrackId -> track.TrackId": 0,
    "playlisttrack.PlaylistId -> playlist.PlaylistId": 0,
    "track.MediaTypeId -> mediatype.MediaTypeId": 0,
    "track.GenreId -> genre.GenreId": 0,
    "track.AlbumId -> album.AlbumId": 0
  },
  "currency": "Unverified data currency; no conversion",
  "boundary_completeness": "Unknown: transaction dates do not prove extract coverage.",
  "nulls": {
    "invoice": {
      "InvoiceId": 0,
      "InvoiceDate": 0,
      "Total": 0
    },
    "invoiceline": {
      "InvoiceLineId": 0,
      "InvoiceId": 0,
      "TrackId": 0,
      "UnitPrice": 0,
      "Quantity": 0
    },
    "track": {
      "TrackId": 0,
      "Name": 0,
      "AlbumId": 0
    },
    "album": {
      "AlbumId": 0,
      "Title": 0
    }
  },
  "duplicate_primary_keys": {
    "invoice": 0,
    "invoiceline": 0,
    "track": 0,
    "album": 0
  },
  "identical_line_values": 0,
  "missing_line_invoice": 0,
  "missing_line_track": 0,
  "tracks_without_album": 0,
  "missing_track_album": 0,
  "invoice_revenue": 2328.5999999999995,
  "line_revenue": 2328.6000000000004,
  "difference": -9.094947017729282e-13,
  "invoice_mismatches": 0,
  "negative_values": 0,
  "safe_for_forecast": true,
  "date_min": "2009-01-01 00:00:00",
  "date_max": "2013-12-22 00:00:00",
  "calendar_months": 60,
  "observed_months": 60,
  "months_without_invoices": [],
  "never_sold_tracks": 1519,
  "never_sold_albums": 43,
  "track_positive_months_median": 1.0,
  "album_positive_months_median": 4.0,
  "track_zero_fraction": 0.9893424683604529,
  "album_zero_fraction": 0.9472142170989433
}
```
