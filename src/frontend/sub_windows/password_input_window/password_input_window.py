from PyQt5.QtGui import QColor
from qfluentwidgets import MessageBoxBase, SubtitleLabel, PasswordLineEdit, TeachingTipView, InfoBarIcon, \
    PopupTeachingTip

from src.backend.db.data_base import DataBase
from src.backend.db.db_records import OperationType
from src.backend.encrypt_libs.loader import micro_ciphers
from src.locales.locales import Locales
from src.utils.config import Config


class PasswordInput(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.widget.setMinimumWidth(480)

        self._l_title: SubtitleLabel = SubtitleLabel()
        self._le_password: PasswordLineEdit = PasswordLineEdit()

        self._locales: Locales = Locales()
        self._db: DataBase = DataBase()

        self.__init_widgets()

    def __init_widgets(self):
        self._l_title.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._l_title.setText(self._locales.get_string('unlock_passwords'))

        self._le_password.setPlaceholderText(self._locales.get_string('master_key_placeholder'))

        self.viewLayout.addWidget(self._l_title)
        self.viewLayout.addWidget(self._le_password)

    def _check_password(self) -> bool:
        encrypted_signature = self._db.get_password_signature()
        cipher_mode = self._db.get_setting('password_cipher')

        signature = micro_ciphers[cipher_mode](
            self._le_password.text().strip(),
            encrypted_signature,
            OperationType.DECRYPT
        )

        return signature == Config.SIGNATURE

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
