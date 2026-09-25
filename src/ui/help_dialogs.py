"""
Ventanas de ayuda: instrucciones de uso y "Acerca de" con redes sociales.
"""

from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
                             QFrame, QPushButton, QScrollArea, QWidget)
from PyQt5.QtCore import Qt, QUrl, QSize
from PyQt5.QtGui import QDesktopServices, QIcon, QPixmap, QPalette, QColor

from src.styles.themes import ThemeManager
from src.ui.animations import fade_in
from src.utils import i18n
from src.utils.i18n import tr
from src.utils.resources import logo_path, social_icon_path
from src.version import APP_VERSION, APP_PUBLISHER, APP_URL

SOCIALS = [
    # (icono, nombre, usuario, color de marca, url)
    ('telegram', 'Telegram', '@onel_crack', '#229ED9', 'https://t.me/onel_crack'),
    ('youtube', 'YouTube', '@OnelCrack', '#FF0033', 'https://www.youtube.com/@OnelCrack'),
    ('facebook', 'Facebook', 'Onel Crack', '#1877F2', 'https://www.facebook.com/profile.php?id=61570586445561'),
    ('instagram', 'Instagram', '@onel_crack', '#E1306C', 'https://www.instagram.com/onel_crack'),
    ('github', 'GitHub', 'TechOGR', '#8b949e', 'https://github.com/TechOGR'),
]

FEATURES = {
    'es': [('📅', 'Gestión semanal'), ('🤖', 'Análisis con IA'), ('💾', 'Persistencia SQLite'),
           ('📊', 'Gráficos 2D / 3D'), ('✨', 'Imagen de resultado'), ('🌗', 'Modo oscuro / claro'),
           ('📤', 'Exportación Excel, CSV, JSON'), ('🌐', 'Español / English')],
    'en': [('📅', 'Weekly management'), ('🤖', 'AI analysis'), ('💾', 'SQLite persistence'),
           ('📊', '2D / 3D charts'), ('✨', 'Result image'), ('🌗', 'Dark / light mode'),
           ('📤', 'Excel, CSV, JSON export'), ('🌐', 'Español / English')],
}

TECH = ['Python', 'PyQt5', 'Matplotlib', 'pandas', 'SQLite', 'Pillow']

INSTRUCTIONS = {
    'es': [
        ('📝', 'Ingreso de datos', [
            'Doble clic en el <b>monto</b> de un día para escribir la ganancia/pérdida.',
            'Doble clic en <b>Sesión</b> para anotar el par de divisas y la duración (aparecen en el gráfico).',
            'Clic derecho en una fila para más opciones, como generar la imagen del día.',
            'Los cambios se guardan automáticamente.',
        ]),
        ('✨', 'Imagen de resultado', [
            'Pulsa <b>Imagen de resultado</b> en la cabecera (<b>Ctrl+G</b>).',
            'Elige el día: se cargan su resultado, par y duración; puedes editarlos antes de generar.',
            'Configura la API key de Pollinations (archivo .env), la imagen de referencia y el motor en '
            '<b>Configuración → IA · Imagen</b>. El motor local dibuja la tarjeta con valores exactos sin conexión.',
        ]),
        ('⚙️', 'Configuración (Ctrl+,)', [
            '<b>Apariencia:</b> modo oscuro, idioma, gráfico 2D/3D, animaciones y leyenda.',
            '<b>Trading:</b> capital inicial, modo edición por capital, consejo del día, nueva semana.',
            '<b>Datos:</b> guardar, cargar, base de datos y exportación.',
        ]),
        ('📊', 'Análisis', [
            'En 3D arrastra el gráfico para rotarlo.',
            'El resumen semanal y el análisis AI están en el panel derecho.',
        ]),
        ('📥', 'Importar y analizar (Ctrl+I)', [
            'Pulsa <b>Importar</b> en la cabecera o arrastra archivos a la ventana.',
            'Acepta el historial de tu bróker (Excel/CSV), exportaciones de W-T-F o cualquier tabla con fecha y resultado.',
            'Verás promedios, KPIs, gráficos, tablas por día/activo y podrás <b>cargar los totales en la semana</b>.',
        ]),
    ],
    'en': [
        ('📝', 'Data entry', [
            "Double-click a day's <b>amount</b> to enter the profit/loss.",
            'Double-click <b>Session</b> to note the currency pair and duration (shown on the chart).',
            "Right-click a row for more options, such as generating that day's image.",
            'Changes are saved automatically.',
        ]),
        ('✨', 'Result image', [
            'Press <b>Result image</b> in the header (<b>Ctrl+G</b>).',
            'Pick the day: its result, pair and duration are loaded and can be edited before generating.',
            'Set your Pollinations API key (.env file), reference image and engine in '
            '<b>Settings → AI · Result image</b>. The local engine draws the card with exact values offline.',
        ]),
        ('⚙️', 'Settings (Ctrl+,)', [
            '<b>Appearance:</b> dark mode, language, 2D/3D chart, animations and legend.',
            '<b>Trading:</b> initial capital, capital edit mode, daily advice, new week.',
            '<b>Data:</b> save, load, database and export.',
        ]),
        ('📊', 'Analysis', [
            'In 3D, drag the chart to rotate it.',
            'Weekly summary and AI analysis are on the right panel.',
        ]),
        ('📥', 'Import & analyze (Ctrl+I)', [
            'Press <b>Import</b> in the header or drop files onto the window.',
            'Accepts your broker history (Excel/CSV), W-T-F exports or any table with a date and a result.',
            'You get averages, KPIs, charts, by-day/by-asset tables and can <b>load the totals into the week</b>.',
        ]),
    ],
}


