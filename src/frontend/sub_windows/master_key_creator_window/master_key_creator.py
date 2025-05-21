from PyQt5.QtGui import QColor
from qfluentwidgets import MessageBoxBase, SubtitleLabel, PasswordLineEdit, ComboBox, TeachingTipView, PopupTeachingTip, \
    InfoBarIcon

from src.backend.encrypt_libs.loader import micro_ciphers
from src.locales.locales import Locales
from src.utils.config import Config


class MasterKeyCreator(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.widget.setMinimumWidth(480)

        self._l_title: SubtitleLabel = SubtitleLabel(self)
        self._le_password: PasswordLineEdit = PasswordLineEdit(self)
        self._le_confirm_password: PasswordLineEdit = PasswordLineEdit(self)
        self._cb_encrypt_mode: ComboBox = ComboBox(self)

        self._locales: Locales = Locales()

        self.__init_widgets()

    def __init_widgets(self):
        self._l_title.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._l_title.setText(self._locales.get_string('create_master_key'))

        self._le_password.setPlaceholderText(self._locales.get_string('password_placeholder'))
        self._le_confirm_password.setPlaceholderText(self._locales.get_string('confirm_password_placeholder'))

        self._cb_encrypt_mode.addItems(micro_ciphers.keys())

        self.viewLayout.addWidget(self._l_title)
        self.viewLayout.addWidget(self._le_password)
        self.viewLayout.addWidget(self._le_confirm_password)
        self.viewLayout.addWidget(self._cb_encrypt_mode)

    def validate(self) -> bool:
        if self._le_password.text().strip() != self._le_confirm_password.text().strip():
            view = TeachingTipView(
                title=self._locales.get_string('error'),
                content=self._locales.get_string('passwords_mismatch'),
                icon=InfoBarIcon.ERROR,
                parent=self,
            )

            tip = PopupTeachingTip.make(
                view=view,
                target=self._le_confirm_password,
                duration=-1,
                parent=self
            )

            view.closed.connect(tip.close)

            return False

        if len(self._le_password.text().strip()) == 0:
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

        if len(self._cb_encrypt_mode.items) == 0:
            view = TeachingTipView(
                title=self._locales.get_string('error'),
                content=self._locales.get_string('no_ciphers'),
                icon=InfoBarIcon.ERROR,
                parent=self,
            )

            tip = PopupTeachingTip.make(
                view=view,
                target=self._cb_encrypt_mode,
                duration=-1,
                parent=self
            )

            view.closed.connect(tip.close)

            return False

        return True

    def get_password(self) -> str:
        return self._le_password.text().strip()

    def get_encrypt_mode(self) -> str:
        return self._cb_encrypt_mode.currentText().strip()
