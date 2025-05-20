import ctypes
from os import getenv
from typing import Literal, Callable

from src.utils.singleton import Singleton

TExtraFunc = Literal[
    'read_cipher_from_file', 'magma_init', 'magma_generate_keys', 'magma_finalize', 'magma_encrypt_data', 'magma_decrypt_data',
    'kyznechik_init', 'kyznechik_generate_keys', 'kyznechik_encrypt_data', 'kyznechik_decrypt_data', 'kyznechik_finalize']


class Config(metaclass=Singleton):
    APP_NAME = 'GOST Encryptor'
    GITHUB_URL = 'https://github.com/LuTiFlekSSer/Encryption_app'
    GITHUB_RELEASES_URL = 'https://github.com/LuTiFlekSSer/Encryption_app/releases'
    SPLASH_SCREEN_TIME = 2

    LOCALES_PATH = 'src/locales/locales.json'

    DB_PATH = f'{getenv('APPDATA')}/{APP_NAME}/'
    DB_FILENAME = 'database.db'

    LIBS_PATH = f'{getenv('APPDATA')}/{APP_NAME}/libs/'
    TEST_FILE_ENCRYPT = 'test_encrypt.txt'
    TEST_FILE_DECRYPT = 'test_decrypt.txt'
    TEST_FILE_SIZE = 1024 * 1024 * 10
    EXTRA_FUNCS: dict[TExtraFunc, Callable] = {
        'read_cipher_from_file': ctypes.CFUNCTYPE(ctypes.c_uint8, ctypes.c_wchar_p, ctypes.c_char_p),
        'magma_init': ctypes.CFUNCTYPE(None),
        'magma_generate_keys': ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_uint8),
                                                ctypes.POINTER(ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)))),
        'magma_finalize': ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8))),
        'magma_encrypt_data': ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)),
                                               ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8)),
        'magma_decrypt_data': ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)),
                                               ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8)),
        'kyznechik_init': ctypes.CFUNCTYPE(None),
        'kyznechik_generate_keys': ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_uint8),
                                                    ctypes.POINTER(ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)))),
        'kyznechik_finalize': ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8))),
        'kyznechik_encrypt_data': ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)),
                                                   ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8)),
        'kyznechik_decrypt_data': ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)),
                                                   ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8))
    }

    GRAY_COLOR_50 = '#F3F3F3'
    GRAY_COLOR_100 = '#DDDDDD'
    GRAY_COLOR_200 = '#C6C6C6'
    GRAY_COLOR_300 = '#B0B0B0'
    GRAY_COLOR_400 = '#9B9B9B'
    GRAY_COLOR_500 = '#868686'
    GRAY_COLOR_600 = '#727272'
    GRAY_COLOR_700 = '#5E5E5E'
    GRAY_COLOR_800 = '#4B4B4B'
    GRAY_COLOR_900 = '#393939'

    THREAD_SLEEP = 0.01
    UPDATE_INTERVAL = 0.1
    PROGRESS_INTERVAL = 1
    PROGRESS_ALPHA = 0.8

    SIGNATURE = ('НАШ Слава Богу 🙏❤СЛАВА РОССИИ 🙏❤АНГЕЛА ХРАНИТЕЛЯ КАЖДОМУ ИЗ ВАС'
                 ' 🙏❤БОЖЕ ХРАНИ РОССИЮ 🙏❤СПАСИБО ВАМ НАШИ МАЛЬЧИКИ').encode('utf-8')
