import ctypes
import hashlib
import os
import time
from collections import defaultdict
from concurrent.futures import Future
from concurrent.futures.thread import ThreadPoolExecutor
from enum import Enum
from threading import Lock
from typing import Callable, Optional

from PyQt5.QtCore import QObject, pyqtSignal

from src.backend.db.data_base import DataBase
from src.backend.db.db_records import HistoryRecord, OperationType
from src.backend.encrypt_libs.additional_lib import AdditionalLib
from src.backend.encrypt_libs.encrypt_lib import EncryptLib, LibStatus, EncryptResult
from src.backend.encrypt_libs.errors import AddTaskError, FileError, SignatureError, FunctionNotFoundError, \
    InvalidKeyError
from src.global_flags import GlobalFlags
from src.utils.config import Config, TExtraFunc
from src.utils.singleton import Singleton


class ReadCipher(Enum):
    SUCCESS = 0
    FILE_ERROR = 1
    SIGNATURE_ERROR = 2


class Events(QObject):
    sig_task_start: pyqtSignal = pyqtSignal(str, float)
    sig_update_progress: pyqtSignal = pyqtSignal(str, int, int)
    sig_update_status: pyqtSignal = pyqtSignal(str, EncryptResult)
    sig_update: pyqtSignal = pyqtSignal()


class TTask:
    def __init__(self,
                 current: ctypes.c_uint64,
                 total: ctypes.c_uint64,
                 output_path: str,
                 input_path: str,
                 uid: str,
                 mode: str,
                 operation: OperationType
                 ):
        self.uid: str = uid
        self.current: ctypes.c_uint64 = current
        self.total: ctypes.c_uint64 = total
        self.future: Optional[Future] = None
        self.input_path: str = input_path
        self.output_path: str = output_path
        self.last_progress: int = -228
        self.mode: str = mode
        self.operation: OperationType = operation


