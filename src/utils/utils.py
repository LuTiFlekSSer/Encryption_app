import os
import sys
from os import PathLike


def resource_path(relative_path: str | PathLike[str]) -> str:
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath('.')

    return os.path.join(base_path, relative_path)
