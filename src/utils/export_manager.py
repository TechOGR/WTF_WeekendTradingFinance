"""
Exportación de semanas de trading a Excel, CSV y JSON.

Todas las salidas parten del mismo registro normalizado (ver `build_week_record`),
así los tres formatos muestran exactamente los mismos números.
"""

import csv
import json
from datetime import datetime, date, timedelta
from typing import Dict, List

import xlsxwriter

from src.utils.i18n import tr
from src.version import APP_NAME, APP_VERSION

DAY_KEYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
DAY_ORDER = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
WITHDRAW_RATIO = 0.30

FORMAT_EXCEL, FORMAT_CSV, FORMAT_JSON = 'excel', 'csv', 'json'
EXTENSIONS = {FORMAT_EXCEL: '.xlsx', FORMAT_CSV: '.csv', FORMAT_JSON: '.json'}


# ---------------------------------------------------------------- datos
def _destination_label(value: str) -> str:
    return {'Retiro Personal': tr('personal_withdrawal'), 'Reinversión': tr('reinvestment')}.get(value, value or '')


def _parse_date(value):
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)).date()
    except (TypeError, ValueError):
        return None


def build_week_record(week: Dict) -> Dict:
    """Normalizar una semana ({week_start_date, initial_capital, data:{día:{...}}}) con totales calculados."""
    start = _parse_date(week.get('week_start_date'))
    initial = float(week.get('initial_capital', 0.0) or 0.0)
    data = week.get('data', {}) or {}
    days_present = [d for d in DAY_ORDER if d in data] + [d for d in data if d not in DAY_ORDER]

    days, cumulative = [], 0.0
    for day in days_present:
        info = data.get(day) or {}
        idx = DAY_ORDER.index(day) if day in DAY_ORDER else None
        amount = float(info.get('amount', 0.0) or 0.0)
        cumulative += amount
        days.append({
            'day': tr(DAY_KEYS[idx]) if idx is not None else day,
            'date': (start + timedelta(days=idx)) if (start and idx is not None) else None,
            'pair': info.get('pair', '') or '',
            'duration': info.get('duration', '') or '',
            'amount': amount,
            'cumulative': cumulative,
            'balance': initial + cumulative,
            'destination': _destination_label(info.get('destination', '')),
        })

    total = cumulative
    traded = [d['amount'] for d in days if abs(d['amount']) > 1e-9]
    wins = sum(1 for a in traded if a > 0)
    withdraw = max(0.0, total) * WITHDRAW_RATIO
    return {
        'start': start,
        'end': (start + timedelta(days=len(days) - 1)) if (start and days) else start,
        'initial': initial,
        'days': days,
        'total': total,
        'percent': (total / initial * 100) if initial else 0.0,
        'final': initial + total,
        'wins': wins,
        'losses': sum(1 for a in traded if a < 0),
        'traded': len(traded),
        'win_rate': (wins / len(traded) * 100) if traded else 0.0,
        'best': max(traded) if traded else 0.0,
        'worst': min(traded) if traded else 0.0,
        'withdraw': withdraw,
        'reinvest': max(0.0, total) - withdraw,
        'next_capital': max(0.0, initial + total - withdraw),
    }


def collect_weeks(model, all_weeks: bool) -> List[Dict]:
    """Semana actual del modelo o, si `all_weeks`, todas las de la base de datos (la actual con sus cambios en memoria)."""
    current = model.to_dict()
    if not all_weeks:
        return [build_week_record(current)]
    weeks = {}
    db = getattr(model, 'db_manager', None)
    if db is not None:
        for row in db.get_all_weeks():
            week = db.load_week_by_date(row['week_start_date'])
            if week:
                weeks[str(week['week_start_date'])] = week
    weeks[str(current['week_start_date'])] = current
    return [build_week_record(weeks[k]) for k in sorted(weeks)]


def count_saved_weeks(model) -> int:
    db = getattr(model, 'db_manager', None)
    dates = {str(r['week_start_date']) for r in (db.get_all_weeks() if db else [])}
    dates.add(str(model.to_dict()['week_start_date']))
    return len(dates)


def _fmt_date(d):
    return d.strftime('%d/%m/%Y') if d else ''


def _headers():
    return [tr('week'), tr('day_column'), tr('date_column', 'Fecha'), tr('currency_pair', 'Par de divisas'),
            tr('session_duration', 'Duración'), tr('result_column', 'Resultado'),
            tr('cumulative_column', 'Acumulado'), tr('balance_column', 'Balance'), tr('destination_column')]


