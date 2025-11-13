"""
Menú principal con opción de modo oscuro
"""

from PyQt5.QtWidgets import (QMenuBar, QMenu, QAction, QMessageBox, QFileDialog,
                             QApplication, QStyle, QDialog, QVBoxLayout, QLabel,
                             QPushButton, QHBoxLayout)
from PyQt5.QtCore import pyqtSignal, Qt, QUrl, QSize
from PyQt5.QtGui import QIcon, QKeySequence, QPixmap, QDesktopServices
import os
import sys
from src.utils.i18n import tr, set_language as set_global_language
from src.utils.i18n import current_language as i18n_current_language

class MainMenuBar(QMenuBar):
    """Menú principal de la aplicación"""
    
    # Señales
    save_triggered = pyqtSignal()
    load_triggered = pyqtSignal()
    load_from_db_triggered = pyqtSignal()
    set_capital_triggered = pyqtSignal()
    theme_changed = pyqtSignal(bool)  # True para modo oscuro
    legend_visibility_changed = pyqtSignal(bool)
    day_capital_edit_mode_changed = pyqtSignal(bool)
    show_daily_advice_triggered = pyqtSignal()
    daily_advice_visibility_changed = pyqtSignal(bool)
    show_weekly_summary_triggered = pyqtSignal()
    start_new_week_triggered = pyqtSignal()
    export_excel_triggered = pyqtSignal()
    export_csv_triggered = pyqtSignal()
    export_json_triggered = pyqtSignal()
    language_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dark_mode = False
        self.current_language = i18n_current_language
        # Referencias a menús y acciones para aplicar traducción
        self._menus = {}
        self._actions = {}
        self.setup_menus()
        self.apply_language()
    
    def setup_menus(self):
        """Configurar los menús"""
        # Menú Archivo
        self._menus['file'] = self.addMenu(tr('menu_file'))
        
        # Acción Guardar
        self._actions['save'] = QAction(tr('save_week'), self)
        self._actions['save'].setShortcut(QKeySequence.Save)
        self._actions['save'].setStatusTip(tr('status_save_week'))
        self._actions['save'].triggered.connect(self.save_triggered.emit)
        self._menus['file'].addAction(self._actions['save'])
        
        # Acción Cargar
        self._actions['load'] = QAction(tr('load_week'), self)
        self._actions['load'].setShortcut(QKeySequence.Open)
        self._actions['load'].setStatusTip(tr('status_load_week'))
        self._actions['load'].triggered.connect(self.load_triggered.emit)
        self._menus['file'].addAction(self._actions['load'])
        
        # Acción Cargar desde BD
        self._actions['load_db'] = QAction(tr('load_from_db'), self)
        self._actions['load_db'].setStatusTip(tr('status_load_db'))
        self._actions['load_db'].triggered.connect(self.load_from_db_triggered.emit)
        self._menus['file'].addAction(self._actions['load_db'])
        
        self._menus['file'].addSeparator()
        
        # Acción Establecer Capital Inicial
        self._actions['set_capital'] = QAction(tr('set_capital'), self)
        self._actions['set_capital'].setStatusTip(tr('status_set_capital'))
        self._actions['set_capital'].triggered.connect(self.set_capital_triggered.emit)
        self._menus['file'].addAction(self._actions['set_capital'])
        
        self._menus['file'].addSeparator()
        
        # Acción Salir
        self._actions['exit'] = QAction(tr('exit'), self)
        self._actions['exit'].setShortcut(QKeySequence.Quit)
        self._actions['exit'].setStatusTip(tr('status_exit'))
        self._actions['exit'].triggered.connect(self.parent().close)
        self._menus['file'].addAction(self._actions['exit'])
        
        # Menú Vista
        self._menus['view'] = self.addMenu(tr('menu_view'))
        
        # Acción Modo Oscuro
        self.dark_mode_action = QAction(tr('dark_mode'), self)
        self.dark_mode_action.setCheckable(True)
        self.dark_mode_action.setStatusTip(tr('status_dark_mode'))
        self.dark_mode_action.triggered.connect(self.toggle_dark_mode)
        self._menus['view'].addAction(self.dark_mode_action)
        self._actions['dark_mode'] = self.dark_mode_action

        # Acción Mostrar/Ocultar Leyenda
        self.legend_toggle_action = QAction(tr('toggle_legend'), self)
        self.legend_toggle_action.setCheckable(True)
        self.legend_toggle_action.setChecked(True)
        self.legend_toggle_action.setStatusTip(tr('status_toggle_legend'))
        self.legend_toggle_action.toggled.connect(self.legend_visibility_changed.emit)
        self._menus['view'].addAction(self.legend_toggle_action)
        self._actions['toggle_legend'] = self.legend_toggle_action

        # Acción Modo edición por capital
        self.capital_edit_mode_action = QAction(tr('capital_edit_mode'), self)
        self.capital_edit_mode_action.setCheckable(True)
        self.capital_edit_mode_action.setStatusTip(tr('status_capital_edit_mode'))
        self.capital_edit_mode_action.toggled.connect(self.day_capital_edit_mode_changed.emit)
        self._menus['view'].addAction(self.capital_edit_mode_action)
        self._actions['capital_edit_mode'] = self.capital_edit_mode_action
        
        # Menú Asistente
        self._menus['assistant'] = self.addMenu(tr('menu_assistant'))
        self._actions['daily_advice'] = QAction(tr('daily_advice'), self)
        self._actions['daily_advice'].setCheckable(True)
        self._actions['daily_advice'].setChecked(True)
        self._actions['daily_advice'].setStatusTip(tr('status_daily_advice'))
        # toggle de visibilidad y disparar actualización de contenido
        self._actions['daily_advice'].toggled.connect(self.daily_advice_visibility_changed.emit)
        self._actions['daily_advice'].triggered.connect(self.show_daily_advice_triggered.emit)
        self._menus['assistant'].addAction(self._actions['daily_advice'])

        self._actions['weekly_summary'] = QAction(tr('weekly_summary'), self)
        self._actions['weekly_summary'].setStatusTip(tr('status_weekly_summary'))
        self._actions['weekly_summary'].triggered.connect(self.show_weekly_summary_triggered.emit)
        self._menus['assistant'].addAction(self._actions['weekly_summary'])

        # Acción: Empezar nueva semana (reiniciar datos)
        self._actions['start_new_week_reset'] = QAction(tr('start_new_week_reset'), self)
        self._actions['start_new_week_reset'].setStatusTip(tr('status_start_new_week_reset'))
        self._actions['start_new_week_reset'].triggered.connect(self.start_new_week_triggered.emit)
        self._menus['assistant'].addAction(self._actions['start_new_week_reset'])
        
        # Menú Exportar
        self._menus['export'] = self.addMenu(tr('menu_export'))
        
        self._actions['export_excel'] = QAction(tr('export_excel'), self)
        self._actions['export_excel'].setShortcut('Ctrl+E')
        self._actions['export_excel'].setStatusTip(tr('status_export_excel'))
        self._actions['export_excel'].triggered.connect(self.export_excel_triggered)
        self._menus['export'].addAction(self._actions['export_excel'])
        
        self._actions['export_csv'] = QAction(tr('export_csv'), self)
        self._actions['export_csv'].setShortcut('Ctrl+Shift+C')
        self._actions['export_csv'].setStatusTip(tr('status_export_csv'))
        self._actions['export_csv'].triggered.connect(self.export_csv_triggered)
        self._menus['export'].addAction(self._actions['export_csv'])
        
        self._actions['export_json'] = QAction(tr('export_json'), self)
        self._actions['export_json'].setStatusTip(tr('status_export_json'))
        self._actions['export_json'].triggered.connect(self.export_json_triggered)
        self._menus['export'].addAction(self._actions['export_json'])
        
        # Menú Ayuda
        self._menus['help'] = self.addMenu(tr('menu_help'))
        
        # Acción Acerca de
        self._actions['about'] = QAction(tr('about'), self)
        self._actions['about'].setStatusTip(tr('status_about'))
        self._actions['about'].triggered.connect(self.show_about)
        self._menus['help'].addAction(self._actions['about'])
        
        # Acción Instrucciones
        self._actions['instructions'] = QAction(tr('instructions'), self)
        self._actions['instructions'].setStatusTip(tr('status_instructions'))
        self._actions['instructions'].triggered.connect(self.show_instructions)
        self._menus['help'].addAction(self._actions['instructions'])

        # Menú Idioma
        self._menus['language'] = self.addMenu(tr('menu_language'))
        self._actions['lang_es'] = QAction('🇪🇸 ' + tr('spanish'), self)
        self._actions['lang_en'] = QAction('🇺🇸 ' + tr('english'), self)
        self._actions['lang_es'].triggered.connect(lambda: self.set_language('es'))
        self._actions['lang_en'].triggered.connect(lambda: self.set_language('en'))
        self._menus['language'].addAction(self._actions['lang_es'])
        self._menus['language'].addAction(self._actions['lang_en'])
    
    def toggle_dark_mode(self, checked):
        """Cambiar entre modo claro y oscuro"""
        self.dark_mode = checked
        self.theme_changed.emit(checked)
        self.apply_theme_to_menu()
    
    def apply_theme_to_menu(self):
        """Aplicar tema al menú"""
        if self.dark_mode:
            # Estilo modo oscuro para el menú
            self.setStyleSheet("""
                QMenuBar {
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                    padding: 5px;
                    border-bottom: 1px solid #2a2a2a;
                }
                
                QMenuBar::item {
                    background-color: transparent;
                    padding: 8px 15px;
                    margin: 2px;
                    border-radius: 4px;
                }
                
                QMenuBar::item:selected {
                    background-color: #2a2a2a;
                    color: #e0e0e0;
                }
                
                QMenuBar::item:pressed {
                    background-color: #3a3a3a;
                    color: #e0e0e0;
                }
                
                QMenu {
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                    border: 1px solid #2a2a2a;
                    border-radius: 4px;
                    padding: 5px;
                }
                
                QMenu::item {
                    padding: 8px 20px;
                    margin: 2px;
                    border-radius: 3px;
                }
                
                QMenu::item:selected {
                    background-color: #2a2a2a;
                    color: #e0e0e0;
                }
                
                QMenu::separator {
                    height: 1px;
                    background-color: #2a2a2a;
                    margin: 5px 10px;
                }
            """)
        else:
            # Estilo modo claro para el menú
            self.setStyleSheet("""
                QMenuBar {
                    background-color: #f8f9fa;
                    color: #2c3e50;
                    padding: 5px;
                    border-bottom: 1px solid #dee2e6;
                }
                
                QMenuBar::item {
                    background-color: transparent;
                    padding: 8px 15px;
                    margin: 2px;
                    border-radius: 4px;
                }
                
                QMenuBar::item:selected {
                    background-color: #e9ecef;
                    color: #3498db;
                }
                
                QMenuBar::item:pressed {
                    background-color: #3498db;
                    color: white;
                }
                
                QMenu {
                    background-color: white;
                    color: #2c3e50;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 5px;
                }
                
                QMenu::item {
                    padding: 8px 20px;
                    margin: 2px;
                    border-radius: 3px;
                }
                
                QMenu::item:selected {
                    background-color: #3498db;
                    color: white;
                }
                
                QMenu::separator {
                    height: 1px;
                    background-color: #dee2e6;
                    margin: 5px 10px;
                }
            """)

    def _t(self, key: str) -> str:
        return tr(key)

    def set_language(self, lang: str):
        """Cambiar idioma y aplicar traducciones básicas"""
        set_global_language(lang)
        self.current_language = lang
        self.apply_language()
        self.language_changed.emit(lang)

    def apply_language(self):
        """Aplicar textos traducidos a menús y acciones principales"""
        # Menús
        if 'file' in self._menus:
            self._menus['file'].setTitle(tr('menu_file'))
        if 'view' in self._menus:
            self._menus['view'].setTitle(tr('menu_view'))
        if 'assistant' in self._menus:
            self._menus['assistant'].setTitle(tr('menu_assistant'))
        if 'export' in self._menus:
            self._menus['export'].setTitle(tr('menu_export'))
        if 'help' in self._menus:
            self._menus['help'].setTitle(tr('menu_help'))
        if 'language' in self._menus:
            self._menus['language'].setTitle(tr('menu_language'))

        # Acciones
        if 'save' in self._actions:
            self._actions['save'].setText(tr('save_week'))
        if 'load' in self._actions:
            self._actions['load'].setText(tr('load_week'))
        if 'load_db' in self._actions:
            self._actions['load_db'].setText(tr('load_from_db'))
        if 'set_capital' in self._actions:
            self._actions['set_capital'].setText(tr('set_capital'))
        if 'exit' in self._actions:
            self._actions['exit'].setText(tr('exit'))
        if 'dark_mode' in self._actions:
            self._actions['dark_mode'].setText(tr('dark_mode'))
        if 'toggle_legend' in self._actions:
            self._actions['toggle_legend'].setText(tr('toggle_legend'))
        if 'capital_edit_mode' in self._actions:
            self._actions['capital_edit_mode'].setText(tr('capital_edit_mode'))
        if 'daily_advice' in self._actions:
            self._actions['daily_advice'].setText(tr('daily_advice'))
        if 'weekly_summary' in self._actions:
            self._actions['weekly_summary'].setText(tr('weekly_summary'))
        if 'start_new_week_reset' in self._actions:
            self._actions['start_new_week_reset'].setText(tr('start_new_week_reset'))
        if 'export_excel' in self._actions:
            self._actions['export_excel'].setText(tr('export_excel'))
        if 'export_csv' in self._actions:
            self._actions['export_csv'].setText(tr('export_csv'))
        if 'export_json' in self._actions:
            self._actions['export_json'].setText(tr('export_json'))
        if 'about' in self._actions:
            self._actions['about'].setText(tr('about'))
        if 'instructions' in self._actions:
            self._actions['instructions'].setText(tr('instructions'))
        if 'lang_es' in self._actions:
            self._actions['lang_es'].setText('🇪🇸 ' + tr('spanish'))
        if 'lang_en' in self._actions:
            self._actions['lang_en'].setText('🇺🇸 ' + tr('english'))

        # StatusTips
        if 'save' in self._actions:
            self._actions['save'].setStatusTip(tr('status_save_week'))
        if 'load' in self._actions:
            self._actions['load'].setStatusTip(tr('status_load_week'))
        if 'load_db' in self._actions:
            self._actions['load_db'].setStatusTip(tr('status_load_db'))
        if 'set_capital' in self._actions:
            self._actions['set_capital'].setStatusTip(tr('status_set_capital'))
        if 'exit' in self._actions:
            self._actions['exit'].setStatusTip(tr('status_exit'))
        if 'dark_mode' in self._actions:
            self._actions['dark_mode'].setStatusTip(tr('status_dark_mode'))
        if 'toggle_legend' in self._actions:
            self._actions['toggle_legend'].setStatusTip(tr('status_toggle_legend'))
        if 'capital_edit_mode' in self._actions:
            self._actions['capital_edit_mode'].setStatusTip(tr('status_capital_edit_mode'))
        if 'daily_advice' in self._actions:
            self._actions['daily_advice'].setStatusTip(tr('status_daily_advice'))
        if 'weekly_summary' in self._actions:
            self._actions['weekly_summary'].setStatusTip(tr('status_weekly_summary'))
        if 'start_new_week_reset' in self._actions:
            self._actions['start_new_week_reset'].setStatusTip(tr('status_start_new_week_reset'))
        if 'export_excel' in self._actions:
            self._actions['export_excel'].setStatusTip(tr('status_export_excel'))
        if 'export_csv' in self._actions:
            self._actions['export_csv'].setStatusTip(tr('status_export_csv'))
        if 'export_json' in self._actions:
            self._actions['export_json'].setStatusTip(tr('status_export_json'))
        if 'about' in self._actions:
            self._actions['about'].setStatusTip(tr('status_about'))
        if 'instructions' in self._actions:
            self._actions['instructions'].setStatusTip(tr('status_instructions'))
    
    def show_about(self):
        """Mostrar diálogo Acerca de"""
        title = tr("about_title")
        if self.current_language == 'es':
            content = """
            <h3>W-T-F (Weekend Trading Finance) Manager</h3>
            <p><strong>Versión:</strong> 2.2</p>
            <p><strong>Descripción:</strong> Aplicación para gestionar y analizar el rendimiento semanal de trading,
            con análisis AI, persistencia de datos y visualizaciones mejoradas.</p>
            <p><strong>Características:</strong></p>
            <ul>
                <li>✅ Gestión de datos semanales</li>
                <li>✅ Análisis AI de rendimiento</li>
                <li>✅ Persistencia en SQLite</li>
                <li>✅ Visualizaciones interactivas</li>
                <li>✅ Modo oscuro/claro</li>
                <li>✅ Exportación de datos</li>
            </ul>
            <p><strong>Tecnologías:</strong> Python, PyQt5, Matplotlib, SQLite</p>
            <p><strong>Creado por:</strong> Onel Crack</p>
            """
            social_label_text = "Sígueme en:"
        else:
            content = """
            <h3>W-T-F (Weekend Trading Finance) Manager</h3>
            <p><strong>Version:</strong> 2.2</p>
            <p><strong>Description:</strong> Application to manage and analyze weekly trading performance,
            with AI analysis, data persistence, and enhanced visualizations.</p>
            <p><strong>Features:</strong></p>
            <ul>
                <li>✅ Weekly data management</li>
                <li>✅ AI performance analysis</li>
                <li>✅ SQLite persistence</li>
                <li>✅ Interactive visualizations</li>
                <li>✅ Dark/Light mode</li>
                <li>✅ Data export</li>
            </ul>
            <p><strong>Tech:</strong> Python, PyQt5, Matplotlib, SQLite</p>
            <p><strong>Created by:</strong> Onel Crack</p>
            """
            social_label_text = "Follow me on:"

        # Crear diálogo personalizado
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setModal(True)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # Contenido principal con icono (restaurar logo en esquina superior izquierda)
        # Resolver ruta de imagen base similar a "Instrucciones"
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.getcwd())
        images_dir = os.path.join(base_dir, 'src', 'images')
        logo_png = os.path.join(images_dir, 'logo.png')

        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        # Icono del diálogo si existe
        try:
            if os.path.exists(logo_png):
                dialog.setWindowIcon(QIcon(logo_png))
                pixmap = QPixmap(logo_png).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_label = QLabel()
                icon_label.setPixmap(pixmap)
                icon_label.setAlignment(Qt.AlignCenter)
                header_layout.addWidget(icon_label, alignment=Qt.AlignCenter)
        except Exception as e:
            print(f"Error al asignar icono al diálogo Acerca de: {e}")

        content_label = QLabel(content)
        content_label.setTextFormat(Qt.RichText)
        content_label.setWordWrap(True)
        content_label.setOpenExternalLinks(True)
        header_layout.addWidget(content_label)
        # Alinear ambos elementos al centro vertical para evitar desalineación en distintos modos
        header_layout.setAlignment(icon_label, Qt.AlignTop)
        header_layout.setAlignment(content_label, Qt.AlignTop)
        main_layout.addLayout(header_layout)

        # Etiqueta de redes sociales
        social_label = QLabel(f"<strong>{social_label_text}</strong>")
        main_layout.addWidget(social_label)

        # Botones de redes sociales
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        # Utilidad: localizar iconos en src/images/socials
        def _icons_dir():
            src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            return os.path.join(src_dir, 'images', 'socials')

        def _find_icon_path(base_name):
            dir_path = _icons_dir()
            candidates = [
                f"{base_name}.png", f"{base_name}.svg", f"{base_name}.jpg", f"{base_name}.ico"
            ]
            for fname in candidates:
                path = os.path.join(dir_path, fname)
                if os.path.isfile(path):
                    return path
            # Búsqueda flexible por nombre contenido
            try:
                for fname in os.listdir(dir_path):
                    lower = fname.lower()
                    if base_name in lower and os.path.isfile(os.path.join(dir_path, fname)):
                        return os.path.join(dir_path, fname)
            except Exception:
                pass
            return None

        def make_social_button(text, bg_color, url, icon_base=None):
            btn = QPushButton(text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(url)
            btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
            # Estilo por red + modo
            base_style = (
                "QPushButton {"
                f"background-color: {bg_color};"
                "color: white; border: none; padding: 8px 12px;"
                "border-radius: 6px; font-weight: bold; }"
                "QPushButton:hover { border: 2px solid white; }"
            )
            btn.setStyleSheet(base_style)
            # Icono si existe
            if icon_base:
                icon_path = _find_icon_path(icon_base)
                if icon_path:
                    btn.setIcon(QIcon(icon_path))
                    btn.setIconSize(QSize(20, 20))
            return btn

        # URLs estimadas basadas en el nombre (actualízalas si es necesario)
        telegram_url = "https://t.me/onel_crack"
        youtube_url = "https://www.youtube.com/@OnelCrack"
        facebook_url = "https://www.facebook.com/profile.php?id=61570586445561"
        instagram_url = "https://www.instagram.com/onel_crack"
        github_url = "https://github.com/TechOGR"

        # Crear botones con emojis
        btn_telegram = make_social_button("Telegram", "#0088cc", telegram_url, icon_base="telegram")
        btn_youtube = make_social_button("YouTube", "#FF0000", youtube_url, icon_base="youtube")
        btn_facebook = make_social_button("Facebook", "#1877F2", facebook_url, icon_base="facebook")
        btn_instagram = make_social_button("Instagram", "#C13584", instagram_url, icon_base="instagram")
        btn_github = make_social_button("GitHub", "#24292e", github_url, icon_base="github")

        buttons_layout.addWidget(btn_telegram)
        buttons_layout.addWidget(btn_youtube)
        buttons_layout.addWidget(btn_facebook)
        buttons_layout.addWidget(btn_instagram)
        buttons_layout.addWidget(btn_github)
        buttons_layout.addStretch()

        main_layout.addLayout(buttons_layout)

        # Botón cerrar
        close_text = tr('close') if hasattr(self, 'current_language') else 'Cerrar'
        close_btn = QPushButton(close_text or 'Cerrar')
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(dialog.accept)
        close_btn.setStyleSheet(
            "QPushButton { background-color: #7f8c8d; color: white; border: none;"
            "padding: 8px 16px; border-radius: 6px; font-weight: bold; }"
            "QPushButton:hover { background-color: #95a5a6; }"
            "QPushButton:pressed { background-color: #707b7c; }"
        )
        main_layout.addWidget(close_btn, alignment=Qt.AlignRight)

        # Aplicar estilo según tema
        if getattr(self, 'dark_mode', False):
            dialog.setStyleSheet(
                "QDialog { background-color: #1e1e1e; }"
                "QLabel { color: #e0e0e0; }"
            )
        else:
            dialog.setStyleSheet(
                "QDialog { background-color: #ffffff; }"
                "QLabel { color: #2c3e50; }"
            )

        dialog.setLayout(main_layout)
        dialog.exec_()
    
    def show_instructions(self):
        """Mostrar instrucciones de uso"""
        title = tr("instructions_title")
        if self.current_language == 'es':
            content = """
            <h3>📖 Instrucciones de Uso</h3>
            <h4>📝 Ingreso de Datos:</h4>
            <ul>
                <li>Haz clic en cualquier celda de la tabla</li>
                <li>Ingresa el monto del día</li>
                <li>Selecciona el destino (Retiro Personal o Reinversión)</li>
                <li>Los cambios se guardan automáticamente</li>
                <li><strong>Modo edición por capital:</strong> Actívalo en Vista para abrir un diálogo al hacer doble clic en el monto del día y calcular Ganancia/Pérdida a partir del capital inicial y actual.</li>
            </ul>
            <h4>💾 Guardar y Cargar:</h4>
            <ul>
                <li><strong>Guardar:</strong> Archivo → Guardar Semana (Ctrl+S)</li>
                <li><strong>Cargar:</strong> Archivo → Cargar Semana (Ctrl+O)</li>
                <li><strong>BD:</strong> Archivo → Cargar desde Base de Datos</li>
                <li><strong>Capital:</strong> Archivo → Establecer Capital Inicial</li>
            </ul>
            <h4>🎨 Personalización:</h4>
            <ul>
                <li>Vista → Modo Oscuro para cambiar el tema</li>
                <li>Vista → Modo edición por capital para editar por capital</li>
                <li>Los gráficos se actualizan automáticamente</li>
                <li>El análisis AI se genera con cada cambio</li>
            </ul>
            <h4>📊 Análisis:</h4>
            <ul>
                <li>Resumen semanal en el panel derecho</li>
                <li>Gráfico de barras con colores por tipo</li>
                <li>Análisis AI con recomendaciones</li>
                <li>Estadísticas de rendimiento</li>
            </ul>
            <p><strong>💡 Consejo:</strong> Usa el análisis AI para mejorar tu estrategia de trading.</p>
            """
        else:
            content = """
            <h3>📖 Usage Instructions</h3>
            <h4>📝 Data Entry:</h4>
            <ul>
                <li>Click any table cell</li>
                <li>Enter the day amount</li>
                <li>Select destination (Personal Withdrawal or Reinvestment)</li>
                <li>Changes are saved automatically</li>
                <li><strong>Capital edit mode:</strong> Enable it under View to open a dialog on double-click of the day amount and compute Profit/Loss from initial and current capital.</li>
            </ul>
            <h4>💾 Save and Load:</h4>
            <ul>
                <li><strong>Save:</strong> File → Save Week (Ctrl+S)</li>
                <li><strong>Load:</strong> File → Load Week (Ctrl+O)</li>
                <li><strong>DB:</strong> File → Load from Database</li>
                <li><strong>Capital:</strong> File → Set Initial Capital</li>
            </ul>
            <h4>🎨 Personalization:</h4>
            <ul>
                <li>View → Dark Mode to change theme</li>
                <li>View → Capital edit mode to edit by capital</li>
                <li>Charts update automatically</li>
                <li>AI analysis is generated on each change</li>
            </ul>
            <h4>📊 Analysis:</h4>
            <ul>
                <li>Weekly summary on the right panel</li>
                <li>Bar chart with colors by type</li>
                <li>AI analysis with recommendations</li>
                <li>Performance statistics</li>
            </ul>
            <p><strong>💡 Tip:</strong> Use AI analysis to improve your trading strategy.</p>
            """
        # Usar QMessageBox explícito y establecer icono con ruta absoluta base_dir/src/images
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.getcwd())
        images_dir = os.path.join(base_dir, 'src', 'images')
        logo_png = os.path.join(images_dir, 'logo.png')
        pixmap = QPixmap(logo_png).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        msg = QMessageBox(self)
        msg.setIconPixmap(pixmap)
        msg.setWindowTitle(title)
        msg.setTextFormat(Qt.RichText)
        msg.setText(content)
        msg.setStandardButtons(QMessageBox.Ok)

        try:
            if os.path.exists(logo_png):
                msg.setWindowIcon(QIcon(logo_png))
            elif os.path.exists(fallback_svg):
                msg.setWindowIcon(QIcon(fallback_svg))
        except Exception as e:
            print(f"Error al asignar icono al diálogo de instrucciones: {e}")

        msg.exec_()