from enum import Enum

from qfluentwidgets import StyleSheetBase, Theme


class StyleSheet(StyleSheetBase, Enum):
    HOME_WINDOW = 'home_window'
    SETTINGS_WINDOW = 'settings_window'
    HISTORY_WINDOW = 'history_window'
    ENCRYPT_WINDOW = 'encrypt_window'
    PASSWORDS_WINDOW = 'passwords_window'

    def path(self, theme=Theme.AUTO):
        return f'src/frontend/style_sheets/qss/{self.value}.qss'