def flat_rows(weeks: List[Dict]) -> List[list]:
    """Filas planas (una por día) usadas por CSV y por la vista previa."""
    rows = []
    for w in weeks:
        for d in w['days']:
            rows.append([_fmt_date(w['start']), d['day'], _fmt_date(d['date']), d['pair'], d['duration'],
                         d['amount'], d['cumulative'], d['balance'], d['destination']])
    return rows


# ---------------------------------------------------------------- CSV
def export_csv(weeks: List[Dict], path: str, include_summary: bool = True, regional: bool = False) -> None:
    """CSV UTF-8 con BOM (Excel muestra bien los acentos).

    regional=True usa ';' como separador y coma decimal (Excel en español).
    """
    delimiter = ';' if regional else ','

    def num(v):
        text = f"{v:.2f}"
        return text.replace('.', ',') if regional else text

    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=delimiter)
        writer.writerow(_headers())
        for row in flat_rows(weeks):
            writer.writerow(row[:5] + [num(v) for v in row[5:8]] + row[8:])
        if include_summary:
            writer.writerow([])
            writer.writerow([tr('week'), tr('capital_initial').rstrip(':'), tr('result_column', 'Resultado'),
                             tr('performance').rstrip(':'), tr('final_balance', 'Balance final'),
                             tr('win_rate', 'Tasa de acierto'), tr('withdraw_30', 'Retiro recomendado (30%)'),
                             tr('next_week_capital', 'Capital próxima semana')])
            for w in weeks:
                writer.writerow([_fmt_date(w['start']), num(w['initial']), num(w['total']), num(w['percent']) + '%',
                                 num(w['final']), f"{w['win_rate']:.0f}%", num(w['withdraw']), num(w['next_capital'])])


