"""
Resumen semanal: balance, KPIs, desglose por día y plan de retiro/reinversión.
"""

from datetime import timedelta

from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
                             QFrame, QPushButton, QWidget, QSizePolicy)
from PyQt5.QtCore import Qt, QRectF, QVariantAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QPixmap, QIcon

from src.styles.themes import ThemeManager
from src.ui.animations import AnimatedNumberLabel, fade_in
from src.utils.advice import get_weekly_summary_message
from src.utils.i18n import tr
from src.utils.resources import logo_path

DAY_KEYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
WITHDRAW_RATIO = 0.30


def _money(v):
    return f"{'-' if v < 0 else ''}${abs(v):,.2f}"


def _signed_money(v):
    return f"{'+' if v >= 0 else '-'}${abs(v):,.2f}"


class _DayBar(QWidget):
    """Barra horizontal divergente (pérdidas a la izquierda, ganancias a la derecha)."""

    def __init__(self, value, max_abs, colors):
        super().__init__()
        self._ratio = (value / max_abs) if max_abs else 0.0
        self._progress = 0.0
        self._c = colors
        self.setMinimumHeight(14)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._anim = QVariantAnimation(self)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setDuration(700)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.valueChanged.connect(self._set_progress)

    def animate(self, delay_ms=0):
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(delay_ms, self._anim.start)

    def _set_progress(self, v):
        self._progress = float(v)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        track = QColor(self._c['border'])
        p.setPen(Qt.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(QRectF(0, h / 2 - 3, w, 6), 3, 3)
        mid = w / 2
        p.setBrush(QColor(self._c['border_strong']))
        p.drawRect(QRectF(mid - 1, 0, 2, h))
        length = abs(self._ratio) * (mid - 2) * self._progress
        if length > 0.5:
            color = QColor(self._c['success'] if self._ratio >= 0 else self._c['danger'])
            x = mid if self._ratio >= 0 else mid - length
            p.setBrush(color)
            p.drawRoundedRect(QRectF(x, h / 2 - 5, length, 10), 5, 5)
        p.end()


class _SplitBar(QWidget):
    """Barra partida retiro / reinversión."""

    def __init__(self, ratio, left_color, right_color, track_color):
        super().__init__()
        self._ratio = ratio
        self._colors = (QColor(left_color), QColor(right_color), QColor(track_color))
        self.setFixedHeight(12)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        r = QRectF(0, 0, self.width(), self.height())
        left, right, track = self._colors
        if self._ratio is None:
            p.setBrush(track)
            p.drawRoundedRect(r, 6, 6)
        else:
            split = r.width() * self._ratio
            p.setBrush(right)
            p.drawRoundedRect(r, 6, 6)
            p.setBrush(left)
            p.drawRoundedRect(QRectF(0, 0, split, r.height()), 6, 6)
            p.drawRect(QRectF(split - 6, 0, 6, r.height()))
        p.end()


class WeeklySummaryDialog(QDialog):
    def __init__(self, model, is_dark=True, parent=None):
        super().__init__(parent)
        self.model = model
        self.c = ThemeManager.colors(is_dark)
        self._animated = []
        self._bars = []
        self.setWindowTitle(tr('weekly_summary_panel'))
        self.setModal(True)
        self.resize(700, 780)

        total = float(model.get_total_profit_loss())
        self.total = total
        self.balance = float(model.get_current_balance())
        self.initial = float(model.initial_capital)
        self.percent = float(model.get_profit_loss_percentage())
        self.withdraw = max(0.0, total) * WITHDRAW_RATIO
        self.reinvest = max(0.0, total) - self.withdraw
        self.next_capital = max(0.0, self.balance - self.withdraw)
        self.days = [(tr(DAY_KEYS[i]) if i < len(DAY_KEYS) else day, model.get_day_details(day))
                     for i, day in enumerate(model.days)]

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_header())

        body = QWidget()
        body.setObjectName('transparent')
        self.body = QVBoxLayout(body)
        self.body.setContentsMargins(24, 20, 24, 20)
        self.body.setSpacing(14)
        self._build_hero()
        self._build_kpis()
        self._build_days()
        self._build_plan()
        self.body.addStretch()
        root.addWidget(body, 1)
        root.addWidget(self._build_footer())

    # ------------------------------------------------------------ secciones
    def _build_header(self):
        header = QFrame()
        header.setObjectName('header')
        hl = QHBoxLayout(header)
        hl.setContentsMargins(24, 16, 24, 16)
        hl.setSpacing(14)
        logo = logo_path()
        if logo:
            self.setWindowIcon(QIcon(logo))
            icon = QLabel()
            icon.setPixmap(QPixmap(logo).scaled(44, 44, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            hl.addWidget(icon)
        texts = QVBoxLayout()
        texts.setSpacing(2)
        title = QLabel(tr('weekly_summary_panel'))
        title.setObjectName('h1')
        texts.addWidget(title)
        start = getattr(self.model, 'week_start_date', None)
        if start:
            end = start + timedelta(days=len(self.model.days) - 1)
            sub = QLabel(f"{tr('week')} {start.strftime('%d/%m/%Y')} → {end.strftime('%d/%m/%Y')}")
            sub.setObjectName('muted')
            texts.addWidget(sub)
        hl.addLayout(texts, 1)
        if self.total > 0:
            text, color = '🎉  ' + tr('week_profitable', 'Semana de ganancias'), self.c['success']
        elif self.total < 0:
            text, color = '💡  ' + tr('week_challenging', 'Semana desafiante'), self.c['danger']
        else:
            text, color = '⏸️  ' + tr('week_flat', 'Semana sin cambios'), self.c['text_secondary']
        badge = QLabel(text)
        badge.setObjectName('chip')
        badge.setStyleSheet(f"color: {color};")
        hl.addWidget(badge, 0, Qt.AlignVCenter)
        return header

    def _card(self, title=None, name='card'):
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
        self._animated.append(card)
        return v

    def _build_hero(self):
        hero = self._card(name='heroCard')
        row = QHBoxLayout()
        left = QVBoxLayout()
        left.setSpacing(4)
        cap = QLabel(tr('current_balance').rstrip(':').upper())
        cap.setObjectName('caption')
        self.balance_label = AnimatedNumberLabel(_money)
        self.balance_label.setStyleSheet('font-size: 30pt; font-weight: 900;')
        left.addWidget(cap)
        left.addWidget(self.balance_label)
        pl_row = QHBoxLayout()
        pl_row.setSpacing(8)
        color = self.c['success'] if self.total >= 0 else self.c['danger']
        self.pl_label = AnimatedNumberLabel(_signed_money)
        self.pl_label.setStyleSheet(f'font-size: 13pt; font-weight: 800; color: {color};')
        pct = QLabel(f"{self.percent:+.2f}%")
        pct.setObjectName('chip')
        pct.setStyleSheet(f"color: {color};")
        pl_row.addWidget(self.pl_label)
        pl_row.addWidget(pct)
        pl_row.addStretch()
        left.addLayout(pl_row)
        row.addLayout(left, 1)

        right = QVBoxLayout()
        right.setSpacing(4)
        cap2 = QLabel(tr('capital_initial').rstrip(':').upper())
        cap2.setObjectName('caption')
        cap2.setAlignment(Qt.AlignRight)
        initial = QLabel(_money(self.initial))
        initial.setStyleSheet('font-size: 14pt; font-weight: 700;')
        initial.setAlignment(Qt.AlignRight)
        right.addWidget(cap2)
        right.addWidget(initial)
        right.addStretch()
        row.addLayout(right)
        hero.addLayout(row)

    def _tile(self, grid, col, title, value, extra='', color=None):
        tile = QFrame()
        tile.setObjectName('cardAlt')
        v = QVBoxLayout(tile)
        v.setContentsMargins(14, 12, 14, 12)
        v.setSpacing(3)
        t = QLabel(title.upper())
        t.setObjectName('caption')
        val = QLabel(value)
        val.setStyleSheet(f"font-size: 13pt; font-weight: 800;{f' color: {color};' if color else ''}")
        e = QLabel(extra)
        e.setObjectName('muted')
        e.setStyleSheet('font-size: 8pt;')
        v.addWidget(t)
        v.addWidget(val)
        v.addWidget(e)
        grid.addWidget(tile, 0, col)

    def _build_kpis(self):
        grid = QGridLayout()
        grid.setSpacing(10)
        amounts = [d['amount'] for _, d in self.days]
        traded = [a for a in amounts if abs(a) > 1e-9]
        wins = sum(1 for a in traded if a > 0)
        win_rate = (wins / len(traded) * 100) if traded else 0.0
        self._tile(grid, 0, tr('win_rate', 'Tasa de acierto'), f"{win_rate:.0f}%",
                   tr('win_days', '{wins} de {total} días').format(wins=wins, total=len(traded)),
                   self.c['success'] if win_rate >= 50 else self.c['warning'])
        if traded:
            best_i = max(range(len(amounts)), key=lambda i: amounts[i])
            worst_i = min(range(len(amounts)), key=lambda i: amounts[i])
            best, worst = amounts[best_i], amounts[worst_i]
            self._tile(grid, 1, tr('best_day', 'Mejor día'), _signed_money(best), self.days[best_i][0],
                       self.c['success'] if best >= 0 else self.c['danger'])
            self._tile(grid, 2, tr('worst_day', 'Peor día'), _signed_money(worst), self.days[worst_i][0],
                       self.c['success'] if worst >= 0 else self.c['danger'])
            avg = sum(traded) / len(traded)
        else:
            self._tile(grid, 1, tr('best_day', 'Mejor día'), '—')
            self._tile(grid, 2, tr('worst_day', 'Peor día'), '—')
            avg = 0.0
        self._tile(grid, 3, tr('daily_average', 'Promedio diario'), _signed_money(avg),
                   tr('per_traded_day', 'por día operado'),
                   self.c['success'] if avg >= 0 else self.c['danger'])
        self.body.addLayout(grid)

    def _build_days(self):
        card = self._card('📅  ' + tr('daily_breakdown', 'Desglose por día'))
        max_abs = max((abs(d['amount']) for _, d in self.days), default=0.0)
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        for i, (name, d) in enumerate(self.days):
            texts = QVBoxLayout()
            texts.setSpacing(0)
            n = QLabel(name)
            n.setStyleSheet('font-weight: 700;')
            texts.addWidget(n)
            details = ' · '.join(x for x in (d['pair'], d['duration']) if x)
            info = QLabel(details or tr('no_session', 'Sin sesión'))
            info.setObjectName('muted')
            info.setStyleSheet('font-size: 8pt;')
            texts.addWidget(info)
            holder = QWidget()
            holder.setObjectName('transparent')
            holder.setLayout(texts)
            holder.setMinimumWidth(130)
            grid.addWidget(holder, i, 0)

            bar = _DayBar(d['amount'], max_abs, self.c)
            self._bars.append(bar)
            grid.addWidget(bar, i, 1)

            amount = d['amount']
            if abs(amount) < 1e-9:
                color, text = self.c['text_muted'], '—'
            else:
                color = self.c['success'] if amount > 0 else self.c['danger']
                text = _signed_money(amount)
            a = QLabel(text)
            a.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            a.setMinimumWidth(90)
            a.setStyleSheet(f'font-weight: 800; color: {color};')
            grid.addWidget(a, i, 2)
        grid.setColumnStretch(1, 1)
        card.addLayout(grid)

    def _build_plan(self):
        card = self._card('💼  ' + tr('money_plan', 'Plan para la próxima semana'))
        profit = max(0.0, self.total)
        bar = _SplitBar(WITHDRAW_RATIO if profit > 0 else None,
                        self.c['success'], self.c['accent'], self.c['border'])
        card.addWidget(bar)

        row = QHBoxLayout()
        row.setSpacing(10)
        for title, value, color in (
            (tr('withdraw_30', 'Retiro recomendado (30%)'), self.withdraw, self.c['success']),
            (tr('suggested_reinvestment', 'Reinversión sugerida'), self.reinvest, self.c['accent']),
            (tr('next_week_capital', 'Capital próxima semana'), self.next_capital, None),
        ):
            box = QVBoxLayout()
            box.setSpacing(2)
            t = QLabel(('● ' if color else '') + title)
            t.setObjectName('muted')
            t.setStyleSheet(f"font-size: 9pt;{f' color: {color};' if color else ''}")
            v = QLabel(_money(value))
            v.setStyleSheet('font-size: 13pt; font-weight: 800;')
            box.addWidget(t)
            box.addWidget(v)
            row.addLayout(box, 1)
        card.addLayout(row)

        if self.total > 0:
            tip = tr('tip_profit', 'Asegura parte de la ganancia y reinvierte el resto: el interés compuesto hace el trabajo.')
        elif self.total < 0:
            tip = tr('tip_loss', 'Revisa tus peores operaciones, reduce el riesgo por operación y protege tu capital.')
        else:
            tip = tr('tip_flat', 'Documenta tus mejores y peores operaciones para aprender más rápido.')
        banner = QFrame()
        banner.setObjectName('banner')
        bl = QHBoxLayout(banner)
        bl.setContentsMargins(12, 8, 12, 8)
        lbl = QLabel('💡 ' + tip)
        lbl.setWordWrap(True)
        bl.addWidget(lbl)
        card.addWidget(banner)

    def _build_footer(self):
        footer = QFrame()
        footer.setObjectName('header')
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(24, 12, 24, 12)
        fl.setSpacing(10)
        self.copy_btn = QPushButton('📋  ' + tr('copy_summary', 'Copiar resumen'))
        self.copy_btn.setObjectName('ghost')
        self.copy_btn.setCursor(Qt.PointingHandCursor)
        self.copy_btn.clicked.connect(self._copy)
        fl.addWidget(self.copy_btn)
        fl.addStretch()
        close = QPushButton(tr('close'))
        close.setObjectName('primary')
        close.setCursor(Qt.PointingHandCursor)
        close.setDefault(True)
        close.clicked.connect(self.accept)
        fl.addWidget(close)
        return footer

    # ------------------------------------------------------------ acciones
    def _copy(self):
        lines = [get_weekly_summary_message(self.model), '']
        for name, d in self.days:
            details = ' · '.join(x for x in (d['pair'], d['duration']) if x)
            lines.append(f"{name}: {_signed_money(d['amount'])}{f'  ({details})' if details else ''}")
        QApplication.clipboard().setText('\n'.join(lines))
        self.copy_btn.setText('✅  ' + tr('copied', 'Copiado'))

    def showEvent(self, event):
        super().showEvent(event)
        self.balance_label.set_value(self.balance)
        self.pl_label.set_value(self.total)
        for i, w in enumerate(self._animated):
            fade_in(w, duration=380, delay=40 + i * 80, slide=10)
        for i, bar in enumerate(self._bars):
            bar.animate(250 + i * 70)
        self._animated = []
