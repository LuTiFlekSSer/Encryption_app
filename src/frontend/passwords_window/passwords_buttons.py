from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QHBoxLayout
from qfluentwidgets import SimpleCardWidget, CommandBar, Action, FluentIcon

from src.frontend.icons.icons import CustomIcons
from src.locales.locales import Locales
from src.utils.config import Config


class PasswordsButtonsCard(SimpleCardWidget):
    add_password: pyqtSignal = pyqtSignal()
    clear_passwords: pyqtSignal = pyqtSignal()
    reset_master_key: pyqtSignal = pyqtSignal()
    lock_passwords: pyqtSignal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('buttons_card')

        self._locales: Locales = Locales()

        self._vl_view_layout: QHBoxLayout = QHBoxLayout(self)
        self._command_bar: CommandBar = CommandBar(self)

        self.__init_widgets()

    def __init_widgets(self):
        self._command_bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self._command_bar.addAction(Action(
            FluentIcon.ADD.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50)),
            self._locales.get_string('add_password'),
            triggered=self.add_password.emit,
        ))
        self._command_bar.addAction(Action(
            CustomIcons.LOCK.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50)),
            self._locales.get_string('lock_passwords'),
            triggered=self.lock_passwords.emit,
        ))
        self._command_bar.addAction(Action(
            FluentIcon.DELETE.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50)),
            self._locales.get_string('clear_passwords'),
            triggered=self.clear_passwords.emit,
        ))
        self._command_bar.addAction(Action(
            FluentIcon.ERASE_TOOL.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50)),
            self._locales.get_string('reset_master_key'),
            triggered=self.reset_master_key.emit,
        ))

        self._vl_view_layout.setContentsMargins(8, 8, 8, 8)
        self._vl_view_layout.setSpacing(0)
        self._vl_view_layout.setAlignment(Qt.AlignTop)

        self._vl_view_layout.addWidget(self._command_bar)
