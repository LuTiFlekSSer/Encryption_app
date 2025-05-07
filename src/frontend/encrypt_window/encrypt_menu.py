from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QHBoxLayout
from qfluentwidgets import SimpleCardWidget, CommandBar, Action, FluentIcon

from src.locales.locales import Locales
from src.utils.config import Config


class EncryptMenu(SimpleCardWidget):
    sig_add_new_task: pyqtSignal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._locales: Locales = Locales()

        self._vl_view_layout: QHBoxLayout = QHBoxLayout(self)
        self._command_bar: CommandBar = CommandBar(self)

        self.__init_widgets()

    def __init_widgets(self):
        self._command_bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self._command_bar.addAction(Action(
            FluentIcon.ADD.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50)),
            self._locales.get_string('add_task'),
            triggered=self.sig_add_new_task.emit,
        ))

        self._vl_view_layout.setContentsMargins(8, 8, 8, 8)
        self._vl_view_layout.setSpacing(0)
        self._vl_view_layout.setAlignment(Qt.AlignTop)

        self._vl_view_layout.addWidget(self._command_bar)
