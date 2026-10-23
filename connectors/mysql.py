"""One short-lived read-only transaction per repository load, inside its worker."""
from contextlib import contextmanager
import mysql.connector


class AppError(Exception):
    def __init__(self, key, detail=''):
        super().__init__(key)
        self.key, self.detail = key, detail


@contextmanager
def read_connection(config):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=config.host, port=config.port, user=config.user,
            database=config.database, password=config.password,
            connection_timeout=7, read_timeout=30, write_timeout=30,
            use_pure=True, autocommit=False, charset='utf8mb4')
        connection.start_transaction(isolation_level='REPEATABLE READ',
                                     readonly=True, consistent_snapshot=True)
        yield connection
    except mysql.connector.Error as exc:
        key = ('auth_error' if exc.errno in (1045, 1698) else
               'database_error' if exc.errno == 1049 else 'connection_error')
        # Server messages may echo user configuration. Only expose a numeric code.
        raise AppError(key, str(exc.errno or 'MySQL')) from None
    finally:
        if connection is not None:
            try:
                connection.rollback()
            finally:
                connection.close()
