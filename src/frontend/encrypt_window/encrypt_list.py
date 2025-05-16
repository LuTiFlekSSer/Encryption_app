import os
import time
from pathlib import Path
from threading import Lock

from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer, QProcess
from PyQt5.QtGui import QFontMetrics, QColor
from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout, QLabel, QHBoxLayout, QWidget
from qfluentwidgets import CardWidget, SimpleCardWidget, PipsPager, PipsScrollButtonDisplayMode, IconWidget, \
    StrongBodyLabel, CaptionLabel, ProgressBar, ToolButton, FluentIcon, InfoBar, InfoBarPosition, BodyLabel, \
    InfoBarIcon, TeachingTipView, PopupTeachingTip

from src.backend.db.data_base import DataBase
from src.backend.db.db_records import OperationType, HistoryRecord
from src.backend.encrypt_libs.encrypt_lib import EncryptResult
from src.backend.encrypt_libs.errors import SignatureError
from src.backend.encrypt_libs.loader import Loader
from src.frontend.icons.icons import LockIcons
from src.frontend.paged_list_view import PagedListView
from src.frontend.sub_windows.file_adder_window.file_adder_window import TEncryptData, Status
from src.locales.locales import Locales
from src.utils.config import Config
from src.utils.utils import get_normalized_size, find_mega_parent, get_file_icon

locales = Locales()
map_status_to_value: dict[Status, str] = {
    Status.WAITING: locales.get_string('waiting'),
    Status.IN_PROGRESS: locales.get_string('in_progress'),
    Status.COMPLETED: locales.get_string('completed'),
    Status.FAILED: locales.get_string('failed'),
}


# todo при расшифровке сделать сообщение, что такого режима нет
# todo info bar при нажатии на карточку с подробным описанием ошибки или открыть результат
# todo оставшееся время

class Events(QObject):
    sig_delete: pyqtSignal = pyqtSignal(str)


events = Events()


class ProgressWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._h_layout: QVBoxLayout = QHBoxLayout(self)
        self._pb_progress: ProgressBar = ProgressBar(self)
        self._l_progress: BodyLabel = BodyLabel(self)

        self.__init_widgets()

    def __init_widgets(self):
        self._h_layout.setContentsMargins(0, 0, 0, 0)
        self._h_layout.setSpacing(8)
        self._h_layout.setAlignment(Qt.AlignCenter)

        self._pb_progress.setRange(0, 100)

        self._l_progress.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))

        self._h_layout.addWidget(self._pb_progress)
        self._h_layout.addWidget(self._l_progress)

    def setValue(self, progress: int):
        self._pb_progress.setValue(progress)
        self._l_progress.setText(f'{progress}%')

    def resume(self):
        self._pb_progress.resume()

    def error(self):
        self._pb_progress.error()


class StatusWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._v_layout: QVBoxLayout = QVBoxLayout(self)
        self._l_status: StrongBodyLabel = StrongBodyLabel(self)
        self._l_eta: CaptionLabel = CaptionLabel(self)
        self._locales: Locales = Locales()

        self.__init_widgets()

    def __init_widgets(self):
        self._v_layout.setContentsMargins(0, 0, 0, 0)
        self._v_layout.setSpacing(0)
        self._v_layout.setAlignment(Qt.AlignTop)

        self._l_status.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._l_eta.setTextColor(QColor(Config.GRAY_COLOR_700), QColor(Config.GRAY_COLOR_200))

        self._v_layout.addWidget(self._l_status)
        self._l_eta.hide()

    def set_status(self, status: str):
        self._l_status.setText(status)

    def format_eta(self, seconds: float) -> str:
        years, seconds = divmod(seconds, 31536000)
        months, seconds = divmod(seconds, 2592000)
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)

        if years >= 1:# todo доделать
            yeats_str = self._locales.get_string('year') if years == 1 else self._locales.get_string('years')
            return f'{int(years)} {} {int(months)} мес.'
        elif months >= 1:
            return f'{int(months)} {} {int(days)} {}'
        elif days >= 1:
            return f'{int(days)} {} {int(hours)} {}'
        else:
            return f'{int(hours):02}:{int(minutes):02}:{int(seconds):02}'

    def update_eta(self, status: Status, current: int, total: int, start_time: float):
        match status:
            case Status.IN_PROGRESS:
                self._l_eta.show()

            case _:
                self._l_eta.hide()


