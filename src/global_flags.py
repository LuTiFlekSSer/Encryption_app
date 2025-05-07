from threading import Event

from src.utils.singleton import Singleton


class GlobalFlags(metaclass=Singleton):
    def __init__(self):
        self.stop_event: Event = Event()
        self.is_running: Event = Event()
