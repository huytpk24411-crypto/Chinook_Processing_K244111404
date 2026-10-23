"""SQL lives here. Invoice totals are fetched separately from invoice lines."""
from dataclasses import dataclass
from datetime import datetime, timezone
import re
import pandas as pd
from connectors.mysql import AppError, read_connection


def identifier(name):
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', str(name)):
        raise AppError('schema_error')
    return '`' + name + '`'


def query(connection, sql, params=()):
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return pd.DataFrame(rows, columns=cursor.column_names)
    finally:
        cursor.close()


@dataclass
class Snapshot:
    invoices: pd.DataFrame
    lines: pd.DataFrame
    tracks: pd.DataFrame
    albums: pd.DataFrame
    schema: pd.DataFrame
    relations: pd.DataFrame
    counts: dict
    foreign_key_checks: dict
    source: str = 'mysql'
    read_at: str | None = None


class ChinookRepository:
    def __init__(self, config):
        self.config = config

    def load(self):
        with read_connection(self.config) as conn:
            schema = query(conn, '''SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE,
                IS_NULLABLE, COLUMN_KEY FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s ORDER BY TABLE_NAME, ORDINAL_POSITION''',
                           (self.config.database,))
            relations = query(conn, '''SELECT TABLE_NAME, COLUMN_NAME,
                REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = %s AND REFERENCED_TABLE_NAME IS NOT NULL''',
                              (self.config.database,))
            tables = {str(t).lower(): t for t in schema.TABLE_NAME.unique()}
            needed = {
                'invoice': ['InvoiceId', 'InvoiceDate', 'Total'],
                'invoiceline': ['InvoiceLineId', 'InvoiceId', 'TrackId', 'UnitPrice', 'Quantity'],
                'track': ['TrackId', 'Name', 'AlbumId'],
                'album': ['AlbumId', 'Title'],
            }
            frames = {}
            for table, columns in needed.items():
                if table not in tables:
                    raise AppError('schema_error', table)
                actual = tables[table]
                mapping = {str(c).lower(): c for c in schema.loc[
                    schema.TABLE_NAME == actual, 'COLUMN_NAME']}
                if any(c.lower() not in mapping for c in columns):
                    raise AppError('schema_error', table)
                fields = ', '.join(f'{identifier(mapping[c.lower()])} AS {identifier(c)}'
                                   for c in columns)
                primary = identifier(mapping[columns[0].lower()])
                frames[table] = query(conn, f'SELECT {fields} FROM {identifier(actual)} ORDER BY {primary}')
            counts = {t: int(query(conn, f'SELECT COUNT(*) AS n FROM {identifier(t)}').iloc[0, 0])
                      for t in tables.values()}
            fk_checks = {}
            for row in relations.itertuples(index=False):
                t, c, rt, rc = row
                # Identifiers come exclusively from server metadata, then are validated.
                sql = (f'SELECT COUNT(*) AS n FROM {identifier(t)} a LEFT JOIN '
                       f'{identifier(rt)} b ON a.{identifier(c)} = b.{identifier(rc)} '
                       f'WHERE a.{identifier(c)} IS NOT NULL AND b.{identifier(rc)} IS NULL')
                fk_checks[f'{t}.{c} -> {rt}.{rc}'] = int(query(conn, sql).iloc[0, 0])
            return Snapshot(frames['invoice'], frames['invoiceline'], frames['track'],
                            frames['album'], schema, relations, counts, fk_checks,
                            f'{self.config.host}:{self.config.port}/{self.config.database}',
                            datetime.now(timezone.utc).isoformat())
