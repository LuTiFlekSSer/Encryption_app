import time
from threading import Thread

from src.backend.encrypt_libs.loader import Loader
from src.global_flags import GlobalFlags
from src.utils.config import Config


class LoaderThread(Thread):
    def __init__(self):
        self._global_flags = GlobalFlags()
        self._sleep_interval: float = Config.THREAD_SLEEP
        self._loader: Loader = Loader()

        super().__init__(target=self._work, name=self.__class__.__name__, daemon=True)

    def _work(self):
        while not self._global_flags.stop_event.is_set():
            self._loader.exec()
            time.sleep(self._sleep_interval)
