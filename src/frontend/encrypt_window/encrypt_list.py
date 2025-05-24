import os
import time
from pathlib import Path
from threading import Lock
from typing import Tuple

from PyQt5.QtCore import Qt, pyqtSignal, QObject, QProcess
from PyQt5.QtGui import QFontMetrics, QColor
from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout, QLabel, QHBoxLayout, QWidget
from qfluentwidgets import CardWidget, SimpleCardWidget, PipsPager, PipsScrollButtonDisplayMode, IconWidget, \
    StrongBodyLabel, CaptionLabel, ProgressBar, ToolButton, FluentIcon, BodyLabel, \
    InfoBarIcon, TeachingTipView, PopupTeachingTip

from src.backend.db.data_base import DataBase
from src.backend.db.db_records import OperationType, HistoryRecord
from src.backend.encrypt_libs.encrypt_lib import EncryptResult
from src.backend.encrypt_libs.errors import SignatureError, FunctionNotFoundError
from src.backend.encrypt_libs.loader import Loader
from src.frontend.icons.icons import CustomIcons
from src.frontend.paged_list_view import PagedListView
from src.frontend.sub_windows.file_adder_window.file_adder_window import TEncryptData, Status
from src.locales.locales import Locales
from src.utils.config import Config
from src.utils.utils import find_mega_parent

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
        self.l_status: StrongBodyLabel = StrongBodyLabel(self)
        self.l_eta: CaptionLabel = CaptionLabel(self)
        self._locales: Locales = Locales()
        self._alpha: float = Config.PROGRESS_ALPHA

        self._eta: str = ''
        self._status: str = ''
        self._lock: Lock = Lock()

        self.__init_widgets()

    def __init_widgets(self):
        self._v_layout.setContentsMargins(0, 0, 0, 0)
        self._v_layout.setSpacing(0)
        self._v_layout.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.l_status.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self.l_eta.setTextColor(QColor(Config.GRAY_COLOR_700), QColor(Config.GRAY_COLOR_200))

        self._v_layout.addWidget(self.l_status)
        self.l_eta.setVisible(False)

    def set_status(self, status: str):
        self._status = status
        self.update_text()

    def _format_eta(self, seconds: float) -> str:
        years, seconds = divmod(seconds, 31536000)
        months, seconds = divmod(seconds, 2592000)
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)

        if years >= 1:
            yeats_str = self._locales.get_string('year') if years == 1 else self._locales.get_string('years')
            return f'{int(years)} {yeats_str} {int(months)} {self._locales.get_string('month')}'
        elif months >= 1:
            return f'{int(months)} {self._locales.get_string('month')} {int(days)} {self._locales.get_string('day')}'
        elif days >= 1:
            return f'{int(days)} {self._locales.get_string('day')} {int(hours)} {self._locales.get_string('hour')}'
        else:
            return f'{int(hours):02}:{int(minutes):02}:{int(seconds):02}'

    def update_eta(self,
                   status: Status,
                   current: int,
                   total: int,
                   start_time: float,
                   estimated_time_per_step: float,
                   last_eta_update: float) -> Tuple[float, float]:
        match status:
            case Status.IN_PROGRESS:
                self._v_layout.addWidget(self.l_eta)
                self.l_eta.setVisible(True)

                if (lt := time.time()) - last_eta_update > Config.PROGRESS_INTERVAL:
                    last_eta_update = lt
                    try:
                        average_time_per_step = (lt - start_time) / current

                        if estimated_time_per_step is None:
                            estimated_time_per_step = average_time_per_step
                        else:
                            estimated_time_per_step = (
                                    self._alpha * average_time_per_step +
                                    (1 - self._alpha) * estimated_time_per_step
                            )

                        remaining_steps = total - current
                        elapsed_time = estimated_time_per_step * remaining_steps

                        eta = self._format_eta(elapsed_time)
                    except ZeroDivisionError:
                        eta = '--------'

                    self._eta = 'ETA: ' + eta

                    self.update_text()

            case _:
                if self.l_eta.isVisible():
                    self._v_layout.removeWidget(self.l_eta)
                    self.l_eta.setVisible(False)

        return estimated_time_per_step, last_eta_update

    def update_text(self):
        with self._lock:
            EncryptCard.set_elided_text(self.l_eta, self._eta)
            EncryptCard.set_elided_text(self.l_status, self._status)


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
        self._w_status: StatusWidget = StatusWidget(self)
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
                    norm_path = os.path.normpath(self._input_path)
                    QProcess.startDetached('explorer', ['/select,', norm_path])
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
        self._h_layout.addWidget(self._op_icon)
        self._h_layout.addWidget(self._l_mode)
        self._h_layout.addWidget(self._pw_progress, alignment=Qt.AlignRight)
        self._h_layout.addWidget(self._w_status)

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

        icon = CustomIcons.LOCK if data['operation'] == OperationType.ENCRYPT else CustomIcons.UNLOCK
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
                else:
                    self._pw_progress.setValue(0)
                    self._pw_progress.resume()

            case Status.IN_PROGRESS:
                self._btn_delete.setEnabled(False)

                self._pw_progress.resume()
                self._pw_progress.setValue(int(data['current'] / data['total'] * 100))
            case Status.COMPLETED:
                self._btn_delete.setEnabled(True)
                self._pw_progress.resume()
                self._pw_progress.setValue(100)

        self._w_status.set_status(map_status_to_value[data['status']])
        data['estimated_time_per_step'], data['last_eta_update'] = self._w_status.update_eta(
            data['status'],
            data['current'],
            data['total'],
            data['start_time'],
            data['estimated_time_per_step'],
            data['last_eta_update']
        )

        self._update_text()

    def resizeEvent(self, a0):
        self._update_text()
        super().resizeEvent(a0)

    def _update_text(self):
        if self._output_path == '':
            return
        max_width = int((self.width() - self._file_icon.width() - self._op_icon.width() - self._pw_progress.width()
                         - self._btn_delete.width() - self._l_mode.width() - 10 * self._h_layout.spacing()) / 4)
        self._l_name_input.setMaximumWidth(max_width)
        self._l_name_output.setMaximumWidth(max_width)
        self._l_path_input.setMaximumWidth(max_width)
        self._l_path_output.setMaximumWidth(max_width)
        self._l_size.setMaximumWidth(max_width)
        self._w_status.setMaximumWidth(max_width)
        self._w_status.l_eta.setMaximumWidth(max_width)
        self._w_status.l_status.setMaximumWidth(max_width)

        self._w_status.update_text()
        self.set_elided_text(self._l_name_input, Path(self._input_path).name)
        self.set_elided_text(self._l_name_output, Path(self._output_path).name)
        self.set_elided_text(self._l_path_input, self._input_path)
        self.set_elided_text(self._l_path_output, self._output_path)
        self.set_elided_text(self._l_size, self._file_size)

    @staticmethod
    def set_elided_text(label: QLabel, text: str):
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

    def _on_delete(self, output_path: str):
        self._encrypt_list.remove_item(output_path)

    def _connect_widget_actions(self):
        events.sig_delete.connect(self._on_delete)

        self._loader.events.sig_update_progress.connect(self._on_update_progress)
        self._loader.events.sig_update_status.connect(self._on_update_status)
        self._loader.events.sig_update.connect(self._on_update)
        self._loader.events.sig_task_start.connect(self._on_sig_task_start)

    def _on_sig_task_start(self, key: str, start_time: float):
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
        self._pager.blockSignals(True)
        self._pager.setPageNumber(total_pages)
        self._pager.setVisibleNumber(min(total_pages, 50))
        self._pager.setCurrentIndex(current_page)
        self._pager.blockSignals(False)

    def add_task(self, data: TEncryptData):
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
            data['status'] = Status.FAILED
            data['status_description'] = 'signature_error'
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

        except FunctionNotFoundError:
            data['status'] = Status.FAILED
            data['mode'] = locales.get_string('failed')
            data['status_description'] = 'function_not_found'
            self._encrypt_list.add_item(data['uid'], data)

            record = HistoryRecord()
            record.input_path = data['input_file']
            record.output_path = data['output_file']
            record.status = False
            record.status_description = 'function_not_found'
            record.mode = data['mode']
            record.operation = data['operation']
            record.time = time.time()

            self._db.add_history_record(record)

        except Exception as e:
            data['status'] = Status.FAILED
            data['status_description'] = 'work_error'
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
