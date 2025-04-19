__all__ = [
    'Locales'
]

import ctypes
import json
import locale

from src.db.data_base import DataBase
from src.locales import errors
from src.utils.config import Config
from src.utils.singleton import Singleton
from src.utils.utils import resource_path


class Locales(metaclass=Singleton):
    with open(resource_path(Config.LOCALES_PATH), encoding='utf-8') as file:
        _locales = json.load(file)

    _language = None

    def __init__(self):
        super().__init__()

        db = DataBase()
        language = db.get_setting('language')

        if language == 'None':
            windll = ctypes.windll.kernel32
            system_language = locale.windows_locale[windll.GetUserDefaultUILanguage()]

            if system_language == 'ru_RU':
                db.set_setting('language', 'ru')
                language = 'ru'
            else:
                db.set_setting('language', 'en')
                language = 'en'

        self.set_language(language)

    @staticmethod
    def get_string(string_name):
        if not isinstance(string_name, str):
            raise TypeError

        if Locales._language is None:
            raise errors.LanguageNotSetError

        try:
            return Locales._locales['strings'][string_name][Locales._language]
        except Exception:
            raise errors.GetStringError

    @staticmethod
    def set_language(language):
        if not isinstance(language, str):
            raise TypeError

        if language not in Locales._locales['languages']:
            raise errors.SetLocaleError

        Locales._language = language

    @staticmethod
    def get_languages():
        return Locales._locales['languages']
