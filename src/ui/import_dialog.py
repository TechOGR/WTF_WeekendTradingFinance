"""
Ventana de importación y análisis: carga uno o varios archivos (Excel, CSV o JSON), detecta el
formato (historial del bróker, exportación de W-T-F o tabla genérica) y muestra promedios, KPIs,
gráficos y tablas. Permite exportar el análisis y volcar los totales diarios en la semana actual.
"""

import os

import numpy as np
import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter, MaxNLocator
from PyQt5.QtCore import Qt, QUrl, pyqtSignal
from PyQt5.QtGui import QCursor, QDesktopServices, QPixmap, QColor, QBrush
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QButtonGroup, QComboBox, QDialog,
                             QDoubleSpinBox, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QHeaderView,
                             QLabel, QMessageBox, QPushButton, QScrollArea, QSizePolicy, QStackedWidget,
                             QTableWidget, QTableWidgetItem, QToolTip, QVBoxLayout, QWidget)

from src.styles.themes import ThemeManager
from src.ui.animations import AnimatedNumberLabel, fade_in
from src.utils import i18n
from src.utils.i18n import tr
from src.utils.import_manager import (FILE_FILTER, KIND_TRADES, OUT_DRAW, OUT_LOSS, OUT_WIN, SOURCE_BROKER,
                                      SOURCE_WTF, SUPPORTED_EXT, analyze, export_analysis_excel, load_files,
                                      week_totals)
from src.utils.resources import logo_path

MAX_TABLE_ROWS = 5000
MONTHS = {
    'es': ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre',
           'Octubre', 'Noviembre', 'Diciembre'],
    'en': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
           'October', 'November', 'December'],
}
WEEKDAY_KEYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']


def _money(v):
    return f"{'-' if v < 0 else ''}${abs(v):,.2f}"


def _signed(v):
    return f"{'+' if v >= 0 else '-'}${abs(v):,.2f}"


def _axis_money(v, _pos=None):
    return f"{'-' if v < 0 else ''}${abs(v):,.0f}"


def _weekday(i):
    return tr(WEEKDAY_KEYS[int(i)]) if 0 <= int(i) < 7 else str(i)


def _direction_label(d):
    return {'up': '▲ ' + tr('dir_up', 'Arriba'), 'down': '▼ ' + tr('dir_down', 'Abajo')}.get(d, d or '—')


def _outcome_label(o):
    return {OUT_WIN: tr('outcome_win', 'Ganada'), OUT_LOSS: tr('outcome_loss', 'Perdida'),
            OUT_DRAW: tr('outcome_draw', 'Empate')}.get(o, o)


# ====================================================================== gráficos
class ChartCanvas(FigureCanvas):
    """Lienzo de matplotlib con los colores del tema y tooltips al pasar el ratón."""

    def __init__(self, colors, height=250):
        self.c = colors
        self.fig = Figure(figsize=(5, height / 100), dpi=100, layout='constrained')
        self.fig.patch.set_facecolor(colors['surface'])
        super().__init__(self.fig)
        self.setMinimumHeight(height)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(height)
        self._bars = []    # (artist, texto)
        self._lines = []   # (ax, xs, ys, textos, marcador, guía)
        self.mpl_connect('motion_notify_event', self._on_move)
        self.mpl_connect('figure_leave_event', lambda _e: self._hide())

    def axes(self, *args, **kwargs):
        ax = self.fig.add_subplot(*args, **kwargs)
        self.style(ax)
        return ax

    def style(self, ax):
        c = self.c
        ax.set_facecolor(c['surface'])
        for side in ('top', 'right', 'left'):
            ax.spines[side].set_visible(False)
        ax.spines['bottom'].set_color(c['border_strong'])
        ax.tick_params(colors=c['text_muted'], labelsize=8, length=0, pad=6)
        ax.grid(axis='y', color=c['border'], linewidth=0.8)
        ax.set_axisbelow(True)
        ax.yaxis.set_major_formatter(FuncFormatter(_axis_money))

    def hover_bars(self, bars, texts):
        for bar, text in zip(bars, texts):
            self._bars.append((bar, text))

    def hover_line(self, ax, xs, ys, texts):
        marker, = ax.plot([], [], 'o', ms=8, color=self.c['accent'], mec=self.c['surface'], mew=2, zorder=5)
        guide = ax.axvline(xs[0] if len(xs) else 0, color=self.c['border_strong'], lw=1, zorder=1)
        guide.set_visible(False)
        self._lines.append((ax, np.asarray(xs, dtype=float), np.asarray(ys, dtype=float), texts, marker, guide))

    def _hide(self):
        QToolTip.hideText()
        changed = False
        for *_, marker, guide in self._lines:
            if guide.get_visible():
                marker.set_data([], [])
                guide.set_visible(False)
                changed = True
        if changed:
            self.draw_idle()

    def _on_move(self, event):
        if event.inaxes is None:
            self._hide()
            return
        for bar, text in self._bars:
            if bar.axes is event.inaxes and bar.contains(event)[0]:
                QToolTip.showText(QCursor.pos(), text, self)
                return
        for ax, xs, ys, texts, marker, guide in self._lines:
            if ax is event.inaxes and len(xs) and event.xdata is not None:
                i = int(np.abs(xs - event.xdata).argmin())
                marker.set_data([xs[i]], [ys[i]])
                guide.set_xdata([xs[i], xs[i]])
                guide.set_visible(True)
                self.draw_idle()
                QToolTip.showText(QCursor.pos(), texts[i], self)
                return
        self._hide()


def _empty_chart(canvas, text):
    ax = canvas.axes(111)
    ax.axis('off')
    ax.text(0.5, 0.5, text, ha='center', va='center', color=canvas.c['text_muted'], fontsize=10,
            transform=ax.transAxes)


def _polar_bars(canvas, ax, labels, values, texts, horizontal=False):
    """Barras de resultado: verde si suma, rojo si resta; 2px de separación con el fondo."""
    c = canvas.c
    colors = [c['success'] if v >= 0 else c['danger'] for v in values]
    pos = np.arange(len(values))
    if horizontal:
        bars = ax.barh(pos, values, height=0.62, color=colors, edgecolor=c['surface'], linewidth=2)
        ax.set_yticks(pos, labels)
        ax.grid(axis='y', visible=False)
        ax.grid(axis='x', color=c['border'], linewidth=0.8)
        ax.xaxis.set_major_formatter(FuncFormatter(_axis_money))
        ax.axvline(0, color=c['border_strong'], lw=1)
        ax.spines['bottom'].set_visible(False)
    else:
        bars = ax.bar(pos, values, width=0.64, color=colors, edgecolor=c['surface'], linewidth=2)
        step = max(1, int(np.ceil(len(labels) / 12)))  # como mucho ~12 etiquetas legibles
        ax.set_xticks(pos[::step], labels[::step])
        ax.axhline(0, color=c['border_strong'], lw=1)
    canvas.hover_bars(bars, texts)
    return bars


