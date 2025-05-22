from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QColor, QDesktopServices
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import DisplayLabel, FluentIcon

from src.frontend.home_window.main_cards import MainCardView
from src.locales.locales import Locales
from src.utils.config import Config
from src.utils.utils import find_mega_parent


class Banner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('w_banner')
        self._locales: Locales = Locales()

        from src.frontend.hmi import MainWindow
        self._hmi: MainWindow = find_mega_parent(self)

        self.__create_widgets()

    def __create_widgets(self):
        self._layout: QVBoxLayout = QVBoxLayout(self)
        self._layout.setSpacing(48)
        self._layout.setContentsMargins(28, 12, 0, 0)
        self._layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self._l_app_name: DisplayLabel = DisplayLabel(self)
        self._l_app_name.setObjectName('l_app_name')
        self._l_app_name.setText(Config.APP_NAME)
        self._l_app_name.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))

        self._card_view: MainCardView = MainCardView(self)

        self._card_view.add_card(FluentIcon.ADD,
                                 self._locales.get_string('add_task'),
                                 self._locales.get_string('add_task_description'),
                                 link_icon=False,
                                 callback=self._add_task_callback
                                 )
        self._card_view.add_card(FluentIcon.GITHUB,
                                 self._locales.get_string('github'),
                                 self._locales.get_string('github_description'),
                                 link_icon=True,
                                 callback=self._github_callback
                                 )

        self._layout.addWidget(self._l_app_name)
        self._layout.addWidget(self._card_view)

    def _add_task_callback(self):
        self._hmi.sig_add_task.emit()

    @staticmethod
    def _github_callback():
        QDesktopServices.openUrl(QUrl(Config.GITHUB_URL))
