import os
import sys
from os import PathLike

from PyQt5.QtWidgets import QWidget


def resource_path(relative_path: str | PathLike[str]) -> str:
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath('.')

    return os.path.join(base_path, relative_path)


def find_mega_parent(widget: QWidget) -> QWidget:
    tmp_widget = widget

    while True:
        if isinstance(tmp_widget, QWidget):
            if hasattr(tmp_widget, 'ULTRA_MEGA_PARENT'):
                return tmp_widget

        elif tmp_widget is None:
            return widget

        tmp_widget = tmp_widget.parent()
