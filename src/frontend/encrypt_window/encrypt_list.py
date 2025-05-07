from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout, QLabel, QHBoxLayout, QWidget
from qfluentwidgets import CardWidget, SimpleCardWidget, PipsPager, PipsScrollButtonDisplayMode, IconWidget, \
    StrongBodyLabel, CaptionLabel

from src.frontend.paged_list_view import PagedListView
from src.locales.locales import Locales


class StatusWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)


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
        self._l_status: StatusWidget = StatusWidget(self)
        self._l_mode: StrongBodyLabel = StrongBodyLabel(self)
        self._op_icon: IconWidget = IconWidget(self)
        self._l_time: StrongBodyLabel = StrongBodyLabel(self)

        self._name: str = ''

    def set_data(self, data):
        pass

    @staticmethod
    def _set_elided_text(label: QLabel, text: str):
        metrics = QFontMetrics(label.font())
        elided = metrics.elidedText(text, Qt.ElideMiddle, label.width())
        label.setText(elided)


class EncryptList(SimpleCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._locales: Locales = Locales()
        self._vl_view_layout: QVBoxLayout = QVBoxLayout(self)
        self._encrypt_list: PagedListView = PagedListView(EncryptCard, parent=self)
        self._pager: PipsPager = PipsPager(self)

        self.__init_widgets()

        self._encrypt_list.add_item('sosal')

    def __init_widgets(self):
        self._pager.setNextButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)
        self._pager.setPreviousButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)

        self._vl_view_layout.setContentsMargins(8, 8, 8, 8)
        self._vl_view_layout.setSpacing(8)
        self._vl_view_layout.setAlignment(Qt.AlignTop)

        self._vl_view_layout.addWidget(self._encrypt_list)
        self._vl_view_layout.addWidget(self._pager, alignment=Qt.AlignCenter)

        self._encrypt_list.pagination_changed.connect(self._on_pagination_changed)

    def _on_pagination_changed(self, current_page: int, total_pages: int):
        self._pager.setPageNumber(total_pages)
        self._pager.setVisibleNumber(min(total_pages, 50))
        self._pager.setCurrentIndex(current_page)
