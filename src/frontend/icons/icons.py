from enum import Enum

from qfluentwidgets import FluentIconBase, Theme


class LockIcons(FluentIconBase, Enum):
    LOCK = 'lock'
    UNLOCK = 'unlock'

    def path(self, theme=Theme.AUTO):
        return f'res/{self.value}.svg'
