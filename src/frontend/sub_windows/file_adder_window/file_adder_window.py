import os.path
from enum import Enum
from typing import TypedDict, Optional

from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QIcon, QColor, QFontMetrics
from PyQt5.QtWidgets import QHBoxLayout, QWidget, QFileDialog
from qfluentwidgets import MessageBoxBase, SubtitleLabel, BodyLabel, LineEdit, PrimaryToolButton, FluentIcon, ComboBox

from src.backend.db.data_base import DataBase
from src.backend.db.db_records import OperationType
from src.backend.encrypt_libs.loader import Loader
from src.locales.locales import Locales
from src.utils.config import Config


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

        self._b_picker.setIcon(FluentIcon.DICTIONARY_ADD)
        self._b_picker.setIconSize(QSize(20, 20))

        self._layout.addWidget(self._l_text)
        self._layout.addSpacing(16)

        self._layout.addWidget(self._le_text)
        self._layout.addSpacing(4)

        self._layout.addWidget(self._b_picker)


locales = Locales()
map_task_type_to_operation: dict[str, OperationType] = {
    locales.get_string(OperationType.ENCRYPT.name): OperationType.ENCRYPT,
    locales.get_string(OperationType.DECRYPT.name): OperationType.DECRYPT
}


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
        self._cb_task_type: ComboBox = ComboBox(self)
        self._cb_cipher: ComboBox = ComboBox(self)
        self._cb_mode: ComboBox = ComboBox(self)

        self.__init_widgets()

    def __init_widgets(self):
        self._l_title.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._l_title.setText(self._locales.get_string('start_task'))

        self._cb_task_type.addItems([self._locales.get_string(OperationType.ENCRYPT.name),
                                self._locales.get_string(OperationType.DECRYPT.name)])
        self._cb_cipher.addItems(self._loader.available_modes.keys())
        self._update_modes()

        self._h_layout.setContentsMargins(0, 0, 0, 0)
        self._h_layout.setSpacing(4)
        self._h_layout.setAlignment(Qt.AlignVCenter)

        self.viewLayout.addWidget(self._l_title)
        self.viewLayout.addSpacing(self.viewLayout.spacing())
        self.viewLayout.addWidget(self._input_picker)
        self.viewLayout.addWidget(self._output_picker)

        self.viewLayout.addLayout(self._h_layout)
        self._h_layout.addWidget(self._cb_task_type)
        self._h_layout.addWidget(self._cb_cipher)
        self._h_layout.addWidget(self._cb_mode)

        self._input_picker.sig_file_opened.connect(self._output_picker.set_path)
        self._cb_cipher.currentIndexChanged.connect(self._update_modes)

    def _update_modes(self):
        self._cb_mode.clear()
        try:
            self._cb_mode.addItems(self._loader.available_modes[self._cb_cipher.currentText()])
        except:
            pass
