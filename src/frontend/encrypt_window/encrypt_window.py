from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import LargeTitleLabel

from src.frontend.encrypt_window.encrypt_list import EncryptList
from src.frontend.encrypt_window.encrypt_menu import EncryptMenu
from src.frontend.style_sheets.style_sheets import StyleSheet
from src.locales.locales import Locales
from src.utils.config import Config


class EncryptWindow(QWidget):
    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.setObjectName(name.replace(' ', '-'))

        self._locales: Locales = Locales()

        self._vl_view_layout: QVBoxLayout = QVBoxLayout(self)
        self._l_title: LargeTitleLabel = LargeTitleLabel(self)
        self._encrypt_menu: EncryptMenu = EncryptMenu(self)
        self._encrypt_list: EncryptList = EncryptList(self)

        self.__init_widgets()
        self._connect_widget_actions()

    def __init_widgets(self):
        StyleSheet.ENCRYPT_WINDOW.apply(self)

        self._vl_view_layout.setContentsMargins(28, 12, 28, 28)
        self._vl_view_layout.setSpacing(0)
        self._vl_view_layout.setAlignment(Qt.AlignTop)

        self._l_title.setText(self._locales.get_string('encrypt_title'))
        self._l_title.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))

        self._vl_view_layout.addWidget(self._l_title)
        self._vl_view_layout.addSpacing(32)

        self._vl_view_layout.addWidget(self._encrypt_menu)
        self._vl_view_layout.addSpacing(4)

        self._vl_view_layout.addWidget(self._encrypt_list)

    def _connect_widget_actions(self):
        pass
