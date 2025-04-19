from os import getenv

from src.utils.singleton import Singleton


class Config(metaclass=Singleton):
    APP_NAME = 'GOST Encryptor'
    SPLASH_SCREEN_TIME = 2

    LOCALES_PATH = 'src/locales/locales.json'

    DB_PATH = f'{getenv('APPDATA')}/{APP_NAME}/'
    DB_FILENAME = 'database.db'
