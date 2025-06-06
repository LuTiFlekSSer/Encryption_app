from PyQt5.QtCore import Qt, QObject, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QFontMetrics
from PyQt5.QtWidgets import QSizePolicy, QHBoxLayout, QLabel, QVBoxLayout
from qfluentwidgets import IconWidget, StrongBodyLabel, ToolButton, SimpleCardWidget, FluentIcon, PipsPager, \
    PipsScrollButtonDisplayMode, InfoBar, InfoBarPosition

from src.backend.db.data_base import DataBase
from src.backend.db.db_records import OperationType
from src.backend.encrypt_libs.loader import micro_ciphers
from src.frontend.icons.icons import CustomIcons
from src.frontend.paged_list_view import PagedListView
from src.frontend.sub_windows.master_key_creator_window.master_key_creator import MasterKeyCreator
from src.frontend.sub_windows.message_box.message_box import MessageBox
from src.frontend.sub_windows.password_creator_window.password_creator_window import PasswordCreator
from src.frontend.sub_windows.password_input_window.password_input_window import PasswordInput
from src.global_flags import GlobalFlags
from src.locales.locales import Locales
from src.master_key_storage.master_key_storage import MasterKeyStorage
from src.utils.config import Config
from src.utils.utils import find_mega_parent


class Events(QObject):
    sig_delete_password: pyqtSignal = pyqtSignal(str)


events = Events()


class PasswordCard(SimpleCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._h_layout: QHBoxLayout = QHBoxLayout(self)
        self._password_icon: IconWidget = IconWidget(self)
        self._l_name_password: StrongBodyLabel = StrongBodyLabel(self)
        self._btn_delete: ToolButton = ToolButton(self)

        self._name: str = ''

        self.__init_widgets()

    def __init_widgets(self):
        self._password_icon.setFixedSize(32, 32)
        self._password_icon.setIcon(CustomIcons.PASSWORD.colored(
            QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50)
        ))

        self._h_layout.setContentsMargins(16, 16, 16, 16)
        self._h_layout.setSpacing(16)
        self._h_layout.setAlignment(Qt.AlignVCenter)

        self._btn_delete.setFixedSize(32, 32)
        icon = FluentIcon.DELETE.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._btn_delete.setIcon(icon)
        self._btn_delete.clicked.connect(lambda: events.sig_delete_password.emit(self._name))

        self._l_name_password.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))

        self._h_layout.addWidget(self._password_icon)
        self._h_layout.addWidget(self._l_name_password, stretch=1)
        self._h_layout.addWidget(self._btn_delete, alignment=Qt.AlignRight)

    def set_data(self, data: str):
        self._name = data
        self._set_elided_text(self._l_name_password, self._name)

    def resizeEvent(self, a0):
        self._update_text()
        super().resizeEvent(a0)

    def _update_text(self):
        max_width = int(
            (self.width() - self._btn_delete.width() - self._password_icon.width() - 4 * self._h_layout.spacing()))

        self._l_name_password.setMaximumWidth(max_width)
        self._set_elided_text(self._l_name_password, self._name)

    @staticmethod
    def _set_elided_text(label: QLabel, text: str):
        metrics = QFontMetrics(label.font())
        elided = metrics.elidedText(text, Qt.ElideMiddle, label.maximumWidth())
        label.setText(elided)


