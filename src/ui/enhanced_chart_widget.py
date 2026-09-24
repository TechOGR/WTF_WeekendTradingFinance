"""
Widget de gráfico mejorado: modo 2D (barras con degradado y brillo neón) y
modo 3D (barras volumétricas rotables con el ratón), ambos animados.
"""

from datetime import datetime, timedelta

import numpy as np
import matplotlib.patches as patches
import matplotlib.patheffects as pe
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.colors import LinearSegmentedColormap, to_rgba
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
from PyQt5.QtCore import QTimer, QVariantAnimation, QEasingCurve, pyqtSignal, Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QSizePolicy, QButtonGroup)

from src.styles.themes import ThemeManager
from src.utils.i18n import tr
from src.utils.settings_store import format_result

DAY_KEYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
WITHDRAWAL_NAMES = ('Retiro Personal', 'Personal Withdrawal')
REINVESTMENT_NAMES = ('Reinversión', 'Reinvestment')


def _mix(c1, c2, t):
    a, b = np.array(to_rgba(c1)), np.array(to_rgba(c2))
    return tuple(a + (b - a) * t)


def _axis_money(v, _pos=None):
    return f"{'-' if v < 0 else ''}${abs(v):,.0f}"


def _short_duration(duration: str) -> str:
    return duration.replace(' min', 'm').replace(' h', 'h').strip()


