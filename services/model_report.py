from config.settings import ARTIFACTS, ROOT


def write_model_report(bundle):
    ARTIFACTS.mkdir(exist_ok=True)
    bundle.scores.to_csv(ARTIFACTS/'evaluation_metrics.csv', index=False, encoding='utf-8-sig')
    bundle.evaluation.to_csv(ARTIFACTS/'evaluation_rows.csv', index=False, encoding='utf-8-sig')
    m = bundle.metadata
    text = ('# Kết quả huấn luyện từ MySQL\n\n'
            f"Nguồn: `{m['source']}`. Thời điểm: {m['created_utc']}.\n\n"
            f"Feature: {m['features']}. Cửa sổ tỷ trọng: {m['allocation_window']} (0 = toàn quá khứ).\n\n"
            'Đánh giá test một bước, estimator cố định trước test. Không phải metric forecast 3/6 bước.\n'
            'Track/album là dự báo phân bổ. Dữ liệu/giả định xem data_audit.md và methodology.md.\n\n'
            '```text\n'+bundle.scores.to_string(index=False)+'\n```\n\n'
            'MAE/RMSE càng thấp càng tốt; MSE đơn vị bình phương. Không khẳng định ML thắng baseline.\n'
            'Nhóm positive_actual chỉ dùng chẩn đoán sau dự báo. macro_seen_MAE chỉ có MAE.\n')
    (ROOT/'docs/model_results.md').write_text(text, encoding='utf-8')
