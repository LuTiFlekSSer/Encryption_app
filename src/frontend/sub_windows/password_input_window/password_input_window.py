from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QSizePolicy, QWidget
from qfluentwidgets import MessageBoxBase, SubtitleLabel, PasswordLineEdit, TeachingTipView, InfoBarIcon, \
    PopupTeachingTip, HyperlinkLabel

from src.backend.db.data_base import DataBase
from src.backend.db.db_records import OperationType
from src.backend.encrypt_libs.errors import InvalidKeyError
from src.backend.encrypt_libs.loader import micro_ciphers
from src.frontend.sub_windows.message_box.message_box import MessageBox
from src.locales.locales import Locales
from src.utils.config import Config
from src.utils.utils import find_mega_parent


class PasswordInput(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.widget.setMinimumWidth(480)

        self._l_title: SubtitleLabel = SubtitleLabel(self)
        self._le_password: PasswordLineEdit = PasswordLineEdit(self)
        self._btn_reset_master_key: HyperlinkLabel = HyperlinkLabel(self)

        self._locales: Locales = Locales()
        self._db: DataBase = DataBase()

        self._hmi: QWidget = find_mega_parent(self)
        self._need_reset: bool = False

        self._mb_reset_master_key = MessageBox(title=self._locales.get_string('reset_master_key_description'),
                                               description=self._locales.get_string('reset_master_key_message'),
                                               parent=self._hmi)
        self._mb_reset_master_key.yesButton.setText(self._locales.get_string('yes'))
        self._mb_reset_master_key.cancelButton.setText(self._locales.get_string('no'))

        self.__init_widgets()

    def __init_widgets(self):
        self._l_title.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._l_title.setText(self._locales.get_string('unlock_passwords'))

        self._le_password.setPlaceholderText(self._locales.get_string('master_key_placeholder'))

        self._btn_reset_master_key.setText(self._locales.get_string('reset_master_key'))
        self._btn_reset_master_key.clicked.connect(self._on_reset_master_key)
        self._btn_reset_master_key.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.viewLayout.addWidget(self._l_title)
        self.viewLayout.addSpacing(self.viewLayout.spacing())
        self.viewLayout.addWidget(self._le_password)
        self.viewLayout.addWidget(self._btn_reset_master_key)

    def _check_password(self) -> bool:
        encrypted_signature = self._db.get_password_signature()
        cipher_mode = self._db.get_setting('password_cipher')

        try:
            signature = micro_ciphers[cipher_mode](
                self._le_password.text().strip(),
                encrypted_signature,
                OperationType.DECRYPT
            )

            return signature == Config.SIGNATURE
        except InvalidKeyError:
            return False

    def _on_reset_master_key(self):
        if self._mb_reset_master_key.exec():
            self._need_reset = True
            self.accept()

    def validate(self) -> bool:
        if self._le_password.text().strip() == '':
            view = TeachingTipView(
                title=self._locales.get_string('error'),
                content=self._locales.get_string('passwords_empty'),
                icon=InfoBarIcon.ERROR,
                parent=self,
            )

            tip = PopupTeachingTip.make(
                view=view,
                target=self._le_password,
                duration=-1,
                parent=self
            )

            view.closed.connect(tip.close)

            return False

        if not self._check_password():
            view = TeachingTipView(
                title=self._locales.get_string('error'),
                content=self._locales.get_string('wrong_password'),
                icon=InfoBarIcon.ERROR,
                parent=self,
            )

            tip = PopupTeachingTip.make(
                view=view,
                target=self._le_password,
                duration=-1,
                parent=self
            )

            view.closed.connect(tip.close)

            return False

        return True

    def get_password(self) -> str:
        return self._le_password.text().strip()

    def need_reset(self) -> bool:
        return self._need_reset

    def keyPressEvent(self, a0):
        if a0.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.yesButton.clicked.emit()
        else:
            super().keyPressEvent(a0)

    def reset(self):
        self._le_password.clear()
        self._need_reset = False
