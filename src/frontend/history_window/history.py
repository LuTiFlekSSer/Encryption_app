import os.path
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import Qt, QProcess
from PyQt5.QtGui import QColor, QFontMetrics
from PyQt5.QtWidgets import QSizePolicy, QHBoxLayout, QLabel, QWidget
from PyQt5.QtWidgets import QVBoxLayout
from qfluentwidgets import SimpleCardWidget, PipsPager, PipsScrollButtonDisplayMode, InfoBarIcon, \
    IconWidget, StrongBodyLabel, CaptionLabel, CardWidget, TeachingTipView, PopupTeachingTip

from src.backend.db.data_base import DataBase
from src.backend.db.db_records import HistoryRecord, OperationType
from src.frontend.icons.icons import LockIcons
from src.frontend.paged_list_view import PagedListView
from src.frontend.sub_windows.message_box import MessageBox
from src.locales.locales import Locales
from src.utils.config import Config
from src.utils.utils import find_mega_parent


class HistoryCard(CardWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._h_layout: QHBoxLayout = QHBoxLayout(self)
        self._status_icon: IconWidget = IconWidget(self)
        self._w1: QWidget = QWidget(self)
        self._v_layout_input: QVBoxLayout = QVBoxLayout(self._w1)
        self._l_name_input: StrongBodyLabel = StrongBodyLabel(self)
        self._l_path_input: CaptionLabel = CaptionLabel(self)
        self._w2: QWidget = QWidget(self)
        self._v_layout_output: QVBoxLayout = QVBoxLayout(self._w2)
        self._l_name_output: StrongBodyLabel = StrongBodyLabel(self)
        self._l_path_output: CaptionLabel = CaptionLabel(self)
        self._l_mode: StrongBodyLabel = StrongBodyLabel(self)
        self._op_icon: IconWidget = IconWidget(self)
        self._l_time: StrongBodyLabel = StrongBodyLabel(self)
        self._locales: Locales = Locales()

        self._input_path: str = ''
        self._output_path: str = ''
        self._status_description: str = ''
        self._mode: str = ''
        self._status: bool = False

        self.__init_widgets()

    def _show_tool_tip(self,
                       title: str,
                       content: str,
                       icon: InfoBarIcon
                       ):

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
        if self._status:
            if os.path.exists(self._input_path):
                QProcess.startDetached('explorer', [f'/select,{os.path.normpath(self._output_path)}'])
            else:
                self._show_tool_tip(
                    title=self._locales.get_string('error'),
                    content=self._locales.get_string('file_not_found'),
                    icon=InfoBarIcon.ERROR
                )
        else:
            self._show_tool_tip(
                title=self._locales.get_string('error'),
                content=self._locales.get_string(self._status_description),
                icon=InfoBarIcon.ERROR
            )

    def __init_widgets(self):
        self._status_icon.setFixedSize(32, 32)
        self._op_icon.setFixedSize(24, 24)

        self._h_layout.setContentsMargins(16, 16, 16, 16)
        self._h_layout.setSpacing(16)
        self._h_layout.setAlignment(Qt.AlignCenter)

        self._v_layout_input.setContentsMargins(0, 0, 0, 0)
        self._v_layout_input.setSpacing(0)
        self._v_layout_input.setAlignment(Qt.AlignTop)

        self._v_layout_output.setContentsMargins(0, 0, 0, 0)
        self._v_layout_output.setSpacing(0)
        self._v_layout_output.setAlignment(Qt.AlignTop)

        self._l_name_input.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._l_path_input.setTextColor(QColor(Config.GRAY_COLOR_700), QColor(Config.GRAY_COLOR_200))
        self._l_name_output.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._l_path_output.setTextColor(QColor(Config.GRAY_COLOR_700), QColor(Config.GRAY_COLOR_200))
        self._l_mode.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._l_time.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))

        self._h_layout.addWidget(self._status_icon)

        self._h_layout.addWidget(self._w1, stretch=1)
        self._v_layout_input.addWidget(self._l_name_input)
        self._v_layout_input.addWidget(self._l_path_input)

        self._h_layout.addWidget(self._w2, stretch=1)
        self._v_layout_output.addWidget(self._l_name_output)
        self._v_layout_output.addWidget(self._l_path_output)

        self._h_layout.addWidget(self._op_icon, stretch=1)
        self._h_layout.addWidget(self._l_mode, stretch=1)

        self._h_layout.addWidget(self._l_time, alignment=Qt.AlignRight)

        self.clicked.connect(self._on_click)

    def set_data(self, data: HistoryRecord):
        self._input_path = data.input_path
        self._output_path = data.output_path
        self._status_description = data.status_description
        self._mode = data.mode
        self._status = data.status

        self._status_icon.setIcon(InfoBarIcon.SUCCESS if data.status else InfoBarIcon.ERROR)
        self._set_elided_text(self._l_name_input, Path(self._input_path).name)
        self._set_elided_text(self._l_name_output, Path(self._output_path).name)
        self._set_elided_text(self._l_path_input, self._input_path)
        self._set_elided_text(self._l_path_output, self._output_path)
        self._set_elided_text(self._l_mode, self._mode)

        icon = LockIcons.LOCK if data.operation == OperationType.ENCRYPT else LockIcons.UNLOCK
        icon = icon.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._op_icon.setIcon(icon)

        self._l_time.setText(datetime.fromtimestamp(data.time).strftime('%Y-%m-%d %H:%M'))

    def resizeEvent(self, a0):
        self._update_text()
        super().resizeEvent(a0)

    def _update_text(self):
        max_width = int(
            (self.width() - self._op_icon.width() - self._status_icon.width() -
             self._l_time.width() - 7 * self._h_layout.spacing()) / 3)
        self._w1.setMaximumWidth(max_width)
        self._w2.setMaximumWidth(max_width)
        self._l_name_input.setMaximumWidth(max_width)
        self._l_path_input.setMaximumWidth(max_width)
        self._l_name_output.setMaximumWidth(max_width)
        self._l_path_output.setMaximumWidth(max_width)
        self._l_mode.setMaximumWidth(max_width)

        self._set_elided_text(self._l_name_input, Path(self._input_path).name)
        self._set_elided_text(self._l_path_input, self._input_path)
        self._set_elided_text(self._l_name_output, Path(self._output_path).name)
        self._set_elided_text(self._l_path_output, self._output_path)
        self._set_elided_text(self._l_mode, self._mode)

    @staticmethod
    def _set_elided_text(label: QLabel, text: str):
        metrics = QFontMetrics(label.font())
        elided = metrics.elidedText(text, Qt.ElideMiddle, label.maximumWidth())
        label.setText(elided)