def _lang():
    return 'es' if i18n.current_language == 'es' else 'en'


def _theme_colors():
    """Paleta del tema activo (se deduce del color de ventana de la aplicación)."""
    window = QApplication.palette().color(QPalette.Window)
    return ThemeManager.colors(window.lightness() < 128)


def _rgba(hex_color, alpha):
    c = QColor(hex_color)
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {alpha})"


def _shortcuts():
    return [('Ctrl+S', tr('save_week')), ('Ctrl+O', tr('load_week')),
            ('Ctrl+G', tr('generate_result_image', 'Generar imagen del resultado')),
            ('Ctrl+,', tr('settings_title', 'Configuración')), ('Ctrl+E', tr('menu_export')),
            ('Ctrl+I', tr('import_title', 'Importar y analizar operaciones')), ('Ctrl+D', tr('dark_mode'))]


class _BaseHelpDialog(QDialog):
    """Estructura común: cabecera con logo, contenido desplazable y pie con acciones."""

    def __init__(self, parent, title, subtitle, window_title):
        super().__init__(parent)
        self.setWindowTitle(window_title)
        self.setModal(True)
        self._animated = []
        logo = logo_path()
        if logo:
            self.setWindowIcon(QIcon(logo))

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QFrame()
        header.setObjectName('header')
        hl = QHBoxLayout(header)
        hl.setContentsMargins(24, 18, 24, 18)
        hl.setSpacing(14)
        if logo:
            icon = QLabel()
            icon.setPixmap(QPixmap(logo).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            hl.addWidget(icon)
        texts = QVBoxLayout()
        texts.setSpacing(2)
        t = QLabel(title)
        t.setObjectName('h1')
        s = QLabel(subtitle)
        s.setObjectName('muted')
        s.setWordWrap(True)
        texts.addWidget(t)
        texts.addWidget(s)
        hl.addLayout(texts, 1)
        root.addWidget(header)

        body = QWidget()
        body.setObjectName('transparent')
        self.body = QVBoxLayout(body)
        self.body.setContentsMargins(24, 20, 24, 20)
        self.body.setSpacing(14)
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.NoFrame)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        area.setWidget(body)
        root.addWidget(area, 1)

        footer = QFrame()
        footer.setObjectName('header')
        self.footer = QHBoxLayout(footer)
        self.footer.setContentsMargins(24, 12, 24, 12)
        self.footer.setSpacing(10)
        root.addWidget(footer)

    def _card(self, title=None, name='card', animate=True):
        card = QFrame()
        card.setObjectName(name)
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(10)
        if title:
            lbl = QLabel(title)
            lbl.setObjectName('h3')
            v.addWidget(lbl)
        self.body.addWidget(card)
        if animate:
            self._animated.append(card)
        return v

    def _caption(self, text, layout=None):
        lbl = QLabel(text.upper())
        lbl.setObjectName('caption')
        (layout or self.body).addWidget(lbl)
        return lbl

    def _button(self, text, slot, name=None):
        btn = QPushButton(text)
        if name:
            btn.setObjectName(name)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(slot)
        return btn

    def showEvent(self, event):
        super().showEvent(event)
        for i, w in enumerate(self._animated):
            fade_in(w, duration=380, delay=40 + i * 70, slide=10)
        self._animated = []


