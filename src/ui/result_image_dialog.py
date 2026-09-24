"""
Ventana "Imagen de resultado": edita par, duración, día y resultado, genera la
tarjeta con Pollinations (edita la imagen de referencia o la genera desde cero)
o en local con Pillow (valores exactos garantizados),
y la muestra con animaciones.
"""

import os
import re
import time
from datetime import datetime

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit,
                             QDoubleSpinBox, QPushButton, QFrame, QFormLayout, QPlainTextEdit,
                             QCheckBox, QWidget, QFileDialog, QApplication, QSizePolicy, QScrollArea)
from PyQt5.QtCore import (Qt, QTimer, QVariantAnimation, QEasingCurve, QRectF, QPointF, QUrl,
                          QPropertyAnimation, pyqtSignal)
from PyQt5.QtGui import (QPainter, QColor, QPixmap, QPainterPath, QLinearGradient, QConicalGradient,
                         QPen, QFont, QDesktopServices)

from src.services.card_renderer import render_card
from src.services.pollinations_image import (ApiWorker, API_KEY_ENV, build_edit_prompt,
                                             build_generation_prompt, edit_trading_card,
                                             generate_trading_card)
from src.styles.themes import ThemeManager
from src.ui.animations import AnimatedNumberLabel, pulse_glow, add_glow
from src.ui.day_details_dialog import make_editable_combo
from src.utils.i18n import tr
from src.utils.settings_store import (CURRENCY_PAIRS, DURATIONS, DAY_NAMES_EN, ENGINE_AI, ENGINE_LOCAL,
                                      format_result)

DAY_KEYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

LOADING_MESSAGES_ES = [
    'Conectando con Pollinations…', 'Enviando la tarjeta de referencia…', 'Componiendo la tarjeta de resultados…',
    'Encendiendo los neones…', 'Renderizando velas japonesas…', 'Puliendo la tipografía…',
    'Últimos retoques…',
]
LOADING_MESSAGES_EN = [
    'Connecting to Pollinations…', 'Sending the reference card…', 'Composing the results card…', 'Lighting up the neons…',
    'Rendering candlesticks…', 'Polishing typography…', 'Final touches…',
]

# Trabajos en curso: se mantienen vivos aunque se cierre la ventana
_RUNNING_WORKERS = set()