class EncryptCard(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._h_layout: QHBoxLayout = QHBoxLayout(self)
        self._file_icon: IconWidget = IconWidget(self)
        self._v_layout_input: QVBoxLayout = QVBoxLayout()
        self._l_name_input: StrongBodyLabel = StrongBodyLabel(self)
        self._l_path_input: CaptionLabel = CaptionLabel(self)
        self._v_layout_output: QVBoxLayout = QVBoxLayout()
        self._l_name_output: StrongBodyLabel = StrongBodyLabel(self)
        self._l_path_output: CaptionLabel = CaptionLabel(self)
        self._l_size: StrongBodyLabel = StrongBodyLabel(self)
        self._l_mode: StrongBodyLabel = StrongBodyLabel(self)
        self._op_icon: IconWidget = IconWidget(self)
        self._pw_progress: ProgressWidget = ProgressWidget(self)
        self._l_status: StrongBodyLabel = StrongBodyLabel(self)
        self._btn_delete: ToolButton = ToolButton(self)

        self._locales: Locales = Locales()

        self.__init_widgets()

        self._input_path: str = ''
        self._output_path: str = ''
        self._file_size: str = ''
        self._uid: str = ''
        self._status: Status = Status.WAITING
        self._status_description: str = ''
        self._start_time: float = 0

    def _show_tool_tip(self,
                       title: str,
                       content: str,
                       icon: InfoBarIcon):

        view = TeachingTipView(
            title=title,
            content=content,
            icon=icon,
            parent=self,
        )

        tip = PopupTeachingTip.make(
            view=view,
            target=self,
            duration=-1,
            parent=self
        )

        view.closed.connect(tip.close)

    def _on_click(self):
        match self._status:
            case Status.COMPLETED:
                if os.path.exists(self._output_path):
                    QProcess.startDetached('explorer', [f'/select,{os.path.normpath(self._output_path)}'])
                else:
                    self._show_tool_tip(
                        title=self._locales.get_string('error'),
                        content=self._locales.get_string('file_not_found'),
                        icon=InfoBarIcon.ERROR
                    )
            case Status.FAILED:
                self._show_tool_tip(
                    title=self._locales.get_string('error'),
                    content=self._locales.get_string(self._status_description),
                    icon=InfoBarIcon.ERROR
                )

            case Status.WAITING:
                self._show_tool_tip(
                    title=self._locales.get_string('waiting'),
                    content=self._locales.get_string('waiting_description'),
                    icon=InfoBarIcon.INFORMATION
                )

            case Status.IN_PROGRESS:
                self._show_tool_tip(
                    title=self._locales.get_string('in_progress'),
                    content=self._locales.get_string('in_progress_description'),
                    icon=InfoBarIcon.INFORMATION
                )

    def __init_widgets(self):
        self._h_layout.setContentsMargins(16, 16, 16, 16)
        self._h_layout.setSpacing(16)
        self._h_layout.setAlignment(Qt.AlignVCenter)

        self._file_icon.setFixedSize(32, 32)
        self._op_icon.setFixedSize(24, 24)

        self._pw_progress.setFixedWidth(160)

        self._btn_delete.setFixedSize(32, 32)
        icon = FluentIcon.DELETE.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._btn_delete.setIcon(icon)
        self._btn_delete.clicked.connect(lambda: events.sig_delete.emit(self._uid))

        self._l_size.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._l_name_input.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._l_name_output.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._l_path_input.setTextColor(QColor(Config.GRAY_COLOR_700), QColor(Config.GRAY_COLOR_200))
        self._l_path_output.setTextColor(QColor(Config.GRAY_COLOR_700), QColor(Config.GRAY_COLOR_200))
        self._l_status.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._l_mode.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))

        self._v_layout_input.setContentsMargins(0, 0, 0, 0)
        self._v_layout_input.setSpacing(0)
        self._v_layout_input.setAlignment(Qt.AlignTop)

        self._v_layout_output.setContentsMargins(0, 0, 0, 0)
        self._v_layout_output.setSpacing(0)
        self._v_layout_output.setAlignment(Qt.AlignTop)

        self._h_layout.addWidget(self._file_icon)

        self._h_layout.addLayout(self._v_layout_input, stretch=1)
        self._v_layout_input.addWidget(self._l_name_input)
        self._v_layout_input.addWidget(self._l_path_input)

        self._h_layout.addLayout(self._v_layout_output, stretch=1)
        self._v_layout_output.addWidget(self._l_name_output)
        self._v_layout_output.addWidget(self._l_path_output)

        self._h_layout.addWidget(self._l_size)
        self._h_layout.addWidget(self._op_icon, alignment=Qt.AlignRight)
        self._h_layout.addWidget(self._l_mode, alignment=Qt.AlignRight)
        self._h_layout.addWidget(self._pw_progress, alignment=Qt.AlignRight)
        self._h_layout.addWidget(self._l_status, alignment=Qt.AlignRight)

        self._h_layout.addWidget(self._btn_delete, alignment=Qt.AlignRight)

        self.clicked.connect(self._on_click)

    def set_data(self, data: TEncryptData):
        self._input_path = data['input_file']
        self._output_path = data['output_file']
        self._uid = data['uid']
        self._file_size = data['file_size']
        self._status = data['status']
        self._status_description = data['status_description']
        self._start_time = data['start_time']

        self._file_icon.setIcon(data['file_icon'])

        self._l_mode.setText(data['mode'])

        icon = LockIcons.LOCK if data['operation'] == OperationType.ENCRYPT else LockIcons.UNLOCK
        icon = icon.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._op_icon.setIcon(icon)

        match data['status']:
            case Status.FAILED:
                self._btn_delete.setEnabled(True)

                self._pw_progress.setValue(100)
                self._pw_progress.error()
            case Status.WAITING:
                self._btn_delete.setEnabled(False)

                if data['current'] >= 0:
                    self._pw_progress.resume()
                    data['status'] = Status.IN_PROGRESS
                    self._pw_progress.setValue(int(data['current'] / data['total'] * 100))
            case Status.IN_PROGRESS:
                self._btn_delete.setEnabled(False)

                self._pw_progress.resume()
                self._pw_progress.setValue(int(data['current'] / data['total'] * 100))
            case Status.COMPLETED:
                self._btn_delete.setEnabled(True)

                self._pw_progress.setValue(100)

        self._l_status.setText(map_status_to_value[data['status']])

        self._update_text()

    def resizeEvent(self, a0):
        self._update_text()
        super().resizeEvent(a0)

    def _update_text(self):
        if self._output_path == '':
            return
        max_width = int((self.width() - self._file_icon.width() - self._op_icon.width() - self._pw_progress.width()
                         - self._l_status.width() - self._btn_delete.width() - self._l_mode.width()
                         - 10 * self._h_layout.spacing()) / 3)
        self._l_name_input.setMaximumWidth(max_width)
        self._l_name_output.setMaximumWidth(max_width)
        self._l_path_input.setMaximumWidth(max_width)
        self._l_path_output.setMaximumWidth(max_width)
        self._l_size.setMaximumWidth(max_width)

        self._set_elided_text(self._l_name_input, Path(self._input_path).name)
        self._set_elided_text(self._l_name_output, Path(self._output_path).name)
        self._set_elided_text(self._l_path_input, self._input_path)
        self._set_elided_text(self._l_path_output, self._output_path)
        self._set_elided_text(self._l_size, self._file_size)

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
        self._hmi: QWidget = find_mega_parent(parent)

        self._loader: Loader = Loader()
        self._lock: Lock = Lock()
        self._db: DataBase = DataBase()

        self.__init_widgets()
        self._connect_widget_actions()

        file = 'E:\\test'
        QTimer.singleShot(5000, lambda: self._add_task(
            {
                'uid': 'u8i92wr43uy9terwuhigfsdrrgeujihsgerfdkbjdh',
                'input_file': file,
                'output_file': file,
                'mode': 'kyznechik-ctr',
                'operation': OperationType.ENCRYPT,
                'total': 1,
                'current': -228,
                'status': Status.WAITING,
                'hash_password': 'oral_cumshot',
                'file_size': get_normalized_size(self._locales, os.path.getsize(file)),
                'file_icon': get_file_icon(file),
                'status_description': '',
                'start_time': 0
            }
        ))

        QTimer.singleShot(6000, lambda: self._add_task(
            {
                'uid': 'u8i92wr43uy9terwuhigfsdrujihsgerfdkbjdh',
                'input_file': "C:\\Users\\boris\\Downloads\\input.txt",
                'output_file': "C:\\Users\\boris\\Downloads\\input.txt",
                'mode': 'kyznechik-ctr',
                'operation': OperationType.ENCRYPT,
                'total': 1,
                'current': -228,
                'status': Status.WAITING,
                'hash_password': 'oral_cumshot',
                'file_size': get_normalized_size(self._locales,
                                                 os.path.getsize("C:\\Users\\boris\\Downloads\\input.txt")),
                'file_icon': get_file_icon("C:\\Users\\boris\\Downloads\\input.txt"),
                'status_description': '',
                'start_time': 0
            }
        ))

    def _on_delete(self, output_path: str):
        self._encrypt_list.remove_item(output_path)

    def _connect_widget_actions(self):
        events.sig_delete.connect(self._on_delete)

        self._loader.events.sig_update_progress.connect(self._on_update_progress)
        self._loader.events.sig_update_status.connect(self._on_update_status)
        self._loader.events.sig_update.connect(self._on_update)

    def _on_task_start(self, key: str, start_time: float):
        self._encrypt_list.items_dict[key]['start_time'] = start_time

    def _on_update(self):
        self._encrypt_list.update_view()
        self.update()

    def _on_update_progress(self, key: str, current: int, total: int):
        self._encrypt_list.items_dict[key]['current'] = current
        self._encrypt_list.items_dict[key]['total'] = total

    def _on_update_status(self, key: str, status: EncryptResult):
        self._encrypt_list.items_dict[key][
            'status'] = Status.COMPLETED if status == EncryptResult.SUCCESS else Status.FAILED
        self._encrypt_list.items_dict[key]['status_description'] = status.name

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
        try:
            match data['operation']:
                case OperationType.ENCRYPT:
                    self._loader.check_encrypt_file(data['input_file'], data['output_file'])
                    self._encrypt_list.add_item(data['uid'], data)
                    self._loader.encrypt(
                        mode=data['mode'],
                        file_in_path=data['input_file'],
                        file_out_path=data['output_file'],
                        hash_password=data['hash_password'],
                        uid=data['uid']
                    )

                case OperationType.DECRYPT:
                    mode = self._loader.check_decrypt_file(data['input_file'], data['output_file'])
                    data['mode'] = mode

                    self._encrypt_list.add_item(data['uid'], data)
                    self._loader.decrypt(
                        mode=data['mode'],
                        file_in_path=data['input_file'],
                        file_out_path=data['output_file'],
                        hash_password=data['hash_password'],
                        uid=data['uid']
                    )

        except SignatureError:
            InfoBar.error(
                title=self._locales.get_string('error'),
                content=self._locales.get_string('signature_error'),
                duration=-1,
                parent=self._hmi,
                position=InfoBarPosition.BOTTOM_RIGHT
            )

            data['status'] = Status.FAILED
            self._encrypt_list.add_item(data['uid'], data)

            record = HistoryRecord()
            record.input_path = data['input_file']
            record.output_path = data['output_file']
            record.status = False
            record.status_description = 'signature_error'
            record.mode = data['mode']
            record.operation = data['operation']
            record.time = time.time()

            self._db.add_history_record(record)

        except Exception as e:
            InfoBar.error(
                title=self._locales.get_string('error'),
                content=self._locales.get_string('work_error'),
                duration=-1,
                parent=self._hmi,
                position=InfoBarPosition.BOTTOM_RIGHT
            )

            data['status'] = Status.FAILED
            self._encrypt_list.add_item(data['uid'], data)

            record = HistoryRecord()
            record.input_path = data['input_file']
            record.output_path = data['output_file']
            record.status = False
            record.status_description = 'work_error'
            record.mode = data['mode']
            record.operation = data['operation']
            record.time = time.time()

            self._db.add_history_record(record)
