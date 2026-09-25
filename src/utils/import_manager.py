"""
Importación y análisis de operaciones desde Excel, CSV o JSON.

Formatos reconocidos (se detectan solos por los encabezados):
- Historial de operaciones del bróker (p. ej. Quotex: Información, Tiempo de apertura,
  Tipo, Cantidad, Ingreso...). Una fila por operación.
- Exportaciones de W-T-F (Excel / CSV / JSON, en español o inglés). Una fila por día.
- Semanas guardadas por W-T-F (weekend_trading_AAAA-MM-DD.json).
- Cualquier tabla con una columna de fecha y otra de resultado (o monto + ingreso).

Todo se normaliza a un DataFrame con las columnas de `COLUMNS` y `analyze()` calcula
las estadísticas que muestra la ventana de importación.
"""

import csv
import io
import json
import os
import re
import unicodedata
import warnings
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

KIND_TRADES, KIND_DAYS = 'trades', 'days'
SOURCE_BROKER, SOURCE_WTF, SOURCE_GENERIC = 'broker', 'wtf', 'generic'
FILE_FILTER = 'Excel / CSV / JSON (*.xlsx *.xlsm *.xls *.csv *.txt *.json)'
SUPPORTED_EXT = ('.xlsx', '.xlsm', '.xls', '.csv', '.txt', '.json')

COLUMNS = ['time', 'close_time', 'asset', 'direction', 'stake', 'payout', 'payout_pct',
           'profit', 'outcome', 'duration', 'id', 'source']
OUT_WIN, OUT_LOSS, OUT_DRAW = 'win', 'loss', 'draw'
WTF_DAYS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
EPS = 1e-9


class ImportError_(Exception):
    """Error legible para el usuario al importar un archivo."""


# ---------------------------------------------------------------- encabezados
def _norm(text) -> str:
    text = unicodedata.normalize('NFKD', str(text or '')).encode('ascii', 'ignore').decode()
    return re.sub(r'\s+', ' ', text.strip().lower().replace('_', ' '))


# Alias normalizados (sin acentos, minúsculas) de cada campo
ALIASES = {
    'time': ['tiempo de apertura', 'hora de apertura', 'fecha de apertura', 'open time', 'opening time',
             'open date', 'fecha y hora', 'datetime', 'fecha', 'date', 'time', 'hora', 'dia fecha'],
    'close_time': ['hora de cierre', 'tiempo de cierre', 'fecha de cierre', 'close time', 'closing time',
                   'expiration', 'expiracion', 'vencimiento'],
    'asset': ['informacion', 'activo', 'asset', 'par de divisas', 'currency pair', 'par', 'pair', 'symbol',
              'simbolo', 'instrumento', 'instrument'],
    'direction': ['tipo', 'direccion', 'direction', 'type', 'side', 'accion'],
    'stake': ['cantidad', 'inversion', 'importe', 'stake', 'investment', 'monto invertido', 'trade amount'],
    'payout': ['ingreso', 'income', 'payout', 'pago', 'retorno', 'return', 'devolucion'],
    'payout_pct': ['beneficio', 'rentabilidad', 'payout %', 'porcentaje', 'profit %'],
    'profit': ['resultado', 'result', 'beneficio neto', 'net profit', 'profit', 'ganancia', 'p/l', 'pnl',
               'ganancia/perdida', 'ganancia / perdida', 'profit/loss', 'monto', 'amount', 'neto'],
    'duration': ['duracion', 'duration', 'session duration'],
    'day': ['dia', 'day'],
    'week': ['semana', 'week'],
    'id': ['id', 'ticket', 'order', 'orden', 'deal'],
}


def _map_headers(row) -> dict:
    """Asignar cada campo a la columna cuyo encabezado coincide (primero coincidencia exacta)."""
    names = [_norm(v) for v in row]
    found = {}
    for exact in (True, False):
        for field, aliases in ALIASES.items():
            if field in found:
                continue
            for alias in aliases:
                for idx, name in enumerate(names):
                    if not name or idx in found.values():
                        continue
                    if (name == alias) if exact else (len(alias) > 3 and name.startswith(alias)):
                        found[field] = idx
                        break
                if field in found:
                    break
    return found


