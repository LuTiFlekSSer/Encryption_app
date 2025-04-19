import os
import sqlite3
from os import cpu_count
from typing import Literal

from src.utils.config import Config
from src.utils.singleton import Singleton

TSettingName = Literal[
    'language',
    'threads',
    'queue_size',
    'window_size',
    'window_mode',
    'theme'
]


class DataBase(metaclass=Singleton):
    def __init__(self):
        super().__init__()

        self._path_to_db: str = Config.DB_PATH
        self._data_base_file: str = Config.DB_FILENAME

        if not os.path.exists(self._path_to_db):
            os.makedirs(self._path_to_db, exist_ok=True)

        self._connection = sqlite3.connect(f'{self._path_to_db}/{self._data_base_file}')

        self._create_db()

    def _create_db(self):
        curr = self._connection.cursor()

        curr.execute(f'''
            CREATE TABLE IF NOT EXISTS settings (
                'name' TEXT PRIMARY KEY NOT NULL,
                'value' TEXT NOT NULL
            )
        ''')

        def set_default_value(name: TSettingName, value: str):
            curr.execute(f'''
                        INSERT INTO settings
                        SELECT '{name}', '{value}'
                        WHERE '{name}' NOT IN (SELECT name FROM settings)
                    ''')

        set_default_value('language', 'None')
        set_default_value('threads', f'{cpu_count()}')
        set_default_value('queue_size', '2')
        set_default_value('window_size', '950 600')
        set_default_value('window_mode', 'normal')
        set_default_value('theme', 'AUTO')


        self._connection.commit()

    def set_setting(self, setting: TSettingName, value: str):
        curr = self._connection.cursor()

        curr.execute('''UPDATE settings
                        SET value = ?
                        WHERE name = ? ''', (value, setting))
        self._connection.commit()

    def get_setting(self, setting: TSettingName) -> str:
        curr = self._connection.cursor()

        curr.execute('''SELECT value
                        FROM settings
                        WHERE name = ?''', (setting,))
        setting = curr.fetchall()
        self._connection.commit()

        if len(setting) == 0:
            raise ValueError

        return setting[0][0]
