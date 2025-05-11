import os
from pathlib import Path
from threading import Lock

from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFontMetrics, QColor
from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout, QLabel, QHBoxLayout
from qfluentwidgets import CardWidget, SimpleCardWidget, PipsPager, PipsScrollButtonDisplayMode, IconWidget, \
    StrongBodyLabel, CaptionLabel, ProgressBar, ToolButton, FluentIcon

from src.backend.db.db_records import OperationType
from src.backend.encrypt_libs.loader import Loader
from src.frontend.icons.icons import LockIcons
from src.frontend.paged_list_view import PagedListView
from src.frontend.sub_windows.file_adder_window.file_adder_window import TEncryptData, Status
from src.locales.locales import Locales
from src.utils.config import Config
from src.utils.utils import get_file_icon, get_normalized_size

locales = Locales()
map_status_to_value: dict[Status, str] = {
    Status.WAITING: locales.get_string('waiting'),
    Status.IN_PROGRESS: locales.get_string('in_progress'),
    Status.COMPLETED: locales.get_string('completed'),
    Status.FAILED: locales.get_string('failed'),
}


class Events(QObject):
    sig_delete: pyqtSignal = pyqtSignal(str)


events = Events()


class EncryptCard(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._h_layout: QHBoxLayout = QHBoxLayout(self)
        self._file_icon: IconWidget = IconWidget(self)
        self._v_layout: QVBoxLayout = QVBoxLayout()
        self._l_name: StrongBodyLabel = StrongBodyLabel(self)
        self._l_size: CaptionLabel = CaptionLabel(self)
        self._l_mode: StrongBodyLabel = StrongBodyLabel(self)
        self._op_icon: IconWidget = IconWidget(self)
        self._pb_progress: ProgressBar = ProgressBar(self)
        self._l_status: StrongBodyLabel = StrongBodyLabel(self)
        self._btn_delete: ToolButton = ToolButton(self)

        self._locales: Locales = Locales()

        self.__init_widgets()

        self._input_path: str = ''
        self._output_path: str = ''

    def __init_widgets(self):
        self._h_layout.setContentsMargins(16, 16, 16, 16)
        self._h_layout.setSpacing(16)
        self._h_layout.setAlignment(Qt.AlignVCenter)

        self._file_icon.setFixedSize(32, 32)
        self._op_icon.setFixedSize(24, 24)

        self._pb_progress.setFixedWidth(160)

        self._btn_delete.setFixedSize(32, 32)
        icon = FluentIcon.DELETE.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._btn_delete.setIcon(icon)
        self._btn_delete.clicked.connect(lambda: events.sig_delete.emit(self._output_path))

        self._pb_progress.setRange(0, 100)

        self._l_size.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._l_name.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._l_status.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._l_mode.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))

        self._v_layout.setContentsMargins(0, 0, 0, 0)
        self._v_layout.setSpacing(0)
        self._v_layout.setAlignment(Qt.AlignTop)

        self._h_layout.addWidget(self._file_icon)
        self._h_layout.addLayout(self._v_layout, stretch=1)
        self._v_layout.addWidget(self._l_name)
        self._v_layout.addWidget(self._l_size)
        self._h_layout.addWidget(self._l_mode, alignment=Qt.AlignRight)
        self._h_layout.addWidget(self._op_icon, alignment=Qt.AlignRight)
        self._h_layout.addWidget(self._pb_progress, alignment=Qt.AlignRight)
        self._h_layout.addWidget(self._l_status, alignment=Qt.AlignRight)

        self._h_layout.addWidget(self._btn_delete, alignment=Qt.AlignRight)

    def set_data(self, data: TEncryptData):
        self._input_path = data['input_file']
        self._output_path = data['output_file']

        file_icon = get_file_icon(data['input_file'])
        self._file_icon.setIcon(file_icon)

        self._l_mode.setText(data['mode'])

        icon = LockIcons.LOCK if data['operation'] == OperationType.ENCRYPT else LockIcons.UNLOCK
        icon = icon.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._op_icon.setIcon(icon)

        self._pb_progress.setValue(data['current'] // data['total'] * 100)

        self._l_status.setText(map_status_to_value[data['status']])

        self._update_text()

    def resizeEvent(self, a0):
        self._update_text()
        super().resizeEvent(a0)

    def _update_text(self):
        if self._output_path == '':
            return
        max_width = (
                self.width() - self._file_icon.width() - self._op_icon.width() - self._pb_progress.width()
                - self._l_status.width() - self._btn_delete.width() - self._l_mode.width() - 8 * 16)
        self._l_name.setMaximumWidth(max_width)
        self._l_size.setMaximumWidth(max_width)

        self._set_elided_text(self._l_name, Path(self._input_path).name)
        self._set_elided_text(self._l_size, get_normalized_size(self._locales, os.path.getsize(self._input_path)))

    @staticmethod
    def _set_elided_text(label: QLabel, text: str):
        metrics = QFontMetrics(label.font())
        elided = metrics.elidedText(text, Qt.ElideMiddle, label.maximumWidth())
        label.setText(elided)


class EncryptList(SimpleCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._locales: Locales = Locales()
        self._vl_view_layout: QVBoxLayout = QVBoxLayout(self)
        self._encrypt_list: PagedListView = PagedListView(EncryptCard, parent=self)
        self._pager: PipsPager = PipsPager(self)

        self._loader: Loader = Loader()
        self._lock: Lock = Lock()

        self.__init_widgets()
        self._connect_widget_actions()

        aboba = {'input_file': os.path.abspath('input.txt'),
                 'output_file': 'output.txt',
                 'mode': 'AES',
                 'operation': OperationType.ENCRYPT,
                 'total': 100,
                 'current': 50,
                 'status': Status.IN_PROGRESS,
                 'hash_password': 'password123'}

        aboba1 = {'input_file': os.path.abspath('input.jpeg'),
                  'output_file': 'output.txtt',
                  'mode': 'AES',
                  'operation': OperationType.ENCRYPT,
                  'total': 100,
                  'current': 50,
                  'status': Status.IN_PROGRESS,
                  'hash_password': 'password123'}

        aboba2 = {'input_file': os.path.abspath('input.bat'),
                  'output_file': 'output.txttt',
                  'mode': 'AES',
                  'operation': OperationType.ENCRYPT,
                  'total': 100,
                  'current': 50,
                  'status': Status.IN_PROGRESS,
                  'hash_password': 'password123'}

        self._encrypt_list.add_item(aboba['output_file'], aboba)
        self._encrypt_list.add_item(aboba1['output_file'], aboba1)
        self._encrypt_list.add_item(aboba2['output_file'], aboba2)

    def _on_delete(self, output_path: str):
        self._encrypt_list.remove_item(output_path)

    def _connect_widget_actions(self):
        events.sig_delete.connect(self._on_delete)
        self._loader.events.sig_update_progress.connect(self._on_update_progress)
        self._loader.events.sig_update_status.connect(self._on_update_status)

    def _on_update_progress(self, key: str, current: int, total: int):
        self._encrypt_list.items_dict[key]['current'] = current
        self._encrypt_list.items_dict[key]['total'] = total

    def _on_update_status(self, key: str, status: Status):
        self._encrypt_list.items_dict[key]['status'] = status

    def __init_widgets(self):
        self._pager.setNextButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)
        self._pager.setPreviousButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)

        self._vl_view_layout.setContentsMargins(8, 8, 8, 8)
        self._vl_view_layout.setSpacing(8)
        self._vl_view_layout.setAlignment(Qt.AlignTop)

        self._vl_view_layout.addWidget(self._encrypt_list)
        self._vl_view_layout.addWidget(self._pager, alignment=Qt.AlignCenter)

        self._encrypt_list.pagination_changed.connect(self._on_pagination_changed)
        self._pager.currentIndexChanged.connect(lambda index: self._encrypt_list.set_page(index))

    def _on_pagination_changed(self, current_page: int, total_pages: int):
        self._pager.setPageNumber(total_pages)
        self._pager.setVisibleNumber(min(total_pages, 50))
        self._pager.setCurrentIndex(current_page)

    def _add_task(self, data: TEncryptData):
        self._encrypt_list.add_item(data['output_file'], data)
        match data['operation']:
            case OperationType.ENCRYPT:
                self._loader.encrypt(
                    mode=data['mode'],
                    file_in_path=data['input_file'],
                    file_out_path=data['output_file'],
                    hash_password=data['hash_password']
                )

            case OperationType.DECRYPT:
                self._loader.decrypt(
                    mode=data['mode'],
                    file_in_path=data['input_file'],
                    file_out_path=data['output_file'],
                    hash_password=data['hash_password']
                )
