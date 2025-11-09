from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt
import os
import sys


class LoadWeekDialog(QDialog):
    def __init__(self, parent=None, tr=lambda k: k):
        super().__init__(parent)
        self.tr = tr
        self.setWindowTitle(self.tr("load_week_dialog_title"))
        self.setModal(True)

        self.selected_file_path = None

        self.list_widget = QListWidget(self)
        self.list_widget.itemDoubleClicked.connect(self._load_selected_and_accept)

        btn_load = QPushButton(self.tr("load_week_action"))
        btn_delete = QPushButton(self.tr("delete_week"))
        btn_cancel = QPushButton(self.tr("cancel"))

        btn_load.clicked.connect(self._load_selected_and_accept)
        btn_delete.clicked.connect(self._delete_selected)
        btn_cancel.clicked.connect(self.reject)

        # Layouts
        main_layout = QVBoxLayout()
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(btn_load)
        buttons_layout.addWidget(btn_delete)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(btn_cancel)

        main_layout.addWidget(self.list_widget)
        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

        # Populate list
        self._populate()

        # Optional: apply dark theme if parent provides it
        if parent is not None and hasattr(parent, "theme_manager"):
            try:
                dark_mode = getattr(parent.theme_manager, "dark_mode", False)
                self.setStyleSheet(parent.theme_manager.get_widget_styles(dark_mode))
            except Exception:
                pass

    def _populate(self):
        self.list_widget.clear()
        saved_dir = self._get_saved_dir()

        if not os.path.isdir(saved_dir):
            # Show info that no folder exists
            QMessageBox.information(self, self.tr("information"), self.tr("no_saved_weeks"))
            return

        files = [f for f in os.listdir(saved_dir) if f.lower().endswith(".json")]
        if not files:
            QMessageBox.information(self, self.tr("information"), self.tr("no_saved_weeks"))
            return

        # Sort by filename descending (recent first) if names contain date
        files.sort(reverse=True)

        for fname in files:
            full_path = os.path.join(saved_dir, fname)
            label = self._format_label(fname)
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, full_path)
            self.list_widget.addItem(item)

    def _get_saved_dir(self) -> str:
        """Resolve the Weekend-Saved path near the executable when frozen, else project root."""
        try:
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
            return os.path.join(base_dir, "Weekend-Saved")
        except Exception:
            return os.path.join(os.getcwd(), "Weekend-Saved")

    def _format_label(self, fname: str) -> str:
        # Expect pattern like weekend_trading_YYYY-MM-DD.json
        base = os.path.splitext(fname)[0]
        if "weekend_trading_" in base:
            date_part = base.split("weekend_trading_")[-1]
            return f"{self.tr('week_label')} {date_part}"
        return base

    def _get_selected_path(self):
        item = self.list_widget.currentItem()
        if item is None:
            return None
        return item.data(Qt.UserRole)

    def _load_selected_and_accept(self):
        path = self._get_selected_path()
        if not path:
            QMessageBox.warning(self, self.tr("warning"), self.tr("select_week_first"))
            return
        self.selected_file_path = path
        self.accept()

    def _delete_selected(self):
        path = self._get_selected_path()
        if not path:
            QMessageBox.warning(self, self.tr("warning"), self.tr("select_week_first"))
            return

        resp = QMessageBox.question(
            self,
            self.tr("confirm_delete_week_title"),
            self.tr("confirm_delete_week_message"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resp != QMessageBox.Yes:
            return

        try:
            os.remove(path)
            QMessageBox.information(self, self.tr("operation_completed"), self.tr("delete_success"))
            self._populate()
        except Exception:
            QMessageBox.critical(self, self.tr("error"), self.tr("delete_error"))

    def get_selected_file_path(self):
        return self.selected_file_path