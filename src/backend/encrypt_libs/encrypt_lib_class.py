import ctypes
import os
from enum import Enum

import win32api

from src.utils.config import Config


class LibStatus(Enum):
    SUCCESS = 0
    LOAD_LIB_ERROR = 1
    LOAD_INFO_ERROR = 2
    GET_INFO_ERROR = 3
    LOAD_FUNCS_ERROR = 4
    TEST_ERROR = 5


class EncryptLib:
    def __init__(self, lib_path: str):
        self._load_status: LibStatus = LibStatus.SUCCESS
        self._cipher: str = ''
        self._mode: str = ''

        try:
            lib = win32api.LoadLibrary(lib_path)
        except Exception:
            self._load_status = LibStatus.LOAD_LIB_ERROR
            return

        try:
            get_cipher_address = win32api.GetProcAddress(lib, 'get_cipher_name')
            get_mode_address = win32api.GetProcAddress(lib, 'get_mode_name')

            if get_cipher_address and get_mode_address:
                self._cipher = ctypes.CFUNCTYPE(ctypes.c_char_p)(get_cipher_address)().decode('utf-8')
                self._mode = ctypes.CFUNCTYPE(ctypes.c_char_p)(get_mode_address)().decode('utf-8')
            else:
                self._load_status = LibStatus.LOAD_INFO_ERROR
                return
        except Exception:
            self._load_status = LibStatus.GET_INFO_ERROR
            return

        try:
            encrypt_address = win32api.GetProcAddress(lib, f'encrypt_{self._cipher}_{self._mode}')
            decrypt_address = win32api.GetProcAddress(lib, f'decrypt_{self._cipher}_{self._mode}')
            func_type = ctypes.CFUNCTYPE(ctypes.c_uint8,
                                         ctypes.c_wchar_p,
                                         ctypes.c_wchar_p,
                                         ctypes.c_wchar_p,
                                         ctypes.POINTER(ctypes.c_uint8),
                                         ctypes.c_uint16,
                                         ctypes.POINTER(ctypes.c_uint64),
                                         ctypes.POINTER(ctypes.c_uint64))

            self._encrypt_func = func_type(encrypt_address)
            self._decrypt_func = func_type(decrypt_address)

        except Exception:
            self._load_status = LibStatus.LOAD_FUNCS_ERROR
            return

        enc_file_name: str = Config.TEST_FILE_ENCRYPT
        dec_file_name: str = Config.TEST_FILE_DECRYPT
        enc_file = open(enc_file_name, 'wb')
        dec_file = open(dec_file_name, 'w')
        dec_file.close()

        test_text = os.urandom(Config.TEST_FILE_SIZE)
        enc_file.write(test_text)
        enc_file.close()

        enc_file_path = os.path.join(os.path.abspath("."), enc_file_name)
        dec_file_path = os.path.join(os.path.abspath("."), dec_file_name)
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

        with open(enc_file_name, 'rb') as f:
            enc_test_text = f.read()
            if enc_test_text != test_text:
                self._load_status = LibStatus.TEST_ERROR
                return

        os.remove(enc_file_name)
        os.remove(dec_file_name)

    def encrypt(self,
                file_in_path: str,
                disk_out_name: str,
                file_out_path: str,
                key: bytearray,
                num_threads: int,
                ):
        return self._encrypt_func(file_in_path,
                                  disk_out_name,
                                  file_out_path,
                                  key,
                                  num_threads,
                                  ctypes.byref(ctypes.c_uint64(0)),
                                  ctypes.byref(ctypes.c_uint64(0)))

    def decrypt(self,
                file_in_path: str,
                disk_out_name: str,
                file_out_path: str,
                key: bytearray,
                num_threads: int,
                ):
        return self._decrypt_func(file_in_path,
                                  disk_out_name,
                                  file_out_path,
                                  key,
                                  num_threads,
                                  ctypes.byref(ctypes.c_uint64(0)),
                                  ctypes.byref(ctypes.c_uint64(0)))


if __name__ == '__main__': #TODO сделать видимость базовых библиотек, починить указатели, сделать лоадер
    aboba = EncryptLib('../../../encryption_algs/libs/release/libmagma-ecb.dll')
    print(aboba._load_status)
    print(aboba._cipher, aboba._mode)
