import ctypes
import os
import tempfile
from enum import Enum
from typing import Callable

import win32api

from src.utils.config import Config


class LibStatus(Enum):
    SUCCESS = 0
    LOAD_LIB_ERROR = 1
    GET_INFO_ERROR = 2
    LOAD_FUNCS_ERROR = 3
    TEST_ERROR = 4


class EncryptResult(Enum):
    SUCCESS = 0
    DISK_INFO_FAILURE = 1
    FILE_OPEN_FAILURE = 2
    FILE_SIZE_FAILURE = 3
    INSUFFICIENT_DISK_SPACE = 4
    OUTPUT_FILE_RESIZE_ERROR = 5
    METADATA_PROCESSING_ERROR = 6
    THREAD_CREATION_FAILURE = 7
    KEY_CREATION_FAILURE = 8
    ENCRYPTION_FILE_PROCESSING_ERROR = 9
    ENCRYPTION_MEMORY_ALLOCATION_ERROR = 10
    ENCRYPTION_FINAL_BYTES_ERROR = 11
    WRONG_PASSWORD = 12


class EncryptLib:
    def __init__(self, lib_path: str):
        self._load_status: LibStatus = LibStatus.SUCCESS
        self._cipher: str = ''
        self._mode: str = ''

        try:
            lib: int = win32api.LoadLibrary(lib_path)
        except Exception:
            self._load_status = LibStatus.LOAD_LIB_ERROR
            return

        try:
            get_cipher_address: int = win32api.GetProcAddress(lib, 'get_cipher_name')
            get_mode_address: int = win32api.GetProcAddress(lib, 'get_mode_name')

            self._cipher: str = ctypes.CFUNCTYPE(ctypes.c_char_p)(get_cipher_address)().decode('utf-8')
            self._mode: str = ctypes.CFUNCTYPE(ctypes.c_char_p)(get_mode_address)().decode('utf-8')
        except Exception:
            self._load_status = LibStatus.GET_INFO_ERROR
            return

        try:
            encrypt_address: int = win32api.GetProcAddress(lib, f'encrypt_{self._cipher}_{self._mode}')
            decrypt_address: int = win32api.GetProcAddress(lib, f'decrypt_{self._cipher}_{self._mode}')
            func_type = ctypes.CFUNCTYPE(ctypes.c_uint8,
                                         ctypes.c_wchar_p,
                                         ctypes.c_wchar_p,
                                         ctypes.c_wchar_p,
                                         ctypes.POINTER(ctypes.c_uint8),
                                         ctypes.c_uint16,
                                         ctypes.POINTER(ctypes.c_uint64),
                                         ctypes.POINTER(ctypes.c_uint64))

            self._encrypt_func: Callable = func_type(encrypt_address)
            self._decrypt_func: Callable = func_type(decrypt_address)

        except Exception:
            self._load_status = LibStatus.LOAD_FUNCS_ERROR
            return

        with (tempfile.TemporaryFile(mode='wb', delete=False) as enc_file,
              tempfile.TemporaryFile(mode='w', delete=False) as dec_file):
            enc_file_path = enc_file.name
            dec_file_path = dec_file.name

            test_text = os.urandom(Config.TEST_FILE_SIZE)
            enc_file.write(test_text)

            enc_file.flush()

        drive, _ = os.path.splitdrive(enc_file_path)

        key_type = ctypes.c_uint8 * 32
        key = key_type(*os.urandom(32))

        self._encrypt_func(enc_file_path,
                           drive,
                           dec_file_path,
                           key,
                           1,
                           ctypes.byref(ctypes.c_uint64(0)),
                           ctypes.byref(ctypes.c_uint64(0)))
        self._decrypt_func(dec_file_path,
                           drive,
                           enc_file_path,
                           key,
                           1,
                           ctypes.byref(ctypes.c_uint64(0)),
                           ctypes.byref(ctypes.c_uint64(0)))

        with open(enc_file_path, 'rb') as f:
            enc_test_text = f.read()
            if enc_test_text != test_text:
                self._load_status = LibStatus.TEST_ERROR
                return

        os.remove(enc_file_path)
        os.remove(dec_file_path)

    @property
    def load_status(self) -> LibStatus:
        return self._load_status

    @property
    def cipher(self) -> str:
        return self._cipher

    @property
    def mode(self) -> str:
        return self._mode

    def encrypt(self,
                file_in_path: str,
                disk_out_name: str,
                file_out_path: str,
                key: bytearray,
                num_threads: int,
                cur_progress: ctypes.POINTER(ctypes.c_uint64),
                total_progress: ctypes.POINTER(ctypes.c_uint64)
                ) -> EncryptResult:
        return EncryptResult(self._encrypt_func(file_in_path,
                                                disk_out_name,
                                                file_out_path,
                                                (ctypes.c_uint8 * len(key)).from_buffer(key),
                                                num_threads,
                                                cur_progress,
                                                total_progress))

    def decrypt(self,
                file_in_path: str,
                disk_out_name: str,
                file_out_path: str,
                key: bytearray,
                num_threads: int,
                cur_progress: ctypes.POINTER(ctypes.c_uint64),
                total_progress: ctypes.POINTER(ctypes.c_uint64)
                ) -> EncryptResult:
        return EncryptResult(self._decrypt_func(file_in_path,
                                                disk_out_name,
                                                file_out_path,
                                                (ctypes.c_uint8 * len(key)).from_buffer(key),
                                                num_threads,
                                                cur_progress,
                                                total_progress))
