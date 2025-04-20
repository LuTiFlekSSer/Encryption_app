from enum import Enum

from qfluentwidgets import StyleSheetBase, Theme, qconfig

from src.utils.utils import resource_path


class StyleSheet(StyleSheetBase, Enum):
    HOME_WINDOW = 'home_window'

    def path(self, theme=Theme.AUTO):
        return resource_path(f'src/frontend/style_sheets/qss/{self.value}.qss')