class InstructionsDialog(_BaseHelpDialog):
    def __init__(self, parent=None):
        super().__init__(parent, '📖 ' + tr('instructions_title'),
                         tr('instructions_subtitle', 'Todo lo que necesitas para registrar y analizar tu semana.'),
                         tr('instructions_title'))
        self.resize(640, 680)
        c = _theme_colors()

        for icon, title, items in INSTRUCTIONS[_lang()]:
            card = self._card(f"{icon}  {title}")
            for text in items:
                row = QHBoxLayout()
                row.setSpacing(10)
                dot = QLabel('●')
                dot.setStyleSheet(f"color: {c['accent']}; font-size: 7pt;")
                dot.setFixedWidth(12)
                row.addWidget(dot, 0, Qt.AlignTop)
                lbl = QLabel(text)
                lbl.setTextFormat(Qt.RichText)
                lbl.setWordWrap(True)
                row.addWidget(lbl, 1)
                card.addLayout(row)

        card = self._card('⌨️  ' + tr('shortcuts', 'Atajos de teclado'))
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        for i, (keys, text) in enumerate(_shortcuts()):
            k = QLabel(keys)
            k.setObjectName('chip')
            k.setAlignment(Qt.AlignCenter)
            label = QLabel(text)
            label.setObjectName('muted')
            grid.addWidget(k, i // 2, (i % 2) * 2)
            grid.addWidget(label, i // 2, (i % 2) * 2 + 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        card.addLayout(grid)
        self.body.addStretch()

        self.footer.addStretch()
        ok = self._button('👍  ' + tr('got_it', 'Entendido'), self.accept, 'primary')
        ok.setDefault(True)
        self.footer.addWidget(ok)


class AboutDialog(_BaseHelpDialog):
    def __init__(self, parent=None):
        super().__init__(parent, 'W-T-F Trading Manager', 'Weekend Trading Finance', tr('about_title'))
        self.resize(660, 760)
        c = _theme_colors()

        # Presentación
        hero = self._card(name='heroCard')
        chips = QHBoxLayout()
        chips.setSpacing(8)
        for text in (f"v{APP_VERSION}", f"{tr('made_by', 'Creado por')} {APP_PUBLISHER}"):
            chip = QLabel(text)
            chip.setObjectName('chip')
            chips.addWidget(chip)
        chips.addStretch()
        hero.addLayout(chips)
        desc = QLabel(tr('about_description',
                         'Aplicación para gestionar y analizar el rendimiento semanal de trading, '
                         'con análisis AI, persistencia de datos y visualizaciones mejoradas.'))
        desc.setWordWrap(True)
        hero.addWidget(desc)

        # Redes sociales
        card = self._card('💬  ' + tr('follow_me', 'Sígueme en'))
        hint = QLabel(tr('follow_me_desc', 'Tutoriales, novedades y resultados de trading.'))
        hint.setObjectName('muted')
        card.addWidget(hint)
        grid = QGridLayout()
        grid.setSpacing(10)
        for i, social in enumerate(SOCIALS):
            grid.addWidget(self._social_button(c, *social), i // 3, i % 3)
        card.addLayout(grid)
        # Características
        card = self._card('🚀  ' + tr('features', 'Características'))
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        for i, (icon, text) in enumerate(FEATURES[_lang()]):
            item = QFrame()
            item.setObjectName('cardAlt')
            il = QHBoxLayout(item)
            il.setContentsMargins(12, 8, 12, 8)
            il.setSpacing(8)
            il.addWidget(QLabel(icon))
            il.addWidget(QLabel(text), 1)
            grid.addWidget(item, i // 2, i % 2)
        card.addLayout(grid)
        tech_row = QHBoxLayout()
        tech_row.setSpacing(6)
        self._caption(tr('technologies', 'Tecnologías'), card)
        for name in TECH:
            chip = QLabel(name)
            chip.setObjectName('chip')
            tech_row.addWidget(chip)
        tech_row.addStretch()
        card.addLayout(tech_row)

        self.body.addStretch()

        repo = self._button('⭐  ' + tr('view_on_github', 'Ver proyecto en GitHub'),
                            lambda: QDesktopServices.openUrl(QUrl(APP_URL)), 'ghost')
        repo.setToolTip(APP_URL)
        self.footer.addWidget(repo)
        self.footer.addStretch()
        close = self._button(tr('close'), self.accept, 'primary')
        close.setDefault(True)
        self.footer.addWidget(close)

    def _social_button(self, c, icon_name, name, handle, color, url):
        btn = QPushButton(f"{name}\n{handle}")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setToolTip(url)
        btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        icon = social_icon_path(icon_name)
        if icon:
            btn.setIcon(QIcon(icon))
            btn.setIconSize(QSize(26, 26))
        btn.setMinimumHeight(58)
        btn.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding: 8px 12px;
                background-color: {c['surface_alt']};
                border: 1px solid {c['border']};
                border-left: 3px solid {color};
                border-radius: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {_rgba(color, 38)};
                border-color: {color};
            }}
            QPushButton:pressed {{ background-color: {_rgba(color, 70)}; }}
        """)
        return btn


def show_about_dialog(parent):
    """Mostrar diálogo Acerca de (con redes sociales)"""
    AboutDialog(parent).exec_()


def show_instructions_dialog(parent):
    """Mostrar instrucciones de uso"""
    InstructionsDialog(parent).exec_()