def _score(mapping) -> int:
    has_result = 'profit' in mapping or ('stake' in mapping and 'payout' in mapping)
    has_when = 'time' in mapping or 'day' in mapping
    return (10 if has_result else 0) + (5 if has_when else 0) + len(mapping)


# ---------------------------------------------------------------- valores
def to_number(value):
    """'$1.234,50', '93%', '-12,5', 12.5 -> float (NaN si no es un número)."""
    if value is None:
        return np.nan
    if isinstance(value, (int, float, np.integer, np.floating)) and not isinstance(value, bool):
        return float(value)
    text = str(value).strip().replace(' ', '').replace(' ', '')
    if not text or text in {'-', '—', 'nan', 'None'}:
        return np.nan
    negative = text.startswith('(') and text.endswith(')')
    text = re.sub(r'[^0-9,.\-+]', '', text)
    if not text:
        return np.nan
    if ',' in text and '.' in text:
        if text.rfind(',') > text.rfind('.'):
            text = text.replace('.', '').replace(',', '.')
        else:
            text = text.replace(',', '')
    elif ',' in text:
        head, _, tail = text.rpartition(',')
        text = text.replace(',', '') if (len(tail) == 3 and text.count(',') > 1) else f"{head.replace(',', '')}.{tail}"
    try:
        number = float(text)
    except ValueError:
        return np.nan
    return -abs(number) if negative else number


