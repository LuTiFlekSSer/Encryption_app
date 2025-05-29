from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import LargeTitleLabel, InfoBarPosition, InfoBar

from src.backend.db.db_records import OperationType
from src.frontend.encrypt_window.encrypt_list import EncryptList
from src.frontend.encrypt_window.encrypt_menu import EncryptMenu
from src.frontend.style_sheets.style_sheets import StyleSheet
from src.frontend.sub_windows.file_adder_window.file_adder_window import FileAdder
from src.global_flags import GlobalFlags
from src.locales.locales import Locales
from src.utils.config import Config
from src.utils.utils import find_mega_parent


class EncryptWindow(QWidget):
    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.setObjectName(name.replace(' ', '-'))

        self._locales: Locales = Locales()

        self._vl_view_layout: QVBoxLayout = QVBoxLayout(self)
        self._l_title: LargeTitleLabel = LargeTitleLabel(self)
        self._encrypt_menu: EncryptMenu = EncryptMenu(self)
        self._encrypt_list: EncryptList = EncryptList(self)

        self._global_flags: GlobalFlags = GlobalFlags()

        from src.frontend.hmi import MainWindow
        self._hmi: MainWindow = find_mega_parent(self)

        self._file_adder = FileAdder(self._hmi)
        self._file_adder.yesButton.setText(self._locales.get_string('confirm'))
        self._file_adder.cancelButton.setText(self._locales.get_string('cancel'))

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
        self._encrypt_menu.sig_add_new_task.connect(self._on_sig_add_task)
        self._hmi.sig_add_task.connect(self._on_sig_add_task)
        self._hmi.sig_external_command.connect(self._on_sig_external_command)

    def _on_sig_external_command(self, operation_type: OperationType, data: str):
        if self._global_flags.modal_open.is_set():
            InfoBar.error(
                title=self._locales.get_string('error'),
                content=self._locales.get_string('finish_current_task'),
                orient=Qt.Horizontal,
                isClosable=False,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,
                parent=self
            )

            return

        self._on_sig_add_task(data, operation_type)

    def _on_sig_add_task(self, input_path: str = '', operation_type: OperationType = OperationType.ENCRYPT):
        if self._hmi.stackedWidget.currentWidget() is not self:
            self._hmi.stackedWidget.setCurrentWidget(self)

        self._global_flags.modal_open.set()

        self._file_adder.reset()
        self._file_adder.set_default_data(input_path, operation_type)

        if self._file_adder.exec():
            try:
                data = self._file_adder.get_data()
            except Exception:
                data = {}

            self._encrypt_list.add_task(data)

        self._global_flags.modal_open.clear()
