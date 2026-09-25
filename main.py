"""
W-T-F (Weekend Trading Finance) Trading Manager
Aplicación principal que integra todos los componentes modulares
"""

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                           QVBoxLayout, QSplitter, QStatusBar, QMessageBox, QFileDialog, 
                           QDialog, QInputDialog, QFrame, QLabel, QPushButton, QScrollArea,
                           QShortcut)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPalette, QColor, QIcon, QPixmap, QKeySequence

# Importar componentes modulares
from src.ui.animations import fade_in, pulse_glow
from src.ui.result_image_dialog import ResultImageDialog
from src.ui.settings_dialog import SettingsDialog
from src.utils.settings_store import SettingsStore
from src.ui.trading_table import TradingTableWidget
from src.ui.summary_panel import SummaryPanel
from src.ui.enhanced_chart_widget import EnhancedChartWidget
from src.ui.capital_dialog import CapitalDialog
from src.ui.weekly_summary_dialog import WeeklySummaryDialog
from src.ui.export_dialog import show_export_dialog
from src.ui.import_dialog import ImportDialog
from src.utils.import_manager import SUPPORTED_EXT
from src.models.trading_model_with_db import TradingDataModelWithDB
from src.models.ai_analyzer import AIAnalyzer
from src.styles.themes import ThemeManager
from src.utils.advice import get_daily_advice
from src.utils.i18n import tr, set_language
from src.ui.load_week_dialog import LoadWeekDialog

