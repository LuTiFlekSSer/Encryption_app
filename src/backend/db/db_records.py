from enum import Enum
from typing import Tuple


class OperationType(Enum):
    DECRYPT = False
    ENCRYPT = True


class HistoryRecord:
    def __init__(self):
        self.idx: int = 0
        self.path: str = ''
        self.status: bool = False
        self.status_description: str = ''
        self.mode: str = ''
        self.operation: OperationType = OperationType.DECRYPT
        self.time: float = 0.0

    def set_data(self,
                 idx: int,
                 path: str,
                 status: bool,
                 status_description: str,
                 mode: str,
                 operation: bool,
                 time: float):
        self.idx = idx
        self.path = path
        self.status = status
        self.status_description = status_description
        self.mode = mode
        self.operation = OperationType(operation)
        self.time = time

    def get_data(self) -> Tuple[str, bool, str, str, bool, float]:
        return self.path, self.status, self.status_description, self.mode, self.operation.value, self.time
