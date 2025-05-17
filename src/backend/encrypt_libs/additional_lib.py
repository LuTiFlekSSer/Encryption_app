import ctypes
import os
from typing import Callable

import win32api

from src.backend.encrypt_libs.encrypt_lib import LibStatus
from src.utils.config import Config, TExtraFunc


class AdditionalLib:
    def __init__(self, lib_path: str):
        self._load_status: LibStatus = LibStatus.SUCCESS
        try:
            lib: int = win32api.LoadLibrary(lib_path)
        except Exception:
            self._load_status = LibStatus.LOAD_LIB_ERROR
            return

        self._funcs: dict[TExtraFunc, Callable] = {}
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
    def funcs(self) -> dict[TExtraFunc, Callable]:
        return self._funcs


# if __name__ == '__main__':
#     os.environ['PATH'] = f'{os.path.abspath('../../../encryption_algs/libs/release/')}{os.pathsep}{os.environ['PATH']}'
#
#     key_type = ctypes.c_uint8 * 32
#     key = key_type(*[i for i in range(32)])
#     KS = ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8))()
#
#     data_type = ctypes.c_uint8 * 8
#     data = data_type(*[i for i in range(8)])
#
#     aboba = AdditionalLib('../../../encryption_algs/libs/release/libmagma-base.dll')
#     if aboba._load_status == LibStatus.SUCCESS:
#         print('Success')
#         aboba.funcs['magma_init']()
#         res = aboba.funcs['magma_generate_keys'](key, ctypes.byref(KS))
#         print('Key gen' if res == 0 else 'Key err')
#         aboba.funcs['magma_encrypt_data'](KS, data, data)
#         aboba.funcs['magma_decrypt_data'](KS, data, data)
#         aboba.funcs['magma_finalize'](KS)
#         print(list(data))
#
#     else:
#         print(aboba._load_status)