class History(SimpleCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._db: DataBase = DataBase()
        self._locales: Locales = Locales()
        self._vl_view_layout: QVBoxLayout = QVBoxLayout(self)
        self._history_list: PagedListView = PagedListView(HistoryCard, parent=self)
        self._pager: PipsPager = PipsPager(self)

        self.__init_widgets()

        self._history_list.set_items({record.idx: record for record in self._db.get_history()})

    def __init_widgets(self):
        self._vl_view_layout.setContentsMargins(8, 8, 8, 8)
        self._vl_view_layout.setSpacing(8)
        self._vl_view_layout.setAlignment(Qt.AlignTop)

        self._pager.setNextButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)
        self._pager.setPreviousButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)

        self._vl_view_layout.addWidget(self._history_list)
        self._vl_view_layout.addWidget(self._pager, alignment=Qt.AlignCenter)

        self._history_list.pagination_changed.connect(self._on_pagination_changed)
        self._pager.currentIndexChanged.connect(lambda index: self._history_list.set_page(index))
        self._db.events.sig_add_history_record.connect(self._history_list.add_item)
        self._db.events.sig_strip_last_history_records.connect(self._history_list.strip_last_items)

    def clear(self):
        message_box = MessageBox(title=self._locales.get_string('clear_history_description'),
                                 description=self._locales.get_string('clear_history_message'),
                                 parent=find_mega_parent(self))

        message_box.yesButton.setText(self._locales.get_string('yes'))
        message_box.cancelButton.setText(self._locales.get_string('no'))

        if message_box.exec():
            self._history_list.clear_items()
            self._db.clear_history()
            self._pager.setPageNumber(0)
            self._pager.setVisibleNumber(0)

    def _on_pagination_changed(self, current_page: int, total_pages: int):
        self._pager.setPageNumber(total_pages)
        self._pager.setVisibleNumber(min(total_pages, 50))
        self._pager.setCurrentIndex(current_page)