# ---------------------------------------------------------------- JSON
def export_json(weeks: List[Dict], path: str, include_summary: bool = True) -> None:
    def day_json(d):
        return {'day': d['day'], 'date': d['date'].isoformat() if d['date'] else None, 'pair': d['pair'],
                'duration': d['duration'], 'amount': round(d['amount'], 2),
                'cumulative': round(d['cumulative'], 2), 'balance': round(d['balance'], 2),
                'destination': d['destination']}

    def week_json(w):
        out = {'week_start_date': w['start'].isoformat() if w['start'] else None,
               'initial_capital': round(w['initial'], 2), 'days': [day_json(d) for d in w['days']]}
        if include_summary:
            out['summary'] = {k: round(w[k], 2) for k in ('total', 'percent', 'final', 'win_rate', 'best', 'worst',
                                                          'withdraw', 'reinvest', 'next_capital')}
            out['summary'].update({k: w[k] for k in ('wins', 'losses', 'traded')})
        return out

    payload = {
        'metadata': {'application': APP_NAME, 'version': APP_VERSION,
                     'exported_at': datetime.now().isoformat(timespec='seconds'), 'weeks': len(weeks)},
        'weeks': [week_json(w) for w in weeks],
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------- Excel
ACCENT = '#6246EA'
GREEN = '#0F9F6E'
RED = '#E11D48'


def _safe_sheet(name: str) -> str:
    for ch in '[]:*?/\\':
        name = name.replace(ch, '-')
    return name[:31]


def export_excel(weeks: List[Dict], path: str, include_charts: bool = True, include_summary: bool = True) -> None:
    wb = xlsxwriter.Workbook(path)
    f = {
        'title': wb.add_format({'bold': True, 'font_size': 18, 'font_color': ACCENT}),
        'subtitle': wb.add_format({'italic': True, 'font_color': '#5B6B86'}),
        'header': wb.add_format({'bold': True, 'font_color': 'white', 'bg_color': ACCENT, 'border': 1,
                                 'align': 'center', 'valign': 'vcenter'}),
        'text': wb.add_format({'border': 1, 'border_color': '#DDE4F0'}),
        'date': wb.add_format({'border': 1, 'border_color': '#DDE4F0', 'num_format': 'dd/mm/yyyy', 'align': 'center'}),
        'money': wb.add_format({'border': 1, 'border_color': '#DDE4F0', 'num_format': '$#,##0.00;[Red]-$#,##0.00'}),
        'result': wb.add_format({'border': 1, 'border_color': '#DDE4F0', 'bold': True,
                                 'num_format': '[Color10]+$#,##0.00;[Red]-$#,##0.00;$0.00'}),
        'pct': wb.add_format({'border': 1, 'border_color': '#DDE4F0', 'num_format': '+0.00%;[Red]-0.00%'}),
        'total_label': wb.add_format({'bold': True, 'top': 2, 'bg_color': '#ECE8FF'}),
        'total_money': wb.add_format({'bold': True, 'top': 2, 'bg_color': '#ECE8FF',
                                      'num_format': '[Color10]+$#,##0.00;[Red]-$#,##0.00;$0.00'}),
        'kpi_label': wb.add_format({'bold': True, 'bg_color': '#F4F7FC', 'border': 1, 'border_color': '#DDE4F0'}),
        'kpi_money': wb.add_format({'bold': True, 'border': 1, 'border_color': '#DDE4F0', 'font_size': 12,
                                    'num_format': '$#,##0.00;[Red]-$#,##0.00'}),
        'kpi_signed': wb.add_format({'bold': True, 'border': 1, 'border_color': '#DDE4F0', 'font_size': 12,
                                     'num_format': '[Color10]+$#,##0.00;[Red]-$#,##0.00;$0.00'}),
        'kpi_pct': wb.add_format({'bold': True, 'border': 1, 'border_color': '#DDE4F0', 'font_size': 12,
                                  'num_format': '0.00%'}),
        'kpi_num': wb.add_format({'bold': True, 'border': 1, 'border_color': '#DDE4F0', 'font_size': 12}),
    }
    headers = _headers()[1:]  # la hoja de una semana no necesita la columna "Semana"

    def write_week_sheet(w):
        name = _safe_sheet(f"{tr('week')} {w['start'].isoformat() if w['start'] else ''}".strip())
        ws = wb.add_worksheet(name)
        ws.hide_gridlines(2)
        ws.write(0, 0, f"{tr('week')} {_fmt_date(w['start'])} → {_fmt_date(w['end'])}", f['title'])
        ws.write(1, 0, f"{tr('capital_initial').rstrip(':')}: ${w['initial']:,.2f}", f['subtitle'])
        top = 3
        for c, h in enumerate(headers):
            ws.write(top, c, h, f['header'])
        first = top + 1
        for i, d in enumerate(w['days']):
            r = first + i
            ws.write(r, 0, d['day'], f['text'])
            if d['date']:
                ws.write_datetime(r, 1, datetime.combine(d['date'], datetime.min.time()), f['date'])
            else:
                ws.write_blank(r, 1, None, f['date'])
            ws.write(r, 2, d['pair'], f['text'])
            ws.write(r, 3, d['duration'], f['text'])
            ws.write_number(r, 4, d['amount'], f['result'])
            # Fórmulas: si editas un resultado en Excel, acumulado y balance se recalculan
            ws.write_formula(r, 5, f"=SUM($E${first + 1}:E{r + 1})", f['money'], d['cumulative'])
            ws.write_formula(r, 6, f"={w['initial']}+F{r + 1}", f['money'], d['balance'])
            ws.write(r, 7, d['destination'], f['text'])
        last = first + len(w['days']) - 1
        total_row = last + 1
        ws.write(total_row, 0, tr('total_week').rstrip(':'), f['total_label'])
        for c in (1, 2, 3, 5, 7):
            ws.write_blank(total_row, c, None, f['total_label'])
        ws.write_formula(total_row, 4, f"=SUM(E{first + 1}:E{last + 1})", f['total_money'], w['total'])
        ws.write_formula(total_row, 6, f"={w['initial']}+E{total_row + 1}", f['total_money'], w['final'])
        ws.conditional_format(first, 4, last, 4, {'type': 'data_bar', 'bar_color': '#63C384',
                                                   'bar_negative_color': '#FF5A5A', 'bar_solid': True})
        ws.set_column(0, 0, 13)
        ws.set_column(1, 1, 12)
        ws.set_column(2, 3, 13)
        ws.set_column(4, 6, 14)
        ws.set_column(7, 7, 18)
        ws.freeze_panes(first, 0)

        if include_charts and w['days']:
            col = wb.add_chart({'type': 'column'})
            col.add_series({
                'name': tr('result_column', 'Resultado'),
                'categories': [name, first, 0, last, 0],
                'values': [name, first, 4, last, 4],
                'points': [{'fill': {'color': GREEN if d['amount'] >= 0 else RED}} for d in w['days']],
                'data_labels': {'value': True, 'num_format': '$#,##0.00'},
                'gap': 80,
            })
            col.set_title({'name': tr('daily_breakdown', 'Desglose por día')})
            col.set_legend({'none': True})
            col.set_y_axis({'num_format': '$#,##0', 'major_gridlines': {'visible': True,
                                                                         'line': {'color': '#E5E9F2'}}})
            col.set_chartarea({'border': {'none': True}})
            ws.insert_chart(top, 9, col, {'x_scale': 1.15, 'y_scale': 1.0})

            line = wb.add_chart({'type': 'line'})
            line.add_series({
                'name': tr('balance_column', 'Balance'),
                'categories': [name, first, 0, last, 0],
                'values': [name, first, 6, last, 6],
                'line': {'color': ACCENT, 'width': 2.5},
                'marker': {'type': 'circle', 'size': 7, 'fill': {'color': ACCENT}, 'border': {'color': ACCENT}},
            })
            line.set_title({'name': tr('balance_evolution', 'Evolución del balance')})
            line.set_legend({'none': True})
            line.set_y_axis({'num_format': '$#,##0'})
            line.set_chartarea({'border': {'none': True}})
            ws.insert_chart(top + 16, 9, line, {'x_scale': 1.15, 'y_scale': 1.0})
        return ws, name, first, last

    def write_summary(ws, w, row, col):
        """Bloque de KPIs a la derecha/abajo de la tabla de una semana."""
        items = [
            (tr('capital_initial').rstrip(':'), w['initial'], 'kpi_money'),
            (tr('total_week').rstrip(':'), w['total'], 'kpi_signed'),
            (tr('performance').rstrip(':'), w['percent'] / 100, 'kpi_pct'),
            (tr('final_balance', 'Balance final'), w['final'], 'kpi_money'),
            (tr('win_rate', 'Tasa de acierto'), w['win_rate'] / 100, 'kpi_pct'),
            (tr('best_day', 'Mejor día'), w['best'], 'kpi_signed'),
            (tr('worst_day', 'Peor día'), w['worst'], 'kpi_signed'),
            (tr('withdraw_30', 'Retiro recomendado (30%)'), w['withdraw'], 'kpi_money'),
            (tr('suggested_reinvestment', 'Reinversión sugerida'), w['reinvest'], 'kpi_money'),
            (tr('next_week_capital', 'Capital próxima semana'), w['next_capital'], 'kpi_money'),
        ]
        ws.write(row, col, tr('weekly_summary_panel'), f['title'])
        for i, (label, value, fmt) in enumerate(items):
            ws.write(row + 2 + i, col, label, f['kpi_label'])
            ws.write_number(row + 2 + i, col + 1, value, f[fmt])
        ws.set_column(col, col, 28)
        ws.set_column(col + 1, col + 1, 16)

    if len(weeks) == 1:
        w = weeks[0]
        ws, name, first, last = write_week_sheet(w)
        if include_summary:
            write_summary(ws, w, last + 4, 0)
            ws.set_column(0, 0, 28)
    else:
        # Historial: una fila por semana + gráfico de evolución
        hs = wb.add_worksheet(_safe_sheet(tr('history', 'Historial')))
        hs.hide_gridlines(2)
        hs.write(0, 0, f"{APP_NAME} · {tr('history', 'Historial')}", f['title'])
        hs.write(1, 0, f"{len(weeks)} {tr('weeks_word', 'semanas')} · "
                       f"{_fmt_date(weeks[0]['start'])} → {_fmt_date(weeks[-1]['end'])}", f['subtitle'])
        h_headers = [tr('week'), tr('capital_initial').rstrip(':'), tr('result_column', 'Resultado'),
                     tr('performance').rstrip(':'), tr('final_balance', 'Balance final'), tr('win_rate', 'Tasa de acierto'),
                     tr('withdraw_30', 'Retiro recomendado (30%)')]
        top = 3
        for c, h in enumerate(h_headers):
            hs.write(top, c, h, f['header'])
        for i, w in enumerate(weeks):
            r = top + 1 + i
            if w['start']:
                hs.write_datetime(r, 0, datetime.combine(w['start'], datetime.min.time()), f['date'])
            else:
                hs.write_blank(r, 0, None, f['date'])
            hs.write_number(r, 1, w['initial'], f['money'])
            hs.write_number(r, 2, w['total'], f['result'])
            hs.write_formula(r, 3, f"=IF(B{r + 1}=0,0,C{r + 1}/B{r + 1})", f['pct'], w['percent'] / 100)
            hs.write_formula(r, 4, f"=B{r + 1}+C{r + 1}", f['money'], w['final'])
            hs.write_number(r, 5, w['win_rate'] / 100, f['pct'])
            hs.write_formula(r, 6, f"=MAX(0,C{r + 1})*{WITHDRAW_RATIO}", f['money'], w['withdraw'])
        first, last = top + 1, top + len(weeks)
        total_row = last + 1
        hs.write(total_row, 0, tr('total_week').rstrip(':').split()[0] if tr('total_week').rstrip(':') else 'Total', f['total_label'])
        hs.write_blank(total_row, 1, None, f['total_label'])
        hs.write_formula(total_row, 2, f"=SUM(C{first + 1}:C{last + 1})", f['total_money'],
                         sum(w['total'] for w in weeks))
        for c in (3, 4, 5):
            hs.write_blank(total_row, c, None, f['total_label'])
        hs.write_formula(total_row, 6, f"=SUM(G{first + 1}:G{last + 1})", f['total_money'],
                         sum(w['withdraw'] for w in weeks))
        hs.conditional_format(first, 2, last, 2, {'type': 'data_bar', 'bar_color': '#63C384',
                                                   'bar_negative_color': '#FF5A5A', 'bar_solid': True})
        hs.set_column(0, 0, 13)
        hs.set_column(1, 6, 17)
        hs.freeze_panes(first, 0)
        hist_name = hs.get_name()
        if include_charts:
            col = wb.add_chart({'type': 'column'})
            col.add_series({
                'name': tr('result_column', 'Resultado'),
                'categories': [hist_name, first, 0, last, 0],
                'values': [hist_name, first, 2, last, 2],
                'points': [{'fill': {'color': GREEN if w['total'] >= 0 else RED}} for w in weeks],
            })
            line = wb.add_chart({'type': 'line'})
            line.add_series({
                'name': tr('final_balance', 'Balance final'),
                'categories': [hist_name, first, 0, last, 0],
                'values': [hist_name, first, 4, last, 4],
                'y2_axis': True,
                'line': {'color': ACCENT, 'width': 2.5},
                'marker': {'type': 'circle', 'size': 6, 'fill': {'color': ACCENT}, 'border': {'color': ACCENT}},
            })
            col.combine(line)
            col.set_title({'name': tr('weekly_evolution', 'Evolución semanal')})
            col.set_legend({'position': 'bottom'})
            col.set_y_axis({'num_format': '$#,##0'})
            line.set_y2_axis({'num_format': '$#,##0'})
            col.set_chartarea({'border': {'none': True}})
            hs.insert_chart(top, 8, col, {'x_scale': 1.4, 'y_scale': 1.2})

        # Detalle de todos los días
        ds = wb.add_worksheet(_safe_sheet(tr('detail', 'Detalle')))
        all_headers = _headers()
        for c, h in enumerate(all_headers):
            ds.write(0, c, h, f['header'])
        r = 1
        for w in weeks:
            for d in w['days']:
                ds.write(r, 0, _fmt_date(w['start']), f['text'])
                ds.write(r, 1, d['day'], f['text'])
                ds.write(r, 2, _fmt_date(d['date']), f['text'])
                ds.write(r, 3, d['pair'], f['text'])
                ds.write(r, 4, d['duration'], f['text'])
                ds.write_number(r, 5, d['amount'], f['result'])
                ds.write_number(r, 6, d['cumulative'], f['money'])
                ds.write_number(r, 7, d['balance'], f['money'])
                ds.write(r, 8, d['destination'], f['text'])
                r += 1
        ds.autofilter(0, 0, max(1, r - 1), len(all_headers) - 1)
        ds.freeze_panes(1, 0)
        ds.set_column(0, 8, 14)

        if include_summary:
            # Una hoja por semana con sus KPIs (las más recientes primero)
            for w in reversed(weeks):
                ws, _, _, last = write_week_sheet(w)
                write_summary(ws, w, last + 4, 0)
                ws.set_column(0, 0, 28)

    wb.set_properties({'title': f"{APP_NAME} export", 'author': APP_NAME,
                       'comments': f"{APP_NAME} v{APP_VERSION}"})
    wb.close()


def export_weeks(weeks: List[Dict], path: str, fmt: str, include_charts=True, include_summary=True,
                 csv_regional=False) -> None:
    """Punto de entrada único. Lanza excepción si algo falla."""
    if fmt == FORMAT_EXCEL:
        export_excel(weeks, path, include_charts, include_summary)
    elif fmt == FORMAT_CSV:
        export_csv(weeks, path, include_summary, csv_regional)
    else:
        export_json(weeks, path, include_summary)
