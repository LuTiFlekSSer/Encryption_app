from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QSizePolicy


class PagedListView(QWidget):
    pageChanged: pyqtSignal = pyqtSignal()

    def __init__(self, item_widget_class, parent=None):
        super().__init__(parent=parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._item_widget_class = item_widget_class

        self._items = []
        self._item_widgets: list[QWidget] = []

        self._first_visible_index: int = 0
        self._visible_count: int = 0

        self._layout: QVBoxLayout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setAlignment(Qt.AlignTop)

        self._scroll_area: QScrollArea = QScrollArea(self)
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._layout.addWidget(self._scroll_area)

        self._container: QWidget = QWidget(self)
        self._container.setObjectName('w_view')
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setSpacing(8)
        self._container_layout.setAlignment(Qt.AlignTop)
        self._scroll_area.setWidget(self._container)

    def set_items(self, items):
        self._items = items
        self._first_visible_index = 0
        self.update_view()

    def resizeEvent(self, event):
        self.update_view()
        return super().resizeEvent(event)

    def update_view(self):
        if not self._items:
            return

        sample = self._item_widgets[0] if self._item_widgets else self._item_widget_class()
        if not self._item_widgets:
            sample.setParent(self)
            sample.hide()

        height_available = self._scroll_area.viewport().height()
        item_height = sample.height() + self._container_layout.spacing()
        new_visible_count = max(1, height_available // item_height)

        while len(self._item_widgets) < new_visible_count:
            widget = self._item_widget_class()
            self._container_layout.addWidget(widget)
            self._item_widgets.append(widget)

        self._visible_count = new_visible_count
        self._update_widgets()

    def _update_widgets(self):
        start = self._first_visible_index
        end = min(len(self._items), start + self._visible_count)

        for i, widget in enumerate(self._item_widgets):
            data_index = start + i
            if data_index < end:
                item_data = self._items[data_index]

                if hasattr(widget, 'set_data'):
                    widget.set_data(item_data)
                else:
                    raise AttributeError('Widget must have set_data method')

                widget.show()
            else:
                widget.hide()

        self.pageChanged.emit()

    def next_page(self):
        if self.can_go_next():
            self._first_visible_index += self._visible_count
            self._update_widgets()

    def prev_page(self):
        if self.can_go_prev():
            self._first_visible_index = max(0, self._first_visible_index - self._visible_count)
            self._update_widgets()

    def can_go_next(self) -> bool:
        return self._first_visible_index + self._visible_count < len(self._items)

    def can_go_prev(self) -> bool:
        return self._first_visible_index > 0

    def add_item(self, data):
        self._items.append(data)
        self.update_view()

    def clear_items(self):
        self._items.clear()
        self._first_visible_index = 0
        self._update_widgets()

    def get_total_items(self) -> int:
        return len(self._items)

    def set_first_index(self, index):
        index = max(0, min(index, len(self._items) - 1))
        self._first_visible_index = index
        self._update_widgets()

    def set_page(self, page_number):
        if self._visible_count == 0:
            self.update_view()

        max_page = max(0, (len(self._items) - 1) // self._visible_count)
        page_number = max(0, min(page_number, max_page))

        self._first_visible_index = page_number * self._visible_count
        self.update_view()

    def get_total_pages(self):
        if self._visible_count == 0:
            self.update_view()

        return max(0, (len(self._items) - 1) // self._visible_count)