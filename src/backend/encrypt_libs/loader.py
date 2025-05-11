import ctypes
import hashlib
import os
import time
from collections import defaultdict
from concurrent.futures import Future
from concurrent.futures.thread import ThreadPoolExecutor
from threading import Lock
from typing import Callable, Optional

from PyQt5.QtCore import QObject, pyqtSignal

from src.backend.db.data_base import DataBase
from src.backend.encrypt_libs.encrypt_lib import EncryptLib, LibStatus, EncryptResult
from src.backend.encrypt_libs.errors import AddTaskError
from src.frontend.sub_windows.file_adder_window.file_adder_window import Status
from src.utils.config import Config
from src.utils.singleton import Singleton


class Events(QObject):
    sig_update_progress: pyqtSignal = pyqtSignal(str, int, int)
    sig_update_status: pyqtSignal = pyqtSignal(str, Status)
    sig_update: pyqtSignal = pyqtSignal()


class TTask:
    def __init__(self,
                 current: ctypes.c_uint64,
                 total: ctypes.c_uint64,
                 output_path: str,
                 input_path: str,
                 ):
        self.current: ctypes.c_uint64 = current
        self.total: ctypes.c_uint64 = total
        self.future: Optional[Future] = None
        self.input_path: str = input_path
        self.output_path: str = output_path
        self.last_progress: int = -228


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
        self._running: defaultdict[str, int] = defaultdict(int)
        self._output_files: set[str] = set()
        self._queue: set[TTask] = set()
        self._last_update: float = 0

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
                hash_password: str):
        with self._lock:
            if file_in_path in self._output_files or \
                    file_out_path in self._output_files or \
                    file_out_path in self._running:
                raise AddTaskError
        # todo если что-то запущено, то нужно поставить флажок в процессе
        cur = ctypes.c_uint64(0)
        total = ctypes.c_uint64(0)
        key = bytearray(hashlib.sha512(hash_password.encode()).digest())  # todo sha512 -> PBKDF2
        drive, _ = os.path.splitdrive(file_out_path)
        threads = int(self._db.get_setting('threads'))

        task = TTask(
            current=cur,
            total=total,
            output_path=file_out_path,
            input_path=file_in_path
        )
        with self._lock:
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
            self._queue.add(task)

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

    def exec(self):
        with self._lock:
            if self._last_update + Config.UPDATE_INTERVAL > (lt := time.time()):
                self.events.sig_update.emit()
                self._last_update = lt

            to_remove = set()

            for task in self._queue:
                if (last_progres := (task.current.value // task.current.value * 100)) != task.last_progress:
                    self.events.sig_update_progress.emit(task.output_path,
                                                         task.current.value,
                                                         task.total.value)
                    task.last_progress = last_progres

                if task.future.done():
                    self.events.sig_update_status.emit(task.output_path,
                                                       Status.COMPLETED if task.future.result() == EncryptResult.SUCCESS
                                                       else Status.FAILED)
                    to_remove.add(task)

                    self._running[task.input_path] -= 1
                    if self._running[task.input_path] == 0:
                        del self._running[task.input_path]

                    self._output_files.remove(task.output_path)

            self._queue -= to_remove
