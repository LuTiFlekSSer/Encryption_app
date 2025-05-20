from src.utils.singleton import Singleton


class MasterKeyStorage(metaclass=Singleton):
    def __init__(self):
        self.master_key: str = ''
