import os.path
from enum import Enum
from typing import TypedDict, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QColor, QFontMetrics
from PyQt5.QtWidgets import QHBoxLayout, QWidget, QFileDialog, QVBoxLayout, QSizePolicy, QStackedWidget
from qfluentwidgets import MessageBoxBase, SubtitleLabel, BodyLabel, LineEdit, PrimaryToolButton, FluentIcon, ComboBox, \
    SegmentedToggleToolWidget, SegmentedWidget, PasswordLineEdit, HyperlinkLabel

from src.backend.db.data_base import DataBase
from src.backend.db.db_records import OperationType
from src.backend.encrypt_libs.loader import Loader
from src.frontend.icons.icons import CustomIcons
from src.locales.locales import Locales
from src.utils.config import Config
from src.utils.utils import find_mega_parent


class Status(Enum):
    WAITING = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    FAILED = 3


TEncryptData = TypedDict('TEncryptData', {
    'uid': str,
    'input_file': str,
    'output_file': str,
    'mode': str,
    'operation': OperationType,
    'total': int,
    'current': int,
    'status': Status,
    'hash_password': str,
    'file_size': str,
    'file_icon': QIcon,
    'status_description': str,
    'start_time': float,
    'estimated_time_per_step': Optional[float],
    'last_eta_update': float
})


class PickerType(Enum):
    OPEN = 0
    SAVE = 1


class FilePicker(QWidget):
    sig_file_opened: pyqtSignal = pyqtSignal(str)

    def __init__(self, text: str, picker_type: PickerType, parent=None):
        super().__init__(parent)

        self._layout: QHBoxLayout = QHBoxLayout(self)
        self._l_text: BodyLabel = BodyLabel(self)
        self._le_text: LineEdit = LineEdit(self)
        self._b_picker: PrimaryToolButton = PrimaryToolButton(self)

        self._path: str = ''
        self._locales: Locales = Locales()
        self._db: DataBase = DataBase()

        self.__init_widgets(text)

        self._b_picker.clicked.connect(lambda _, p=picker_type: self._on_picker_clicked(p))

    def _on_picker_clicked(self, picker_type: PickerType):
        directory = self._db.get_setting('last_input_path')
        if not os.path.exists(directory):
            directory = '.'
            self._db.set_setting('last_input_path', directory)

        if picker_type == PickerType.OPEN:
            file_path, _ = QFileDialog.getOpenFileName(
                parent=None,
                caption=self._locales.get_string('select_input_path'),
                directory=directory,
                filter=self._locales.get_string('filter')
            )

        else:
            if self._path != '' and os.path.exists(self._path):
                directory = self._path

            file_path, _ = QFileDialog.getSaveFileName(
                parent=None,
                caption=self._locales.get_string('select_output_path'),
                directory=directory,
                filter=self._locales.get_string('filter')
            )

        if file_path:
            if picker_type == PickerType.OPEN:
                self._db.set_setting('last_input_path', os.path.dirname(file_path))

            self._path = file_path
            self._set_elided_text(self._le_text, file_path)

            self.sig_file_opened.emit(self._path)

    def get_path(self) -> str:
        return self._path

    def set_path(self, path: str):
        if self._path == '':
            self._path = path
            self._set_elided_text(self._le_text, self._path)

    @staticmethod
    def _set_elided_text(edit: LineEdit, text: str):
        metrics = QFontMetrics(edit.font())
        elided = metrics.elidedText(text, Qt.ElideMiddle, edit.width() - 20)
        edit.setText(elided)

    def __init_widgets(self, text: str):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)

        self._l_text.setText(text)
        self._l_text.setTextColor(Config.GRAY_COLOR_900, Config.GRAY_COLOR_50)

        self._le_text.setReadOnly(True)

        self._b_picker.setIcon(FluentIcon.ADD_TO)

        self._layout.addWidget(self._l_text)
        self._layout.addSpacing(16)

        self._layout.addWidget(self._le_text)
        self._layout.addWidget(self._b_picker)


