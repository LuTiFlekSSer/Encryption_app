from enum import Enum
from typing import TypedDict

from src.backend.db.db_records import OperationType


class Status(Enum):
    WAITING = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    FAILED = 3


TEncryptData = TypedDict('TEncryptData', {
    'input_file': str,
    'output_file': str,
    'mode': str,
    'operation': OperationType,
    'total': int,
    'current': int,
    'status': Status,
    'hash_password': str,
})
