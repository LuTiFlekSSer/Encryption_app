from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QVBoxLayout
from qfluentwidgets import SimpleCardWidget, PipsPager, PipsScrollButtonDisplayMode

from src.frontend.paged_list_view import PagedListView


class HistoryRecord(SimpleCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_data(self, data):
        pass


class History(SimpleCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._vl_view_layout: QVBoxLayout = QVBoxLayout(self)
        self._history_list: PagedListView = PagedListView(HistoryRecord, parent=self)
        self._pager: PipsPager = PipsPager(self)

        self.__init_widgets()

        self._history_list.set_items([0 for i in range(100000)])

    def __init_widgets(self):
        self._vl_view_layout.setContentsMargins(8, 8, 8, 8)
        self._vl_view_layout.setSpacing(8)
        self._vl_view_layout.setAlignment(Qt.AlignTop)

        self._pager.setNextButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)
        self._pager.setPreviousButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)

        self._vl_view_layout.addWidget(self._history_list)
        self._vl_view_layout.addWidget(self._pager, alignment=Qt.AlignCenter)

    def reset_page(self):
        self._history_list.set_page(0)
        self._pager.setPageNumber(self._history_list.get_total_pages())
        self._pager.setVisibleNumber(min(self._history_list.get_total_pages(), 50))

    def clear(self):
        self._history_list.clear_items()
        self._pager.setPageNumber(0)
        self._pager.setVisibleNumber(0)