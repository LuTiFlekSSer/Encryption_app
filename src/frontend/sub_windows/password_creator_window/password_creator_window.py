import hashlib

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QVBoxLayout
from qfluentwidgets import MessageBoxBase, SubtitleLabel, PasswordLineEdit, TeachingTipView, PopupTeachingTip, \
    InfoBarIcon, LineEdit

from src.backend.db.db_records import PasswordRecord
from src.locales.locales import Locales
from src.utils.config import Config


class PasswordCreator(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.widget.setMinimumWidth(480)

        self.layout: QVBoxLayout = QVBoxLayout()
        self._l_title: SubtitleLabel = SubtitleLabel(self)
        self._le_password_name: LineEdit = LineEdit(self)
        self._le_password: PasswordLineEdit = PasswordLineEdit(self)
        self._le_confirm_password: PasswordLineEdit = PasswordLineEdit(self)

        self._locales: Locales = Locales()

        self.__init_widgets()

    def __init_widgets(self):
        self._l_title.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._l_title.setText(self._locales.get_string('create_password'))

        self._le_password_name.setPlaceholderText(self._locales.get_string('password_name_placeholder'))
        self._le_password.setPlaceholderText(self._locales.get_string('password_placeholder'))
        self._le_confirm_password.setPlaceholderText(self._locales.get_string('confirm_password_placeholder'))

        self.viewLayout.addWidget(self._l_title)
        self.viewLayout.addWidget(self._le_password_name)
        self.viewLayout.addWidget(self._le_password)
        self.viewLayout.addWidget(self._le_confirm_password)

    def validate(self) -> bool:
        if self._le_password.text() != self._le_confirm_password.text():
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

        if len(self._le_password.text()) == 0:
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

        if self._le_password_name.text() == '':
            view = TeachingTipView(
                title=self._locales.get_string('error'),
                content=self._locales.get_string('no_name'),
                icon=InfoBarIcon.ERROR,
                parent=self,
            )

            tip = PopupTeachingTip.make(
                view=view,
                target=self._le_password_name,
                duration=-1,
                parent=self
            )

            view.closed.connect(tip.close)

            return False

        return True

    def get_password_record(self) -> PasswordRecord:
        record = PasswordRecord()
        record.name = self._le_password_name.text()
        record.password = hashlib.sha512(self._le_password.text().encode()).digest()  # todo PBKDF2

        return record
