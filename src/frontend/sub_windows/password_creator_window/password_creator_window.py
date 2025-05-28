from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from qfluentwidgets import MessageBoxBase, SubtitleLabel, PasswordLineEdit, TeachingTipView, PopupTeachingTip, \
    InfoBarIcon, LineEdit

from src.backend.db.db_records import PasswordRecord
from src.locales.locales import Locales
from src.streebog.streebog import Streebog
from src.utils.config import Config


class PasswordCreator(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.widget.setMinimumWidth(480)

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
        self.viewLayout.addSpacing(self.viewLayout.spacing())
        self.viewLayout.addWidget(self._le_password_name)
        self.viewLayout.addWidget(self._le_password)
        self.viewLayout.addWidget(self._le_confirm_password)

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

        if self._le_password_name.text().strip() == '':
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
        record.name = self._le_password_name.text().strip()
        record.password = Streebog.calc_hash(self._le_password.text().strip().encode())

        return record

    def set_password(self, password: str):
        self._le_password.setText(password)
        self._le_confirm_password.setText(password)

    def keyPressEvent(self, a0):
        if a0.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.yesButton.clicked.emit()
        else:
            super().keyPressEvent(a0)

    def reset(self):
        self._le_password_name.clear()
        self._le_password.clear()
        self._le_confirm_password.clear()