class MainWindow(QMainWindow):
    """Ventana principal de la aplicación W-T-F Trading Manager"""
    
    def __init__(self):
        super().__init__()
        self.data_model = None
        self.ai_analyzer = None
        self.theme_manager = None
        self.dark_mode = False  # Agregar atributo dark_mode
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Configurar la interfaz de usuario principal"""
        self.setWindowTitle(tr("app_title"))
        self.setGeometry(80, 60, 1440, 960)
        self.setAcceptDrops(True)

        # Establecer icono de la aplicación con ruta absoluta base + src/images
        self.logo_path = None
        try:
            base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.getcwd())
            images_dir = os.path.join(base_dir, 'src', 'images')
            logo_png = os.path.join(images_dir, 'logo.png')
            fallback_svg = os.path.join(images_dir, 'app_icon.svg')
            if os.path.exists(logo_png):
                self.logo_path = logo_png
                self.setWindowIcon(QIcon(logo_png))
            elif os.path.exists(fallback_svg):
                self.setWindowIcon(QIcon(fallback_svg))
        except Exception as e:
            print(f"Error al cargar el icono de la ventana: {e}")

        # Crear modelo de datos y configuración persistente
        self.data_model = TradingDataModelWithDB()
        self.settings = SettingsStore(self.data_model.db_manager)
        set_language(self.settings.get('language'))
        self.dark_mode = self.settings.get_bool('dark_mode')
        self.ai_analyzer = AIAnalyzer()
        self.theme_manager = ThemeManager()

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Cabecera (reemplaza la barra de menús: todo vive en Configuración)
        main_layout.addWidget(self._build_header())

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(18, 16, 18, 12)
        main_layout.addWidget(body, 1)

        # Crear splitter para layout flexible
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Panel izquierdo: Tabla + gráfico en tarjetas
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(14)

        self.table_card = QFrame()
        self.table_card.setObjectName('card')
        table_layout = QVBoxLayout(self.table_card)
        table_layout.setContentsMargins(16, 14, 16, 12)
        table_title_row = QHBoxLayout()
        self.table_title = QLabel('📅 ' + tr('week_results', 'Resultados de la semana'))
        self.table_title.setObjectName('h2')
        self.table_hint = QLabel(tr('table_hint', 'Doble clic para editar · clic derecho para más opciones'))
        self.table_hint.setObjectName('muted')
        table_title_row.addWidget(self.table_title)
        table_title_row.addStretch()
        table_title_row.addWidget(self.table_hint)
        table_layout.addLayout(table_title_row)
        self.table_widget = TradingTableWidget(self.data_model)
        self.table_widget.default_pair = self.settings.get('default_pair')
        self.table_widget.default_duration = self.settings.get('default_duration')
        self.table_widget.set_capital_edit_mode(self.settings.get_bool('capital_edit_mode'))
        table_layout.addWidget(self.table_widget)
        left_layout.addWidget(self.table_card)

        # Gráfico mejorado
        self.chart_card = QFrame()
        self.chart_card.setObjectName('card')
        chart_layout = QVBoxLayout(self.chart_card)
        chart_layout.setContentsMargins(0, 0, 0, 6)
        self.chart_widget = EnhancedChartWidget()
        self.chart_widget.legend_visible = self.settings.get_bool('legend_visible')
        self.chart_widget.set_animations_enabled(self.settings.get_bool('chart_animations'))
        self.chart_widget.set_mode(self.settings.get('chart_mode'))
        chart_layout.addWidget(self.chart_widget)
        left_layout.addWidget(self.chart_card, 1)

        # Panel derecho: Resumen y análisis (desplazable)
        self.summary_panel = SummaryPanel()
        self.summary_panel.advice_group.setVisible(self.settings.get_bool('show_daily_advice'))
        summary_scroll = QScrollArea()
        summary_scroll.setWidgetResizable(True)
        summary_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        summary_scroll.setWidget(self.summary_panel)
        summary_scroll.setMinimumWidth(380)

        # Añadir paneles al splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(summary_scroll)

        # Configurar proporciones del splitter (70% - 30%)
        splitter.setSizes([1000, 420])
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)

        body_layout.addWidget(splitter)

        # Barra de estado
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("✅ " + tr("loading"))

        self._setup_shortcuts()

        # Aplicar tema guardado (oscuro por defecto)
        self.apply_theme(self.dark_mode)

        # Cargar datos iniciales
        self.load_initial_data()
        # Actualizar título con la semana actual tras cargar datos
        try:
            self.update_window_title_with_week()
        except Exception:
            pass

        for i, w in enumerate((self.table_card, self.chart_card)):
            fade_in(w, duration=650, delay=80 + i * 140)

    def _build_header(self):
        """Cabecera con marca, semana y acciones principales."""
        header = QFrame()
        header.setObjectName('header')
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(12)

        if self.logo_path:
            logo = QLabel()
            logo.setPixmap(QPixmap(self.logo_path).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            layout.addWidget(logo)
        brand = QVBoxLayout()
        brand.setSpacing(0)
        name = QLabel('W-T-F')
        name.setObjectName('brand')
        tagline = QLabel('Weekend Trading Finance')
        tagline.setObjectName('caption')
        brand.addWidget(name)
        brand.addWidget(tagline)
        layout.addLayout(brand)
        layout.addSpacing(10)
        self.week_chip = QLabel('')
        self.week_chip.setObjectName('chip')
        layout.addWidget(self.week_chip)
        layout.addStretch()

        self.image_btn = QPushButton('✨  ' + tr('result_image_title', 'Imagen de resultado'))
        self.image_btn.setObjectName('primary')
        self.image_btn.setCursor(Qt.PointingHandCursor)
        self.image_btn.setToolTip(tr('generate_result_image', 'Generar imagen del resultado') + '  (Ctrl+G)')
        self.image_btn.clicked.connect(lambda: self.open_result_image())
        layout.addWidget(self.image_btn)

        self.import_btn = QPushButton('📥  ' + tr('import_analyze', 'Importar'))
        self.import_btn.setToolTip(tr('import_title', 'Importar y analizar operaciones') + '  (Ctrl+I)')
        self.import_btn.setCursor(Qt.PointingHandCursor)
        self.import_btn.clicked.connect(lambda: self.open_import())
        layout.addWidget(self.import_btn)

        self.save_btn = QPushButton('💾')
        self.save_btn.setToolTip(tr('save_week') + '  (Ctrl+S)')
        self.save_btn.clicked.connect(self.save_week)
        self.theme_btn = QPushButton('')
        self.theme_btn.setToolTip(tr('dark_mode') + '  (Ctrl+D)')
        self.theme_btn.clicked.connect(lambda: self.set_dark_mode(not self.dark_mode))
        self.settings_btn = QPushButton('⚙️')
        self.settings_btn.setToolTip(tr('settings_title', 'Configuración') + '  (Ctrl+,)')
        self.settings_btn.clicked.connect(lambda: self.open_settings())
        for b in (self.save_btn, self.theme_btn, self.settings_btn):
            b.setObjectName('ghost')
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedWidth(46)
            b.setMinimumWidth(46)
            b.setStyleSheet('font-size: 13pt; padding: 6px;')
            layout.addWidget(b)
        return header

    def _setup_shortcuts(self):
        for keys, slot in (
            (QKeySequence.Save, self.save_week),
            (QKeySequence.Open, self.load_week),
            ('Ctrl+G', lambda: self.open_result_image()),
            ('Ctrl+,', lambda: self.open_settings()),
            ('Ctrl+E', lambda: self.export_data()),
            ('Ctrl+I', lambda: self.open_import()),
            ('Ctrl+D', lambda: self.set_dark_mode(not self.dark_mode)),
            (QKeySequence.Quit, self.close),
        ):
            QShortcut(QKeySequence(keys), self, activated=slot)

    # ------------------------------------------------------------------
    # Acciones invocadas desde la ventana de Configuración
    def open_settings(self, page='appearance'):
        dialog = SettingsDialog(self, self.settings, page)
        dialog.exec_()
        # Refrescar valores por defecto que usa la tabla
        self.table_widget.default_pair = self.settings.get('default_pair')
        self.table_widget.default_duration = self.settings.get('default_duration')

    def open_import(self, paths=None):
        """Ventana para importar Excel/CSV/JSON y analizar las operaciones con gráficos."""
        dialog = ImportDialog(self.data_model, self.settings, self.dark_mode, self, paths)
        dialog.week_updated.connect(lambda: self.on_day_updated(None))
        dialog.exec_()

    # Soltar archivos sobre la ventana principal abre el análisis
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and any(u.toLocalFile().lower().endswith(SUPPORTED_EXT)
                                              for u in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.toLocalFile().lower().endswith(SUPPORTED_EXT)]
        if paths:
            self.open_import(paths)

    def open_result_image(self, day=None):
        dialog = ResultImageDialog(self, self.data_model, self.settings, self.dark_mode,
                                   initial_day=day or self.table_widget.selected_day(),
                                   open_settings=self.open_settings)
        dialog.day_updated.connect(self.on_day_updated)
        dialog.exec_()

    def on_day_updated(self, day):
        self.table_widget.load_data()
        self.on_data_changed()

    def set_dark_mode(self, is_dark: bool):
        self.settings.set('dark_mode', bool(is_dark))
        self.apply_theme(bool(is_dark))

    def change_language(self, lang: str):
        set_language(lang)
        self.settings.set('language', lang)
        self.on_language_changed(lang)

    def set_chart_mode(self, mode: str):
        self.settings.set('chart_mode', mode)
        self.chart_widget.set_mode(mode)

    def set_chart_animations(self, enabled: bool):
        self.chart_widget.set_animations_enabled(enabled)

    def set_capital_edit_mode(self, enabled: bool):
        self.table_widget.set_capital_edit_mode(enabled)

    def update_window_title_with_week(self):
        """Actualizar el título de la ventana para mostrar la semana actual."""
        try:
            from datetime import datetime, timedelta
            base_title = tr("app_title")
            week_date = getattr(self.data_model, 'week_start_date', None)
            if not week_date:
                today = datetime.now().date()
                week_date = today - timedelta(days=today.weekday())
            # Formato: App Title — Semana YYYY-MM-DD
            self.setWindowTitle(f"{base_title} — {tr('week')} {week_date.isoformat()}")
            self.week_chip.setText(f"📅 {tr('week')} {week_date.strftime('%d/%m/%Y')}")
        except Exception:
            # Fallback al título base si algo falla
            self.setWindowTitle(tr("app_title"))
    
    def setup_connections(self):
        """Configurar conexiones entre componentes"""
        # Conexiones de la tabla
        self.table_widget.data_changed.connect(self.on_data_changed)
        self.table_widget.save_status_changed.connect(self.update_save_status)
        self.table_widget.generate_image_requested.connect(self.open_result_image)

        # Persistir el modo del gráfico elegido desde sus botones 2D/3D
        self.chart_widget.mode_changed.connect(lambda m: self.settings.set('chart_mode', m))

        # Mostrar consejo del día al iniciar
        self.show_daily_advice()

    def apply_theme(self, is_dark: bool):
        """Aplicar tema profesional a toda la aplicación"""
        self.dark_mode = is_dark

        # El ThemeManager aplica un único stylesheet a nivel de QApplication,
        # por lo que cubre automáticamente ventana principal, tabla,
        # barra de estado y cualquier diálogo (presente o futuro).
        self.theme_manager.apply_theme(self, is_dark)
        self.theme_btn.setText('☀️' if is_dark else '🌙')

        # Colores dinámicos de cada componente
        self.chart_widget.set_theme(is_dark)
        self.table_widget.set_theme(is_dark)
        self.summary_panel.set_theme(is_dark)

        # Brillo del botón principal acorde al tema
        accent = self.theme_manager.colors(is_dark)['accent']
        if hasattr(self.image_btn, '_pulse_anim'):
            self.image_btn._pulse_anim.stop()
        pulse_glow(self.image_btn, accent, low=10, high=30)

    def on_toggle_legend(self, visible: bool):
        """Mostrar u ocultar la leyenda del gráfico desde el menú."""
        try:
            self.chart_widget.set_legend_visible(visible)
        except Exception:
            pass
    
    def load_initial_data(self):
        """Cargar datos iniciales al iniciar la aplicación"""
        try:
            # Intentar cargar la última semana guardada
            if self.data_model.load_latest_week():
                self.table_widget.load_data()
                self.update_chart()  # Actualizar gráfico con datos cargados
                self.update_summary()
                self.status_bar.showMessage("✅ " + tr("initial_data_loaded_db"), 3000)
                # Consejos al cargar datos
                self.show_daily_advice()
                # Si es sábado, mostrar resumen semanal
                try:
                    from datetime import datetime
                    if datetime.now().weekday() == 5:
                        self.show_weekly_summary_notification()
                        # Realizar rollover automático a la nueva semana
                        self.perform_saturday_rollover()
                except Exception:
                    pass
            else:
                # Si no hay datos, preguntar por el capital inicial
                self.ask_for_initial_capital()
                # Actualizar gráfico con datos vacíos
                self.update_chart()
                self.status_bar.showMessage("ℹ️ " + tr("no_previous_data_new_week"), 3000)
                self.show_daily_advice()
                # Si es sábado, mostrar resumen semanal
                try:
                    from datetime import datetime
                    if datetime.now().weekday() == 5:
                        self.show_weekly_summary_notification()
                        # Realizar rollover automático a la nueva semana
                        self.perform_saturday_rollover()
                except Exception:
                    pass
                
        except Exception as e:
            QMessageBox.warning(self, tr("warning"), 
                              f"{tr('load_error')}: {str(e)}\n"
                              f"{tr('operation_failed')}.")
            # Asegurar que el gráfico se actualice incluso si hay error
            self.update_chart()
    
    @pyqtSlot()
    def on_data_changed(self):
        """Manejar cambios en los datos"""
        try:
            # Actualizar gráfico
            self.update_chart()
            
            # Actualizar resumen y análisis AI
            self.update_summary()
            
            # Guardar automáticamente en base de datos
            self.data_model.save_current_week()
            
        except Exception as e:
            QMessageBox.critical(self, tr("error"), f"{tr('operation_failed')}: {str(e)}")
    
    def update_chart(self):
        """Actualizar el gráfico con datos actuales"""
        try:
            self.chart_widget.update_chart(self.data_model)
        except Exception as e:
            print(f"Error al actualizar gráfico: {e}")
    
    def update_summary(self):
        """Actualizar el panel de resumen con análisis AI"""
        try:
            # Obtener resumen de datos
            summary_data = self.data_model.get_weekly_summary()
            
            # Generar análisis AI
            ai_analysis = self.ai_analyzer.analyze_weekly_performance(summary_data, self.data_model.data)
            
            # Preparar datos del capital
            capital_data = {
                'initial_capital': self.data_model.initial_capital,
                'current_balance': self.data_model.get_current_balance(),
                'total_profit_loss': self.data_model.get_total_profit_loss(),
                'profit_loss_percentage': self.data_model.get_profit_loss_percentage()
            }
            
            # Actualizar panel
            self.summary_panel.update_summary(summary_data, ai_analysis, capital_data)
            # Actualizar consejo del día
            try:
                advice = get_daily_advice(self.data_model)
                self.summary_panel.update_daily_advice(advice)
            except Exception:
                pass
            
        except Exception as e:
            print(f"Error al actualizar resumen: {e}")
            # Mostrar resumen sin análisis AI
            summary_data = self.data_model.get_weekly_summary()
            capital_data = {
                'initial_capital': getattr(self.data_model, 'initial_capital', 100.0),
                'current_balance': getattr(self.data_model, 'initial_capital', 100.0),
                'total_profit_loss': 0,
                'profit_loss_percentage': 0
            }
            self.summary_panel.update_summary(summary_data, {}, capital_data)
            # Intentar actualizar consejo del día
            try:
                advice = get_daily_advice(self.data_model)
                self.summary_panel.update_daily_advice(advice)
            except Exception:
                pass

    def show_daily_advice(self):
        """Mostrar consejo del día en el panel y en la barra de estado."""
        try:
            advice = get_daily_advice(self.data_model)
            self.summary_panel.update_daily_advice(advice)
            self.status_bar.showMessage("📌 " + tr("daily_advice"), 3000)
        except Exception as e:
            print(f"Error al generar consejo del día: {e}")

    def on_toggle_daily_advice_visibility(self, visible: bool):
        """Mostrar/Ocultar el grupo de consejo del día desde el menú."""
        try:
            self.summary_panel.advice_group.setVisible(visible)
            msg = ("✅ " + tr('daily_advice') if visible else "🙈 " + tr('daily_advice'))
            self.status_bar.showMessage(msg, 2000)
        except Exception as e:
            print(f"No se pudo cambiar visibilidad del consejo: {e}")

    def show_weekly_summary_notification(self):
        """Mostrar notificación de resumen semanal (útil para sábados)."""
        try:
            WeeklySummaryDialog(self.data_model, self.dark_mode, self).exec_()
        except Exception as e:
            QMessageBox.warning(self, tr("warning"), f"{tr('operation_failed')}: {e}")

    def perform_saturday_rollover(self):
        """Si es sábado, crea automáticamente la nueva semana para el lunes próximo con capital actualizado.
        Evita sobreescribir la semana previa creando un nuevo registro y archivo con datos en cero.
        """
        try:
            from datetime import timedelta
            # Calcular el lunes próximo respecto a la semana cargada
            current_week_start = getattr(self.data_model, 'week_start_date', None)
            if not current_week_start:
                return

            next_monday_date = current_week_start + timedelta(days=7)

            # Si ya estamos en la semana del próximo lunes, no repetir
            if self.data_model.week_start_date >= next_monday_date:
                return

            # Calcular retiro recomendado y nuevo capital
            total = float(self.data_model.get_total_profit_loss())
            balance = float(self.data_model.get_current_balance())
            withdraw = max(0.0, total) * 0.30
            new_initial = max(0.0, balance - withdraw)

            # Crear nueva semana en el modelo/BD
            created = self.data_model.start_new_week(next_monday_date, new_initial)
            if not created:
                QMessageBox.warning(self, tr("warning"), tr("operation_failed"))
                return

            # Actualizar UI con datos reiniciados
            self.table_widget.load_data()
            self.update_chart()
            self.update_summary()

            # Guardar automáticamente archivo JSON de la nueva semana
            try:
                self.save_week()
            except Exception:
                pass

            # Mensaje de estado informativo
            self.status_bar.showMessage(
                f"✅ {tr('week')} {next_monday_date.isoformat()} | {tr('capital_initial')} ${new_initial:.2f}",
                5000
            )
            # Actualizar título con nueva semana
            try:
                self.update_window_title_with_week()
            except Exception:
                pass
        except Exception as e:
            print(f"Error en rollover del sábado: {e}")

    def start_new_week_reset(self):
        """Crear manualmente una nueva semana con datos en cero para evitar sobreescritura.
        Útil si se omitió el sábado y se abre el domingo u otro día.
        """
        try:
            from datetime import timedelta
            current_week_start = getattr(self.data_model, 'week_start_date', None)
            if not current_week_start:
                QMessageBox.warning(self, tr("warning"), tr("capital_required"))
                return

            confirm = QMessageBox.question(
                self,
                tr("confirm"),
                tr("status_start_new_week_reset"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if confirm != QMessageBox.Yes:
                return

            next_monday_date = current_week_start + timedelta(days=7)

            if self.data_model.week_start_date >= next_monday_date:
                QMessageBox.information(self, tr("information"), tr("operation_completed"))
                return

            total = float(self.data_model.get_total_profit_loss())
            balance = float(self.data_model.get_current_balance())
            withdraw = max(0.0, total) * 0.30
            new_initial = max(0.0, balance - withdraw)

            created = self.data_model.start_new_week(next_monday_date, new_initial)
            if not created:
                QMessageBox.warning(self, tr("warning"), tr("operation_failed"))
                return

            self.table_widget.load_data()
            self.update_chart()
            self.update_summary()

            try:
                self.save_week()
            except Exception:
                pass

            self.status_bar.showMessage(
                f"🆕 {tr('week')} {next_monday_date.isoformat()} | {tr('capital_initial')} ${new_initial:.2f}",
                5000
            )
            # Actualizar título con nueva semana
            try:
                self.update_window_title_with_week()
            except Exception:
                pass
        except Exception as e:
            QMessageBox.warning(self, tr("warning"), f"{tr('operation_failed')}: {e}")
    
    def on_language_changed(self, lang: str):
        """Actualizar textos y re-traducir widgets principales."""
        # Actualizar título de la ventana con semana
        try:
            self.update_window_title_with_week()
        except Exception:
            self.setWindowTitle(tr("app_title"))
        # Retraducir tabla de trading
        if hasattr(self.table_widget, 'apply_language'):
            self.table_widget.apply_language()
        # Retraducir panel de resumen
        if hasattr(self.summary_panel, 'apply_language'):
            self.summary_panel.apply_language()
        # Retraducir gráfico
        if hasattr(self.chart_widget, 'apply_language'):
            self.chart_widget.apply_language()
        # Cabecera y tarjetas
        self.image_btn.setText('✨  ' + tr('result_image_title', 'Imagen de resultado'))
        self.import_btn.setText('📥  ' + tr('import_analyze', 'Importar'))
        self.table_title.setText('📅 ' + tr('week_results', 'Resultados de la semana'))
        self.table_hint.setText(tr('table_hint', 'Doble clic para editar · clic derecho para más opciones'))
    
    @pyqtSlot(str)
    def update_save_status(self, status):
        """Actualizar estado de guardado"""
        self.status_bar.showMessage(status, 3000)
        
        # Actualizar también el panel de resumen
        self.summary_panel.update_status(status)
    
    def save_week(self):
        """Guardar automáticamente la semana en la carpeta de semanas sin diálogo"""
        try:
            from datetime import datetime, timedelta

            # Carpeta de semanas configurable (por defecto Weekend-Saved junto a la app)
            save_folder = self.settings.weeks_dir()
            os.makedirs(save_folder, exist_ok=True)

            # Determinar el lunes de la semana a guardar
            monday_date = None
            if hasattr(self.data_model, 'week_start_date') and self.data_model.week_start_date:
                monday_date = self.data_model.week_start_date
            else:
                today = datetime.now()
                monday_date = today - timedelta(days=today.weekday())

            # Nombre de archivo basado en el lunes de la semana
            monday_str = monday_date.strftime("%Y-%m-%d")
            default_filename = f"weekend_trading_{monday_str}.json"
            filepath = os.path.join(save_folder, default_filename)

            # Guardar en archivo JSON directamente
            if self.data_model.save_to_file(filepath):
                self.update_save_status("✅ " + tr("save_success"))
            else:
                self.update_save_status("❌ " + tr("save_error"))

        except Exception as e:
            QMessageBox.critical(self, tr("save_error"), str(e))
            self.update_save_status("❌ " + tr("save_error"))
    
    def load_week(self):
        """Cargar semana desde un diálogo que lista las semanas guardadas."""
        try:
            dialog = LoadWeekDialog(self, tr=tr, folder=self.settings.weeks_dir())
            if dialog.exec_() == QDialog.Accepted:
                filename = dialog.get_selected_file_path()
                if not filename:
                    QMessageBox.warning(self, tr("warning"), tr("select_week_first"))
                    return
                if self.data_model.load_from_file(filename):
                    self.table_widget.load_data()
                    self.update_chart()
                    self.update_summary()
                    self.update_save_status("✅ " + tr("load_success"))
                    # Actualizar título con semana cargada
                    try:
                        self.update_window_title_with_week()
                    except Exception:
                        pass
                else:
                    self.update_save_status("❌ " + tr("load_error"))
        except Exception as e:
            QMessageBox.critical(self, tr("load_error"), str(e))
            self.update_save_status("❌ " + tr("load_error"))
    
    def load_from_database(self):
        """Cargar desde base de datos"""
        try:
            weeks = self.data_model.get_all_saved_weeks()

            if not weeks:
                QMessageBox.information(self, tr("information"), tr("file_not_found"))
                return

            if len(weeks) == 1:
                week_date = weeks[0]
            else:
                # Crear diálogo de selección
                from PyQt5.QtWidgets import QInputDialog
                dialog = QInputDialog(self)
                dialog.setWindowTitle(tr("load_week_title"))
                dialog.setLabelText(tr("week") + ":")
                dialog.setComboBoxItems([f"{tr('week')} {w}" for w in weeks])

                if dialog.exec_() == QInputDialog.Accepted:
                    item = dialog.textValue()
                    # Extraer fecha de la semana usando clave traducida
                    prefix = tr("week") + " "
                    week_date = item.replace(prefix, "")
                else:
                    return

            # Cargar la semana seleccionada
            if self.data_model.load_week(week_date):
                self.table_widget.load_data()
                self.update_chart()
                self.update_summary()
                # Actualizar título con semana cargada
                try:
                    self.update_window_title_with_week()
                except Exception:
                    pass
                self.update_save_status(f"✅ {tr('week')} {week_date} {tr('load_success')}")
            else:
                QMessageBox.warning(self, tr("warning"), f"{tr('load_error')} {week_date}")

        except Exception as e:
            QMessageBox.critical(self, tr("error"), f"{tr('load_error')} {str(e)}")
            self.update_save_status("❌ " + tr("load_error"))

    def ask_for_initial_capital(self):
        """Preguntar por el capital inicial al iniciar una semana nueva"""
        try:
            dialog = CapitalDialog(100.0, self, first_time=True)  # Capital inicial por defecto: $100

            if dialog.exec_() == CapitalDialog.Accepted:
                new_capital = dialog.get_capital()
                self.data_model.initial_capital = new_capital
                self.data_model.save_current_week()
                self.update_summary()
                self.status_bar.showMessage(f"✅ {tr('capital_initial')} ${new_capital:.2f}", 3000)
                # Actualizar título (semana actual por defecto)
                try:
                    self.update_window_title_with_week()
                except Exception:
                    pass
            else:
                # Si cancela, usar valor por defecto
                self.data_model.initial_capital = 100.0
                self.data_model.save_current_week()
                self.update_summary()
                self.status_bar.showMessage(f"ℹ️ {tr('capital_initial')} $100.00", 3000)
                try:
                    self.update_window_title_with_week()
                except Exception:
                    pass
                
        except Exception as e:
            # En caso de error, usar valor por defecto
            self.data_model.initial_capital = 100.0
            print(f"Error al preguntar por capital inicial: {e}")
    
    def set_initial_capital(self):
        """Abrir diálogo para establecer el capital inicial"""
        try:
            dialog = CapitalDialog(self.data_model.initial_capital, self)

            if dialog.exec_() == CapitalDialog.Accepted:
                new_capital = dialog.get_capital()
                if new_capital != self.data_model.initial_capital:
                     self.data_model.initial_capital = new_capital
                     self.data_model.save_current_week()
                     self.update_summary()
                     self.update_save_status(f"✅ {tr('capital_initial')} ${new_capital:.2f}")
        except Exception as e:
            QMessageBox.critical(self, tr("error"), f"{tr('operation_failed')}: {str(e)}")
            self.update_save_status("❌ " + tr("operation_failed"))
    
    def export_data(self, fmt=None):
        """Abrir la ventana de exportación (fmt preselecciona Excel, CSV o JSON)."""
        try:
            show_export_dialog(self.data_model, self.settings, fmt, self.dark_mode, self)
        except Exception as e:
            QMessageBox.critical(self, tr("error"), f"{tr('export_error')}: {str(e)}")
            self.update_save_status("❌ " + tr("export_error"))

    def export_to_excel(self):
        self.export_data('excel')

    def export_to_csv(self):
        self.export_data('csv')

    def export_to_json(self):
        self.export_data('json')

    def closeEvent(self, event):
        """Manejar cierre de la aplicación"""
        try:
            # Guardar estado actual antes de cerrar
            self.data_model.save_current_week()
            event.accept()
        except Exception as e:
            reply = QMessageBox.question(self, tr("confirm_close_title"),
                                       f"{tr('save_error')}: {str(e)}\n{tr('close_anyway_question')}",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()

def main():
    """Función principal"""
    # En el ejecutable empaquetado, trabajar siempre desde la carpeta de instalación:
    # así trading_data.db, src/images y Weekend-Saved no dependen de cómo se lanzó la app.
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))

    app = QApplication(sys.argv)
    
    # Configurar estilo de la aplicación
    app.setStyle('Fusion')
    
    # Establecer icono global para toda la aplicación usando ruta absoluta base + src/images
    try:
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.getcwd())
        images_dir = os.path.join(base_dir, 'src', 'images')
        logo_png = os.path.join(images_dir, 'logo.png')
        fallback_svg = os.path.join(images_dir, 'app_icon.svg')
        if os.path.exists(logo_png):
            app.setWindowIcon(QIcon(logo_png))
        elif os.path.exists(fallback_svg):
            app.setWindowIcon(QIcon(fallback_svg))
    except Exception as e:
        print(f"Error al establecer icono global: {e}")
    
    # Crear y mostrar ventana principal con aparición suave
    window = MainWindow()
    window.setWindowOpacity(0.0)
    window.show()
    intro = QPropertyAnimation(window, b"windowOpacity", window)
    intro.setDuration(550)
    intro.setStartValue(0.0)
    intro.setEndValue(1.0)
    intro.setEasingCurve(QEasingCurve.OutCubic)
    intro.start()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
