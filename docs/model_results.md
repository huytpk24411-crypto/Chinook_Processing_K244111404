# Kết quả huấn luyện từ MySQL

Nguồn: `localhost:3306/chinook`. Thời điểm: 2026-10-23T11:51:20.102140+00:00.

Feature: ['lag1', 'mean3', 'mean6']. Cửa sổ tỷ trọng: 0 (0 = toàn quá khứ).

Đánh giá test một bước, estimator cố định trước test. Không phải metric forecast 3/6 bước.
Track/album là dự báo phân bổ. Dữ liệu/giả định xem data_audit.md và methodology.md.

```text
scope   method          subset     n      MAE       MSE     RMSE
track   linear             all 21018 0.022610  0.012478 0.111705
track   linear positive_actual   228 1.036958  1.124894 1.060610
track   linear     seen_before 11025 0.027740  0.006954 0.083389
track   linear  macro_seen_MAE  1905 0.027392       NaN      NaN
album   linear             all  2082 0.214897  0.338332 0.581663
album   linear positive_actual   110 2.022985  5.985946 2.446619
album   linear     seen_before  1824 0.245293  0.386188 0.621441
album   linear  macro_seen_MAE   304 0.245293       NaN      NaN
total   linear             all     6 3.887679 24.020521 4.901074
total   linear positive_actual     6 3.887679 24.020521 4.901074
total   linear     seen_before     6 3.887679 24.020521 4.901074
total   linear  macro_seen_MAE     1 3.887679       NaN      NaN
track previous             all 21018 0.022050  0.022965 0.151543
track previous positive_actual   228 1.042632  1.136942 1.066275
track previous     seen_before 11025 0.026672  0.026947 0.164155
track previous  macro_seen_MAE  1905 0.046073       NaN      NaN
album previous             all  2082 0.215937  0.608818 0.780268
album previous positive_actual   110 2.107091  6.212909 2.492571
album previous     seen_before  1824 0.246480  0.694934 0.833627
album previous  macro_seen_MAE   304 0.246480       NaN      NaN
total previous             all     6 2.000000 24.000000 4.898979
total previous positive_actual     6 2.000000 24.000000 4.898979
total previous     seen_before     6 2.000000 24.000000 4.898979
total previous  macro_seen_MAE     1 2.000000       NaN      NaN
track    mean3             all 21018 0.021924  0.015836 0.125841
track    mean3 positive_actual   228 1.042632  1.136942 1.066275
track    mean3     seen_before 11025 0.026433  0.013355 0.115565
track    mean3  macro_seen_MAE  1905 0.036487       NaN      NaN
album    mean3             all  2082 0.218156  0.439662 0.663070
album    mean3 positive_actual   110 2.131091  6.454469 2.540565
album    mean3     seen_before  1824 0.249013  0.501851 0.708415
album    mean3  macro_seen_MAE   304 0.249013       NaN      NaN
total    mean3             all     6 2.440000 24.580800 4.957903
total    mean3 positive_actual     6 2.440000 24.580800 4.957903
total    mean3     seen_before     6 2.440000 24.580800 4.957903
total    mean3  macro_seen_MAE     1 2.440000       NaN      NaN
```

MAE/RMSE càng thấp càng tốt; MSE đơn vị bình phương. Không khẳng định ML thắng baseline.
Nhóm positive_actual chỉ dùng chẩn đoán sau dự báo. macro_seen_MAE chỉ có MAE.
