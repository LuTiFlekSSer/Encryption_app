from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import LargeTitleLabel

from src.frontend.history_window.history import History
from src.frontend.history_window.history_buttons import HistoryButtonsCard
from src.frontend.style_sheets.style_sheets import StyleSheet
from src.locales.locales import Locales
from src.utils.config import Config


class HistoryWindow(QWidget):
    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.setObjectName('w_view')

        self._locales: Locales = Locales()

        self._vl_view_layout: QVBoxLayout = QVBoxLayout(self)
        self._l_title: LargeTitleLabel = LargeTitleLabel(self)
        self._buttons_card: HistoryButtonsCard = HistoryButtonsCard(self)
        self._history: History = History(self)

        self.__init_widgets()
        self._connect_widget_actions()

    def __init_widgets(self):
        StyleSheet.HISTORY_WINDOW.apply(self)

        self._l_title.setText(self._locales.get_string('history'))
        self._l_title.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))

        self._vl_view_layout.setContentsMargins(28, 12, 28, 28)
        self._vl_view_layout.setSpacing(0)
        self._vl_view_layout.setAlignment(Qt.AlignTop)

        self._vl_view_layout.addWidget(self._l_title)
        self._vl_view_layout.addSpacing(32)

        self._vl_view_layout.addWidget(self._buttons_card)
        self._vl_view_layout.addSpacing(4)

        self._vl_view_layout.addWidget(self._history)

    def _connect_widget_actions(self):
        self._buttons_card.clear_history.connect(self._clear_history)

    def _clear_history(self):
        self._history.clear()
