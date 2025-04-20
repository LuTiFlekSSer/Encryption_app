from os import getenv

from src.utils.singleton import Singleton


class Config(metaclass=Singleton):
    APP_NAME = 'GOST Encryptor'
    GITHUB_URL = 'https://github.com/LuTiFlekSSer/Encryption_app'
    SPLASH_SCREEN_TIME = 2

    LOCALES_PATH = 'src/locales/locales.json'

    DB_PATH = f'{getenv('APPDATA')}/{APP_NAME}/'
    DB_FILENAME = 'database.db'

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