class ImageViewer(QWidget):
    """Lienzo que muestra el estado vacío, la carga animada o la imagen resultante."""

    def __init__(self, is_dark=True, parent=None):
        super().__init__(parent)
        self.is_dark = is_dark
        self.state = 'empty'
        self.message = ''
        self.pixmap = None
        self.aspect = 9 / 16
        self._angle = 0.0
        self._shimmer = 0.0
        self._reveal = 1.0
        self.setMinimumSize(360, 420)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._spin = QVariantAnimation(self)
        self._spin.setStartValue(0.0)
        self._spin.setEndValue(360.0)
        self._spin.setDuration(1100)
        self._spin.setLoopCount(-1)
        self._spin.valueChanged.connect(self._on_spin)

        self._reveal_anim = QVariantAnimation(self)
        self._reveal_anim.setStartValue(0.0)
        self._reveal_anim.setEndValue(1.0)
        self._reveal_anim.setDuration(900)
        self._reveal_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._reveal_anim.valueChanged.connect(self._on_reveal)

    def _on_spin(self, v):
        self._angle = float(v)
        self._shimmer = (self._shimmer + 0.012) % 1.6
        self.update()

    def _on_reveal(self, v):
        self._reveal = float(v)
        self.update()

    def set_aspect(self, ratio: str):
        try:
            w, h = (float(x) for x in ratio.split(':'))
            self.aspect = w / h
        except Exception:
            self.aspect = 9 / 16
        self.update()

    def set_loading(self, message):
        self.state = 'loading'
        self.message = message
        self._spin.start()
        self.update()

    def set_message(self, message):
        self.message = message
        self.update()

    def set_image(self, pixmap: QPixmap):
        self._spin.stop()
        self.state = 'image'
        self.pixmap = pixmap
        self._reveal_anim.stop()
        self._reveal_anim.start()

    def set_error(self, message):
        self._spin.stop()
        self.state = 'error'
        self.message = message
        self.update()

    def _frame_rect(self, aspect):
        margin = 24
        avail = QRectF(margin, margin, self.width() - 2 * margin, self.height() - 2 * margin)
        w = avail.width()
        h = w / aspect
        if h > avail.height():
            h = avail.height()
            w = h * aspect
        return QRectF(avail.center().x() - w / 2, avail.center().y() - h / 2, w, h)

    def paintEvent(self, event):
        c = ThemeManager.colors(self.is_dark)
        p = QPainter(self)
        p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing)

        if self.state == 'image' and self.pixmap and not self.pixmap.isNull():
            aspect = self.pixmap.width() / max(1, self.pixmap.height())
            rect = self._frame_rect(aspect)
            scale = 0.92 + 0.08 * self._reveal
            center = rect.center()
            rect = QRectF(center.x() - rect.width() * scale / 2, center.y() - rect.height() * scale / 2 + (1 - self._reveal) * 30,
                          rect.width() * scale, rect.height() * scale)
            # Halo de color detrás de la imagen
            glow = QColor(c['accent'])
            for i in range(6, 0, -1):
                glow.setAlphaF(0.035 * self._reveal)
                p.setPen(Qt.NoPen)
                p.setBrush(glow)
                p.drawRoundedRect(rect.adjusted(-i * 4, -i * 4, i * 4, i * 4), 20 + i * 4, 20 + i * 4)
            path = QPainterPath()
            path.addRoundedRect(rect, 18, 18)
            p.setClipPath(path)
            p.setOpacity(self._reveal)
            p.drawPixmap(rect.toRect(), self.pixmap)
            p.setClipping(False)
            p.setOpacity(1.0)
            p.setPen(QPen(QColor(c['border_strong']), 1))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(rect, 18, 18)
            p.end()
            return

        rect = self._frame_rect(self.aspect)
        path = QPainterPath()
        path.addRoundedRect(rect, 18, 18)
        p.fillPath(path, QColor(c['surface_alt']))

        if self.state == 'loading':
            # Barrido brillante diagonal
            p.setClipPath(path)
            x = rect.left() - rect.width() * 0.6 + rect.width() * 1.8 * (self._shimmer / 1.6)
            grad = QLinearGradient(QPointF(x, rect.top()), QPointF(x + rect.width() * 0.5, rect.bottom()))
            band = QColor(c['accent'])
            band.setAlpha(0)
            grad.setColorAt(0.0, band)
            band.setAlpha(40)
            grad.setColorAt(0.5, band)
            band.setAlpha(0)
            grad.setColorAt(1.0, band)
            p.fillRect(rect, grad)
            # Esqueleto de la tarjeta
            skel = QColor(c['text'])
            skel.setAlpha(18)
            p.setPen(Qt.NoPen)
            p.setBrush(skel)
            w = rect.width()
            p.drawRoundedRect(QRectF(rect.center().x() - w * 0.18, rect.top() + rect.height() * 0.08, w * 0.36, rect.height() * 0.04), 6, 6)
            card = QRectF(rect.left() + w * 0.1, rect.top() + rect.height() * 0.2, w * 0.8, rect.height() * 0.5)
            p.drawRoundedRect(card, 16, 16)
            p.setClipping(False)

            # Spinner con degradado cónico
            r = min(rect.width(), rect.height()) * 0.09
            center = rect.center()
            cg = QConicalGradient(center, -self._angle)
            cg.setColorAt(0.0, QColor(c['accent2']))
            cg.setColorAt(0.5, QColor(c['accent']))
            end = QColor(c['accent'])
            end.setAlpha(0)
            cg.setColorAt(1.0, end)
            pen = QPen(cg, max(4.0, r * 0.18))
            pen.setCapStyle(Qt.RoundCap)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawArc(QRectF(center.x() - r, center.y() - r, 2 * r, 2 * r), int(-self._angle * 16), 280 * 16)

            p.setPen(QColor(c['text_secondary']))
            f = QFont('Segoe UI', 10, QFont.DemiBold)
            p.setFont(f)
            p.drawText(QRectF(rect.left() + 10, center.y() + r + 14, rect.width() - 20, 60),
                       Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, self.message)
        else:
            dash = QPen(QColor(c['border_strong']), 1.5, Qt.DashLine)
            p.setPen(dash)
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 18, 18)
            icon = '⚠️' if self.state == 'error' else '🖼️'
            p.setFont(QFont('Segoe UI Emoji', 34))
            p.setPen(QColor(c['text']))
            p.drawText(QRectF(rect.left(), rect.center().y() - 90, rect.width(), 60), Qt.AlignCenter, icon)
            p.setFont(QFont('Segoe UI', 10))
            p.setPen(QColor(c['danger'] if self.state == 'error' else c['text_secondary']))
            text = self.message or tr('image_placeholder', 'Tu tarjeta de resultado aparecerá aquí.\nAjusta los datos y pulsa «Generar imagen».')
            p.drawText(QRectF(rect.left() + 24, rect.center().y() - 20, rect.width() - 48, rect.height() / 2),
                       Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, text)
        p.end()


