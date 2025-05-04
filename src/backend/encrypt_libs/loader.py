import ctypes
import os
from concurrent.futures import Future
from concurrent.futures.thread import ThreadPoolExecutor
import hashlib
from dataclasses import dataclass
from threading import Lock

from PyQt5.QtCore import QObject, pyqtSignal
from src.backend.db.data_base import DataBase
from src.backend.encrypt_libs.encrypt_lib import EncryptLib, LibStatus
from src.utils.config import Config
from src.utils.singleton import Singleton


class Events(QObject):
    sig_update_progress: pyqtSignal = pyqtSignal(str, int, int)


UInt64Pointer = ctypes.POINTER(ctypes.c_uint64)


@dataclass
class TTask:
    current: ctypes.POINTER(ctypes.c_uint64)
    total: ctypes.POINTER(ctypes.c_uint64)
    future: Future


class Loader(metaclass=Singleton):
    events = Events()

    def __init__(self):
        super().__init__()
        path_to_libs: str = Config.LIBS_PATH
        os.environ['PATH'] = f'{os.path.abspath(path_to_libs)}{os.pathsep}{os.environ['PATH']}'
        if not os.path.exists(path_to_libs):
            os.makedirs(path_to_libs, exist_ok=True)

        self._libs: dict[str, EncryptLib] = {}
        self._db: DataBase = DataBase()
        self._pool: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=int(self._db.get_setting('queue_size')))
        self._lock: Lock = Lock()
        self._running: dict[str, TTask] = {}
        self._in_out: dict[str, str] = {}

        for file_name in os.listdir(path_to_libs):
            if file_name.endswith('.dll'):
                cur_lib = EncryptLib(path_to_libs + file_name)
                match cur_lib.load_status:
                    case LibStatus.LOAD_LIB_ERROR | LibStatus.GET_INFO_ERROR:
                        pass
                    case _:
                        self._libs[f'{cur_lib.cipher}-{cur_lib.mode}'] = cur_lib

    def encrypt(self,
                mode: str,
                file_in_path: str,
                file_out_path: str,
                hash_password: str): # ^-^ Может завтра? ^-^
        if self._in_out[file_in_path]==file_in_path: # Входной файл равен выходному
            raise ValueError

        cur = ctypes.byref(ctypes.c_uint64(0))
        total = ctypes.byref(ctypes.c_uint64(0))
        key = bytearray(hashlib.sha512(hash_password.encode()).digest())  # todo sha512 -> PBKDF2
        drive, _ = os.path.splitdrive(file_out_path)
        threads = int(self._db.get_setting('threads'))

        self._pool.submit(self._libs[mode].encrypt,
                          file_in_path,
                          drive,
                          file_out_path,
                          key,
                          threads,
                          cur,
                          total)

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

    def exec(self):
        pass
