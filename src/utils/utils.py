import os
import sys
from os import PathLike

from PyQt5.QtCore import QFileInfo, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QFileIconProvider


def get_normalized_size(locales, size: int) -> str:
    for unit in [locales.get_string('B'),
                 locales.get_string('KB'),
                 locales.get_string('MB'),
                 locales.get_string('GB'),
                 locales.get_string('TB')]:
        if size < 1024:
            return f'{size:.2f} {unit}'

        size /= 1024

    return f'{size:.2f} {locales.get_string('PB')}'


def get_file_icon(file_path: str, size: QSize = QSize(128, 128)) -> QIcon:
    # todo получать картинку не от конкретного файла, а от типа файла
    file_info = QFileInfo(file_path)
    provider = QFileIconProvider()
    icon = provider.icon(file_info)

    pixmap = icon.pixmap(size)
    pixmap_copy = pixmap.copy()

    return QIcon(pixmap_copy)


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