class Passwords(SimpleCardWidget):
    sig_change_window_state: pyqtSignal = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._db: DataBase = DataBase()
        self._locales: Locales = Locales()
        self._key_storage: MasterKeyStorage = MasterKeyStorage()
        self._global_flags: GlobalFlags = GlobalFlags()

        self._vl_view_layout: QVBoxLayout = QVBoxLayout(self)
        self._password_list: PagedListView = PagedListView(PasswordCard, parent=self)
        self._pager: PipsPager = PipsPager(self)

        from src.frontend.hmi import MainWindow
        self._hmi: MainWindow = find_mega_parent(self)

        self._master_key_creator = MasterKeyCreator(self._hmi)
        self._master_key_creator.yesButton.setText(self._locales.get_string('confirm'))
        self._master_key_creator.cancelButton.setText(self._locales.get_string('cancel'))

        self._password_creator = PasswordCreator(self._hmi)
        self._password_creator.yesButton.setText(self._locales.get_string('confirm'))
        self._password_creator.cancelButton.setText(self._locales.get_string('cancel'))

        self._password_input = PasswordInput(self._hmi)
        self._password_input.yesButton.setText(self._locales.get_string('confirm'))
        self._password_input.cancelButton.setText(self._locales.get_string('cancel'))

        self._mb_func_not_found = MessageBox(title=self._locales.get_string('function_not_found'),
                                             description=self._locales.get_string('master_key_not_available'),
                                             parent=self._hmi)
        self._mb_func_not_found.yesButton.setText(self._locales.get_string('yes'))
        self._mb_func_not_found.cancelButton.setText(self._locales.get_string('no'))

        self._mb_clear_passwords = MessageBox(title=self._locales.get_string('clear_passwords_description'),
                                              description=self._locales.get_string('clear_passwords_message'),
                                              parent=self._hmi)
        self._mb_clear_passwords.yesButton.setText(self._locales.get_string('yes'))
        self._mb_clear_passwords.cancelButton.setText(self._locales.get_string('no'))

        self._mb_reset_master_key = MessageBox(title=self._locales.get_string('reset_master_key_description'),
                                               description=self._locales.get_string('reset_master_key_message'),
                                               parent=self._hmi)
        self._mb_reset_master_key.yesButton.setText(self._locales.get_string('yes'))
        self._mb_reset_master_key.cancelButton.setText(self._locales.get_string('no'))

        self._mb_remove_password = MessageBox(title=self._locales.get_string('remove_password_description'),
                                              description=self._locales.get_string('remove_password_message'),
                                              parent=self._hmi)
        self._mb_remove_password.yesButton.setText(self._locales.get_string('yes'))
        self._mb_remove_password.cancelButton.setText(self._locales.get_string('no'))

        self.__init_widgets()

    def __init_widgets(self):
        self._vl_view_layout.setContentsMargins(8, 8, 8, 8)
        self._vl_view_layout.setSpacing(8)
        self._vl_view_layout.setAlignment(Qt.AlignTop)

        self._pager.setNextButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)
        self._pager.setPreviousButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)

        self._vl_view_layout.addWidget(self._password_list)
        self._vl_view_layout.addWidget(self._pager, alignment=Qt.AlignCenter)

        self._password_list.pagination_changed.connect(self._on_pagination_changed)
        self._pager.currentIndexChanged.connect(lambda index: self._password_list.set_page(index))
        events.sig_delete_password.connect(self._on_sig_delete_password)
        self._hmi.stackedWidget.view.aniFinished.connect(self._on_sig_ani_finished)
        self._hmi.sig_check_passwords.connect(self._on_sig_check_passwords)
        self._hmi.sig_add_new_password.connect(self.add_password)

    def _on_sig_check_passwords(self):
        if not self._key_storage.master_key:
            self.check_master_key()

        result = bool(self._key_storage.master_key)
        self._hmi.sig_passwords_check_completed.emit(result)

    def check_master_key(self):
        if self._db.get_setting('password_cipher') == '':
            self._master_key_creator.reset()
            self._global_flags.modal_open.set()

            if self._master_key_creator.exec():
                self._key_storage.master_key = self._master_key_creator.get_password()
                self._db.set_setting('password_cipher', self._master_key_creator.get_encrypt_mode())

                encrypt_function = micro_ciphers[self._master_key_creator.get_encrypt_mode()]
                password_signature = encrypt_function(self._master_key_creator.get_password(),
                                                      Config.SIGNATURE,
                                                      OperationType.ENCRYPT)

                self._db.set_password_signature(password_signature)
                self.sig_change_window_state.emit(True)
            else:
                self.sig_change_window_state.emit(False)
                if self._hmi.stackedWidget.currentWidget() is self.parent():
                    self._hmi.navigationInterface.history.pop()

            self._global_flags.modal_open.clear()

        else:
            if self._db.get_setting('password_cipher') not in micro_ciphers:
                self._global_flags.modal_open.set()

                if self._mb_func_not_found.exec():
                    self.reset_master_key(True)


                else:
                    self.sig_change_window_state.emit(False)
                    if self._hmi.stackedWidget.currentWidget() is self.parent():
                        self._hmi.navigationInterface.history.pop()

                self._global_flags.modal_open.clear()

                return
            else:
                if self._key_storage.master_key == '':
                    self._password_input.reset()
                    self._global_flags.modal_open.set()

                    if self._password_input.exec():
                        if self._password_input.need_reset():
                            self.reset_master_key(True)
                            return

                        self._key_storage.master_key = self._password_input.get_password()
                        self._password_list.set_items(
                            {record.name: record.name for record in self._db.get_all_passwords()})
                        self.sig_change_window_state.emit(True)
                    else:
                        self.sig_change_window_state.emit(False)
                        if self._hmi.stackedWidget.currentWidget() is self.parent():
                            self._hmi.navigationInterface.history.pop()

                    self._global_flags.modal_open.clear()

    def _on_sig_ani_finished(self):
        if self._hmi.stackedWidget.currentWidget() is self.parent():
            QTimer.singleShot(0, self.check_master_key)

    def clear_passwords(self):
        self._global_flags.modal_open.set()

        if self._mb_clear_passwords.exec():
            self._password_list.clear_items()
            self._db.remove_all_passwords()
            self._pager.setPageNumber(0)
            self._pager.setVisibleNumber(0)

        self._global_flags.modal_open.clear()

    def reset_master_key(self, skip_message: bool = False):
        self._global_flags.modal_open.set()

        if skip_message or self._mb_reset_master_key.exec():
            self._key_storage.master_key = ''
            self._password_list.clear_items()
            self._db.remove_all_passwords()
            self._db.set_setting('password_cipher', '')
            self._pager.setPageNumber(0)
            self._pager.setVisibleNumber(0)

            self.sig_change_window_state.emit(False)
            self.check_master_key()

        self._global_flags.modal_open.clear()

    def _on_sig_delete_password(self, name: str):
        self._global_flags.modal_open.set()

        if self._mb_remove_password.exec():
            self._password_list.remove_item(name)
            self._db.remove_password(name)

        self._global_flags.modal_open.clear()

    def add_password(self, password: str = ''):
        self._password_creator.reset()
        self._password_creator.set_password(password)

        self._global_flags.modal_open.set()

        if self._password_creator.exec():
            if (record := self._password_creator.get_password_record()).name in self._password_list.items_dict:
                InfoBar.error(
                    title=self._locales.get_string('error'),
                    content=self._locales.get_string('password_already_exists'),
                    orient=Qt.Horizontal,
                    isClosable=False,
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    duration=3000,
                    parent=self._hmi
                )

                return

            self._global_flags.modal_open.clear()

            encrypt_function = micro_ciphers[self._db.get_setting('password_cipher')]
            record.password = encrypt_function(self._key_storage.master_key,
                                               record.password,
                                               OperationType.ENCRYPT)

            self._db.add_password(record)
            self._password_list.add_item(record.name, record.name)

    def lock_passwords(self):
        self._key_storage.master_key = ''
        self._password_list.clear_items()
        self._hmi.navigationInterface.history.pop()
        self.sig_change_window_state.emit(False)

    def _on_pagination_changed(self, current_page: int, total_pages: int):
        self._pager.blockSignals(True)
        self._pager.setPageNumber(total_pages)
        self._pager.setVisibleNumber(min(total_pages, 50))
        self._pager.setCurrentIndex(current_page)
        self._pager.blockSignals(False)
