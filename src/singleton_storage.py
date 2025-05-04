from src.backend.db.data_base import DataBase
from src.backend.encrypt_libs.loader import Loader
from src.global_flags import GlobalFlags
from src.locales.locales import Locales


class SingletonStorage:
    def __init__(self):
        data_base = DataBase()
        locales = Locales()
        global_flags = GlobalFlags()
        loader = Loader()
