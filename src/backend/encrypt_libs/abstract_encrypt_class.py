from abc import ABC, abstractmethod
from enum import Enum
from typing import TypedDict


class LibStatus(Enum):
    SUCCESS = 0
    LOAD_ERROR = 1
    TEST_ERROR = 2


TTestResult = TypedDict('TTestResult', {
    'algorithm': str,
    'mode': str,
    'status': LibStatus,
})


class AbstractEncryptLib(ABC):
    def __init__(self, lib_path: str):
        self._is_loaded: bool = False

    @abstractmethod
    def perform_lib_test(self) -> TTestResult:
        pass

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @abstractmethod
    def encrypt(self,
                file_in_path: str,
                disk_out_name: str,
                file_out_path: str,
                key: bytearray,
                num_threads: int,
                ):
        pass

    @abstractmethod
    def decrypt(self,
                file_in_path: str,
                disk_out_name: str,
                file_out_path: str,
                key: bytearray,
                num_threads: int,
                ):
        pass
