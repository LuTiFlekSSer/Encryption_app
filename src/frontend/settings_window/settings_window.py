from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import ScrollArea, LargeTitleLabel

from src.frontend.settings_window.settings import AppSettings, EncryptionSettings
from src.frontend.style_sheets.style_sheets import StyleSheet
from src.locales.locales import Locales
from src.utils.config import Config


class SettingsWindow(ScrollArea):
    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.setObjectName(name.replace(' ', '-'))

        self._locales: Locales = Locales()

        self._w_view: QWidget = QWidget(self)
        self._vl_view_layout: QVBoxLayout = QVBoxLayout(self._w_view)
        self._l_title: LargeTitleLabel = LargeTitleLabel(self)

        self._encryption_settings: EncryptionSettings = EncryptionSettings(self)
        self._app_settings: AppSettings = AppSettings(self)

        self.__init_widgets()
        self._connect_widget_actions()

    def __init_widgets(self):
        StyleSheet.SETTINGS_WINDOW.apply(self)

        self._w_view.setObjectName('w_view')
        self._l_title.setText(self._locales.get_string('settings'))
        self._l_title.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))

        self._vl_view_layout.setContentsMargins(28, 12, 28, 28)
        self._vl_view_layout.setSpacing(0)
        self._vl_view_layout.setAlignment(Qt.AlignTop)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self._w_view)
        self.setWidgetResizable(True)

        self._vl_view_layout.addWidget(self._l_title)
        self._vl_view_layout.addSpacing(32)

        self._vl_view_layout.addWidget(self._encryption_settings)
        self._vl_view_layout.addSpacing(16)

        self._vl_view_layout.addWidget(self._app_settings)
        self._vl_view_layout.addSpacing(16)

    def _connect_widget_actions(self):
        pass