class Loader(metaclass=Singleton):
    events = Events()

    def __init__(self):
        super().__init__()
        path_to_libs: str = Config.LIBS_PATH
        os.environ['PATH'] = f'{os.path.abspath(path_to_libs)}{os.pathsep}{os.environ['PATH']}'
        if not os.path.exists(path_to_libs):
            os.makedirs(path_to_libs, exist_ok=True)

        self._libs: dict[str, EncryptLib] = {}
        self._extra_libs: dict[TExtraFunc, Callable] = {}
        self._db: DataBase = DataBase()
        self._pool: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=int(self._db.get_setting('queue_size')))
        self._lock: Lock = Lock()
        self._running: defaultdict[str, int] = defaultdict(int)
        self._file_sizes: dict[str, int] = {}
        self._output_files: set[str] = set()
        self._queue: set[TTask] = set()
        self._last_update: float = 0
        self._global_flags: GlobalFlags = GlobalFlags()

        for file_name in os.listdir(path_to_libs):
            if file_name.endswith('.dll'):
                cur_lib = EncryptLib(path_to_libs + file_name)

                match cur_lib.load_status:
                    case LibStatus.LOAD_LIB_ERROR:
                        pass
                    case LibStatus.GET_INFO_ERROR:
                        extra_lib = AdditionalLib(path_to_libs + file_name)
                        if extra_lib.load_status == LibStatus.SUCCESS:
                            self._extra_libs.update(extra_lib.funcs)
                    case _:
                        self._libs[f'{cur_lib.cipher}-{cur_lib.mode}'] = cur_lib

    def _get_cipher(self, file_path: str) -> str:
        if 'read_cipher_from_file' not in self._extra_libs:
            raise FunctionNotFoundError

        cipher_info = ctypes.create_string_buffer(256)
        res = self._extra_libs['read_cipher_from_file'](file_path, cipher_info)

        match res:
            case ReadCipher.FILE_ERROR:
                raise FileError
            case ReadCipher.SIGNATURE_ERROR:
                raise SignatureError
            case _:
                return cipher_info.value.decode('utf-8')

    def micro_magma(self, password: str, text: bytes, op: OperationType) -> bytes:
        if any(func not in self._extra_libs for func in
               ['magma_init', 'magma_generate_keys', 'magma_encrypt_data', 'magma_decrypt_data', 'magma_finalize']):
            raise FunctionNotFoundError  # Magma-base не найдена

        if len(text) == 0:
            raise ValueError

        key_type = ctypes.c_uint8 * 32  # todo Сделать нормально после PBKDF2
        key = hashlib.sha512(password.encode()).digest()
        key = key_type(*key[:32])

        KS = ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8))()

        self._extra_libs['magma_init']()
        res = self._extra_libs['magma_generate_keys'](key, ctypes.byref(KS))
        if res != 0:
            raise InvalidKeyError  # Не сгенерил ключи

        byte_text = bytearray(text)
        if op == OperationType.ENCRYPT:
            metadata = bytearray([128] + [0] * (8 - (len(byte_text) % 8) - 1))
            byte_text += metadata

        result = bytearray(len(byte_text))
        data_type = ctypes.c_uint8 * 8

        for i in range(len(byte_text) // 8):
            data = data_type(*byte_text[i * 8:(i + 1) * 8])

            if op == OperationType.ENCRYPT:
                self._extra_libs['magma_encrypt_data'](KS, data, data)
            else:
                self._extra_libs['magma_decrypt_data'](KS, data, data)

            result[i * 8:(i + 1) * 8] = bytes(data)

        self._extra_libs['magma_finalize'](KS)
        if op == OperationType.DECRYPT:
            idx = -1
            while result[idx] != 128:
                idx -= 1
            result = result[:idx]

        return bytes(result)

    def micro_kyznechik(self, password: str, text: bytes, op: OperationType) -> bytes:
        if any(func not in self._extra_libs for func in
               ['kyznechik_init', 'kyznechik_generate_keys', 'kyznechik_encrypt_data', 'kyznechik_decrypt_data',
                'kyznechik_finalize']):
            raise FunctionNotFoundError  # Kyznechik-base не найден

        if len(text) == 0:
            raise ValueError

        key_type = ctypes.c_uint8 * 32  # todo Сделать нормально после PBKDF2
        key = hashlib.sha512(password.encode()).digest()
        key = key_type(*key[:32])

        KS = ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8))()

        self._extra_libs['kyznechik_init']()
        res = self._extra_libs['kyznechik_generate_keys'](key, ctypes.byref(KS))
        if res != 0:
            raise InvalidKeyError  # Не сгенерил ключи

        byte_text = bytearray(text)
        if op == OperationType.ENCRYPT:
            metadata = bytearray([128] + [0] * (16 - (len(byte_text) % 16) - 1))
            byte_text += metadata

        result = bytearray(len(byte_text))
        data_type = ctypes.c_uint8 * 16

        for i in range(len(byte_text) // 16):
            data = data_type(*byte_text[i * 16:(i + 1) * 16])

            if op == OperationType.ENCRYPT:
                self._extra_libs['kyznechik_encrypt_data'](KS, data, data)
            else:
                self._extra_libs['kyznechik_decrypt_data'](KS, data, data)

            result[i * 16:(i + 1) * 16] = bytes(data)

        self._extra_libs['kyznechik_finalize'](KS)
        if op == OperationType.DECRYPT:
            idx = -1
            while result[idx] != 128:
                idx -= 1
            result = result[:idx]

        return bytes(result)

    def check_encrypt_file(self, file_in_path: str, file_out_path: str):
        with self._lock:
            if file_in_path in self._output_files or \
                    file_out_path in self._output_files or \
                    file_out_path in self._running:
                raise AddTaskError

    def check_decrypt_file(self, file_in_path: str, file_out_path: str) -> str:
        with self._lock:
            if file_in_path in self._output_files or \
                    file_out_path in self._output_files or \
                    file_out_path in self._running:
                raise AddTaskError

            return self._get_cipher(file_in_path)

    def encrypt(self,
                mode: str,
                file_in_path: str,
                file_out_path: str,
                hash_password: str,
                uid: str):
        cur = ctypes.c_uint64(0)
        total = ctypes.c_uint64(1)
        key = bytearray(hashlib.sha512(hash_password.encode()).digest())  # todo sha512 -> PBKDF2
        drive, _ = os.path.splitdrive(file_out_path)
        threads = int(self._db.get_setting('threads'))

        task = TTask(
            current=cur,
            total=total,
            output_path=file_out_path,
            input_path=file_in_path,
            uid=uid,
            mode=mode,
            operation=OperationType.ENCRYPT
        )
        with self._lock:
            self._global_flags.is_running.set()

            future = self._pool.submit(self._execute_task,
                                       self._libs[mode].encrypt,
                                       file_in_path,
                                       drive,
                                       file_out_path,
                                       key,
                                       threads,
                                       ctypes.byref(cur),
                                       ctypes.byref(total),
                                       task)

            task.future = future

            self._running[file_in_path] += 1
            self._output_files.add(file_out_path)

    def decrypt(self,
                mode: str,
                file_in_path: str,
                file_out_path: str,
                hash_password: str,
                uid: str):
        if mode not in self._libs:
            raise FunctionNotFoundError

        cur = ctypes.c_uint64(0)
        total = ctypes.c_uint64(1)
        key = bytearray(hashlib.sha512(hash_password.encode()).digest())  # todo sha512 -> PBKDF2
        drive, _ = os.path.splitdrive(file_out_path)
        threads = int(self._db.get_setting('threads'))

        task = TTask(
            current=cur,
            total=total,
            output_path=file_out_path,
            input_path=file_in_path,
            uid=uid,
            mode=mode,
            operation=OperationType.DECRYPT
        )
        with self._lock:
            self._global_flags.is_running.set()

            future = self._pool.submit(self._execute_task,
                                       self._libs[mode].decrypt,
                                       file_in_path,
                                       drive,
                                       file_out_path,
                                       key,
                                       threads,
                                       ctypes.byref(cur),
                                       ctypes.byref(total),
                                       task)

            task.future = future

            self._running[file_in_path] += 1
            self._output_files.add(file_out_path)

    def _execute_task(self,
                      func: Callable,
                      file_in_path: str,
                      drive: str,
                      file_out_path: str,
                      key: bytearray,
                      num_threads: int,
                      cur_progress: ctypes.POINTER(ctypes.c_uint64),
                      total_progress: ctypes.POINTER(ctypes.c_uint64),
                      task: TTask
                      ) -> EncryptResult:
        with self._lock:
            self.events.sig_task_start.emit(task.uid, time.time())
            self._queue.add(task)
            self._file_sizes[task.input_path] = os.path.getsize(task.input_path)

        return func(file_in_path,
                    drive,
                    file_out_path,
                    key,
                    num_threads,
                    cur_progress,
                    total_progress)

    @property
    def status(self) -> dict[str, LibStatus]:
        st: dict[str, LibStatus] = {}
        for key in self._libs:
            st[key] = self._libs[key].load_status
        return st

    @property
    def available_modes(self) -> dict[str, list[str]]:
        st: dict[str, list[str]] = {}
        for value in self._libs.values():
            if value.load_status == LibStatus.SUCCESS:
                st.setdefault(value.cipher, []).append(value.mode)
        return st

    def get_file_size(self, path: str) -> int:
        with self._lock:
            if path in self._file_sizes:
                return self._file_sizes[path]
            else:
                raise FileNotFoundError

    def exec(self):
        with self._lock:
            if self._last_update + Config.UPDATE_INTERVAL < (lt := time.time()):
                self.events.sig_update.emit()
                self._last_update = lt

            to_remove = set()

            for task in self._queue:
                if (last_progres := (int(task.current.value /
                                         (task.total.value + 0.00001) * 100))) != task.last_progress:
                    self.events.sig_update_progress.emit(task.uid,
                                                         task.current.value,
                                                         task.total.value)
                    task.last_progress = last_progres

                if task.future.done():
                    self._file_sizes.pop(task.input_path)
                    self.events.sig_update_status.emit(task.uid, task.future.result())

                    record = HistoryRecord()
                    record.input_path = task.input_path
                    record.output_path = task.output_path
                    record.status = task.future.result() == EncryptResult.SUCCESS
                    record.status_description = task.future.result().name
                    record.mode = task.mode
                    record.operation = task.operation
                    record.time = time.time()

                    self._db.add_history_record(record)

                    to_remove.add(task)

                    self._running[task.input_path] -= 1
                    if self._running[task.input_path] == 0:
                        del self._running[task.input_path]

                    self._output_files.remove(task.output_path)

            self._queue -= to_remove
            if len(self._queue) == 0:
                self._global_flags.is_running.clear()


TMicroFunc = Callable[[str, bytes, OperationType], bytes]
_micro_ciphers: dict[str, TMicroFunc] = {
    'magma': Loader().micro_magma,
    'kyznechik': Loader().micro_kyznechik
}
micro_ciphers: dict[str, TMicroFunc] = {}

for key, func in _micro_ciphers.items():
    try:
        func('1', b'1', OperationType.ENCRYPT)
        micro_ciphers[key] = func
    except:
        pass

if __name__ == '__main__':
    loader = Loader()
    aboba = 'НАШ Слава Богу 🙏❤СЛАВА РОССИИ 🙏❤АНГЕЛА ХРАНИТЕЛЯ КАЖДОМУ ИЗ ВАС 🙏❤БОЖЕ ХРАНИ РОССИЮ 🙏❤СПАСИБО ВАМ НАШИ МАЛЬЧИКИ'.encode(
        'utf-8')
    print(aboba.hex())
    aboba = loader.micro_magma('sosal', aboba, OperationType.ENCRYPT)
    print(aboba.hex())
    aboba = loader.micro_magma('sosal', aboba, OperationType.DECRYPT)
    print(aboba.hex())
