"""
Gestión de temas para la aplicación W-T-F Trading Manager

Un único stylesheet por tema cubre toda la aplicación (ventana principal,
menús, diálogos, mensajes emergentes, etc). Se aplica a nivel de
QApplication para que cualquier ventana o diálogo -incluso los creados
dinámicamente como QMessageBox- herede automáticamente los mismos colores,
evitando pantallas "claras" sueltas cuando el modo oscuro está activo.

Los widgets usan objectName para variantes (#card, #primary, #ghost, ...),
de modo que ningún componente necesita colores escritos a mano.
"""

import os
import tempfile

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor


class ThemeManager:
    """Gestor de temas para la aplicación"""

    # Paleta de colores - tema claro
    LIGHT = {
        'bg': '#eef2f9',
        'bg_deep': '#e3e9f4',
        'surface': '#ffffff',
        'surface_alt': '#f4f7fc',
        'elevated': '#ffffff',
        'border': '#dde4f0',
        'border_strong': '#c5d0e3',
        'text': '#101828',
        'text_secondary': '#5b6b86',
        'text_muted': '#8a97ad',
        'accent': '#6246ea',
        'accent2': '#0091ff',
        'accent_hover': '#7258ff',
        'accent_pressed': '#4f35d4',
        'accent_text': '#ffffff',
        'accent_soft': '#ece8ff',
        'success': '#0f9f6e',
        'success_bg': '#e3f7ef',
        'success_border': '#b6e8d3',
        'danger': '#e11d48',
        'danger_bg': '#fde8ed',
        'danger_border': '#f7c0cc',
        'warning': '#d97706',
        'warning_bg': '#fff4e0',
        'warning_border': '#fbdca3',
        'disabled_bg': '#e5e9f2',
        'disabled_text': '#a3adc2',
        'scroll_track': 'transparent',
        'scroll_handle': '#c9d2e3',
        'scroll_handle_hover': '#a9b5cc',
        'tooltip_bg': '#101828',
        'tooltip_text': '#f3f5fb',
    }

    # Paleta de colores - tema oscuro
    DARK = {
        'bg': '#070a12',
        'bg_deep': '#04060c',
        'surface': '#0e1421',
        'surface_alt': '#131b2b',
        'elevated': '#18223a',
        'border': '#1d2740',
        'border_strong': '#2b3a5c',
        'text': '#e8edf7',
        'text_secondary': '#8b97b0',
        'text_muted': '#5d6a85',
        'accent': '#7c5cff',
        'accent2': '#00d4ff',
        'accent_hover': '#9178ff',
        'accent_pressed': '#6445f0',
        'accent_text': '#ffffff',
        'accent_soft': '#1e1a3d',
        'success': '#00e5a0',
        'success_bg': '#062a20',
        'success_border': '#0d4a37',
        'danger': '#ff4d6d',
        'danger_bg': '#2e0c16',
        'danger_border': '#5a1a2a',
        'warning': '#ffb547',
        'warning_bg': '#2d2109',
        'warning_border': '#5a4519',
        'disabled_bg': '#161d2d',
        'disabled_text': '#4b5670',
        'scroll_track': 'transparent',
        'scroll_handle': '#26324d',
        'scroll_handle_hover': '#34446a',
        'tooltip_bg': '#18223a',
        'tooltip_text': '#e8edf7',
    }

    def __init__(self):
        self.current_theme = "dark"
        self.themes = {
            "light": self._build_stylesheet(self.LIGHT),
            "dark": self._build_stylesheet(self.DARK),
        }

    @staticmethod
    def _arrow_icon(color: str) -> str:
        """Crear (una vez) un SVG de flecha del color dado y devolver su ruta para QSS."""
        path = os.path.join(tempfile.gettempdir(), f"wtf_arrow_{color.lstrip('#')}.svg")
        if not os.path.exists(path):
            svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12">'
                   f'<path d="M2.5 4.5 L6 8 L9.5 4.5" fill="none" stroke="{color}" stroke-width="1.8" '
                   f'stroke-linecap="round" stroke-linejoin="round"/></svg>')
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(svg)
            except OSError:
                return ''
        return path.replace(os.sep, '/')

    @classmethod
    def colors(cls, is_dark: bool) -> dict:
        return cls.DARK if is_dark else cls.LIGHT

    def _build_stylesheet(self, c: dict) -> str:
        """Construir el stylesheet completo de la aplicación a partir de una paleta de tokens."""
        grad = f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {c['accent']}, stop:1 {c['accent2']})"
        grad_hover = f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {c['accent_hover']}, stop:1 {c['accent2']})"
        return f"""
            /* Estilo general */
            QWidget {{
                background-color: {c['bg']};
                color: {c['text']};
                font-family: 'Segoe UI', 'Inter', 'Arial', sans-serif;
                font-size: 10pt;
            }}

            QMainWindow, QDialog, QMessageBox, QFileDialog, QInputDialog {{
                background-color: {c['bg']};
                color: {c['text']};
            }}

            QToolTip {{
                background-color: {c['tooltip_bg']};
                color: {c['tooltip_text']};
                border: 1px solid {c['border_strong']};
                padding: 6px 10px;
                border-radius: 6px;
            }}

            /* Tarjetas */
            QFrame#card {{
                background-color: {c['surface']};
                border: 1px solid {c['border']};
                border-radius: 16px;
            }}
            QFrame#cardAlt {{
                background-color: {c['surface_alt']};
                border: 1px solid {c['border']};
                border-radius: 12px;
            }}
            QFrame#heroCard {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {c['accent_soft']}, stop:1 {c['surface']});
                border: 1px solid {c['border_strong']};
                border-radius: 18px;
            }}
            QFrame#header {{
                background-color: {c['surface']};
                border: none;
                border-bottom: 1px solid {c['border']};
            }}
            QFrame#banner {{
                background-color: {c['warning_bg']};
                border: 1px solid {c['warning_border']};
                border-radius: 10px;
            }}
            QFrame#sidebar {{
                background-color: {c['surface']};
                border: none;
                border-right: 1px solid {c['border']};
            }}
            QFrame#card QLabel, QFrame#cardAlt QLabel, QFrame#heroCard QLabel,
            QFrame#header QLabel, QFrame#banner QLabel, QFrame#sidebar QLabel {{
                background: transparent;
                border: none;
            }}
            QFrame#card QWidget#transparent, QWidget#transparent {{
                background: transparent;
            }}

            /* Tipografía */
            QLabel {{
                background-color: transparent;
                color: {c['text']};
            }}
            QLabel#h1 {{ font-size: 18pt; font-weight: 800; }}
            QLabel#h2 {{ font-size: 13pt; font-weight: 700; }}
            QLabel#h3 {{ font-size: 11pt; font-weight: 700; }}
            QLabel#muted {{ color: {c['text_secondary']}; }}
            QLabel#caption {{
                color: {c['text_muted']};
                font-size: 8pt;
                font-weight: 700;
            }}
            QLabel#brand {{ font-size: 15pt; font-weight: 900; }}
            QLabel#chip, QFrame QLabel#chip {{
                background-color: {c['accent_soft']};
                color: {c['accent_hover']};
                border: 1px solid {c['border_strong']};
                border-radius: 11px;
                padding: 3px 12px;
                font-weight: 700;
                font-size: 9pt;
            }}
            QLabel#positive {{ color: {c['success']}; font-weight: 700; }}
            QLabel#negative {{ color: {c['danger']}; font-weight: 700; }}
            QLabel#status_label {{
                background-color: {c['success_bg']};
                color: {c['success']};
                padding: 8px;
                border-radius: 10px;
                border: 1px solid {c['success_border']};
                font-size: 9pt;
            }}

            /* QTableWidget */
            QTableWidget {{
                background-color: {c['surface']};
                alternate-background-color: {c['surface_alt']};
                gridline-color: transparent;
                selection-background-color: {c['accent_soft']};
                selection-color: {c['text']};
                border: none;
                border-radius: 12px;
                padding: 2px;
                outline: none;
            }}
            QTableWidget::item {{
                padding: 8px;
                border: none;
                border-bottom: 1px solid {c['border']};
            }}
            QTableWidget::item:hover {{
                background-color: {c['surface_alt']};
            }}
            QTableWidget::item:selected {{
                background-color: {c['accent_soft']};
                color: {c['text']};
            }}
            QHeaderView {{ background-color: transparent; border: none; }}
            QHeaderView::section {{
                background-color: {c['surface']};
                color: {c['text_muted']};
                padding: 10px 8px;
                border: none;
                border-bottom: 2px solid {c['border_strong']};
                font-weight: 700;
                font-size: 8pt;
            }}
            QTableCornerButton::section {{ background-color: {c['surface']}; border: none; }}

            /* Botones */
            QPushButton {{
                background-color: {c['surface_alt']};
                color: {c['text']};
                border: 1px solid {c['border_strong']};
                border-radius: 10px;
                padding: 8px 16px;
                font-weight: 600;
                min-width: 70px;
            }}
            QPushButton:hover {{
                border-color: {c['accent']};
                background-color: {c['elevated']};
            }}
            QPushButton:pressed {{ background-color: {c['accent_soft']}; }}
            QPushButton:disabled {{
                background-color: {c['disabled_bg']};
                color: {c['disabled_text']};
                border-color: {c['disabled_bg']};
            }}
            QPushButton#primary {{
                background-color: {grad};
                color: {c['accent_text']};
                border: none;
                padding: 10px 20px;
                font-weight: 700;
            }}
            QPushButton#primary:hover {{ background-color: {grad_hover}; }}
            QPushButton#primary:pressed {{ background-color: {c['accent_pressed']}; }}
            QPushButton#primary:disabled {{
                background-color: {c['disabled_bg']};
                color: {c['disabled_text']};
            }}
            QPushButton#ghost {{
                background-color: transparent;
                border: 1px solid transparent;
                color: {c['text_secondary']};
            }}
            QPushButton#ghost:hover {{
                background-color: {c['surface_alt']};
                border-color: {c['border']};
                color: {c['text']};
            }}
            QPushButton#danger {{
                background-color: {c['danger_bg']};
                color: {c['danger']};
                border: 1px solid {c['danger_border']};
            }}
            QPushButton#danger:hover {{ border-color: {c['danger']}; }}
            QPushButton#segment {{
                background-color: transparent;
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 4px 12px;
                min-width: 36px;
                color: {c['text_secondary']};
                font-weight: 700;
            }}
            QPushButton#segment:checked {{
                background-color: {grad};
                color: {c['accent_text']};
                border-color: transparent;
            }}

            /* Entradas */
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                background-color: {c['surface_alt']};
                color: {c['text']};
                border: 1px solid {c['border_strong']};
                border-radius: 10px;
                padding: 7px 12px;
                selection-background-color: {c['accent']};
                selection-color: {c['accent_text']};
                min-height: 20px;
            }}
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
                border: 1px solid {c['accent']};
                background-color: {c['elevated']};
            }}
            QLineEdit:disabled {{
                background-color: {c['disabled_bg']};
                color: {c['disabled_text']};
            }}
            QSpinBox::up-button, QSpinBox::down-button,
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
                width: 0; border: none;
            }}
            QComboBox::drop-down {{ border: none; width: 24px; }}
            QComboBox::down-arrow {{
                image: url({self._arrow_icon(c['text_secondary'])});
                width: 12px; height: 12px;
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {c['elevated']};
                color: {c['text']};
                border: 1px solid {c['border_strong']};
                border-radius: 8px;
                selection-background-color: {c['accent']};
                selection-color: {c['accent_text']};
                outline: none;
                padding: 4px;
            }}

            QTextEdit, QPlainTextEdit {{
                background-color: {c['surface_alt']};
                color: {c['text']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 8px;
                selection-background-color: {c['accent']};
                selection-color: {c['accent_text']};
            }}
            QTextEdit:focus, QPlainTextEdit:focus {{ border: 1px solid {c['accent']}; }}

            QCheckBox {{ background: transparent; spacing: 10px; }}
            QCheckBox::indicator {{
                width: 18px; height: 18px;
                border-radius: 5px;
                border: 1px solid {c['border_strong']};
                background-color: {c['surface_alt']};
            }}
            QCheckBox::indicator:checked {{ background-color: {grad}; border-color: {c['accent']}; }}

            /* QGroupBox */
            QGroupBox {{
                background-color: {c['surface']};
                border: 1px solid {c['border']};
                border-radius: 12px;
                margin-top: 14px;
                padding-top: 14px;
                font-weight: 600;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                background-color: transparent;
                color: {c['accent_hover']};
            }}

            /* Navegación lateral (configuración) */
            QListWidget#nav {{
                background: transparent;
                border: none;
                outline: none;
                padding: 6px;
            }}
            QListWidget#nav::item {{
                color: {c['text_secondary']};
                padding: 12px 14px;
                margin: 2px 0;
                border-radius: 10px;
                font-weight: 600;
            }}
            QListWidget#nav::item:hover {{
                background-color: {c['surface_alt']};
                color: {c['text']};
            }}
            QListWidget#nav::item:selected {{
                background-color: {c['accent_soft']};
                color: {c['accent_hover']};
                border-left: 3px solid {c['accent']};
            }}

            /* QListWidget genérico (selector de semanas guardadas) */
            QListWidget {{
                background-color: {c['surface']};
                color: {c['text']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 4px;
                outline: none;
            }}
            QListWidget::item {{ padding: 8px; border-radius: 6px; }}
            QListWidget::item:hover {{ background-color: {c['surface_alt']}; }}
            QListWidget::item:selected {{
                background-color: {c['accent']};
                color: {c['accent_text']};
            }}

            QScrollArea {{ background: transparent; border: none; }}
            QScrollArea > QWidget > QWidget {{ background: transparent; }}

            /* QScrollBar */
            QScrollBar:vertical {{
                background-color: {c['scroll_track']};
                width: 10px; margin: 2px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {c['scroll_handle']};
                border-radius: 3px; min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{ background-color: {c['scroll_handle_hover']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                border: none; background: none; height: 0;
            }}
            QScrollBar:horizontal {{
                background-color: {c['scroll_track']};
                height: 10px; margin: 2px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {c['scroll_handle']};
                border-radius: 3px; min-width: 30px;
            }}
            QScrollBar::handle:horizontal:hover {{ background-color: {c['scroll_handle_hover']}; }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                border: none; background: none; width: 0;
            }}

            /* QSplitter */
            QSplitter::handle {{ background-color: transparent; }}
            QSplitter::handle:horizontal {{ width: 8px; }}
            QSplitter::handle:vertical {{ height: 8px; }}

            /* QStatusBar */
            QStatusBar {{
                background-color: {c['surface']};
                color: {c['text_secondary']};
                border-top: 1px solid {c['border']};
            }}
            QStatusBar QLabel {{ color: {c['text_secondary']}; background-color: transparent; }}

            /* QMenu (menús contextuales) */
            QMenuBar {{
                background-color: {c['surface']};
                color: {c['text']};
                border-bottom: 1px solid {c['border']};
            }}
            QMenu {{
                background-color: {c['elevated']};
                color: {c['text']};
                border: 1px solid {c['border_strong']};
                border-radius: 10px;
                padding: 6px;
            }}
            QMenu::item {{ padding: 8px 22px; margin: 1px; border-radius: 6px; }}
            QMenu::item:selected {{ background-color: {c['accent']}; color: {c['accent_text']}; }}
            QMenu::item:disabled {{ color: {c['disabled_text']}; }}
            QMenu::separator {{ height: 1px; background-color: {c['border']}; margin: 5px 10px; }}
        """

    def apply_theme(self, widget, is_dark: bool):
        """Aplicar tema a toda la aplicación (no solo al widget indicado)."""
        self.current_theme = "dark" if is_dark else "light"
        stylesheet = self.themes[self.current_theme]

        app = QApplication.instance()
        if app is not None:
            # Aplicar a nivel de aplicación: cubre automáticamente diálogos,
            # QMessageBox y cualquier ventana futura sin necesidad de recorrer
            # manualmente el árbol de widgets.
            app.setStyleSheet(stylesheet)
            self.apply_palette(app, is_dark)
        else:
            widget.setStyleSheet(stylesheet)
            if hasattr(widget, 'setPalette'):
                self.apply_palette(widget, is_dark)

    def apply_palette(self, widget, is_dark: bool):
        """Aplicar paleta de colores nativa (afecta widgets sin stylesheet propio)."""
        c = self.DARK if is_dark else self.LIGHT
        palette = QPalette()

        palette.setColor(QPalette.Window, QColor(c['bg']))
        palette.setColor(QPalette.WindowText, QColor(c['text']))
        palette.setColor(QPalette.Base, QColor(c['surface']))
        palette.setColor(QPalette.AlternateBase, QColor(c['surface_alt']))
        palette.setColor(QPalette.ToolTipBase, QColor(c['tooltip_bg']))
        palette.setColor(QPalette.ToolTipText, QColor(c['tooltip_text']))
        palette.setColor(QPalette.Text, QColor(c['text']))
        palette.setColor(QPalette.Button, QColor(c['surface']))
        palette.setColor(QPalette.ButtonText, QColor(c['text']))
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(c['accent']))
        palette.setColor(QPalette.Highlight, QColor(c['accent']))
        palette.setColor(QPalette.HighlightedText, QColor(c['accent_text']))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(c['disabled_text']))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(c['disabled_text']))

        widget.setPalette(palette)

    def get_widget_styles(self, is_dark: bool):
        """Devolver el stylesheet completo del tema (útil para aplicarlo a un widget puntual)."""
        return self.themes["dark" if is_dark else "light"]
