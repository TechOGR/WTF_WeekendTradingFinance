"""
Utilidades de animación y widgets animados reutilizables.
"""

from PyQt5.QtWidgets import (QGraphicsOpacityEffect, QGraphicsDropShadowEffect, QLabel,
                             QAbstractButton, QSizePolicy)
from PyQt5.QtCore import (Qt, QPropertyAnimation, QVariantAnimation, QEasingCurve,
                          QAbstractAnimation, QPoint, QRectF, QSize, pyqtProperty,
                          QParallelAnimationGroup)
from PyQt5.QtGui import QColor, QPainter, QPalette


def fade_in(widget, duration=450, delay=0, slide=0):
    """Aparición suave (opacidad 0 -> 1), opcionalmente deslizando desde abajo."""
    effect = QGraphicsOpacityEffect(widget)
    effect.setOpacity(0.0)
    widget.setGraphicsEffect(effect)

    group = QParallelAnimationGroup(widget)
    opacity = QPropertyAnimation(effect, b"opacity", widget)
    opacity.setDuration(duration)
    opacity.setStartValue(0.0)
    opacity.setEndValue(1.0)
    opacity.setEasingCurve(QEasingCurve.OutCubic)
    group.addAnimation(opacity)

    if slide:
        end = widget.pos()
        move = QPropertyAnimation(widget, b"pos", widget)
        move.setDuration(duration)
        move.setStartValue(end + QPoint(0, slide))
        move.setEndValue(end)
        move.setEasingCurve(QEasingCurve.OutCubic)
        group.addAnimation(move)

    # Quitar el efecto al terminar: evita artefactos de render y deja libre
    # el slot de efecto gráfico para sombras/brillos.
    group.finished.connect(lambda: widget.setGraphicsEffect(None))
    if delay:
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(delay, lambda: group.start(QAbstractAnimation.DeleteWhenStopped))
    else:
        group.start(QAbstractAnimation.DeleteWhenStopped)
    return group


def add_glow(widget, color, blur=28, offset=(0, 6)):
    """Sombra de color (efecto neón) bajo el widget."""
    glow = QGraphicsDropShadowEffect(widget)
    glow.setBlurRadius(blur)
    glow.setColor(QColor(color))
    glow.setOffset(*offset)
    widget.setGraphicsEffect(glow)
    return glow


def pulse_glow(widget, color, low=14, high=40, duration=1600):
    """Brillo neón que 'respira' indefinidamente."""
    glow = add_glow(widget, color, low, (0, 0))
    anim = QVariantAnimation(widget)
    anim.setStartValue(float(low))
    anim.setKeyValueAt(0.5, float(high))
    anim.setEndValue(float(low))
    anim.setDuration(duration)
    anim.setLoopCount(-1)
    anim.setEasingCurve(QEasingCurve.InOutSine)
    anim.valueChanged.connect(lambda v: glow.setBlurRadius(v))
    anim.start()
    widget._pulse_anim = anim
    return anim


class AnimatedNumberLabel(QLabel):
    """QLabel que anima el cambio de un valor numérico (efecto contador)."""

    def __init__(self, fmt=lambda v: f"${v:,.2f}", parent=None):
        super().__init__(parent)
        self._fmt = fmt
        self._value = 0.0
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(900)
        self._anim.setEasingCurve(QEasingCurve.OutExpo)
        self._anim.valueChanged.connect(self._render)
        self.setText(self._fmt(0.0))

    def set_format(self, fmt):
        self._fmt = fmt
        self.setText(self._fmt(self._value))

    def value(self):
        return self._value

    def set_value(self, value, animate=True):
        value = float(value or 0.0)
        self._anim.stop()
        if not animate or abs(value - self._value) < 1e-9:
            self._value = value
            self.setText(self._fmt(value))
            return
        self._anim.setStartValue(float(self._value))
        self._anim.setEndValue(value)
        self._value = value
        self._anim.start()

    def _render(self, v):
        self.setText(self._fmt(float(v)))


class ToggleSwitch(QAbstractButton):
    """Interruptor tipo iOS con desplazamiento animado del botón."""

    def __init__(self, parent=None, checked=False):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._offset = 1.0 if checked else 0.0
        self._anim = QPropertyAnimation(self, b"offset", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self.toggled.connect(self._animate)

    def sizeHint(self):
        return QSize(46, 26)

    def get_offset(self):
        return self._offset

    def set_offset(self, value):
        self._offset = value
        self.update()

    offset = pyqtProperty(float, get_offset, set_offset)

    def setChecked(self, checked):
        super().setChecked(checked)
        if not hasattr(self, '_anim') or self._anim.state() != QAbstractAnimation.Running:
            self._offset = 1.0 if checked else 0.0
            self.update()

    def _animate(self, checked):
        self._anim.stop()
        self._anim.setStartValue(self._offset)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        pal = self.palette()
        on = pal.color(QPalette.Highlight)
        off = QColor(pal.color(QPalette.Text))
        off.setAlpha(55)
        track = QColor(
            int(off.red() + (on.red() - off.red()) * self._offset),
            int(off.green() + (on.green() - off.green()) * self._offset),
            int(off.blue() + (on.blue() - off.blue()) * self._offset),
            int(off.alpha() + (255 - off.alpha()) * self._offset),
        )
        r = QRectF(1, 1, self.width() - 2, self.height() - 2)
        p.setPen(Qt.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        d = r.height() - 6
        x = r.left() + 3 + (r.width() - d - 6) * self._offset
        p.setBrush(QColor('#ffffff'))
        p.drawEllipse(QRectF(x, r.top() + 3, d, d))
        p.end()
