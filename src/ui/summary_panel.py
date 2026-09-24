"""
Panel de resumen: tarjetas KPI animadas, consejo del día y análisis AI.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
                             QFrame, QTextEdit)
from PyQt5.QtCore import Qt
from src.styles.themes import ThemeManager
from src.ui.animations import AnimatedNumberLabel, fade_in
from src.utils.i18n import tr


def _money(v):
    return f"{'-' if v < 0 else ''}${abs(v):,.2f}"


def _signed_money(v):
    return f"{'+' if v >= 0 else '-'}${abs(v):,.2f}"


def _percent(v):
    return f"{v:+.2f}%"


class _StatTile(QFrame):
    """Mini tarjeta con título y valor animado."""

    def __init__(self, title, fmt=_money):
        super().__init__()
        self.setObjectName('cardAlt')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)
        self.title = QLabel(title.upper())
        self.title.setObjectName('caption')
        self.value = AnimatedNumberLabel(fmt)
        self.value.setStyleSheet('font-size: 14pt; font-weight: 800;')
        self.extra = QLabel('')
        self.extra.setObjectName('muted')
        self.extra.setStyleSheet('font-size: 8pt;')
        layout.addWidget(self.title)
        layout.addWidget(self.value)
        layout.addWidget(self.extra)

    def set_title(self, title):
        self.title.setText(title.upper())

    def set_color(self, color):
        self.value.setStyleSheet(f'font-size: 14pt; font-weight: 800; color: {color};')


class SummaryPanel(QWidget):
    """Panel de resumen mejorado para mostrar estadísticas y análisis"""

    def __init__(self):
        super().__init__()
        self.is_dark = True
        self.last_summary = {}
        self.last_capital = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(12)

        # ---- Tarjeta principal: balance
        self.hero = QFrame()
        self.hero.setObjectName('heroCard')
        hero_layout = QVBoxLayout(self.hero)
        hero_layout.setContentsMargins(20, 18, 20, 18)
        hero_layout.setSpacing(6)
        self.title_label = QLabel(tr('weekly_summary_panel').upper())
        self.title_label.setObjectName('caption')
        self.balance_caption = QLabel(tr('current_balance').rstrip(':').upper())
        self.balance_caption.setObjectName('caption')
        self.current_balance_label = AnimatedNumberLabel(_money)
        self.current_balance_label.setStyleSheet('font-size: 28pt; font-weight: 900;')

        pl_row = QHBoxLayout()
        pl_row.setSpacing(8)
        self.profit_loss_label = AnimatedNumberLabel(_signed_money)
        self.profit_loss_label.setStyleSheet('font-size: 13pt; font-weight: 800;')
        self.pl_percent_label = QLabel('+0.00%')
        self.pl_percent_label.setObjectName('chip')
        pl_row.addWidget(self.profit_loss_label)
        pl_row.addWidget(self.pl_percent_label)
        pl_row.addStretch()

        self.initial_capital_label = QLabel(f"{tr('capital_initial')} $100.00")
        self.initial_capital_label.setObjectName('muted')

        hero_layout.addWidget(self.title_label)
        hero_layout.addSpacing(4)
        hero_layout.addWidget(self.balance_caption)
        hero_layout.addWidget(self.current_balance_label)
        hero_layout.addLayout(pl_row)
        hero_layout.addWidget(self.initial_capital_label)
        layout.addWidget(self.hero)

        # ---- Rejilla de KPIs
        grid = QGridLayout()
        grid.setSpacing(10)
        self.withdrawal_tile = _StatTile(tr('personal_withdrawal'))
        self.reinvestment_tile = _StatTile(tr('reinvestment'))
        self.total_tile = _StatTile(tr('total_week'), _signed_money)
        self.performance_tile = _StatTile(tr('performance'), _percent)
        grid.addWidget(self.withdrawal_tile, 0, 0)
        grid.addWidget(self.reinvestment_tile, 0, 1)
        grid.addWidget(self.total_tile, 1, 0)
        grid.addWidget(self.performance_tile, 1, 1)
        layout.addLayout(grid)
        # Compatibilidad con código existente
        self.withdrawal_group, self.reinvestment_group = self.withdrawal_tile, self.reinvestment_tile
        self.total_group, self.performance_group = self.total_tile, self.performance_tile
        self.days_label = self.performance_tile.extra
        self.days_label.setText(tr('days_label').format(positive=0, negative=0))

        # ---- Consejo del día
        self.advice_group = QFrame()
        self.advice_group.setObjectName('card')
        advice_layout = QVBoxLayout(self.advice_group)
        advice_layout.setContentsMargins(16, 14, 16, 14)
        self.advice_title = QLabel('💡 ' + tr('daily_advice_title'))
        self.advice_title.setObjectName('h3')
        self.daily_advice_label = QLabel('')
        self.daily_advice_label.setWordWrap(True)
        self.daily_advice_label.setObjectName('muted')
        advice_layout.addWidget(self.advice_title)
        advice_layout.addWidget(self.daily_advice_label)
        layout.addWidget(self.advice_group)

        # ---- Análisis AI
        self.ai_group = QFrame()
        self.ai_group.setObjectName('card')
        ai_layout = QVBoxLayout(self.ai_group)
        ai_layout.setContentsMargins(16, 14, 16, 14)
        ai_layout.setSpacing(8)
        self.ai_title = QLabel('🤖 ' + tr('ai_analysis_title'))
        self.ai_title.setObjectName('h3')
        self.ai_summary_label = QLabel(tr('loading'))
        self.ai_summary_label.setWordWrap(True)
        self.ai_details_text = QTextEdit()
        self.ai_details_text.setReadOnly(True)
        self.ai_details_text.setMinimumHeight(140)
        ai_layout.addWidget(self.ai_title)
        ai_layout.addWidget(self.ai_summary_label)
        ai_layout.addWidget(self.ai_details_text)
        layout.addWidget(self.ai_group)

        # ---- Estado
        self.status_label = QLabel(tr('operation_completed'))
        self.status_label.setObjectName('status_label')
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        layout.addStretch()

        self._apply_static_styles()
        for i, w in enumerate((self.hero, self.withdrawal_tile, self.reinvestment_tile,
                               self.total_tile, self.performance_tile, self.advice_group, self.ai_group)):
            fade_in(w, duration=600, delay=120 + i * 70)

    # ------------------------------------------------------------------
    def update_summary(self, summary_data: dict, ai_analysis: dict, capital_data: dict = None):
        """Actualizar el panel con nuevos datos"""
        if summary_data is not None:
            self.last_summary = summary_data
        if capital_data is not None:
            self.last_capital = capital_data

        if capital_data:
            initial = capital_data.get('initial_capital', 100.0)
            self.initial_capital_label.setText(f"{tr('capital_initial')} {_money(initial)}")
            self.current_balance_label.set_value(capital_data.get('current_balance', initial))
            self.profit_loss_label.set_value(capital_data.get('total_profit_loss', 0))
            self.pl_percent_label.setText(_percent(capital_data.get('profit_loss_percentage', 0)))

        summary_data = summary_data or {}
        self.withdrawal_tile.value.set_value(summary_data.get('total_withdrawal', 0))
        self.reinvestment_tile.value.set_value(summary_data.get('total_reinvestment', 0))
        self.total_tile.value.set_value(summary_data.get('total_weekly', 0))
        self.performance_tile.value.set_value(summary_data.get('performance_percentage', 0))
        self.days_label.setText(tr('days_label').format(
            positive=summary_data.get('positive_days', 0), negative=summary_data.get('negative_days', 0)))
        self._apply_dynamic_colors()

        if ai_analysis:
            self.ai_summary_label.setText(ai_analysis.get('summary', tr('no_analysis')))
            details = ""
            if 'insights' in ai_analysis:
                details += f"🔍 {tr('insights')}:\n" + ''.join(f"• {i}\n" for i in ai_analysis['insights']) + "\n"
            if 'recommendations' in ai_analysis:
                details += f"💡 {tr('recommendations')}:\n" + ''.join(f"• {r}\n" for r in ai_analysis['recommendations']) + "\n"
            if 'risk_assessment' in ai_analysis:
                details += f"⚠️  {tr('risk_assessment')}:\n{ai_analysis['risk_assessment']}\n"
            if 'performance_rating' in ai_analysis:
                details += f"\n⭐ {tr('rating')}: {ai_analysis['performance_rating']}"
            self.ai_details_text.setPlainText(details)

    def update_daily_advice(self, advice: dict):
        """Actualizar el consejo del día en el panel."""
        if not advice:
            self.daily_advice_label.setText("")
            return
        title = advice.get('title', tr('daily_advice_title'))
        message = advice.get('message', '').replace("\n", "<br>")
        self.daily_advice_label.setText(f"<b>{title}</b><br><br>{message}")

    def apply_language(self):
        """Aplicar traducciones a títulos y etiquetas del panel"""
        self.title_label.setText(tr('weekly_summary_panel').upper())
        self.balance_caption.setText(tr('current_balance').rstrip(':').upper())
        self.withdrawal_tile.set_title(tr('personal_withdrawal'))
        self.reinvestment_tile.set_title(tr('reinvestment'))
        self.total_tile.set_title(tr('total_week'))
        self.performance_tile.set_title(tr('performance'))
        self.advice_title.setText('💡 ' + tr('daily_advice_title'))
        self.ai_title.setText('🤖 ' + tr('ai_analysis_title'))
        if self.last_capital:
            self.initial_capital_label.setText(
                f"{tr('capital_initial')} {_money(self.last_capital.get('initial_capital', 100.0))}")
        s = self.last_summary or {}
        self.days_label.setText(tr('days_label').format(
            positive=s.get('positive_days', 0), negative=s.get('negative_days', 0)))

    def update_status(self, status: str):
        """Actualizar el estado"""
        self.status_label.setText(status)
        c = ThemeManager.colors(self.is_dark)
        if "❌" in status or "Error" in status:
            state = 'danger'
        elif "✅" in status or "Guardado" in status or "Listo" in status or "Saved" in status:
            state = 'success'
        else:
            state = 'warning'
        self.status_label.setStyleSheet(
            f"background-color: {c[state + '_bg']}; color: {c[state]}; "
            f"border: 1px solid {c[state + '_border']}; border-radius: 10px; padding: 8px; font-size: 9pt;")

    def set_theme(self, is_dark: bool):
        """Aplicar colores dependientes del tema."""
        self.is_dark = is_dark
        self._apply_static_styles()
        self._apply_dynamic_colors()

    # ------------------------------------------------------------------
    def _apply_static_styles(self):
        c = ThemeManager.colors(self.is_dark)
        self.ai_summary_label.setStyleSheet(
            f"background-color: {c['accent_soft']}; color: {c['accent_hover']}; padding: 10px; "
            f"border-radius: 10px; border: 1px solid {c['border_strong']}; font-weight: 600;")
        self.ai_details_text.setStyleSheet("font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 9pt;")
        self.withdrawal_tile.set_color(c['success'])
        self.reinvestment_tile.set_color(c['warning'])
        self.status_label.setStyleSheet("")

    def _apply_dynamic_colors(self):
        c = ThemeManager.colors(self.is_dark)
        pl = self.last_capital.get('total_profit_loss', 0) if self.last_capital else 0
        pl_color = c['success'] if pl >= 0 else c['danger']
        self.profit_loss_label.setStyleSheet(f'font-size: 13pt; font-weight: 800; color: {pl_color};')
        bg = c['success_bg'] if pl >= 0 else c['danger_bg']
        border = c['success_border'] if pl >= 0 else c['danger_border']
        self.pl_percent_label.setStyleSheet(
            f"background-color: {bg}; color: {pl_color}; border: 1px solid {border}; "
            f"border-radius: 11px; padding: 3px 10px; font-weight: 800; font-size: 9pt;")

        total = (self.last_summary or {}).get('total_weekly', 0)
        self.total_tile.set_color(c['success'] if total >= 0 else c['danger'])
        perf = (self.last_summary or {}).get('performance_percentage', 0)
        self.performance_tile.set_color(c['success'] if perf >= 0 else c['danger'])
