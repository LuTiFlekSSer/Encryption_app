from enum import Enum

from qfluentwidgets import StyleSheetBase, Theme

from src.utils.utils import resource_path


class StyleSheet(StyleSheetBase, Enum):
    HOME_WINDOW = 'home_window'
    SETTINGS_WINDOW = 'settings_window'
    HISTORY_WINDOW = 'history_window'

    def path(self, theme=Theme.AUTO):
        return resource_path(f'src/frontend/style_sheets/qss/{self.value}.qss')
