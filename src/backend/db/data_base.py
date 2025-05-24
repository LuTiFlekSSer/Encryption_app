import os
import sqlite3
import uuid
from os import cpu_count
from threading import Lock
from typing import Literal, List

from PyQt5.QtCore import QObject, pyqtSignal

from src.backend.db.db_records import HistoryRecord, PasswordRecord
from src.utils.config import Config
from src.utils.singleton import Singleton

TSettingName = Literal[
    'language',
    'threads',
    'queue_size',
    'window_size',
    'window_mode',
    'theme',
    'history_size',
    'password_cipher',
    'last_input_path'
]


class Events(QObject):
    sig_add_history_record: pyqtSignal = pyqtSignal(str, HistoryRecord)
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
                'input_path' TEXT NOT NULL,
                'output_path' TEXT NOT NULL,
                'status' BOOLEAN NOT NULL,
                'status_description' TEXT NOT NULL,
                'mode' TEXT NOT NULL,
                'operation' BOOLEAN NOT NULL,
                'time' FLOAT NOT NULL
            )
        ''')  # operation  False - decrypt True - encrypt

        curr.execute(f'''
            CREATE TABLE IF NOT EXISTS passwords (
                'name' TEXT PRIMARY KEY NOT NULL,
                'password' BLOB NOT NULL
            )
        ''')

        curr.execute(f'''
            CREATE TABLE IF NOT EXISTS password_signature (
                'signature' BLOB NOT NULL
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
        set_default_value('window_size', '1000 600')
        set_default_value('window_mode', 'normal')
        set_default_value('theme', 'AUTO')
        set_default_value('history_size', '1000')
        set_default_value('password_cipher', '')
        set_default_value('last_input_path', '.')

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

            curr.execute(
                '''INSERT INTO history (input_path, output_path, status, status_description, mode, operation, time)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''', record.get_data())
            self._connection.commit()

            self.events.sig_add_history_record.emit(str(uuid.uuid4()), record)
            self._strip_history()

    def get_history(self) -> List[HistoryRecord]:
        with self._lock:
            curr = self._connection.cursor()

            curr.execute('''SELECT idx, input_path, output_path, status, status_description, mode, operation, time
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

    def add_password(self, record: PasswordRecord):
        with self._lock:
            curr = self._connection.cursor()

            curr.execute('''SELECT 1
                            FROM passwords
                            WHERE name = ? LIMIT 1''', (record.name,))

            if curr.fetchone() is None:
                curr.execute('''INSERT INTO passwords (name, password)
                                VALUES (?, ?)''', record.get_data())
            else:
                raise ValueError
            self._connection.commit()

    def get_password(self, name: str) -> bytes:
        with self._lock:
            curr = self._connection.cursor()

            curr.execute('''SELECT password
                            FROM passwords
                            WHERE name = ?''', (name,))
            password = curr.fetchall()
            self._connection.commit()

            if len(password) == 0:
                raise ValueError

            return password[0][0]

    def get_all_passwords(self) -> List[PasswordRecord]:
        with self._lock:
            curr = self._connection.cursor()

            curr.execute('''SELECT name, password
                            FROM passwords''')
            passwords = curr.fetchall()
            self._connection.commit()

            records = []
            for record in passwords:
                password_record = PasswordRecord()
                password_record.set_data(*record)
                records.append(password_record)

            return records

    def remove_password(self, name: str):
        with self._lock:
            curr = self._connection.cursor()

            curr.execute('''SELECT 1
                            FROM passwords
                            WHERE name = ? LIMIT 1''', (name,))

            if curr.fetchone() is not None:
                curr.execute('''DELETE
                                FROM passwords
                                WHERE name = ?''', (name,))
            else:
                raise ValueError

            self._connection.commit()

    def remove_all_passwords(self):
        with self._lock:
            curr = self._connection.cursor()

            curr.execute('''DELETE
                            FROM passwords''')
            self._connection.commit()

    def get_password_signature(self) -> bytes:
        with self._lock:
            curr = self._connection.cursor()

            curr.execute('''SELECT signature
                            FROM password_signature''')
            signature = curr.fetchall()
            self._connection.commit()

            if len(signature) == 0:
                raise ValueError

            return signature[0][0]

    def set_password_signature(self, signature: bytes):
        with self._lock:
            curr = self._connection.cursor()

            curr.execute('''SELECT 1
                            FROM password_signature LIMIT 1''')

            if curr.fetchone() is None:
                curr.execute('''INSERT INTO password_signature (signature)
                                VALUES (?)''', (signature,))
            else:
                curr.execute('''UPDATE password_signature
                                SET signature = ?''', (signature,))

            self._connection.commit()