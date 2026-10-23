"""Project-relative configuration. Passwords are never persisted by the UI."""
from dataclasses import dataclass, field
from pathlib import Path
import json
import os
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / 'artifacts'
PREFERENCES = ROOT / 'config' / 'preferences.json'


@dataclass(frozen=True)
class DatabaseConfig:
    host: str = 'localhost'
    port: int = 3306
    user: str = 'root'
    database: str = 'chinook'
    password: str = field(default='', repr=False)

    @classmethod
    def from_env(cls):
        # Read on each call without copying secrets into global process state.
        # Explicit process variables take precedence over the local file.
        saved = dotenv_values(ROOT / '.env')
        def value(name, default=''):
            return os.environ.get(name, saved.get(name) or default)
        try:
            port = int(value('MYSQL_PORT', '3306'))
        except ValueError:
            port = 3306
        return cls(value('MYSQL_HOST', 'localhost'), port,
                   value('MYSQL_USER', 'root'), value('MYSQL_DATABASE', 'chinook'),
                   value('MYSQL_PASSWORD'))


def read_preferences():
    try:
        return json.loads(PREFERENCES.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {'language': 'vi'}


def save_language(language):
    PREFERENCES.write_text(json.dumps({'language': language}), encoding='utf-8')
