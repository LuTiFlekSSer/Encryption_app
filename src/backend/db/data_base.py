import os
import sqlite3
from os import cpu_count
from threading import Lock
from typing import Literal, List

from PyQt5.QtCore import QObject, pyqtSignal

from src.backend.db.db_records import HistoryRecord
from src.utils.config import Config
from src.utils.singleton import Singleton

TSettingName = Literal[
    'language',
    'threads',
    'queue_size',
    'window_size',
    'window_mode',
    'theme',
    'history_size'
]


class Events(QObject):
    sig_add_history_record: pyqtSignal = pyqtSignal(HistoryRecord)
    sig_strip_last_history_records: pyqtSignal = pyqtSignal(int)


class DataBase(metaclass=Singleton):
    events = Events()

    def __init__(self):
        super().__init__()

        self._path_to_db: str = Config.DB_PATH
        self._data_base_file: str = Config.DB_FILENAME
        self._lock: Lock = Lock()
        self._max_history_size: int = 0

        if not os.path.exists(self._path_to_db):
            os.makedirs(self._path_to_db, exist_ok=True)

        self._connection = sqlite3.connect(f'{self._path_to_db}/{self._data_base_file}', check_same_thread=False)

        self._create_db()

    def _create_db(self):
        curr = self._connection.cursor()

        curr.execute(f'''
            CREATE TABLE IF NOT EXISTS settings (
                'name' TEXT PRIMARY KEY NOT NULL,
                'value' TEXT NOT NULL
            )
        ''')

        curr.execute(f'''
            CREATE TABLE IF NOT EXISTS history (
                'idx' INTEGER PRIMARY KEY ASC,
                'path' TEXT NOT NULL,
                'status' BOOLEAN NOT NULL,
                'status_description' TEXT NOT NULL,
                'mode' TEXT NOT NULL,
                'operation' BOOLEAN NOT NULL,
                'time' FLOAT NOT NULL
            )
        ''')  # operation  False - decrypt True - encrypt

        def set_default_value(name: TSettingName, value: str):
            curr.execute(f'''
                        INSERT INTO settings
                        SELECT '{name}', '{value}'
                        WHERE '{name}' NOT IN (SELECT name FROM settings)
                    ''')

        set_default_value('language', 'None')
        set_default_value('threads', f'{cpu_count()}')
        set_default_value('queue_size', '2')
        set_default_value('window_size', '1000 600')
        set_default_value('window_mode', 'normal')
        set_default_value('theme', 'AUTO')
        set_default_value('history_size', '1000')

        self._max_history_size = int(self.get_setting('history_size'))
        self._strip_history()

        self._connection.commit()

    def _strip_history(self):
        curr = self._connection.cursor()

        if curr.execute('''SELECT COUNT(*)
                           FROM history''').fetchone()[0] > self._max_history_size:
            curr.execute('''DELETE
                            FROM history
                            WHERE idx NOT IN (SELECT idx
                                              FROM history
                                              ORDER BY time DESC
                                LIMIT ?)''', (self._max_history_size,))

            self._connection.commit()

            self.events.sig_strip_last_history_records.emit(self._max_history_size)

    def set_setting(self, setting: TSettingName, value: str):
        with self._lock:
            curr = self._connection.cursor()

            curr.execute('''UPDATE settings
                            SET value = ?
                            WHERE name = ? ''', (value, setting))

            self._connection.commit()

            if setting == 'history_size':
                self._max_history_size = int(value)
                self._strip_history()

    def get_setting(self, setting: TSettingName) -> str:
        with self._lock:
            curr = self._connection.cursor()

            curr.execute('''SELECT value
                            FROM settings
                            WHERE name = ?''', (setting,))
            setting = curr.fetchall()
            self._connection.commit()

            if len(setting) == 0:
                raise ValueError

            return setting[0][0]

    def add_history_record(self, record: HistoryRecord):
        with self._lock:
            curr = self._connection.cursor()

            curr.execute('''INSERT INTO history (path, status, status_description, mode, operation, time)
                            VALUES (?, ?, ?, ?, ?, ?)''', record.get_data())
            self._connection.commit()

            self.events.sig_add_history_record.emit(record)
            self._strip_history()

    def get_history(self) -> List[HistoryRecord]:
        with self._lock:
            curr = self._connection.cursor()

            curr.execute('''SELECT path, status, status_description, mode, operation, time
                            FROM history
                            ORDER BY time DESC''')
            history = curr.fetchall()
            self._connection.commit()

            records = []
            for record in history:
                history_record = HistoryRecord()
                history_record.set_data(*record)
                records.append(history_record)

            return records

    def clear_history(self):
        with self._lock:
            curr = self._connection.cursor()

            curr.execute('''DELETE
                            FROM history''')
            self._connection.commit()