# ====================================================================== tablas
class _NumItem(QTableWidgetItem):
    """Celda que ordena por su valor numérico."""

    def __init__(self, text, value):
        super().__init__(text)
        self.setData(Qt.UserRole, value)

    def __lt__(self, other):
        a, b = self.data(Qt.UserRole), other.data(Qt.UserRole)
        try:
            return float(a) < float(b)
        except (TypeError, ValueError):
            return str(a) < str(b)


# ====================================================================== ventana
class ImportDialog(QDialog):
    week_updated = pyqtSignal()

    def __init__(self, model, settings, is_dark=True, parent=None, paths=None):
        super().__init__(parent)
        self.model = model
        self.settings = settings
        self.c = ThemeManager.colors(is_dark)
        self.df = None
        self.view = None
        self.stats = None
        self.setWindowTitle(tr('import_title', 'Importar y analizar operaciones'))
        self.setModal(True)
        self.setAcceptDrops(True)
        screen = QApplication.primaryScreen()
        geo = screen.availableGeometry() if screen else None
        self.resize(min(1180, geo.width() - 80) if geo else 1180, min(900, geo.height() - 60) if geo else 900)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_header())
        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_empty_state())
        self.pages.addWidget(self._build_analysis())
        root.addWidget(self.pages, 1)
        root.addWidget(self._build_footer())
        self._update_actions()
        if paths:
            self.load(paths)

    # ------------------------------------------------------------ estructura
    def _build_header(self):
        header = QFrame()
        header.setObjectName('header')
        hl = QHBoxLayout(header)
        hl.setContentsMargins(24, 14, 24, 14)
        hl.setSpacing(14)
        logo = logo_path()
        if logo:
            icon = QLabel()
            icon.setPixmap(QPixmap(logo).scaled(44, 44, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            hl.addWidget(icon)
        texts = QVBoxLayout()
        texts.setSpacing(2)
        title = QLabel('📥 ' + tr('import_title', 'Importar y analizar operaciones'))
        title.setObjectName('h1')
        self.subtitle = QLabel(tr('import_subtitle', 'Excel o CSV de tu bróker o exportado desde W-T-F: '
                                                     'promedios, gráficos y estadísticas al instante.'))
        self.subtitle.setObjectName('muted')
        texts.addWidget(title)
        texts.addWidget(self.subtitle)
        hl.addLayout(texts, 1)
        self.source_chip = QLabel('')
        self.source_chip.setObjectName('chip')
        self.source_chip.hide()
        hl.addWidget(self.source_chip, 0, Qt.AlignVCenter)
        open_btn = QPushButton('📂  ' + tr('open_files', 'Abrir archivos…'))
        open_btn.setObjectName('primary')
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.clicked.connect(self.choose_files)
        hl.addWidget(open_btn, 0, Qt.AlignVCenter)
        return header

    def _build_empty_state(self):
        page = QWidget()
        page.setObjectName('transparent')
        v = QVBoxLayout(page)
        v.setContentsMargins(40, 30, 40, 30)
        v.setSpacing(18)
        v.addStretch()

        self.drop_zone = QFrame()
        self.drop_zone.setObjectName('heroCard')
        dz = QVBoxLayout(self.drop_zone)
        dz.setContentsMargins(30, 34, 30, 34)
        dz.setSpacing(10)
        big = QLabel('📊')
        big.setAlignment(Qt.AlignCenter)
        big.setStyleSheet('font-size: 40pt;')
        t = QLabel(tr('drop_title', 'Arrastra aquí tus archivos'))
        t.setObjectName('h2')
        t.setAlignment(Qt.AlignCenter)
        d = QLabel(tr('drop_desc', 'o pulsa el botón para elegirlos. Puedes combinar varios archivos: '
                                   'las operaciones repetidas (mismo ID) se cuentan una sola vez.'))
        d.setObjectName('muted')
        d.setWordWrap(True)
        d.setAlignment(Qt.AlignCenter)
        btn = QPushButton('📂  ' + tr('open_files', 'Abrir archivos…'))
        btn.setObjectName('primary')
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self.choose_files)
        for w in (big, t, d):
            dz.addWidget(w)
        dz.addWidget(btn, 0, Qt.AlignCenter)
        v.addWidget(self.drop_zone)

        row = QHBoxLayout()
        row.setSpacing(12)
        for icon, title, desc in (
            ('🏦', tr('fmt_broker', 'Historial del bróker'),
             tr('fmt_broker_desc', 'Una fila por operación: activo, hora, dirección, monto e ingreso '
                                   '(p. ej. Quotex).')),
            ('📈', tr('fmt_wtf', 'Exportación de W-T-F'),
             tr('fmt_wtf_desc', 'Excel, CSV o JSON exportado desde esta app, o una semana guardada.')),
            ('🧾', tr('fmt_generic', 'Tabla propia'),
             tr('fmt_generic_desc', 'Cualquier hoja con una columna de fecha y otra de resultado.')),
        ):
            card = QFrame()
            card.setObjectName('card')
            cv = QVBoxLayout(card)
            cv.setContentsMargins(16, 14, 16, 14)
            cv.setSpacing(4)
            h = QLabel(f'{icon}  {title}')
            h.setObjectName('h3')
            p = QLabel(desc)
            p.setObjectName('muted')
            p.setWordWrap(True)
            p.setStyleSheet('font-size: 9pt;')
            cv.addWidget(h)
            cv.addWidget(p)
            cv.addStretch()
            row.addWidget(card, 1)
        v.addLayout(row)
        v.addStretch()
        return page

    def _build_analysis(self):
        page = QWidget()
        page.setObjectName('transparent')
        v = QVBoxLayout(page)
        v.setContentsMargins(24, 14, 24, 8)
        v.setSpacing(12)

        # Filtros + pestañas en una sola fila
        bar = QHBoxLayout()
        bar.setSpacing(10)
        self.tab_group = QButtonGroup(self)
        self.tab_group.setExclusive(True)
        for i, text in enumerate(['📋  ' + tr('tab_summary', 'Resumen'), '📊  ' + tr('tab_charts', 'Gráficos'),
                                  '📅  ' + tr('tab_days', 'Por día'), '🧾  ' + tr('tab_operations', 'Operaciones')]):
            b = QPushButton(text)
            b.setObjectName('segment')
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.setMinimumHeight(32)
            self.tab_group.addButton(b, i)
            bar.addWidget(b)
        self.tab_group.button(0).setChecked(True)
        self.tab_group.buttonClicked[int].connect(self._switch_tab)
        bar.addStretch()

        self.period_combo = QComboBox()
        self.period_combo.setMinimumWidth(170)
        self.asset_combo = QComboBox()
        self.asset_combo.setMinimumWidth(150)
        self.capital_spin = QDoubleSpinBox()
        self.capital_spin.setRange(0, 10_000_000)
        self.capital_spin.setDecimals(2)
        self.capital_spin.setPrefix('$ ')
        self.capital_spin.setMinimumWidth(110)
        self.capital_spin.setValue(float(getattr(self.model, 'initial_capital', 0.0) or 0.0))
        self.capital_spin.setToolTip(tr('capital_ref_tip', 'Capital de referencia para el balance, '
                                                           'el crecimiento % y el drawdown %'))
        for label, widget in ((tr('period', 'Período'), self.period_combo), (tr('asset', 'Activo'), self.asset_combo),
                              (tr('capital_short', 'Capital'), self.capital_spin)):
            lbl = QLabel(label)
            lbl.setObjectName('muted')
            bar.addWidget(lbl)
            bar.addWidget(widget)
        self.period_combo.currentIndexChanged.connect(self.refresh)
        self.asset_combo.currentIndexChanged.connect(self.refresh)
        self.capital_spin.editingFinished.connect(self.refresh)
        v.addLayout(bar)

        self.tabs = QStackedWidget()
        self.tab_layouts = []
        for _ in range(4):
            body = QWidget()
            body.setObjectName('transparent')
            layout = QVBoxLayout(body)
            layout.setContentsMargins(0, 0, 6, 12)
            layout.setSpacing(12)
            area = QScrollArea()
            area.setWidgetResizable(True)
            area.setFrameShape(QFrame.NoFrame)
            area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            area.setWidget(body)
            self.tabs.addWidget(area)
            self.tab_layouts.append(layout)
        v.addWidget(self.tabs, 1)
        return page

    def _build_footer(self):
        footer = QFrame()
        footer.setObjectName('header')
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(24, 12, 24, 12)
        fl.setSpacing(10)
        self.status = QLabel(tr('import_hint', 'Formatos: .xlsx, .xls, .csv, .json'))
        self.status.setObjectName('muted')
        self.status.setWordWrap(True)
        fl.addWidget(self.status, 1)
        self.export_btn = QPushButton('📤  ' + tr('export_analysis', 'Exportar análisis'))
        self.export_btn.setToolTip(tr('export_analysis_tip', 'Guardar KPIs, resumen diario, activos y '
                                                             'operaciones en Excel (con gráficos)'))
        self.export_btn.clicked.connect(self.export_analysis)
        self.apply_btn = QPushButton('📅  ' + tr('apply_to_week', 'Cargar en la semana'))
        self.apply_btn.clicked.connect(self.apply_to_week)
        close = QPushButton(tr('close'))
        close.setObjectName('ghost')
        close.clicked.connect(self.accept)
        for b in (self.export_btn, self.apply_btn, close):
            b.setCursor(Qt.PointingHandCursor)
            fl.addWidget(b)
        return footer

    # ------------------------------------------------------------ carga
    def choose_files(self):
        folder = self.settings.get('import_dir') or os.path.expanduser('~')
        paths, _ = QFileDialog.getOpenFileNames(self, tr('open_files', 'Abrir archivos…'), folder, FILE_FILTER)
        if paths:
            self.load(paths)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and any(u.toLocalFile().lower().endswith(SUPPORTED_EXT)
                                              for u in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.toLocalFile().lower().endswith(SUPPORTED_EXT)]
        if paths:
            self.load(paths)

    def load(self, paths):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            df, errors = load_files(paths)
        finally:
            QApplication.restoreOverrideCursor()
        if errors:
            QMessageBox.warning(self, tr('warning'), tr('import_errors', 'No se pudieron leer algunos archivos:')
                                + '\n\n' + '\n\n'.join(f'• {name}: {msg}' for name, msg in errors))
        if df is None or df.empty:
            return
        self.settings.set('import_dir', os.path.dirname(paths[0]))
        self.df = df
        source = df.attrs.get('source_type')
        chip = {SOURCE_BROKER: '🏦 ' + tr('fmt_broker', 'Historial del bróker'),
                SOURCE_WTF: '📈 ' + tr('fmt_wtf', 'Exportación de W-T-F')}.get(source, '🧾 ' + tr('fmt_generic', 'Tabla propia'))
        self.source_chip.setText(chip)
        self.source_chip.show()
        files = df.attrs.get('files', [])
        unit = tr('operations_word', 'operaciones') if df.attrs['kind'] == KIND_TRADES else tr('days_word', 'días')
        self.subtitle.setText(f"{', '.join(files[:3])}{'…' if len(files) > 3 else ''} · {len(df)} {unit}")
        self._fill_filters()
        self.pages.setCurrentIndex(1)
        self.refresh()

    def _fill_filters(self):
        df = self.df
        lang = i18n.current_language if i18n.current_language in MONTHS else 'es'
        self.period_combo.blockSignals(True)
        self.asset_combo.blockSignals(True)
        self.period_combo.clear()
        self.period_combo.addItem(tr('all_period', 'Todo el período'), 'all')
        self.period_combo.addItem(tr('last_7_days', 'Últimos 7 días'), 'd7')
        self.period_combo.addItem(tr('last_30_days', 'Últimos 30 días'), 'd30')
        for p in sorted(df['time'].dt.to_period('M').unique(), reverse=True):
            self.period_combo.addItem(f"🗓  {MONTHS[lang][p.month - 1]} {p.year}", f'm:{p}')
        mondays = (df['time'].dt.normalize() - pd.to_timedelta(df['time'].dt.weekday, unit='D')).unique()
        for m in sorted(mondays, reverse=True):
            m = pd.Timestamp(m)
            self.period_combo.addItem(f"📅  {tr('week')} {m.strftime('%d/%m/%Y')}", f'w:{m.date().isoformat()}')
        self.asset_combo.clear()
        self.asset_combo.addItem(tr('all_assets', 'Todos'), None)
        for asset in df['asset'][df['asset'] != ''].value_counts().index:
            self.asset_combo.addItem(asset, asset)
        self.asset_combo.setEnabled(self.asset_combo.count() > 2)
        self.period_combo.blockSignals(False)
        self.asset_combo.blockSignals(False)

    def _filtered(self):
        df = self.df
        key = self.period_combo.currentData() or 'all'
        last = df['time'].max().normalize()
        if key == 'd7':
            df = df[df['time'] >= last - pd.Timedelta(days=6)]
        elif key == 'd30':
            df = df[df['time'] >= last - pd.Timedelta(days=29)]
        elif key.startswith('m:'):
            df = df[df['time'].dt.to_period('M').astype(str) == key[2:]]
        elif key.startswith('w:'):
            start = pd.Timestamp(key[2:])
            df = df[(df['time'] >= start) & (df['time'] < start + pd.Timedelta(days=7))]
        asset = self.asset_combo.currentData()
        if asset:
            df = df[df['asset'] == asset]
        df = df.copy()
        df.attrs = dict(self.df.attrs)
        return df

    # ------------------------------------------------------------ render
    def refresh(self, *_):
        if self.df is None:
            return
        self.view = self._filtered()
        for layout in self.tab_layouts:
            self._clear(layout)
        if self.view.empty:
            self.stats = None
            for layout in self.tab_layouts:
                msg = QLabel('🔍 ' + tr('no_rows_filter', 'No hay operaciones con estos filtros.'))
                msg.setObjectName('muted')
                msg.setAlignment(Qt.AlignCenter)
                layout.addWidget(msg)
                layout.addStretch()
            self._update_actions()
            return
        self.stats = analyze(self.view, self.capital_spin.value())
        self._render_summary(self.tab_layouts[0])
        self._render_charts(self.tab_layouts[1])
        self._render_days(self.tab_layouts[2])
        self._render_operations(self.tab_layouts[3])
        self._update_actions()
        s = self.stats
        self.status.setText(f"🗓  {s['first'].strftime('%d/%m/%Y')} → {s['last'].strftime('%d/%m/%Y')}  ·  "
                            f"{s['trading_days']} {tr('trading_days_word', 'días operados')}  ·  "
                            f"{s['count']} {self._unit()}")
        fade_in(self.tabs.currentWidget(), duration=320, slide=8)

    @staticmethod
    def _clear(layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                ImportDialog._clear(item.layout())

    def _is_trades(self):
        return self.stats and self.stats['kind'] == KIND_TRADES

    def _unit(self):
        return tr('operations_word', 'operaciones') if self._is_trades() else tr('days_word', 'días')

    def _card(self, layout, title=None, subtitle=None, name='card'):
        card = QFrame()
        card.setObjectName(name)
        v = QVBoxLayout(card)
        v.setContentsMargins(18, 14, 18, 14)
        v.setSpacing(8)
        if title:
            head = QHBoxLayout()
            t = QLabel(title)
            t.setObjectName('h3')
            head.addWidget(t)
            head.addStretch()
            if subtitle:
                s = QLabel(subtitle)
                s.setObjectName('muted')
                s.setStyleSheet('font-size: 8.5pt;')
                head.addWidget(s)
            v.addLayout(head)
        layout.addWidget(card)
        return v

    def _pos_neg(self, v):
        return self.c['success'] if v > 1e-9 else self.c['danger'] if v < -1e-9 else self.c['text_secondary']

    # ---- Resumen
    def _render_summary(self, layout):
        s = self.stats
        trades = self._is_trades()

        hero = self._card(layout, name='heroCard')
        row = QHBoxLayout()
        left = QVBoxLayout()
        left.setSpacing(2)
        cap = QLabel(tr('net_result', 'Resultado neto').upper())
        cap.setObjectName('caption')
        net = AnimatedNumberLabel(_signed)
        net.setStyleSheet(f"font-size: 28pt; font-weight: 900; color: {self._pos_neg(s['net'])};")
        net.set_value(s['net'])
        detail = []
        if s['growth_pct'] is not None:
            detail.append(f"{s['growth_pct']:+.2f}% {tr('over_capital', 'sobre')} {_money(s['initial_capital'])}")
        if s['roi'] is not None:
            detail.append(f"ROI {s['roi']:+.2f}% {tr('over_staked', 'sobre lo invertido')}")
        sub = QLabel('  ·  '.join(detail))
        sub.setObjectName('muted')
        left.addWidget(cap)
        left.addWidget(net)
        left.addWidget(sub)
        row.addLayout(left, 1)
        right = QVBoxLayout()
        right.setSpacing(2)
        for caption, value in (
            (tr('daily_average', 'Promedio diario'), _signed(s['avg_day'])),
            (tr('avg_per_op', 'Promedio por operación') if trades else tr('green_days', 'Días en verde'),
             _signed(s['avg_op']) if trades else f"{s['green_days']} / {s['trading_days']}"),
        ):
            c = QLabel(caption.upper())
            c.setObjectName('caption')
            c.setAlignment(Qt.AlignRight)
            val = QLabel(value)
            val.setAlignment(Qt.AlignRight)
            val.setStyleSheet('font-size: 14pt; font-weight: 800;')
            right.addWidget(c)
            right.addWidget(val)
        row.addLayout(right)
        hero.addLayout(row)

        grid = QGridLayout()
        grid.setSpacing(10)
        tiles = [
            (tr('win_rate', 'Tasa de acierto'), f"{s['win_rate']:.1f}%",
             f"{s['wins']} {tr('won_short', 'gan.')} · {s['losses']} {tr('lost_short', 'perd.')}"
             + (f" · {s['draws']} {tr('draw_short', 'emp.')}" if s['draws'] else ''),
             self.c['success'] if s['win_rate'] >= self._breakeven() else self.c['warning']),
            (tr('profit_factor', 'Profit factor'),
             f"{s['profit_factor']:.2f}" if s['profit_factor'] is not None else '∞',
             tr('profit_factor_desc', 'ganancias ÷ pérdidas'),
             self.c['success'] if (s['profit_factor'] or 99) >= 1 else self.c['danger']),
            (tr('operations_word', 'operaciones').capitalize() if trades else tr('trading_days_word', 'días operados').capitalize(),
             f"{s['count']}", f"{s['ops_per_day']:.1f} {tr('per_day', 'por día')}" if trades
             else f"{s['green_days']} {tr('in_green', 'en verde')}", None),
            (tr('avg_win', 'Ganancia media'), _signed(s['avg_win']), tr('per_winner', 'por operación ganada')
             if trades else tr('per_green_day', 'por día en verde'), self.c['success']),
            (tr('avg_loss', 'Pérdida media'), _signed(s['avg_loss']), tr('per_loser', 'por operación perdida')
             if trades else tr('per_red_day', 'por día en rojo'), self.c['danger'] if s['losses'] else None),
            (tr('best_day', 'Mejor día'), _signed(s['best_day'][1]), s['best_day'][0].strftime('%d/%m/%Y'),
             self._pos_neg(s['best_day'][1])),
            (tr('worst_day', 'Peor día'), _signed(s['worst_day'][1]), s['worst_day'][0].strftime('%d/%m/%Y'),
             self._pos_neg(s['worst_day'][1])),
            (tr('max_drawdown', 'Máx. drawdown'), _money(-s['max_drawdown']) if s['max_drawdown'] else '$0.00',
             f"{s['max_drawdown_pct']:.1f}% {tr('from_peak', 'desde el máximo')}" if s['max_drawdown_pct'] is not None
             else tr('drawdown_desc', 'mayor caída acumulada'), self.c['danger'] if s['max_drawdown'] else None),
            (tr('streaks', 'Rachas máximas'), f"{s['win_streak']} ✔ · {s['loss_streak']} ✖",
             tr('streaks_desc', 'ganadas / perdidas seguidas'), None),
        ]
        if trades and s['staked'] is not None:
            tiles += [
                (tr('total_staked', 'Total invertido'), _money(s['staked']), tr('volume', 'volumen operado'), None),
                (tr('avg_stake', 'Monto medio'), _money(s['avg_stake']), tr('per_operation', 'por operación'), None),
                (tr('avg_payout', 'Payout medio'), f"{s['avg_payout_pct']:.1f}%" if s['avg_payout_pct'] else '—',
                 f"{tr('breakeven', 'Acierto mínimo')}: {self._breakeven():.1f}%", None),
            ]
        cols = 4
        for i, (title, value, extra, color) in enumerate(tiles):
            grid.addWidget(self._tile(title, value, extra, color), i // cols, i % cols)
        for col in range(cols):
            grid.setColumnStretch(col, 1)
        layout.addLayout(grid)

        card = self._card(layout, '📈  ' + (tr('balance_evolution', 'Evolución del balance') if s['initial_capital']
                                           else tr('cumulative_evolution', 'Resultado acumulado')),
                          tr('hover_hint', 'Pasa el ratón por el gráfico para ver cada punto'))
        card.addWidget(self._equity_chart())

        insights = self._insights()
        if insights:
            card = self._card(layout, '🧠  ' + tr('insights', 'Lectura rápida'))
            for text in insights:
                lbl = QLabel('•  ' + text)
                lbl.setWordWrap(True)
                lbl.setTextFormat(Qt.RichText)
                card.addWidget(lbl)
        layout.addStretch()

    def _tile(self, title, value, extra='', color=None):
        tile = QFrame()
        tile.setObjectName('cardAlt')
        v = QVBoxLayout(tile)
        v.setContentsMargins(14, 11, 14, 11)
        v.setSpacing(2)
        t = QLabel(title.upper())
        t.setObjectName('caption')
        val = QLabel(value)
        val.setStyleSheet(f"font-size: 14pt; font-weight: 800;{f' color: {color};' if color else ''}")
        e = QLabel(extra)
        e.setObjectName('muted')
        e.setStyleSheet('font-size: 8pt;')
        v.addWidget(t)
        v.addWidget(val)
        v.addWidget(e)
        return tile

    def _breakeven(self):
        """Tasa de acierto mínima para no perder con el payout medio (100 / (1 + payout))."""
        p = (self.stats or {}).get('avg_payout_pct')
        return 100 / (1 + p / 100) if p else 50.0

    def _equity_chart(self):
        s, c = self.stats, self.c
        view = self.view
        canvas = ChartCanvas(c, 300)
        gs = canvas.fig.add_gridspec(2, 1, height_ratios=[3, 1])
        ax = canvas.fig.add_subplot(gs[0])
        dd = canvas.fig.add_subplot(gs[1], sharex=ax)
        canvas.style(ax)
        canvas.style(dd)
        n = len(view)
        xs = np.arange(1, n + 1)
        base = s['initial_capital']
        ys = s['equity']
        ax.plot(xs, ys, color=c['accent'], lw=2, zorder=3)
        ax.fill_between(xs, base, ys, where=ys >= base, color=c['success'], alpha=0.12, lw=0, interpolate=True)
        ax.fill_between(xs, base, ys, where=ys < base, color=c['danger'], alpha=0.12, lw=0, interpolate=True)
        ax.axhline(base, color=c['border_strong'], lw=1, ls='--')
        ax.tick_params(labelbottom=False)
        ax.margins(x=0.01)
        dd.fill_between(xs, s['drawdown'], 0, color=c['danger'], alpha=0.35, lw=0, step=None)
        dd.plot(xs, s['drawdown'], color=c['danger'], lw=1)
        dd.set_ylabel('DD', color=c['text_muted'], fontsize=8)
        dd.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=10))
        dd.set_xlabel('#' + (tr('operation', 'operación') if self._is_trades() else tr('day_word', 'día')),
                      color=c['text_muted'], fontsize=8)
        # Separadores de día cuando son operaciones
        if self._is_trades():
            day_change = np.flatnonzero(view['time'].dt.normalize().diff().fillna(pd.Timedelta(0)) > pd.Timedelta(0))
            for i in day_change:
                ax.axvline(i + 0.5, color=c['border'], lw=0.8, zorder=0)
        fmt = '%d/%m %H:%M' if self._is_trades() else '%d/%m/%Y'
        texts = []
        for i, row in enumerate(view.itertuples(index=False)):
            label = f"<b>#{i + 1}</b> · {row.time.strftime(fmt)}"
            if row.asset:
                label += f" · {row.asset}"
            texts.append(f"{label}<br>{tr('result_label', 'Resultado')}: <b>{_signed(row.profit)}</b>"
                         f"<br>{tr('balance_column', 'Balance') if base else tr('cumulative_label', 'Acumulado')}: "
                         f"<b>{_money(ys[i])}</b><br>DD: {_money(s['drawdown'][i])}")
        canvas.hover_line(ax, xs, ys, texts)
        return canvas

    def _insights(self):
        s, out = self.stats, []
        green, red = self.c['success'], self.c['danger']

        def col(v):
            return f"<b style='color:{green if v >= 0 else red}'>{_signed(v)}</b>"

        if self._is_trades():
            be = self._breakeven()
            if s['avg_payout_pct']:
                verdict = (tr('above_breakeven', 'por encima') if s['win_rate'] >= be
                           else tr('below_breakeven', 'por debajo'))
                out.append(tr('insight_breakeven', 'Con un payout medio de {p:.1f}% necesitas acertar al menos el '
                                                   '<b>{be:.1f}%</b> para no perder; vas <b>{v}</b> con {wr:.1f}%.')
                           .format(p=s['avg_payout_pct'], be=be, v=verdict, wr=s['win_rate']))
            out.append(tr('insight_expectancy', 'Esperanza por operación: {e} (ganancia media {w} · pérdida media {l}).')
                       .format(e=col(s['avg_op']), w=_signed(s['avg_win']), l=_signed(s['avg_loss'])))
            hours = s['by_hour']
            if hours is not None and len(hours) > 1:
                best = hours['net'].idxmax()
                worst = hours['net'].idxmin()
                out.append(tr('insight_hours', 'Mejor franja horaria: <b>{b:02d}:00–{b1:02d}:00</b> ({bn}, {bw:.0f}% acierto). '
                                              'Peor: <b>{w:02d}:00–{w1:02d}:00</b> ({wn}).')
                           .format(b=int(best), b1=(int(best) + 1) % 24, bn=col(hours.loc[best, 'net']),
                                   bw=hours.loc[best, 'win_rate'], w=int(worst), w1=(int(worst) + 1) % 24,
                                   wn=col(hours.loc[worst, 'net'])))
            dirs = s['by_direction']
            if dirs is not None and len(dirs) > 1:
                parts = [f"{_direction_label(d)}: {r['win_rate']:.0f}% · {col(r['net'])}" for d, r in dirs.iterrows()]
                out.append(tr('insight_direction', 'Por dirección — {parts}.').format(parts='  |  '.join(parts)))
            stakes = s['by_stake']
            if stakes is not None and len(stakes) > 2:
                worst = stakes['net'].idxmin()
                if stakes.loc[worst, 'net'] < 0 and worst > stakes.index.to_series().median():
                    out.append(tr('insight_stake', 'Con montos de <b>{s}</b> el resultado es {n} ({wr:.0f}% acierto): '
                                                   'revisa la gestión de riesgo al subir la inversión.')
                               .format(s=_money(worst), n=col(stakes.loc[worst, 'net']),
                                       wr=stakes.loc[worst, 'win_rate']))
        else:
            out.append(tr('insight_days', '{g} de {t} días en verde · promedio diario {a}.')
                       .format(g=s['green_days'], t=s['trading_days'], a=col(s['avg_day'])))
            wd = s['by_weekday']
            if len(wd) > 1:
                best = wd['net'].idxmax()
                out.append(tr('insight_weekday', 'Tu mejor día de la semana es <b>{d}</b> ({n} en total).')
                           .format(d=_weekday(best), n=col(wd.loc[best, 'net'])))
        assets = s['by_asset']
        if len(assets) > 1:
            best = assets['net'].idxmax()
            out.append(tr('insight_asset', 'Activo más rentable: <b>{a}</b> ({n} en {o} {u}).')
                       .format(a=best, n=col(assets.loc[best, 'net']), o=int(assets.loc[best, 'ops']), u=self._unit()))
        if s['max_drawdown'] > 0:
            out.append(tr('insight_drawdown', 'La mayor caída desde un máximo fue de <b>{d}</b>; '
                                              'racha máxima de {l} pérdidas seguidas.')
                       .format(d=_money(s['max_drawdown']), l=s['loss_streak']))
        return out

    # ---- Gráficos
    def _render_charts(self, layout):
        s, c = self.stats, self.c
        grid = QGridLayout()
        grid.setSpacing(12)
        charts = [
            ('📅  ' + tr('chart_daily', 'Resultado por día'), self._chart_daily()),
            ('🎯  ' + tr('chart_outcomes', 'Ganadas / perdidas'), self._chart_outcomes()),
        ]
        if s['by_hour'] is not None:
            charts.append(('🕒  ' + tr('chart_hours', 'Resultado por hora'), self._chart_group(
                s['by_hour'], lambda h: f"{int(h):02d}h", lambda h: f"{int(h):02d}:00–{(int(h) + 1) % 24:02d}:00")))
        charts.append(('🗓  ' + tr('chart_weekday', 'Resultado por día de la semana'), self._chart_group(
            s['by_weekday'], lambda d: _weekday(d)[:3], _weekday)))
        if len(s['by_asset']) > 1 or s['by_direction'] is None:
            top = s['by_asset'].reindex(s['by_asset']['net'].abs().sort_values().index[-8:]).sort_values('net')
            charts.append(('💱  ' + tr('chart_assets', 'Resultado por activo'),
                           self._chart_group(top, str, str, horizontal=True)))
        if s['by_direction'] is not None:
            charts.append(('↕  ' + tr('chart_direction', 'Resultado por dirección'), self._chart_group(
                s['by_direction'], _direction_label, _direction_label)))
        if s['by_stake'] is not None and len(s['by_stake']) > 1:
            charts.append(('💵  ' + tr('chart_stake', 'Resultado por monto invertido'), self._chart_group(
                s['by_stake'], lambda v: f"${v:,.0f}", lambda v: _money(v))))
        if s['kind'] != KIND_TRADES and len(self.view) > 3:
            charts.append(('📊  ' + tr('chart_distribution', 'Distribución de resultados'), self._chart_hist()))
        for i, (title, canvas) in enumerate(charts):
            box = QVBoxLayout()
            holder = QWidget()
            holder.setObjectName('transparent')
            holder.setLayout(box)
            box.setContentsMargins(0, 0, 0, 0)
            card = self._card(box, title)
            card.addWidget(canvas)
            grid.addWidget(holder, i // 2, i % 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)
        layout.addStretch()

    def _chart_daily(self):
        s = self.stats
        by_day = s['by_day']
        canvas = ChartCanvas(self.c, 260)
        ax = canvas.axes(111)
        labels = [d.strftime('%d/%m') for d in by_day.index]
        texts = [f"<b>{_weekday(d.weekday())} {d.strftime('%d/%m/%Y')}</b><br>{_signed(r['net'])}"
                 f"<br>{int(r['ops'])} {self._unit()} · {r['win_rate']:.0f}% {tr('win_rate_short', 'acierto')}"
                 for d, r in by_day.iterrows()]
        _polar_bars(canvas, ax, labels, by_day['net'].tolist(), texts)
        avg = s['avg_day']
        ax.axhline(avg, color=self.c['text_secondary'], lw=1.2, ls=(0, (4, 3)))
        ax.annotate(f"{tr('average', 'Promedio')} {_signed(avg)}", xy=(1, avg), xycoords=('axes fraction', 'data'),
                    xytext=(-4, 4), textcoords='offset points', ha='right', va='bottom', zorder=6,
                    color=self.c['text_secondary'], fontsize=8, fontweight='bold',
                    bbox={'boxstyle': 'round,pad=0.3', 'facecolor': self.c['surface'], 'edgecolor': 'none'})
        return canvas

    def _chart_outcomes(self):
        s, c = self.stats, self.c
        canvas = ChartCanvas(c, 260)
        ax = canvas.axes(111)
        ax.axis('off')
        parts = [(tr('outcome_wins', 'Ganadas'), s['wins'], c['success']),
                 (tr('outcome_losses', 'Perdidas'), s['losses'], c['danger']),
                 (tr('outcome_draws', 'Empates'), s['draws'], c['text_muted'])]
        parts = [p for p in parts if p[1] > 0]
        wedges, _ = ax.pie([p[1] for p in parts], colors=[p[2] for p in parts], startangle=90, counterclock=False,
                           wedgeprops={'width': 0.32, 'edgecolor': c['surface'], 'linewidth': 2})
        ax.text(0, 0.08, f"{s['win_rate']:.1f}%", ha='center', va='center', fontsize=20, fontweight='bold',
                color=c['text'])
        ax.text(0, -0.2, tr('win_rate', 'Tasa de acierto'), ha='center', va='center', fontsize=8,
                color=c['text_muted'])
        total = sum(p[1] for p in parts)
        ax.legend(wedges, [f"{p[0]}  {p[1]} ({p[1] / total * 100:.0f}%)" for p in parts], loc='center left',
                  bbox_to_anchor=(1.0, 0.5), frameon=False, labelcolor=c['text_secondary'], fontsize=9)
        ax.set_aspect('equal')
        canvas.hover_bars(wedges, [f"<b>{p[0]}</b><br>{p[1]} · {p[1] / total * 100:.1f}%" for p in parts])
        return canvas

    def _chart_group(self, frame, short, long, horizontal=False):
        canvas = ChartCanvas(self.c, 260 if not horizontal else max(260, 60 + 30 * len(frame)))
        ax = canvas.axes(111)
        texts = [f"<b>{long(k)}</b><br>{_signed(r['net'])} · {int(r['ops'])} {self._unit()}"
                 f"<br>{r['win_rate']:.0f}% {tr('win_rate_short', 'acierto')} · "
                 f"{tr('average', 'Promedio')} {_signed(r['avg'])}" for k, r in frame.iterrows()]
        _polar_bars(canvas, ax, [short(k) for k in frame.index], frame['net'].tolist(), texts, horizontal)
        return canvas

    def _chart_hist(self):
        c = self.c
        canvas = ChartCanvas(c, 260)
        ax = canvas.axes(111)
        values = self.view['profit'].values
        bins = min(20, max(5, len(values) // 2))
        counts, edges, patches = ax.hist(values, bins=bins, edgecolor=c['surface'], linewidth=2)
        for patch, left in zip(patches, edges[:-1]):
            patch.set_facecolor(c['success'] if left >= 0 else c['danger'])
        ax.xaxis.set_major_formatter(FuncFormatter(_axis_money))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{int(v)}"))
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        canvas.hover_bars(patches, [f"{_signed(a)} … {_signed(b)}<br><b>{int(n)}</b> {self._unit()}"
                                    for a, b, n in zip(edges[:-1], edges[1:], counts)])
        return canvas

    # ---- Tablas
    def _table(self, headers, rows, sort_col=0, order=Qt.AscendingOrder):
        """rows: [[(texto, valor_orden, color|None, alineación_derecha)]]"""
        table = QTableWidget(len(rows), len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(34)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setShowGrid(False)
        for r, row in enumerate(rows):
            for col, (text, value, color, right) in enumerate(row):
                item = _NumItem(text, value)
                if color:
                    item.setForeground(QBrush(QColor(color)))
                item.setTextAlignment((Qt.AlignRight if right else Qt.AlignLeft) | Qt.AlignVCenter)
                table.setItem(r, col, item)
        table.setSortingEnabled(True)
        table.sortItems(sort_col, order)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setMinimumHeight(min(620, 64 + 34 * max(len(rows), 3)))
        return table

    def _render_days(self, layout):
        s = self.stats
        by_day = s['by_day']
        muted = self.c['text_muted']
        rows = []
        for d, r in by_day.iterrows():
            staked = r['staked']
            rows.append([
                (d.strftime('%d/%m/%Y'), d.value, None, False),
                (_weekday(d.weekday()), d.weekday(), muted, False),
                (str(int(r['ops'])), int(r['ops']), None, True),
                (f"{int(r['wins'])} / {int(r['losses'])}", int(r['wins']), None, True),
                (f"{r['win_rate']:.0f}%", float(r['win_rate']), None, True),
                (_money(staked) if pd.notna(staked) else '—', float(staked) if pd.notna(staked) else 0, None, True),
                (_signed(r['avg']), float(r['avg']), self._pos_neg(r['avg']), True),
                (_signed(r['net']), float(r['net']), self._pos_neg(r['net']), True),
                (_signed(r['cumulative']), float(r['cumulative']), self._pos_neg(r['cumulative']), True),
            ])
        headers = [tr('date_column', 'Fecha'), tr('day_column', 'Día'), tr('ops_short', 'Ops'),
                   tr('won_lost', 'Gan. / Perd.'), tr('win_rate_short', 'acierto').capitalize(),
                   tr('staked', 'Invertido'), tr('average', 'Promedio'), tr('net', 'Neto'),
                   tr('cumulative_column', 'Acumulado')]
        card = self._card(layout, '📅  ' + tr('tab_days', 'Por día'),
                          f"{len(by_day)} {tr('trading_days_word', 'días operados')} · "
                          f"{tr('daily_average', 'Promedio diario')} {_signed(s['avg_day'])}")
        card.addWidget(self._table(headers, rows))

        assets = s['by_asset'].sort_values('net', ascending=False)
        if len(assets):
            rows = [[(str(a), str(a), None, False),
                     (str(int(r['ops'])), int(r['ops']), None, True),
                     (f"{r['win_rate']:.0f}%", float(r['win_rate']), None, True),
                     (_signed(r['avg']), float(r['avg']), self._pos_neg(r['avg']), True),
                     (_signed(r['net']), float(r['net']), self._pos_neg(r['net']), True)]
                    for a, r in assets.iterrows()]
            card = self._card(layout, '💱  ' + tr('by_asset', 'Por activo'))
            card.addWidget(self._table([tr('asset', 'Activo'), tr('ops_short', 'Ops'),
                                        tr('win_rate_short', 'acierto').capitalize(), tr('average', 'Promedio'),
                                        tr('net', 'Neto')], rows, 4, Qt.DescendingOrder))
        layout.addStretch()

    def _render_operations(self, layout):
        view = self.view.iloc[::-1]  # las más recientes primero (también al limitar filas)
        shown = view.head(MAX_TABLE_ROWS)
        trades = self._is_trades()
        rows = []
        outcome_color = {OUT_WIN: self.c['success'], OUT_LOSS: self.c['danger'], OUT_DRAW: self.c['text_muted']}
        for row in shown.itertuples(index=False):
            cells = [(row.time.strftime('%d/%m/%Y %H:%M:%S' if trades else '%d/%m/%Y'), row.time.value, None, False),
                     (row.asset or '—', row.asset, None, False)]
            if trades:
                cells += [(_direction_label(row.direction), row.direction, None, False),
                          (_money(row.stake) if pd.notna(row.stake) else '—', row.stake if pd.notna(row.stake) else 0, None, True),
                          (_money(row.payout) if pd.notna(row.payout) else '—', row.payout if pd.notna(row.payout) else 0, None, True)]
            else:
                cells.append((row.duration or '—', row.duration, None, False))
            cells += [(_signed(row.profit), float(row.profit), self._pos_neg(row.profit), True),
                      (_outcome_label(row.outcome), row.outcome, outcome_color.get(row.outcome), False)]
            rows.append(cells)
        headers = [tr('date_column', 'Fecha'), tr('asset', 'Activo')]
        headers += ([tr('direction', 'Dirección'), tr('stake', 'Monto'), tr('payout', 'Ingreso')] if trades
                    else [tr('session_duration', 'Duración')])
        headers += [tr('result_column', 'Resultado'), tr('status_column', 'Estado')]
        note = f"{len(view)} {self._unit()}"
        if len(view) > MAX_TABLE_ROWS:
            note += ' · ' + tr('showing_first', 'mostrando las primeras {n}').format(n=MAX_TABLE_ROWS)
        card = self._card(layout, '🧾  ' + tr('tab_operations', 'Operaciones'), note)
        card.addWidget(self._table(headers, rows, 0, Qt.DescendingOrder))
        layout.addStretch()

    def _switch_tab(self, index):
        self.tabs.setCurrentIndex(index)
        fade_in(self.tabs.currentWidget(), duration=300, slide=8)

    # ------------------------------------------------------------ acciones
    def _week_totals(self):
        if self.view is None or self.view.empty:
            return {}
        return week_totals(self.view, getattr(self.model, 'week_start_date', None), self.model.days)

    def _update_actions(self):
        has = self.stats is not None
        self.export_btn.setEnabled(has)
        totals = self._week_totals() if has else {}
        self.apply_btn.setEnabled(bool(totals))
        start = getattr(self.model, 'week_start_date', None)
        week = start.strftime('%d/%m/%Y') if start else ''
        self.apply_btn.setToolTip(
            tr('apply_to_week_tip', 'Escribe el resultado neto de cada día en la semana actual ({w})').format(w=week)
            if totals else tr('apply_to_week_none', 'No hay operaciones de la semana actual ({w}) con estos filtros')
            .format(w=week))

    def apply_to_week(self):
        totals = self._week_totals()
        if not totals:
            return
        lines = []
        for day, info in totals.items():
            old = float(self.model.data[day].get('amount', 0.0) or 0.0)
            change = f"  ({tr('replaces', 'antes')} {_signed(old)})" if abs(old) > 1e-9 and abs(old - info['amount']) > 1e-9 else ''
            lines.append(f"• {day} {info['date'].strftime('%d/%m')}: {_signed(info['amount'])} · "
                         f"{info['ops']} {self._unit()}{change}")
        answer = QMessageBox.question(
            self, tr('apply_to_week', 'Cargar en la semana'),
            tr('apply_to_week_confirm', 'Se escribirá el resultado neto de estos días en la semana actual:') +
            '\n\n' + '\n'.join(lines), QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if answer != QMessageBox.Yes:
            return
        for day, info in totals.items():
            self.model.update_day(day, info['amount'])
            current = self.model.get_day_details(day)
            if info['pair'] and not current['pair']:
                self.model.set_day_details(day, info['pair'], current['duration'])
        self.week_updated.emit()
        self.status.setText('✅ ' + tr('week_updated_from_import', 'Semana actualizada con {n} días importados')
                            .format(n=len(totals)))

    def export_analysis(self):
        if self.stats is None:
            return
        s = self.stats
        folder = self.settings.get('export_dir') or os.path.expanduser('~')
        os.makedirs(folder, exist_ok=True)
        name = f"analisis_{s['first'].strftime('%Y-%m-%d')}_{s['last'].strftime('%Y-%m-%d')}.xlsx"
        path, _ = QFileDialog.getSaveFileName(self, tr('export_analysis', 'Exportar análisis'),
                                              os.path.join(folder, name), 'Excel (*.xlsx)')
        if not path:
            return
        if not path.lower().endswith('.xlsx'):
            path += '.xlsx'
        kpis = [
            (tr('net_result', 'Resultado neto'), s['net'], 'signed'),
            (tr('win_rate', 'Tasa de acierto'), s['win_rate'], 'pct'),
            (tr('outcome_wins', 'Ganadas'), s['wins'], 'num'),
            (tr('outcome_losses', 'Perdidas'), s['losses'], 'num'),
            (tr('outcome_draws', 'Empates'), s['draws'], 'num'),
            (tr('profit_factor', 'Profit factor'), s['profit_factor'], 'num'),
            (tr('avg_per_op', 'Promedio por operación'), s['avg_op'], 'signed'),
            (tr('daily_average', 'Promedio diario'), s['avg_day'], 'signed'),
            (tr('avg_win', 'Ganancia media'), s['avg_win'], 'signed'),
            (tr('avg_loss', 'Pérdida media'), s['avg_loss'], 'signed'),
            (tr('best_day', 'Mejor día'), s['best_day'][1], 'signed'),
            (tr('worst_day', 'Peor día'), s['worst_day'][1], 'signed'),
            (tr('max_drawdown', 'Máx. drawdown'), -s['max_drawdown'], 'money'),
            (tr('total_staked', 'Total invertido'), s['staked'], 'money'),
            (tr('avg_stake', 'Monto medio'), s['avg_stake'], 'money'),
            ('ROI', s['roi'], 'pct'),
            (tr('avg_payout', 'Payout medio'), s['avg_payout_pct'], 'pct'),
            (tr('trading_days_word', 'días operados').capitalize(), s['trading_days'], 'num'),
        ]
        labels = {
            'title': tr('import_title', 'Importar y analizar operaciones'),
            'subtitle': f"{s['first'].strftime('%d/%m/%Y')} → {s['last'].strftime('%d/%m/%Y')} · "
                        f"{', '.join(self.df.attrs.get('files', []))}",
            'summary': tr('tab_summary', 'Resumen'), 'by_day': tr('tab_days', 'Por día'),
            'by_asset': tr('by_asset', 'Por activo'), 'operations': tr('tab_operations', 'Operaciones'),
            'asset': tr('asset', 'Activo'), 'chart_daily': tr('chart_daily', 'Resultado por día'),
            'chart_equity': tr('cumulative_evolution', 'Resultado acumulado'),
            'kpis': kpis,
            'day_headers': [tr('date_column', 'Fecha'), tr('ops_short', 'Ops'), tr('outcome_wins', 'Ganadas'),
                            tr('outcome_losses', 'Perdidas'), tr('win_rate', 'Tasa de acierto'),
                            tr('staked', 'Invertido'), tr('net', 'Neto'), tr('cumulative_column', 'Acumulado')],
            'op_headers': [tr('date_column', 'Fecha'), tr('asset', 'Activo'), tr('direction', 'Dirección'),
                           tr('stake', 'Monto'), tr('payout', 'Ingreso'), tr('result_column', 'Resultado'),
                           tr('status_column', 'Estado')],
            'outcomes': {k: _outcome_label(k) for k in (OUT_WIN, OUT_LOSS, OUT_DRAW)},
            'directions': {'up': tr('dir_up', 'Arriba'), 'down': tr('dir_down', 'Abajo')},
        }
        try:
            export_analysis_excel(self.view, s, path, labels)
        except PermissionError:
            QMessageBox.warning(self, tr('warning'), tr('file_in_use', 'No se pudo escribir: ¿el archivo está abierto en Excel?'))
            return
        except Exception as e:
            QMessageBox.critical(self, tr('error'), f"{tr('export_error')}: {e}")
            return
        self.settings.set('export_dir', os.path.dirname(path))
        self.status.setText(f"✅ {tr('export_success', 'Exportado')}: {os.path.basename(path)}")
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def showEvent(self, event):
        super().showEvent(event)
        if self.df is None:
            fade_in(self.drop_zone, duration=420, slide=10)