class EnhancedChartWidget(QWidget):
    """Widget de gráfico con modos 2D / 3D y animación de crecimiento."""

    mode_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.is_dark = True
        self.legend_visible = True
        self.legend_position = 'upper_right'  # opciones: outside_right, upper_right, upper_center
        self.mode = '3d'
        self.animations_enabled = True
        self.last_data_model = None
        self._view = None  # (elev, azim) elegido por el usuario en 3D
        self._items = []

        self._anim = QVariantAnimation(self)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setDuration(1100)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.valueChanged.connect(lambda v: self._render(float(v), intro=True))
        self._anim.finished.connect(lambda: self._render(1.0, intro=True))

        self.setup_ui()

    # ------------------------------------------------------------------ UI
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 8)
        layout.setSpacing(6)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(0)
        self.title_label = QLabel(tr('weekly_performance_title'))
        self.title_label.setObjectName('h2')
        self.subtitle_label = QLabel('')
        self.subtitle_label.setObjectName('muted')
        titles.addWidget(self.title_label)
        titles.addWidget(self.subtitle_label)
        header.addLayout(titles)
        header.addStretch()

        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.mode_buttons = {}
        for key, text in (('2d', '2D'), ('3d', '3D')):
            btn = QPushButton(text)
            btn.setObjectName('segment')
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(tr('chart_mode_tooltip', 'Cambiar vista del gráfico (en 3D puedes arrastrar para rotar)'))
            btn.clicked.connect(lambda _=False, k=key: self.set_mode(k, emit=True))
            self.mode_group.addButton(btn)
            self.mode_buttons[key] = btn
            header.addWidget(btn)
        self.mode_buttons[self.mode].setChecked(True)
        layout.addLayout(header)

        self.figure = Figure(figsize=(12, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.setMinimumHeight(300)
        layout.addWidget(self.canvas)

    def showEvent(self, event):
        """Tras mostrar el widget, redibujar para capturar el tamaño real."""
        super().showEvent(event)
        QTimer.singleShot(0, lambda: self._render(1.0) if self._items else None)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._items and self._anim.state() != QVariantAnimation.Running:
            # Recalcular redondeos 2D según la nueva proporción
            if self.mode == '2d':
                QTimer.singleShot(0, lambda: self._render(1.0))

    # ------------------------------------------------------------- API
    def update_chart(self, data_model, animate=True):
        """Actualizar el gráfico con datos del modelo"""
        self.last_data_model = data_model
        try:
            self._items = self._collect(data_model)
        except Exception as e:
            print(f"{tr('chart_error_update')}: {e}")
            self.show_error_message(str(e))
            return

        total = sum(i['amount'] for i in self._items if not i['placeholder'])
        c = self._c()
        color = c['success'] if total >= 0 else c['danger']
        self.subtitle_label.setText(
            f"{tr('total_week')} <span style='color:{color}; font-weight:800'>{format_result(total)}</span>"
        )

        if animate and self.animations_enabled and self.isVisible():
            self._anim.stop()
            self._anim.start()
        else:
            self._render(1.0)

    def set_mode(self, mode: str, emit=False):
        if mode not in ('2d', '3d'):
            return
        changed = mode != self.mode
        self.mode = mode
        self.mode_buttons[mode].setChecked(True)
        if changed and self.last_data_model is not None:
            self._view = None
            self.update_chart(self.last_data_model)
        if emit and changed:
            self.mode_changed.emit(mode)

    def set_animations_enabled(self, enabled: bool):
        self.animations_enabled = bool(enabled)

    def set_theme(self, is_dark: bool):
        """Cambiar tema del gráfico"""
        self.is_dark = is_dark
        if self.last_data_model is not None:
            self.update_chart(self.last_data_model, animate=False)

    def set_legend_visible(self, visible: bool):
        self.legend_visible = bool(visible)
        if self._items:
            self._render(1.0)

    def set_legend_position(self, position: str):
        if position in ('outside_right', 'upper_right', 'upper_center'):
            self.legend_position = position
            if self._items:
                self._render(1.0)

    def apply_language(self):
        self.title_label.setText(tr('weekly_performance_title'))
        if self.last_data_model is not None:
            self.update_chart(self.last_data_model, animate=False)

    def clear_chart(self):
        self.figure.clear()
        self.canvas.draw()

    def show_error_message(self, error_msg):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, f"{tr('chart_error_load')}:\n{error_msg}", ha='center', va='center',
                transform=ax.transAxes, fontsize=12, color=self._c()['danger'], weight='bold')
        ax.axis('off')
        self.canvas.draw()

    # ------------------------------------------------------------ datos
    def _c(self):
        return ThemeManager.colors(self.is_dark)

    def _collect(self, data_model):
        c = self._c()
        items = []
        model_days = list(getattr(data_model, 'days', []))
        for i, day in enumerate(model_days):
            amount = float(data_model.daily_amounts.get(day, 0) or 0)
            destination = data_model.daily_destinations.get(day, '')
            info = data_model.data.get(day, {}) if hasattr(data_model, 'data') else {}
            label = tr(DAY_KEYS[i])[:3] if i < len(DAY_KEYS) else day[:3]
            if amount < 0:
                color = c['danger']
            elif amount == 0:
                color = c['text_muted']
            elif destination in REINVESTMENT_NAMES or destination == tr('reinvestment'):
                color = c['warning']
            else:
                color = c['success']
            items.append({
                'label': label, 'amount': amount, 'color': color, 'placeholder': False,
                'pair': info.get('pair', '') or '', 'duration': info.get('duration', '') or '',
            })
        # Fin de semana visual (sin operaciones)
        for key in ('saturday', 'sunday'):
            if len(items) < 7:
                items.append({'label': tr(key)[:3], 'amount': 0.0, 'color': c['text_muted'],
                              'placeholder': True, 'pair': '', 'duration': ''})

        # Índice del día de hoy si la semana cargada es la actual
        self._today_index = None
        week_start = getattr(data_model, 'week_start_date', None)
        if week_start:
            delta = (datetime.now().date() - week_start).days
            if 0 <= delta < len(items):
                self._today_index = delta
        return items

    def _limits(self):
        amounts = [i['amount'] for i in self._items]
        real = [i['amount'] for i in self._items if not i['placeholder']]
        cum = np.cumsum(real) if real else np.array([0.0])
        lo = min(0.0, min(amounts), float(cum.min()))
        hi = max(0.0, max(amounts), float(cum.max()))
        span = (hi - lo) or 10.0
        return lo, hi, span, cum

    # ----------------------------------------------------------- render
    def _render(self, t, intro=False):
        if not self._items:
            return
        try:
            # Conservar la cámara elegida por el usuario al redibujar en 3D
            if not intro and self.figure.axes and hasattr(self.figure.axes[0], 'elev'):
                ax = self.figure.axes[0]
                self._view = (ax.elev, ax.azim)
            self.figure.clear()
            self.figure.patch.set_facecolor(self._c()['surface'])
            if self.mode == '3d':
                self._render_3d(t, intro)
            else:
                self._render_2d(t)
            self.canvas.draw_idle()
        except Exception as e:
            print(f"{tr('chart_error_update')}: {e}")

    def _legend_handles(self):
        c = self._c()
        handles = [
            patches.Patch(color=c['success'], label=tr('legend_gain_withdrawal')),
            patches.Patch(color=c['warning'], label=tr('legend_gain_reinvestment')),
            patches.Patch(color=c['danger'], label=tr('legend_loss')),
        ]
        from matplotlib.lines import Line2D
        handles.append(Line2D([0], [0], color=c['accent2'], lw=2, marker='o', markersize=5,
                              label=tr('cumulative_label', 'Acumulado')))
        return handles

    def _draw_legend(self, target, is_fig=False):
        if not self.legend_visible:
            return
        c = self._c()
        kwargs = dict(handles=self._legend_handles(), frameon=False, fontsize=8,
                      labelcolor=c['text_secondary'], handlelength=1.2, handleheight=0.8,
                      columnspacing=1.4)
        if self.legend_position == 'outside_right' and not is_fig:
            target.legend(loc='upper left', bbox_to_anchor=(1.01, 1.0), ncol=1, **kwargs)
        elif self.legend_position == 'upper_center':
            target.legend(loc='upper center', ncol=4, **kwargs)
        elif is_fig:
            target.legend(loc='upper left', ncol=4, bbox_to_anchor=(0.01, 0.99), **kwargs)
        else:
            target.legend(loc='upper right', ncol=4, **kwargs)

    # ---- 2D --------------------------------------------------------
    def _render_2d(self, t):
        c = self._c()
        fig = self.figure
        ax = fig.add_subplot(111)
        right = 0.84 if (self.legend_visible and self.legend_position == 'outside_right') else 0.985
        fig.subplots_adjust(left=0.075, right=right, top=0.95, bottom=0.1)
        ax.set_facecolor(c['surface'])

        items = self._items
        n = len(items)
        xs = np.arange(n)
        lo, hi, span, cum = self._limits()
        y0 = lo - span * 0.22 if lo < 0 else -span * 0.06
        y1 = hi + span * 0.34
        ax.set_xlim(-0.6, n - 0.4)
        ax.set_ylim(y0, y1)
        ax.set_autoscale_on(False)

        # Fondo con degradado sutil hacia el acento
        bg = LinearSegmentedColormap.from_list('bg', [c['surface'], _mix(c['surface'], c['accent'], 0.10)])
        ax.imshow(np.linspace(0, 1, 256).reshape(-1, 1), extent=[-0.6, n - 0.4, y0, y1],
                  aspect='auto', cmap=bg, origin='lower', zorder=0, interpolation='bicubic')

        # Día actual resaltado
        if self._today_index is not None:
            ax.axvspan(self._today_index - 0.46, self._today_index + 0.46,
                       color=c['accent'], alpha=0.07, zorder=0.5, lw=0)

        # Proporción de unidades para esquinas redondeadas circulares
        bbox = ax.get_window_extent()
        aspect = ((y1 - y0) / max(bbox.height, 1)) / ((n - 0.4 + 0.6) / max(bbox.width, 1))
        width = 0.56
        pad = span * 0.04

        for x, item in zip(xs, items):
            h = item['amount'] * t
            if item['placeholder'] or item['amount'] == 0:
                ghost = patches.FancyBboxPatch(
                    (x - width / 2, -span * 0.012), width, span * 0.024,
                    boxstyle=f"round,pad=0,rounding_size={width / 2 * 0.25}", mutation_aspect=aspect,
                    facecolor=_mix(c['surface'], c['text_muted'], 0.35), edgecolor='none', zorder=2)
                ax.add_patch(ghost)
                continue

            base, height = (0, h) if h >= 0 else (h, -h)
            radius = min(0.14, (height / aspect) / 2) if height > 0 else 0
            box = f"round,pad=0,rounding_size={radius}" if radius > 0.005 else "square,pad=0"
            color = item['color']

            # Brillo neón (capas difusas detrás de la barra)
            if self.is_dark:
                for lw, alpha in ((22, 0.04), (13, 0.07), (6, 0.12)):
                    ax.add_patch(patches.FancyBboxPatch(
                        (x - width / 2, base), width, height, boxstyle=box, mutation_aspect=aspect,
                        facecolor='none', edgecolor=color, linewidth=lw, alpha=alpha, zorder=2,
                        joinstyle='round'))

            bar = patches.FancyBboxPatch(
                (x - width / 2, base), width, height, boxstyle=box, mutation_aspect=aspect,
                facecolor='none', edgecolor=_mix(color, '#ffffff', 0.35), linewidth=0.9, zorder=4)
            ax.add_patch(bar)
            # Relleno con degradado recortado a la forma de la barra
            dark = _mix(color, c['surface'], 0.55)
            light = _mix(color, '#ffffff', 0.18)
            cmap = LinearSegmentedColormap.from_list('bar', [dark, color, light])
            grad = np.linspace(0, 1, 128).reshape(-1, 1)
            if h < 0:
                grad = grad[::-1]
            im = ax.imshow(grad, extent=[x - width / 2, x + width / 2, base, base + height],
                           aspect='auto', cmap=cmap, origin='lower', zorder=3, interpolation='bicubic')
            im.set_clip_path(bar)

            # Etiquetas (aparecen al final de la animación)
            alpha = max(0.0, min(1.0, (t - 0.55) / 0.45))
            if alpha > 0:
                stroke = [pe.withStroke(linewidth=3, foreground=c['surface'])]
                if h >= 0:
                    ty, va, ty2 = h + pad, 'bottom', h + pad + span * 0.075
                else:
                    ty, va, ty2 = h - pad, 'top', h - pad - span * 0.075
                ax.text(x, ty, format_result(item['amount']), ha='center', va=va, fontsize=10,
                        fontweight='bold', color=color, alpha=alpha, zorder=6, path_effects=stroke)
                note = ' · '.join(filter(None, [item['pair'], _short_duration(item['duration'])]))
                if note:
                    ax.text(x, ty2, note, ha='center', va=va, fontsize=7.5, color=c['text_secondary'],
                            alpha=alpha, zorder=6, path_effects=stroke)

        # Curva de P/L acumulado con brillo
        real_x = xs[:len(cum)]
        cum_t = cum * t
        ax.fill_between(real_x, cum_t, 0, color=c['accent2'], alpha=0.06, zorder=1, lw=0)
        for lw, alpha in ((9, 0.05), (5, 0.12)):
            ax.plot(real_x, cum_t, color=c['accent2'], lw=lw, alpha=alpha, zorder=5,
                    solid_capstyle='round')
        ax.plot(real_x, cum_t, color=c['accent2'], lw=2, zorder=5, marker='o', markersize=6,
                markerfacecolor=c['surface'], markeredgecolor=c['accent2'], markeredgewidth=2)

        # Promedio diario
        real = [i['amount'] for i in items if not i['placeholder']]
        if real:
            avg = float(np.mean(real))
            ax.axhline(avg, color=c['accent'], ls=(0, (4, 4)), lw=1.2, alpha=0.7, zorder=1.5)
            ax.text(n - 0.45, avg, f" {tr('average_label')} {format_result(avg)}", ha='right',
                    va='bottom', fontsize=8, color=c['accent_hover'], zorder=6,
                    path_effects=[pe.withStroke(linewidth=3, foreground=c['surface'])])
        ax.axhline(0, color=c['border_strong'], lw=1, zorder=1.6)

        # Ejes
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_xticks(xs)
        ax.set_xticklabels([i['label'] for i in items], fontsize=10, fontweight='bold')
        for lbl, item in zip(ax.get_xticklabels(), items):
            lbl.set_color(c['text_muted'] if item['placeholder'] else c['text'])
        ax.tick_params(axis='both', length=0, pad=8)
        ax.tick_params(axis='y', colors=c['text_muted'], labelsize=8)
        ax.yaxis.set_major_formatter(FuncFormatter(_axis_money))
        ax.grid(True, axis='y', color=c['border'], lw=0.8, ls=(0, (1, 3)), alpha=0.9)
        ax.set_axisbelow(True)
        self._draw_legend(ax)

    # ---- 3D --------------------------------------------------------
    def _render_3d(self, t, intro):
        c = self._c()
        fig = self.figure
        ax = fig.add_subplot(111, projection='3d')
        fig.subplots_adjust(left=-0.03, right=1.0, top=1.1, bottom=-0.08)
        ax.set_facecolor(c['surface'])

        items = self._items
        n = len(items)
        xs = np.arange(n)
        lo, hi, span, cum = self._limits()
        z0 = lo - span * 0.1 if lo < 0 else 0
        z1 = hi + span * 0.25

        # Paneles transparentes y rejilla sutil
        grid_rgba = to_rgba(c['border_strong'], 0.6)
        for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
            axis.set_pane_color(to_rgba(c['surface'], 0.0))
            axis.pane.set_edgecolor(to_rgba(c['border'], 0.8))
            try:
                axis._axinfo['grid'].update(color=grid_rgba, linewidth=0.5, linestyle=':')
                axis._axinfo['axisline']['color'] = to_rgba(c['border'], 0.0)
            except Exception:
                pass
        ax.zaxis.set_pane_color(to_rgba(c['accent'], 0.035))

        # Suelo luminoso en z=0
        gx, gy = np.meshgrid(np.linspace(-0.7, n - 0.3, 2), np.linspace(-0.7, 1.1, 2))
        ax.plot_surface(gx, gy, np.zeros_like(gx), color=to_rgba(c['accent'], 0.10 if self.is_dark else 0.06),
                        shade=False, linewidth=0, zorder=0)

        dx = dy = 0.56
        for x, item in zip(xs, items):
            h = item['amount'] * t
            if item['placeholder'] or item['amount'] == 0:
                ax.bar3d(x - dx / 2, 0, 0, dx, dy, span * 0.012, color=to_rgba(c['text_muted'], 0.25),
                         shade=False, linewidth=0, zorder=2)
                continue
            if abs(h) < 1e-9:
                continue
            base = min(0.0, h)
            ax.bar3d(x - dx / 2, 0, base, dx, dy, abs(h), color=to_rgba(item['color'], 0.93),
                     shade=True, edgecolor=to_rgba(_mix(item['color'], '#ffffff', 0.4), 0.9),
                     linewidth=0.5, zorder=3)

            alpha = max(0.0, min(1.0, (t - 0.55) / 0.45))
            if alpha > 0:
                top = h + span * 0.05 if h >= 0 else h - span * 0.07
                ax.text(x, dy / 2, top, format_result(item['amount']), ha='center', va='bottom',
                        fontsize=9.5, fontweight='bold', color=item['color'], alpha=alpha, zorder=10,
                        path_effects=[pe.withStroke(linewidth=3, foreground=c['surface'])])
                note = ' · '.join(filter(None, [item['pair'], _short_duration(item['duration'])]))
                if note:
                    ax.text(x, dy / 2, top + span * (0.09 if h >= 0 else -0.09), note, ha='center',
                            va='bottom', fontsize=7, color=c['text_secondary'], alpha=alpha, zorder=10)

        # Curva acumulada en la fila trasera con líneas de caída
        cx = xs[:len(cum)]
        cy = np.full(len(cum), -0.45)
        cz = cum * t
        ax.plot(cx, cy, cz, color=c['accent2'], lw=6, alpha=0.12, zorder=4)
        ax.plot(cx, cy, cz, color=c['accent2'], lw=2, marker='o', markersize=5,
                markerfacecolor=c['surface'], markeredgecolor=c['accent2'], zorder=5)
        for x, z in zip(cx, cz):
            ax.plot([x, x], [-0.45, -0.45], [0, z], color=c['accent2'], lw=0.8, alpha=0.3, ls=':', zorder=4)

        ax.set_xlim(-0.7, n - 0.3)
        ax.set_ylim(-0.7, 1.1)
        ax.set_zlim(z0, z1)
        ax.set_xticks(xs)
        ax.set_xticklabels([i['label'] for i in items], fontsize=9, fontweight='bold')
        for lbl, item in zip(ax.get_xticklabels(), items):
            lbl.set_color(c['text_muted'] if item['placeholder'] else c['text'])
        ax.set_yticks([])
        ax.zaxis.set_major_formatter(FuncFormatter(_axis_money))
        ax.tick_params(axis='z', colors=c['text_muted'], labelsize=8, pad=6)
        ax.tick_params(axis='x', pad=0)
        try:
            ax.set_box_aspect((3.0, 1.0, 1.15), zoom=1.22)
        except TypeError:
            ax.set_box_aspect((3.0, 1.0, 1.15))

        # Cámara: barrido cinematográfico en la intro, luego la vista del usuario
        if intro and t < 1.0:
            ax.view_init(elev=6 + 16 * t, azim=-110 + 38 * t)
        elif self._view and not intro:
            ax.view_init(elev=self._view[0], azim=self._view[1])
        else:
            ax.view_init(elev=22, azim=-72)
        self._draw_legend(fig, is_fig=True)
