from enum import Enum

from qfluentwidgets import StyleSheetBase, Theme, qconfig

from src.utils.utils import resource_path


class StyleSheet(StyleSheetBase, Enum):
    HOME_WINDOW = 'home_window'

    def path(self, theme=Theme.AUTO):
        theme = qconfig.theme if theme == Theme.AUTO else theme
        return resource_path(f'src/style_sheets/qss/{theme.value.lower()}/{self.value}.qss')
