import pathlib
import tempfile

from PyQt5.QtCore import QFileInfo, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QFileIconProvider
from qfluentwidgets import MSFluentWindow


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
    suffix = pathlib.Path(file_path).suffix

    with tempfile.NamedTemporaryFile(suffix=suffix) as tmp_file:
        file_path = tmp_file.name

    file_info = QFileInfo(file_path)
    provider = QFileIconProvider()
    icon = provider.icon(file_info)

    pixmap = icon.pixmap(size)
    pixmap_copy = pixmap.copy()

    return QIcon(pixmap_copy)


def find_mega_parent(widget: QWidget) -> MSFluentWindow | QWidget:
    tmp_widget = widget

    while True:
        if isinstance(tmp_widget, MSFluentWindow):
            if hasattr(tmp_widget, 'ULTRA_MEGA_PARENT'):
                return tmp_widget

        elif tmp_widget is None:
            return widget

        tmp_widget = tmp_widget.parent()