def _to_datetime(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    text = series.astype(str).str.strip()
    iso = pd.to_datetime(text, errors='coerce', format='ISO8601')
    if iso.notna().mean() >= 0.8:
        return iso
    parsed = pd.to_datetime(series, errors='coerce', dayfirst=True)
    return parsed.where(parsed.notna(), iso)


def _clean_direction(value) -> str:
    n = _norm(value)
    if n in {'arriba', 'up', 'call', 'compra', 'buy', 'higher', 'alza', 'sube'}:
        return 'up'
    if n in {'abajo', 'down', 'put', 'venta', 'sell', 'lower', 'baja', 'baja'}:
        return 'down'
    return ''


# ---------------------------------------------------------------- lectura
def _read_csv_rows(path):
    raw = open(path, 'rb').read()
    for encoding in ('utf-8-sig', 'cp1252', 'latin-1'):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    sample = text[:4096]
    try:
        delimiter = csv.Sniffer().sniff(sample, delimiters=',;\t|').delimiter
    except csv.Error:
        delimiter = ';' if sample.count(';') > sample.count(',') else ','
    return [row for row in csv.reader(io.StringIO(text), delimiter=delimiter)]


def _read_tables(path):
    """Devolver [(nombre, filas)] con las filas crudas de cada hoja/tabla del archivo."""
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.csv', '.txt'):
        return [(os.path.basename(path), _read_csv_rows(path))]
    if ext in ('.xlsx', '.xlsm', '.xls'):
        try:
            with warnings.catch_warnings():  # extensiones de Excel que openpyxl no entiende
                warnings.simplefilter('ignore')
                sheets = pd.read_excel(path, sheet_name=None, header=None, dtype=object)
        except ImportError as e:
            raise ImportError_('Para leer archivos .xls antiguos instala "xlrd" o guárdalo como .xlsx '
                               f'desde Excel. ({e})')
        tables = []
        for name, df in sheets.items():
            rows = df.where(pd.notna(df), None).values.tolist()
            tables.append((str(name), rows))
        return tables
    raise ImportError_(f'Formato no soportado: {ext or "sin extensión"}')


def _rows_to_frame(rows, header_idx, mapping):
    """Filas bajo el encabezado hasta la primera fila vacía (así se ignoran los bloques de resumen)."""
    records = []
    for row in rows[header_idx + 1:]:
        cells = [c for c in row if c is not None and str(c).strip() != '']
        if not cells:
            if records:
                break
            continue
        first = _norm(row[0]) if row else ''
        if first.startswith('total'):
            continue
        records.append({field: (row[idx] if idx < len(row) else None) for field, idx in mapping.items()})
    return pd.DataFrame(records)


def _frame_from_table(rows, source_name):
    """Encontrar el encabezado (primeras 25 filas) y normalizar la tabla. Devuelve None si no encaja."""
    best = None
    for i, row in enumerate(rows[:25]):
        mapping = _map_headers(row)
        score = _score(mapping)
        if score >= 15 and (best is None or score > best[0]):
            best = (score, i, mapping)
    if not best:
        return None
    _, header_idx, mapping = best
    raw = _rows_to_frame(rows, header_idx, mapping)
    if raw.empty:
        return None
    return _normalize(raw, source_name)


def _normalize(raw: pd.DataFrame, source_name: str) -> pd.DataFrame:
    out = pd.DataFrame(index=raw.index)
    num = lambda col: raw[col].map(to_number) if col in raw else pd.Series(np.nan, index=raw.index)

    stake, payout, profit = num('stake'), num('payout'), num('profit')
    has_trade_cols = 'stake' in raw and 'payout' in raw
    if has_trade_cols:
        profit = profit.where(profit.notna(), payout - stake) if 'profit' in raw else payout - stake
    out['stake'] = stake
    out['payout'] = payout
    out['profit'] = profit
    pct = num('payout_pct')
    out['payout_pct'] = pct.where(pct.isna() | (pct > 1.5), pct * 100)  # 0.93 -> 93

    if 'time' in raw:
        out['time'] = _to_datetime(raw['time'])
    else:
        out['time'] = pd.NaT
    out['close_time'] = _to_datetime(raw['close_time']) if 'close_time' in raw else pd.NaT

    # Exportaciones de W-T-F sin fecha por fila: semana + día
    if out['time'].isna().all() and 'day' in raw and 'week' in raw:
        weeks = _to_datetime(raw['week'])
        offsets = raw['day'].map(lambda d: _day_index(d))
        out['time'] = [w + timedelta(days=o) if pd.notna(w) and o is not None else pd.NaT
                       for w, o in zip(weeks, offsets)]

    out['asset'] = raw['asset'].map(lambda v: str(v).strip() if v is not None else '') if 'asset' in raw else ''
    out['direction'] = raw['direction'].map(_clean_direction) if 'direction' in raw else ''
    out['duration'] = raw['duration'].map(lambda v: str(v).strip() if v else '') if 'duration' in raw else ''
    out['id'] = raw['id'].map(lambda v: str(v).strip() if v is not None else '') if 'id' in raw else ''
    out['source'] = source_name

    out = out[out['profit'].notna() & out['time'].notna()].copy()
    kind = KIND_TRADES if (has_trade_cols or out['direction'].astype(bool).any()) else KIND_DAYS
    if kind == KIND_DAYS:
        out = out[out['profit'].abs() > EPS]  # días sin operar
    out['outcome'] = np.where(out['profit'] > EPS, OUT_WIN, np.where(out['profit'] < -EPS, OUT_LOSS, OUT_DRAW))
    out.attrs['kind'] = kind
    return out[COLUMNS]


def _day_index(value):
    n = _norm(value)
    names = [[_norm(d) for d in WTF_DAYS],
             ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']]
    for lst in names:
        if n in lst:
            return lst.index(n)
    return None


# ---------------------------------------------------------------- JSON
def _frame_from_json(path):
    with open(path, 'r', encoding='utf-8-sig') as f:
        payload = json.load(f)
    rows = []
    name = os.path.basename(path)
    if isinstance(payload, dict) and isinstance(payload.get('weeks'), list):  # exportación W-T-F
        for week in payload['weeks']:
            start = _parse_date(week.get('week_start_date'))
            for i, d in enumerate(week.get('days', [])):
                date = _parse_date(d.get('date')) or (start + timedelta(days=i) if start else None)
                rows.append((date, d.get('pair', ''), d.get('duration', ''), d.get('amount', 0)))
    elif isinstance(payload, dict) and isinstance(payload.get('data'), dict):  # semana guardada
        start = _parse_date(payload.get('week_start_date'))
        for day, info in payload['data'].items():
            idx = _day_index(day)
            if start is None or idx is None or not isinstance(info, dict):
                continue
            rows.append((start + timedelta(days=idx), info.get('pair', ''), info.get('duration', ''),
                         info.get('amount', 0)))
    elif isinstance(payload, list):  # lista genérica de objetos
        return _frame_from_table([list(payload[0].keys())] + [list(r.values()) for r in payload], name) \
            if payload and isinstance(payload[0], dict) else None
    if not rows:
        return None
    raw = pd.DataFrame(rows, columns=['time', 'asset', 'duration', 'profit'])
    raw['time'] = pd.to_datetime(raw['time'])
    return _normalize(raw, name)


def _parse_date(value):
    try:
        return datetime.fromisoformat(str(value)[:10]) if value else None
    except ValueError:
        return None


# ---------------------------------------------------------------- API pública
def load_file(path: str) -> pd.DataFrame:
    """Leer un archivo y devolver el DataFrame normalizado (attrs: kind, source_type, sheet)."""
    if not os.path.isfile(path):
        raise ImportError_(f'No se encontró el archivo: {path}')
    if os.path.splitext(path)[1].lower() == '.json':
        frame = _frame_from_json(path)
        if frame is None or frame.empty:
            raise ImportError_('El JSON no contiene semanas ni operaciones reconocibles.')
        frame.attrs.update(source_type=SOURCE_WTF, sheet='')
        return frame

    candidates = []
    for sheet, rows in _read_tables(path):
        frame = _frame_from_table(rows, os.path.basename(path))
        if frame is not None and not frame.empty:
            candidates.append((sheet, frame))
    if not candidates:
        raise ImportError_('No se encontró ninguna tabla con fecha y resultado.\n'
                           'Se necesita una columna de fecha y otra de resultado '
                           '(o de monto invertido + ingreso).')
    # Preferir operaciones individuales; si no, la hoja con más filas (p. ej. "Detalle")
    sheet, frame = max(candidates, key=lambda c: (c[1].attrs['kind'] == KIND_TRADES, len(c[1])))
    frame.attrs['sheet'] = sheet
    frame.attrs['source_type'] = SOURCE_BROKER if frame.attrs['kind'] == KIND_TRADES else (
        SOURCE_WTF if _looks_like_wtf(frame) else SOURCE_GENERIC)
    return frame


def _looks_like_wtf(frame):
    return frame['direction'].eq('').all() and frame['stake'].isna().all()


def load_files(paths):
    """Combinar varios archivos (sin duplicar operaciones con el mismo ID). Devuelve (df, errores)."""
    frames, errors = [], []
    for path in paths:
        try:
            frames.append(load_file(path))
        except ImportError_ as e:
            errors.append((os.path.basename(path), str(e)))
        except Exception as e:  # archivo dañado, bloqueado, etc.
            errors.append((os.path.basename(path), f'{type(e).__name__}: {e}'))
    if not frames:
        return None, errors
    kinds = {f.attrs['kind'] for f in frames}
    sources = {f.attrs.get('source_type') for f in frames}
    df = pd.concat(frames, ignore_index=True)
    with_id = df['id'].astype(str).str.len() > 0
    df = pd.concat([df[with_id].drop_duplicates('id'), df[~with_id]], ignore_index=True)
    df = df.sort_values('time', kind='stable').reset_index(drop=True)
    df.attrs['kind'] = KIND_TRADES if kinds == {KIND_TRADES} else KIND_DAYS
    df.attrs['source_type'] = sources.pop() if len(sources) == 1 else SOURCE_GENERIC
    df.attrs['files'] = [os.path.basename(p) for p in paths]
    return df, errors


def clean_asset(name: str) -> str:
    """'NZD/CAD (OTC)' -> 'NZD/CAD' (para el par de la semana)."""
    return re.sub(r'\s*\(.*?\)\s*', '', str(name or '')).strip()


# ---------------------------------------------------------------- análisis
def _streaks(outcomes):
    best_win = best_loss = cur_win = cur_loss = 0
    for o in outcomes:
        if o == OUT_WIN:
            cur_win, cur_loss = cur_win + 1, 0
        elif o == OUT_LOSS:
            cur_win, cur_loss = 0, cur_loss + 1
        best_win, best_loss = max(best_win, cur_win), max(best_loss, cur_loss)
    return best_win, best_loss


def _group(df, key):
    g = df.groupby(key, sort=True)
    out = pd.DataFrame({
        'ops': g.size(),
        'wins': g['outcome'].apply(lambda s: int((s == OUT_WIN).sum())),
        'losses': g['outcome'].apply(lambda s: int((s == OUT_LOSS).sum())),
        'staked': g['stake'].sum(min_count=1),
        'net': g['profit'].sum(),
    })
    decided = out['wins'] + out['losses']
    out['win_rate'] = np.where(decided > 0, out['wins'] / decided.replace(0, 1) * 100, 0.0)
    out['avg'] = out['net'] / out['ops']
    return out


def analyze(df: pd.DataFrame, initial_capital: float = 0.0) -> dict:
    """Estadísticas completas del conjunto (ya filtrado)."""
    kind = df.attrs.get('kind', KIND_TRADES)
    n = len(df)
    profit = df['profit']
    wins, losses = int((df['outcome'] == OUT_WIN).sum()), int((df['outcome'] == OUT_LOSS).sum())
    draws = n - wins - losses
    gross_win = float(profit[profit > 0].sum())
    gross_loss = float(-profit[profit < 0].sum())
    staked = float(df['stake'].sum(min_count=1)) if df['stake'].notna().any() else None
    net = float(profit.sum())

    cumulative = profit.cumsum()
    equity = initial_capital + cumulative
    peak = np.maximum.accumulate(np.concatenate([[initial_capital], equity.values]))[1:] if n else np.array([])
    drawdown = (equity.values - peak) if n else np.array([])
    max_dd = float(-drawdown.min()) if n else 0.0
    dd_idx = int(drawdown.argmin()) if n else 0
    max_dd_pct = (max_dd / peak[dd_idx] * 100) if n and peak[dd_idx] > EPS else None

    dates = df['time'].dt.normalize()
    by_day = _group(df.assign(date=dates), 'date')
    by_day['cumulative'] = by_day['net'].cumsum()
    by_asset = _group(df.assign(asset_key=df['asset'].replace('', '—')), 'asset_key').sort_values('net')
    by_weekday = _group(df.assign(wd=df['time'].dt.weekday), 'wd')
    by_hour = _group(df.assign(hour=df['time'].dt.hour), 'hour') if kind == KIND_TRADES else None
    by_direction = (_group(df[df['direction'] != ''], 'direction')
                    if (df['direction'] != '').any() else None)
    by_stake = (_group(df[df['stake'].notna()], 'stake') if kind == KIND_TRADES and df['stake'].notna().any()
                else None)

    best_win_streak, best_loss_streak = _streaks(df['outcome'].tolist())
    decided = wins + losses
    trading_days = len(by_day)
    return {
        'kind': kind,
        'count': n,
        'wins': wins, 'losses': losses, 'draws': draws,
        'win_rate': (wins / decided * 100) if decided else 0.0,
        'net': net,
        'gross_win': gross_win, 'gross_loss': gross_loss,
        'profit_factor': (gross_win / gross_loss) if gross_loss > EPS else None,
        'avg_op': net / n if n else 0.0,
        'avg_win': float(profit[profit > 0].mean()) if wins else 0.0,
        'avg_loss': float(profit[profit < 0].mean()) if losses else 0.0,
        'best': float(profit.max()) if n else 0.0,
        'worst': float(profit.min()) if n else 0.0,
        'staked': staked,
        'avg_stake': float(df['stake'].mean()) if staked is not None else None,
        'roi': (net / staked * 100) if staked else None,
        'avg_payout_pct': float(df['payout_pct'].mean()) if df['payout_pct'].notna().any() else None,
        'initial_capital': initial_capital,
        'growth_pct': (net / initial_capital * 100) if initial_capital > EPS else None,
        'max_drawdown': max_dd, 'max_drawdown_pct': max_dd_pct,
        'win_streak': best_win_streak, 'loss_streak': best_loss_streak,
        'trading_days': trading_days,
        'avg_day': net / trading_days if trading_days else 0.0,
        'ops_per_day': n / trading_days if trading_days else 0.0,
        'best_day': (by_day['net'].idxmax(), float(by_day['net'].max())) if trading_days else None,
        'worst_day': (by_day['net'].idxmin(), float(by_day['net'].min())) if trading_days else None,
        'green_days': int((by_day['net'] > EPS).sum()),
        'first': df['time'].min() if n else None,
        'last': df['time'].max() if n else None,
        'equity': equity.values, 'drawdown': drawdown,
        'by_day': by_day, 'by_asset': by_asset, 'by_weekday': by_weekday, 'by_hour': by_hour,
        'by_direction': by_direction, 'by_stake': by_stake,
    }


def week_totals(df: pd.DataFrame, week_start, day_names):
    """Resultado neto y activo más operado de cada día de la semana indicada.

    Devuelve {día_modelo: {'amount', 'ops', 'pair', 'date'}} solo para días con operaciones.
    """
    if week_start is None or df is None or df.empty:
        return {}
    start = pd.Timestamp(week_start).normalize()
    result = {}
    for idx, day in enumerate(day_names):
        date = start + pd.Timedelta(days=idx)
        rows = df[df['time'].dt.normalize() == date]
        if rows.empty:
            continue
        assets = rows['asset'][rows['asset'] != '']
        result[day] = {
            'amount': round(float(rows['profit'].sum()), 2),
            'ops': len(rows),
            'pair': clean_asset(assets.value_counts().idxmax()) if not assets.empty else '',
            'date': date.date(),
        }
    return result


def export_analysis_excel(df: pd.DataFrame, stats: dict, path: str, labels: dict) -> None:
    """Guardar el análisis (KPIs, resumen diario, por activo y operaciones) en un .xlsx con gráficos."""
    import xlsxwriter
    wb = xlsxwriter.Workbook(path)
    accent, green, red = '#6246EA', '#0F9F6E', '#E11D48'
    f = {
        'title': wb.add_format({'bold': True, 'font_size': 18, 'font_color': accent}),
        'sub': wb.add_format({'italic': True, 'font_color': '#5B6B86'}),
        'header': wb.add_format({'bold': True, 'font_color': 'white', 'bg_color': accent, 'border': 1,
                                 'align': 'center'}),
        'label': wb.add_format({'bold': True, 'bg_color': '#F4F7FC', 'border': 1, 'border_color': '#DDE4F0'}),
        'text': wb.add_format({'border': 1, 'border_color': '#DDE4F0'}),
        'num': wb.add_format({'border': 1, 'border_color': '#DDE4F0', 'num_format': '0.##'}),
        'money': wb.add_format({'border': 1, 'border_color': '#DDE4F0', 'num_format': '$#,##0.00;[Red]-$#,##0.00'}),
        'signed': wb.add_format({'border': 1, 'border_color': '#DDE4F0', 'bold': True,
                                 'num_format': '[Color10]+$#,##0.00;[Red]-$#,##0.00;$0.00'}),
        'pct': wb.add_format({'border': 1, 'border_color': '#DDE4F0', 'num_format': '0.0"%"'}),
        'date': wb.add_format({'border': 1, 'border_color': '#DDE4F0', 'num_format': 'dd/mm/yyyy'}),
        'datetime': wb.add_format({'border': 1, 'border_color': '#DDE4F0', 'num_format': 'dd/mm/yyyy hh:mm:ss'}),
    }
    L = labels.get

    ws = wb.add_worksheet(L('summary', 'Resumen')[:31])
    ws.hide_gridlines(2)
    ws.write(0, 0, L('title', 'Análisis de operaciones'), f['title'])
    ws.write(1, 0, L('subtitle', ''), f['sub'])
    for i, (label, value, fmt) in enumerate(labels.get('kpis', [])):
        ws.write(3 + i, 0, label, f['label'])
        if value is None:
            ws.write(3 + i, 1, '—', f['text'])
        elif isinstance(value, str):
            ws.write(3 + i, 1, value, f['text'])
        else:
            ws.write_number(3 + i, 1, float(value), f[fmt])
    ws.set_column(0, 0, 30)
    ws.set_column(1, 1, 18)

    by_day = stats['by_day']
    ds = wb.add_worksheet(L('by_day', 'Por día')[:31])
    heads = labels.get('day_headers', ['Fecha', 'Ops', 'Ganadas', 'Perdidas', '% acierto', 'Invertido', 'Neto', 'Acumulado'])
    for c, h in enumerate(heads):
        ds.write(0, c, h, f['header'])
    for r, (date, row) in enumerate(by_day.iterrows(), start=1):
        ds.write_datetime(r, 0, pd.Timestamp(date).to_pydatetime(), f['date'])
        ds.write_number(r, 1, int(row['ops']), f['num'])
        ds.write_number(r, 2, int(row['wins']), f['num'])
        ds.write_number(r, 3, int(row['losses']), f['num'])
        ds.write_number(r, 4, float(row['win_rate']), f['pct'])
        if pd.notna(row['staked']):
            ds.write_number(r, 5, float(row['staked']), f['money'])
        else:
            ds.write(r, 5, '—', f['text'])
        ds.write_number(r, 6, float(row['net']), f['signed'])
        ds.write_number(r, 7, float(row['cumulative']), f['money'])
    last = len(by_day)
    ds.set_column(0, 7, 13)
    ds.freeze_panes(1, 0)
    if last:
        chart = wb.add_chart({'type': 'column'})
        chart.add_series({'name': heads[6], 'categories': [ds.get_name(), 1, 0, last, 0],
                          'values': [ds.get_name(), 1, 6, last, 6],
                          'points': [{'fill': {'color': green if v >= 0 else red}} for v in by_day['net']]})
        chart.set_title({'name': L('chart_daily', 'Resultado por día')})
        chart.set_legend({'none': True})
        chart.set_y_axis({'num_format': '$#,##0'})
        ds.insert_chart(1, 9, chart, {'x_scale': 1.3, 'y_scale': 1.1})
        line = wb.add_chart({'type': 'line'})
        line.add_series({'name': heads[7], 'categories': [ds.get_name(), 1, 0, last, 0],
                         'values': [ds.get_name(), 1, 7, last, 7], 'line': {'color': accent, 'width': 2.25}})
        line.set_title({'name': L('chart_equity', 'Evolución acumulada')})
        line.set_legend({'none': True})
        line.set_y_axis({'num_format': '$#,##0'})
        ds.insert_chart(18, 9, line, {'x_scale': 1.3, 'y_scale': 1.1})

    by_asset = stats['by_asset'].sort_values('net', ascending=False)
    as_ = wb.add_worksheet(L('by_asset', 'Por activo')[:31])
    for c, h in enumerate([L('asset', 'Activo')] + heads[1:7]):
        as_.write(0, c, h, f['header'])
    for r, (asset, row) in enumerate(by_asset.iterrows(), start=1):
        as_.write(r, 0, str(asset), f['text'])
        as_.write_number(r, 1, int(row['ops']), f['num'])
        as_.write_number(r, 2, int(row['wins']), f['num'])
        as_.write_number(r, 3, int(row['losses']), f['num'])
        as_.write_number(r, 4, float(row['win_rate']), f['pct'])
        as_.write(r, 5, float(row['staked']) if pd.notna(row['staked']) else '—',
                  f['money'] if pd.notna(row['staked']) else f['text'])
        as_.write_number(r, 6, float(row['net']), f['signed'])
    as_.set_column(0, 0, 20)
    as_.set_column(1, 6, 13)

    os_ = wb.add_worksheet(L('operations', 'Operaciones')[:31])
    op_heads = labels.get('op_headers', ['Fecha', 'Activo', 'Dirección', 'Monto', 'Ingreso', 'Resultado', 'Estado'])
    for c, h in enumerate(op_heads):
        os_.write(0, c, h, f['header'])
    outcome_names = labels.get('outcomes', {})
    direction_names = labels.get('directions', {})
    for r, row in enumerate(df.itertuples(index=False), start=1):
        os_.write_datetime(r, 0, row.time.to_pydatetime(), f['datetime'])
        os_.write(r, 1, row.asset, f['text'])
        os_.write(r, 2, direction_names.get(row.direction, row.direction), f['text'])
        for c, v in ((3, row.stake), (4, row.payout)):
            if pd.notna(v):
                os_.write_number(r, c, float(v), f['money'])
            else:
                os_.write(r, c, '—', f['text'])
        os_.write_number(r, 5, float(row.profit), f['signed'])
        os_.write(r, 6, outcome_names.get(row.outcome, row.outcome), f['text'])
    os_.autofilter(0, 0, max(1, len(df)), len(op_heads) - 1)
    os_.freeze_panes(1, 0)
    os_.set_column(0, 0, 20)
    os_.set_column(1, 6, 13)
    wb.close()