class TitledComboBox(QWidget):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)

        self._layout: QVBoxLayout = QVBoxLayout(self)
        self._l_text: BodyLabel = BodyLabel(text, self)
        self.cb_items: ComboBox = ComboBox(self)

        self.__init_widgets()

    def __init_widgets(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self._layout.setAlignment(Qt.AlignTop)

        self._layout.addWidget(self._l_text)
        self._layout.addWidget(self.cb_items)

    def update_items(self, items: list[str]):
        self.cb_items.clear()
        self.cb_items.addItems(items)


class NewPasswordWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._locales: Locales = Locales()

        self._layout: QVBoxLayout = QVBoxLayout(self)
        self._le_password: PasswordLineEdit = PasswordLineEdit(self)
        self._btn_save: HyperlinkLabel = HyperlinkLabel(self)

        self.__init_widgets()

    def __init_widgets(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self._layout.setAlignment(Qt.AlignTop)

        self._le_password.setPlaceholderText(self._locales.get_string('password_placeholder'))
        self._btn_save.setText(self._locales.get_string('save_password'))

        self._layout.addWidget(self._le_password)
        self._layout.addWidget(self._btn_save)


class SavedPasswordWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._layout: QVBoxLayout = QVBoxLayout(self)
        self.cb_password: ComboBox = ComboBox(self)
        self._widget: QWidget = QWidget(self)

        self.__init_widgets()

    def __init_widgets(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._layout.addWidget(self.cb_password)
        self._layout.addWidget(self._widget)


class PasswordPicker(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self._locales: Locales = Locales()

        from src.frontend.hmi import MainWindow
        self._hmi: MainWindow = find_mega_parent(self)

        self._layout: QVBoxLayout = QVBoxLayout(self)
        self._l_password: BodyLabel = BodyLabel(self)
        self._stacked_widget: QStackedWidget = QStackedWidget(self)
        self._sw_mode: SegmentedWidget = SegmentedWidget(self)
        self._saved_passwords: SavedPasswordWidget = SavedPasswordWidget(self)
        self._password_widget: NewPasswordWidget = NewPasswordWidget(self)

        self.__init_widgets()

    def __init_widgets(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self._layout.setAlignment(Qt.AlignTop)

        self._l_password.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._l_password.setText(self._locales.get_string('password'))

        self._password_widget.setObjectName("password_widget")

        self._saved_passwords.setObjectName("cb_password")

        self._stacked_widget.addWidget(self._password_widget)
        self._stacked_widget.addWidget(self._saved_passwords)

        self._sw_mode.addItem(
            self._password_widget.objectName(),
            self._locales.get_string('new_password'),
            onClick=lambda: self._stacked_widget.setCurrentWidget(self._password_widget)
        )
        self._sw_mode.addItem(
            self._saved_passwords.objectName(),
            self._locales.get_string('saved_password'),
            onClick=self._on_saved_passwords
        )
        self._sw_mode.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self._stacked_widget.currentChanged.connect(self._on_sig_current_index_changed)
        self._stacked_widget.setCurrentWidget(self._password_widget)
        self._sw_mode.setCurrentItem(self._password_widget.objectName())

        self._layout.addWidget(self._l_password)
        self._layout.addWidget(self._sw_mode)
        self._layout.addSpacing(4)
        self._layout.addWidget(self._stacked_widget)

    def _on_saved_passwords(self):
        if self._sw_mode.currentRouteKey() == self._saved_passwords.objectName():
            self._hmi.sig_check_passwords.emit()
        else:
            self._stacked_widget.setCurrentWidget(self._saved_passwords)

    def _on_sig_current_index_changed(self, index: int):
        widget = self._stacked_widget.widget(index)
        self._sw_mode.setCurrentItem(widget.objectName())


class FileAdder(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.widget.setMinimumWidth(480)

        self._locales: Locales = Locales()
        self._loader: Loader = Loader()

        self._l_title: SubtitleLabel = SubtitleLabel(self)
        self._input_picker: FilePicker = FilePicker(self._locales.get_string('input_file'), PickerType.OPEN, self)
        self._output_picker: FilePicker = FilePicker(self._locales.get_string('output_file'), PickerType.SAVE, self)
        self._h_layout: QHBoxLayout = QHBoxLayout()
        self._v_type_layout: QVBoxLayout = QVBoxLayout()
        self._l_type_text: BodyLabel = BodyLabel(self)
        self._tw_task_type: SegmentedToggleToolWidget = SegmentedToggleToolWidget(self)
        self._cb_cipher: TitledComboBox = TitledComboBox(self._locales.get_string('algorithm'), self)
        self._cb_mode: TitledComboBox = TitledComboBox(self._locales.get_string('mode'), self)
        self._password_picker: PasswordPicker = PasswordPicker(self)

        self.__init_widgets()

    def __init_widgets(self):
        self._l_title.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._l_title.setText(self._locales.get_string('start_task'))

        self._l_type_text.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._l_type_text.setText(self._locales.get_string('task_type'))

        self._tw_task_type.addItem(
            routeKey=OperationType.ENCRYPT.name,
            icon=CustomIcons.LOCK.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50)),
            onClick=self._on_task_type_encrypt
        )
        self._tw_task_type.addItem(
            routeKey=OperationType.DECRYPT.name,
            icon=CustomIcons.UNLOCK.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50)),
            onClick=self._on_task_type_decrypt
        )
        self._tw_task_type.setCurrentItem(OperationType.ENCRYPT.name)
        self._tw_task_type.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self._cb_cipher.cb_items.addItems(self._loader.available_modes.keys())
        self._update_modes()

        self._h_layout.setContentsMargins(0, 0, 0, 0)
        self._h_layout.setSpacing(4)
        self._h_layout.setAlignment(Qt.AlignVCenter)

        self._v_type_layout.setContentsMargins(0, 0, 0, 0)
        self._v_type_layout.setSpacing(4)
        self._v_type_layout.setAlignment(Qt.AlignTop)

        self.viewLayout.addWidget(self._l_title)
        self.viewLayout.addSpacing(self.viewLayout.spacing())
        self.viewLayout.addWidget(self._input_picker)
        self.viewLayout.addWidget(self._output_picker)

        self.viewLayout.addLayout(self._h_layout)
        self._h_layout.addLayout(self._v_type_layout)
        self._v_type_layout.addWidget(self._l_type_text)
        self._v_type_layout.addWidget(self._tw_task_type)
        self._h_layout.addWidget(self._cb_cipher)
        self._h_layout.addWidget(self._cb_mode)
        self.viewLayout.addWidget(self._password_picker)

        self._input_picker.sig_file_opened.connect(self._output_picker.set_path)
        self._cb_cipher.cb_items.currentIndexChanged.connect(self._update_modes)

    def _update_modes(self):
        self._cb_mode.cb_items.clear()
        try:
            self._cb_mode.cb_items.addItems(self._loader.available_modes[self._cb_cipher.cb_items.currentText()])
        except:
            pass

    def _on_task_type_encrypt(self):
        self._h_layout.addWidget(self._cb_cipher)
        self._h_layout.addWidget(self._cb_mode)
        self._cb_cipher.setVisible(True)
        self._cb_mode.setVisible(True)

    def _on_task_type_decrypt(self):
        self._h_layout.removeWidget(self._cb_cipher)
        self._h_layout.removeWidget(self._cb_mode)
        self._cb_cipher.setVisible(False)
        self._cb_mode.setVisible(False)
