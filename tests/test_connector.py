import unittest
from unittest.mock import patch
import mysql.connector
from config.settings import DatabaseConfig
from connectors.mysql import read_connection, AppError


class ConnectorTests(unittest.TestCase):
    def test_config_rereads_local_file_without_global_secret_side_effects(self):
        import os
        with patch.dict(os.environ, {}, clear=True), patch('config.settings.dotenv_values', side_effect=[
                {'MYSQL_DATABASE':'chinook','MYSQL_PASSWORD':'test_first'},
                {'MYSQL_DATABASE':'chinook','MYSQL_PASSWORD':'test_changed'}]):
            self.assertEqual(DatabaseConfig.from_env().password, 'test_first')
            self.assertEqual(DatabaseConfig.from_env().password, 'test_changed')
            self.assertNotIn('MYSQL_PASSWORD', os.environ)

    def test_process_config_takes_precedence_over_local_file(self):
        with patch.dict('os.environ', {'MYSQL_DATABASE':'process_db'}, clear=True), patch(
                'config.settings.dotenv_values', return_value={'MYSQL_DATABASE':'file_db'}):
            self.assertEqual(DatabaseConfig.from_env().database, 'process_db')

    def test_transaction_is_readonly_and_always_closed(self):
        class Connection:
            rolled_back = closed = False
            def start_transaction(self, **kwargs): self.options = kwargs
            def rollback(self): self.rolled_back = True
            def close(self): self.closed = True
        connection = Connection()
        with patch('connectors.mysql.mysql.connector.connect', return_value=connection):
            with self.assertRaises(RuntimeError):
                with read_connection(DatabaseConfig()): raise RuntimeError('test')
        self.assertTrue(connection.options['readonly'])
        self.assertTrue(connection.options['consistent_snapshot'])
        self.assertTrue(connection.rolled_back and connection.closed)

    def test_server_message_is_not_exposed(self):
        error = mysql.connector.Error(msg='sensitive connection information', errno=1045)
        with patch('connectors.mysql.mysql.connector.connect', side_effect=error):
            with self.assertRaises(AppError) as ctx:
                with read_connection(DatabaseConfig()): pass
        self.assertEqual(ctx.exception.key, 'auth_error')
        self.assertEqual(ctx.exception.detail, '1045')
        self.assertNotIn('sensitive', str(ctx.exception))