class ResultImageDialog(QDialog):
    """Ventana para previsualizar y generar la imagen del resultado."""

    day_updated = pyqtSignal(str)  # día cuyo par/duración/resultado se guardó

    def __init__(self, parent, data_model, settings, is_dark=True, initial_day=None, open_settings=None):
        super().__init__(parent)
        self.data_model = data_model
        self.settings = settings
        self.is_dark = is_dark
        self.open_settings = open_settings
        self.worker = None
        self.image_bytes = None
        self.image_mime = 'image/png'
        self.saved_path = None
        self._started = 0.0
        self._msg_index = 0

        self.setWindowTitle(tr('result_image_title', 'Imagen de resultado'))
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        self.resize(1180, 780)
        self._build_ui()
        self._load_day(initial_day or self._default_day())

        self._tick = QTimer(self)
        self._tick.setInterval(250)
        self._tick.timeout.connect(self._on_tick)

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        c = ThemeManager.colors(self.is_dark)
        root = QHBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(18)

        # ---------- Panel izquierdo (formulario)
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFixedWidth(400)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left = QFrame()
        left.setObjectName('card')
        left_scroll.setWidget(left)
        form_layout = QVBoxLayout(left)
        form_layout.setContentsMargins(22, 22, 22, 22)
        form_layout.setSpacing(14)

        title = QLabel('✨ ' + tr('result_image_title', 'Imagen de resultado'))
        title.setObjectName('h1')
        subtitle = QLabel(tr('result_image_subtitle',
                             'Edita tu tarjeta con IA (Pollinations) o créala en local con valores exactos.'))
        subtitle.setObjectName('muted')
        subtitle.setWordWrap(True)
        form_layout.addWidget(title)
        form_layout.addWidget(subtitle)

        # Aviso si falta la clave
        self.banner = QFrame()
        self.banner.setObjectName('banner')
        banner_layout = QHBoxLayout(self.banner)
        banner_layout.setContentsMargins(12, 10, 12, 10)
        self.banner_text = banner_text = QLabel('')
        banner_text.setWordWrap(True)
        banner_text.setStyleSheet(f"color: {c['warning']}; font-weight: 600;")
        banner_btn = QPushButton(tr('configure', 'Configurar'))
        banner_btn.clicked.connect(self._go_to_settings)
        banner_layout.addWidget(banner_text, 1)
        banner_layout.addWidget(banner_btn)
        form_layout.addWidget(self.banner)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.day_combo = QComboBox()
        for i, day in enumerate(self.data_model.days):
            label = tr(DAY_KEYS[i]) if i < len(DAY_KEYS) else day
            self.day_combo.addItem(label, day)
        self.day_combo.currentIndexChanged.connect(lambda _: self._load_day(self.day_combo.currentData()))

        self.pair_combo = make_editable_combo(CURRENCY_PAIRS, self.settings.get('default_pair'))
        self.duration_combo = make_editable_combo(DURATIONS, self.settings.get('default_duration'))
        self.day_text = QLineEdit()
        self.day_text.setToolTip(tr('day_text_tooltip', 'Texto del día tal como aparecerá en la imagen'))
        self.result_spin = QDoubleSpinBox()
        self.result_spin.setRange(-10_000_000, 10_000_000)
        self.result_spin.setDecimals(2)
        self.result_spin.setPrefix('$ ')
        self.result_spin.setSingleStep(1.0)

        self.engine_combo = QComboBox()
        self.engine_combo.addItem('✨  ' + tr('engine_ai', 'IA · Pollinations'), ENGINE_AI)
        self.engine_combo.addItem('🎯  ' + tr('engine_local', 'Local · valores exactos (Pillow)'), ENGINE_LOCAL)
        self.engine_combo.setCurrentIndex(0 if self.settings.get('image_engine') == ENGINE_AI else 1)
        self.engine_combo.currentIndexChanged.connect(self._on_engine_changed)
        form.addRow(tr('image_engine', 'Motor'), self.engine_combo)
        form.addRow(tr('trading_day', 'Día operado'), self.day_combo)
        form.addRow(tr('currency_pair', 'Par de divisas'), self.pair_combo)
        form.addRow(tr('session_duration', 'Duración'), self.duration_combo)
        form.addRow(tr('day_in_image', 'Día (en imagen)'), self.day_text)
        form.addRow(tr('result_label', 'Resultado'), self.result_spin)
        form_layout.addLayout(form)

        # Vista previa grande del resultado
        preview = QFrame()
        preview.setObjectName('heroCard')
        pv = QVBoxLayout(preview)
        pv.setContentsMargins(16, 12, 16, 14)
        pv.setSpacing(2)
        cap = QLabel('TOTAL PROFIT')
        cap.setObjectName('caption')
        cap.setAlignment(Qt.AlignCenter)
        self.result_preview = AnimatedNumberLabel(format_result)
        self.result_preview.setAlignment(Qt.AlignCenter)
        self.meta_preview = QLabel('')
        self.meta_preview.setObjectName('muted')
        self.meta_preview.setAlignment(Qt.AlignCenter)
        pv.addWidget(cap)
        pv.addWidget(self.result_preview)
        pv.addWidget(self.meta_preview)
        form_layout.addWidget(preview)

        self.save_to_day = QCheckBox(tr('save_to_day', 'Guardar par, duración y resultado en el día'))
        self.save_to_day.setChecked(True)
        form_layout.addWidget(self.save_to_day)

        # Prompt desplegable
        self.prompt_toggle = QPushButton('▸  ' + tr('show_prompt', 'Ver prompt final'))
        self.prompt_toggle.setObjectName('ghost')
        self.prompt_toggle.setCheckable(True)
        self.prompt_toggle.toggled.connect(self._toggle_prompt)
        self.prompt_view = QPlainTextEdit()
        self.prompt_view.setReadOnly(True)
        self.prompt_view.setMaximumHeight(0)
        self.prompt_view.setStyleSheet("font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 8.5pt;")
        form_layout.addWidget(self.prompt_toggle)
        form_layout.addWidget(self.prompt_view)
        self._prompt_anim = QPropertyAnimation(self.prompt_view, b"maximumHeight", self)
        self._prompt_anim.setDuration(320)
        self._prompt_anim.setEasingCurve(QEasingCurve.OutCubic)

        form_layout.addStretch()

        self.generate_btn = QPushButton('✨  ' + tr('generate_image', 'Generar imagen'))
        self.generate_btn.setObjectName('primary')
        self.generate_btn.setMinimumHeight(48)
        self.generate_btn.setCursor(Qt.PointingHandCursor)
        self.generate_btn.setStyleSheet('font-size: 11.5pt;')
        self.generate_btn.clicked.connect(self.generate)
        pulse_glow(self.generate_btn, c['accent'])
        form_layout.addWidget(self.generate_btn)

        self.status = QLabel('')
        self.status.setObjectName('muted')
        self.status.setWordWrap(True)
        self.status.setAlignment(Qt.AlignCenter)
        form_layout.addWidget(self.status)
        self.fallback_btn = QPushButton('🎯  ' + tr('try_local', 'Generar en local con valores exactos'))
        self.fallback_btn.setObjectName('ghost')
        self.fallback_btn.clicked.connect(self._fallback_local)
        self.fallback_btn.setVisible(False)
        form_layout.addWidget(self.fallback_btn)

        root.addWidget(left_scroll)

        # ---------- Panel derecho (visor)
        right = QFrame()
        right.setObjectName('card')
        rv = QVBoxLayout(right)
        rv.setContentsMargins(16, 14, 16, 16)
        rv.setSpacing(10)
        top = QHBoxLayout()
        viewer_title = QLabel(tr('preview', 'Vista previa'))
        viewer_title.setObjectName('h2')
        self.model_chip = QLabel('')
        self.model_chip.setObjectName('chip')
        top.addWidget(viewer_title)
        top.addStretch()
        top.addWidget(self.model_chip)
        rv.addLayout(top)

        self.viewer = ImageViewer(self.is_dark)
        self._apply_ref_aspect()
        rv.addWidget(self.viewer, 1)

        actions = QHBoxLayout()
        self.save_btn = QPushButton('💾  ' + tr('save_as', 'Guardar como…'))
        self.copy_btn = QPushButton('📋  ' + tr('copy', 'Copiar'))
        self.folder_btn = QPushButton('📂  ' + tr('open_folder', 'Abrir carpeta'))
        self.save_btn.clicked.connect(self.save_as)
        self.copy_btn.clicked.connect(self.copy_image)
        self.folder_btn.clicked.connect(self.open_folder)
        for b in (self.save_btn, self.copy_btn):
            b.setEnabled(False)
        actions.addWidget(self.save_btn)
        actions.addWidget(self.copy_btn)
        actions.addWidget(self.folder_btn)
        actions.addStretch()
        close_btn = QPushButton(tr('close'))
        close_btn.setObjectName('ghost')
        close_btn.clicked.connect(self.reject)
        actions.addWidget(close_btn)
        rv.addLayout(actions)

        root.addWidget(right, 1)
        add_glow(right, QColor(0, 0, 0, 120 if self.is_dark else 40), 40, (0, 10))

        for w in (self.pair_combo, self.duration_combo):
            w.currentTextChanged.connect(self._refresh_preview)
        self.day_text.textChanged.connect(self._refresh_preview)
        self.result_spin.valueChanged.connect(self._refresh_preview)
        self.day_text.textChanged.connect(self._refresh_model_chip)
        self._refresh_model_chip()
        self._refresh_banner()

    # ------------------------------------------------------------ helpers
    def _default_day(self):
        """Hoy si es día de la semana; si no, el último día con resultado."""
        wd = datetime.now().weekday()
        days = self.data_model.days
        if wd < len(days) and self.data_model.data[days[wd]]['amount'] != 0:
            return days[wd]
        for day in reversed(days):
            if self.data_model.data[day]['amount'] != 0:
                return day
        return days[min(wd, len(days) - 1)]

    def _load_day(self, day):
        if day not in self.data_model.data:
            return
        idx = self.day_combo.findData(day)
        if idx >= 0 and idx != self.day_combo.currentIndex():
            self.day_combo.blockSignals(True)
            self.day_combo.setCurrentIndex(idx)
            self.day_combo.blockSignals(False)
        details = self.data_model.get_day_details(day)
        self.pair_combo.setCurrentText(details['pair'] or self.settings.get('default_pair'))
        self.duration_combo.setCurrentText(details['duration'] or self.settings.get('default_duration'))
        self.day_text.setText(DAY_NAMES_EN.get(day, day))
        self.result_spin.setValue(details['amount'])
        self._refresh_preview()

    def _refresh_preview(self, *_):
        c = ThemeManager.colors(self.is_dark)
        amount = self.result_spin.value()
        color = c['success'] if amount >= 0 else c['danger']
        self.result_preview.setStyleSheet(f'font-size: 26pt; font-weight: 900; color: {color};')
        self.result_preview.set_value(amount)
        self.meta_preview.setText(
            f"{self.pair_combo.currentText()}  ·  ⏱ {self.duration_combo.currentText()}  ·  📅 {self.day_text.text()}")
        self.prompt_view.setPlainText(self._prompt())

    # ------------------------------------------------------ modo / prompt
    def _engine(self):
        return self.engine_combo.currentData()

    def _has_reference(self):
        return os.path.isfile(self.settings.get('image_ref_path'))

    def _values(self):
        """Valores dinámicos de la tarjeta tal como se escribirán."""
        return {
            'asset': self.pair_combo.currentText().strip(),
            'duration': self.duration_combo.currentText().strip(),
            'day': self.day_text.text().strip(),
            'profit': format_result(self.result_spin.value()),
        }

    def _reference_values(self):
        return {k: self.settings.get('ref_' + k) for k in ('asset', 'duration', 'day', 'profit')}

    def _prompt(self):
        if self._engine() == ENGINE_LOCAL:
            return tr('local_no_prompt', 'Motor local: la tarjeta se dibuja con Pillow, sin prompt.')
        if self._has_reference():
            return build_edit_prompt(self._reference_values(), self._values()) or \
                tr('no_changes', 'Sin cambios: los valores coinciden con la imagen de referencia.')
        return build_generation_prompt(self.settings.get('poll_generation_template'), self._values())

    def _refresh_model_chip(self):
        if self._engine() == ENGINE_LOCAL:
            self.model_chip.setText('🎯 ' + tr('local_exact', 'Local · exacto'))
            return
        model = self.settings.get('poll_image_model').split('/')[-1]
        mode = ('✏️ ' + tr('mode_edit', 'Edición')) if self._has_reference() else ('🆕 ' + tr('mode_new', 'Desde cero'))
        self.model_chip.setText(f"{mode} · {model}")

    def _missing_requirement(self):
        """Texto del aviso si falta algo para generar; '' si todo está listo."""
        if self._engine() == ENGINE_AI and not os.environ.get(API_KEY_ENV, '').strip():
            return '🔑 ' + tr('api_key_missing', 'Falta la API key de Pollinations (POLLINATIONS_API_KEY en .env).')
        return ''

    def _refresh_banner(self):
        text = self._missing_requirement()
        self.banner_text.setText(text)
        self.banner.setVisible(bool(text))

    def _apply_ref_aspect(self):
        pix = QPixmap(self.settings.get('image_ref_path'))
        use_ref = self._engine() == ENGINE_AI and not pix.isNull()
        self.viewer.set_aspect(f"{pix.width()}:{pix.height()}" if use_ref else '9:16')

    def _on_engine_changed(self, *_):
        self.settings.set('image_engine', self._engine())
        self.fallback_btn.setVisible(False)
        self._refresh_banner()
        self._refresh_model_chip()
        self._apply_ref_aspect()
        self._refresh_preview()

    def _fallback_local(self):
        self.engine_combo.setCurrentIndex(self.engine_combo.findData(ENGINE_LOCAL))
        self.generate()

    def _toggle_prompt(self, show):
        self.prompt_toggle.setText(('▾  ' if show else '▸  ') + tr('show_prompt', 'Ver prompt final'))
        self._prompt_anim.stop()
        self._prompt_anim.setStartValue(self.prompt_view.maximumHeight())
        self._prompt_anim.setEndValue(220 if show else 0)
        self._prompt_anim.start()

    def _go_to_settings(self):
        if self.open_settings:
            self.open_settings('ai')
            self._refresh_banner()
            self._apply_ref_aspect()
            self._refresh_model_chip()
            self._refresh_preview()

    def _messages(self):
        from src.utils import i18n
        return LOADING_MESSAGES_EN if i18n.current_language == 'en' else LOADING_MESSAGES_ES

    def _on_tick(self):
        elapsed = time.time() - self._started
        msgs = self._messages()
        index = min(int(elapsed // 3), len(msgs) - 1)
        self.viewer.set_message(msgs[index])
        self.status.setText(f"⏳ {elapsed:.0f}s")

    # ----------------------------------------------------------- acciones
    def generate(self):
        missing = self._missing_requirement()
        if missing:
            self._refresh_banner()
            self.viewer.set_error(missing)
            return
        if self.worker is not None:
            return

        day = self.day_combo.currentData()
        if self.save_to_day.isChecked() and day:
            if abs(self.data_model.data[day]['amount'] - self.result_spin.value()) > 1e-9:
                self.data_model.update_day(day, self.result_spin.value())
            self.data_model.set_day_details(day, self.pair_combo.currentText(), self.duration_combo.currentText())
            self.day_updated.emit(day)

        self.image_bytes = None
        self.saved_path = None
        self.save_btn.setEnabled(False)
        self.copy_btn.setEnabled(False)
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText('⏳  ' + tr('generating', 'Generando…'))
        self._apply_ref_aspect()
        self.viewer.set_loading(self._messages()[0])
        self._started = time.time()
        self._tick.start()

        values = self._values()
        model = self.settings.get('poll_image_model')
        if self._engine() == ENGINE_LOCAL:
            worker = ApiWorker(lambda: (render_card(values['asset'], values['duration'], values['day'],
                                                    values['profit'], self.result_spin.value() >= 0),
                                        'image/png'))
        elif self._has_reference():
            worker = ApiWorker(edit_trading_card, self.settings.get('image_ref_path'),
                               build_edit_prompt(self._reference_values(), values), model)
        else:
            worker = ApiWorker(generate_trading_card, self._prompt(), model)
        self.fallback_btn.setVisible(False)
        worker.succeeded.connect(self._on_success)
        worker.failed.connect(self._on_error)
        worker.finished.connect(lambda w=worker: _RUNNING_WORKERS.discard(w))
        _RUNNING_WORKERS.add(worker)
        self.worker = worker
        worker.start()

    def _finish(self):
        self._tick.stop()
        self.worker = None
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText('🔁  ' + tr('regenerate', 'Generar de nuevo'))

    def _on_success(self, result):
        self._finish()
        data, mime = result[0], result[1]
        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            self._on_error(tr('image_decode_error', 'No se pudo leer la imagen recibida.'))
            return
        self.image_bytes, self.image_mime = data, mime
        self.viewer.set_image(pixmap)
        self.save_btn.setEnabled(True)
        self.copy_btn.setEnabled(True)
        elapsed = time.time() - self._started
        msg = f"✅ {tr('image_ready', 'Imagen lista')} ({elapsed:.0f}s)"
        if self.settings.get_bool('image_autosave'):
            path = self._autosave()
            if path:
                msg += f"\n💾 {os.path.basename(path)}"
        self.status.setText(msg)

    def _on_error(self, message):
        self._finish()
        self.viewer.set_error(message)
        self.fallback_btn.setVisible(self._engine() == ENGINE_AI)
        self.status.setText('❌ ' + tr('image_error', 'No se pudo generar la imagen'))

    def _extension(self):
        return '.jpg' if 'jpeg' in (self.image_mime or '') else '.png'

    def _default_filename(self):
        pair = re.sub(r'[^A-Za-z0-9]+', '-', self.pair_combo.currentText()).strip('-') or 'pair'
        day = re.sub(r'[^A-Za-z0-9]+', '-', self.day_text.text()).strip('-') or 'day'
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"WTF_{pair}_{day}_{stamp}{self._extension()}"

    def _output_dir(self):
        return self.settings.get('image_output_dir')

    def _autosave(self):
        try:
            folder = self._output_dir()
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, self._default_filename())
            with open(path, 'wb') as f:
                f.write(self.image_bytes)
            self.saved_path = path
            return path
        except OSError as e:
            print(f"No se pudo guardar la imagen automáticamente: {e}")
            return None

    def save_as(self):
        if not self.image_bytes:
            return
        folder = self._output_dir()
        os.makedirs(folder, exist_ok=True)
        path, _ = QFileDialog.getSaveFileName(
            self, tr('save_as', 'Guardar como…'), os.path.join(folder, self._default_filename()),
            'Imagen (*.png *.jpg)')
        if path:
            with open(path, 'wb') as f:
                f.write(self.image_bytes)
            self.status.setText(f"💾 {path}")

    def copy_image(self):
        if self.viewer.pixmap:
            QApplication.clipboard().setPixmap(self.viewer.pixmap)
            self.status.setText('📋 ' + tr('copied', 'Imagen copiada al portapapeles'))

    def open_folder(self):
        folder = self._output_dir()
        os.makedirs(folder, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def done(self, result):
        # Si hay una generación en curso, desconectar la ventana (el hilo termina solo)
        if self.worker is not None:
            try:
                self.worker.succeeded.disconnect()
                self.worker.failed.disconnect()
            except TypeError:
                pass
            self.worker = None
        self._tick.stop()
        super().done(result)
