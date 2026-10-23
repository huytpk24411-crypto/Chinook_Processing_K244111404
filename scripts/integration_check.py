"""Local, read-only MySQL integration. No fixtures or alternative data sources."""
import argparse
from dataclasses import replace
from getpass import getpass
import json
from config.settings import DatabaseConfig, ARTIFACTS
from connectors.mysql import AppError
from repositories.chinook import ChinookRepository
from services.data import audit, build_data, Filters
from services.audit_report import write_audit
from services.model_report import write_model_report
from ml.forecast import train, forecast, eligible
from ml.persistence import save_bundle, load_bundle
from ui.translations import Translator


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ask-password', action='store_true')
    parser.add_argument('--audit-only', action='store_true')
    args = parser.parse_args()
    config = DatabaseConfig.from_env()
    if args.ask_password: config = replace(config, password=getpass('MySQL password (not saved): '))
    try:
        snapshot = ChinookRepository(config).load()
        report = audit(snapshot); write_audit(report)
        print('Live MySQL audit written: docs/data_audit.md')
        print(json.dumps(report['table_counts'], ensure_ascii=False))
        if args.audit_only: return 0
        dates = snapshot.invoices.InvoiceDate
        data = build_data(snapshot, Filters(str(dates.min().date()), str(dates.max().date())))
        data.reconciliation().to_csv(ARTIFACTS/'reconciliation.csv', index=False)
        if not eligible(data):
            print(Translator('en')('insufficient_history'))
            forecast(data, method='mean3').to_csv(ARTIFACTS/'baseline_forecast.csv', index=False)
            return 0
        bundle = train(data); write_model_report(bundle)
        model_path = ARTIFACTS/'revenue_model.json'; save_bundle(bundle, model_path)
        loaded = load_bundle(model_path, data)
        first = forecast(data, bundle, horizon=6)
        second = forecast(data, loaded, horizon=6)
        if not first.equals(second): raise AppError('model_incompatible')
        for horizon in (1,3,6):
            rows = forecast(data, bundle, horizon=horizon)
            rows.to_csv(ARTIFACTS/f'forecast_{horizon}m.csv', index=False, encoding='utf-8-sig')
            check = rows.groupby(['month','scope']).predicted.sum().unstack()
            if (check.total-check.track).abs().max() > .000001 or (check.total-check.album).abs().max() > .000001:
                raise AppError('quality_block')
        print('Training, held-out evaluation, all scopes, 1/3/6 month forecasts and JSON roundtrip passed.')
        return 0
    except AppError as exc:
        print(Translator('en')(exc.key), f'Code: {exc.detail}' if exc.detail else '')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
