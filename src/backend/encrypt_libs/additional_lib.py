import ctypes
import os
from typing import Callable

import win32api

from src.backend.encrypt_libs.encrypt_lib import LibStatus
from src.utils.config import Config


class AdditionalLib:
    def __init__(self, lib_path: str):
        self._load_status: LibStatus = LibStatus.SUCCESS
        try:
            lib: int = win32api.LoadLibrary(lib_path)
        except Exception:
            self._load_status = LibStatus.LOAD_LIB_ERROR
            return

        self._funcs: dict[str, Callable] = {}
        find_any: bool = False

        for name, func in Config.EXTRA_FUNCS.items():
            try:
                func_address: int = win32api.GetProcAddress(lib, name)
                self._funcs[name] = func(func_address)
                find_any = True
            except Exception:
                pass

        if not find_any:
            self._load_status = LibStatus.GET_INFO_ERROR
            return

    @property
    def load_status(self) -> LibStatus:
        return self._load_status

    @property
    def funcs(self) -> dict[str, Callable]:
        return self._funcs


if __name__ == '__main__':
    os.environ['PATH'] = f'{os.path.abspath('../../../encryption_algs/libs/release/')}{os.pathsep}{os.environ['PATH']}'

    aboba = AdditionalLib('../../../encryption_algs/libs/release/libutils.dll')
    if aboba._load_status == LibStatus.SUCCESS:
        print('Success')
        hui = ctypes.create_string_buffer(256)
        res = aboba.funcs['read_cipher_from_file']('../../../input.txt', hui)
        print(type(res))
        print(hui.value.decode('utf-8'))

    else:
        print(aboba._load_status)
