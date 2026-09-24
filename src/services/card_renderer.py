"""
Renderizado local de la tarjeta de resultados con Pillow.

Garantiza que los valores financieros aparezcan exactamente como se escriben
(la IA puede equivocarse con el texto). Gratuito, sin conexión e instantáneo.
Estilo: fintech oscuro, glassmorphism, fondo de velas desenfocado y neón verde.
"""

import io
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
GREEN = (0, 230, 150)
RED = (255, 64, 96)
QUOTEX_RED = (238, 42, 60)
WHITE = (245, 247, 252)
GREY = (140, 150, 170)

_FONT_DIRS = [os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts'), '/usr/share/fonts/truetype/dejavu']
_FONT_FILES = {
    'black': ['seguibl.ttf', 'segoeuib.ttf', 'arialbd.ttf', 'DejaVuSans-Bold.ttf'],
    'bold': ['segoeuib.ttf', 'arialbd.ttf', 'DejaVuSans-Bold.ttf'],
    'semibold': ['seguisb.ttf', 'segoeuib.ttf', 'arialbd.ttf', 'DejaVuSans-Bold.ttf'],
    'regular': ['segoeui.ttf', 'arial.ttf', 'DejaVuSans.ttf'],
}


def _font(weight, size):
    for d in _FONT_DIRS:
        for name in _FONT_FILES[weight]:
            path = os.path.join(d, name)
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _fit_font(draw, text, weight, size, max_width):
    font = _font(weight, size)
    while size > 20 and draw.textlength(text, font=font) > max_width:
        size -= 4
        font = _font(weight, size)
    return font


def _background():
    """Fondo muy oscuro con velas japonesas desenfocadas y reflejo inferior."""
    bg = Image.new('RGB', (W, H), (6, 8, 14))
    layer = Image.new('RGB', (W, H), (0, 0, 0))
    d = ImageDraw.Draw(layer)
    rnd = random.Random(42)
    price = H * 0.42
    x = -20
    while x < W + 40:
        change = rnd.uniform(-70, 70)
        o, c = price, price + change
        hi, lo = min(o, c) - rnd.uniform(10, 60), max(o, c) + rnd.uniform(10, 60)
        color = (0, 170, 110) if c < o else (200, 40, 70)
        d.line([(x + 14, hi), (x + 14, lo)], fill=color, width=4)
        d.rectangle([x, min(o, c), x + 28, max(o, c)], fill=color)
        price = min(max(c, H * 0.25), H * 0.6)
        x += 46
    layer = layer.filter(ImageFilter.GaussianBlur(9))
    bg = Image.blend(bg, layer, 0.8)
    # Reflejo sobre superficie brillante
    reflection = layer.transpose(Image.FLIP_TOP_BOTTOM).filter(ImageFilter.GaussianBlur(18))
    mask = Image.linear_gradient('L').resize((W, H)).point(lambda v: int(v * 0.25))
    bg.paste(reflection, (0, int(H * 0.2)), mask)
    # Viñeta
    vignette = Image.new('L', (W, H), 0)
    ImageDraw.Draw(vignette).ellipse((-W * 0.4, -H * 0.2, W * 1.4, H * 1.2), fill=255)
    vignette = vignette.filter(ImageFilter.GaussianBlur(160))
    return Image.composite(bg, Image.new('RGB', (W, H), (2, 3, 6)), vignette)


def _glow_text(img, xy, text, font, color, radius=22, strength=2, anchor='mm'):
    glow = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).text(xy, text, font=font, fill=color + (255,), anchor=anchor)
    glow = glow.filter(ImageFilter.GaussianBlur(radius))
    for _ in range(strength):
        img.alpha_composite(glow)
    ImageDraw.Draw(img).text(xy, text, font=font, fill=color + (255,), anchor=anchor)


def _icon_clock(d, cx, cy, r, color):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color, width=5)
    d.line([(cx, cy), (cx, cy - r * 0.55)], fill=color, width=5)
    d.line([(cx, cy), (cx + r * 0.45, cy + r * 0.2)], fill=color, width=5)


def _icon_calendar(d, cx, cy, r, color):
    d.rounded_rectangle((cx - r, cy - r * 0.8, cx + r, cy + r), 6, outline=color, width=5)
    d.line([(cx - r, cy - r * 0.3), (cx + r, cy - r * 0.3)], fill=color, width=5)
    for dx in (-0.45, 0.45):
        d.line([(cx + r * dx, cy - r * 1.05), (cx + r * dx, cy - r * 0.6)], fill=color, width=5)


def _icon_pulse(d, cx, cy, r, color):
    pts = [(cx - r, cy), (cx - r * 0.4, cy), (cx - r * 0.15, cy - r * 0.8), (cx + r * 0.15, cy + r * 0.8),
           (cx + r * 0.4, cy), (cx + r, cy)]
    d.line(pts, fill=color, width=5, joint='curve')


def render_card(asset: str, duration: str, day: str, profit: str, positive: bool = True) -> bytes:
    """Dibujar la tarjeta completa y devolver los bytes PNG."""
    img = _background().convert('RGBA')
    d = ImageDraw.Draw(img)
    accent = GREEN if positive else RED

    # Logo QUOTEX (marca de texto)
    logo_font = _font('black', 84)
    _glow_text(img, (W // 2, 250), 'QUOTEX', logo_font, QUOTEX_RED, radius=18, strength=1)

    # Panel de vidrio con borde y reflejo neón inferior
    x0, y0, x1, y1 = 90, 470, W - 90, 1450
    under = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ImageDraw.Draw(under).rounded_rectangle((x0 + 60, y1 - 30, x1 - 60, y1 + 40), 40, fill=accent + (150,))
    img.alpha_composite(under.filter(ImageFilter.GaussianBlur(60)))
    blurred = img.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(28))
    img.paste(blurred, (x0, y0))
    glass = Image.new('RGBA', img.size, (0, 0, 0, 0))
    g = ImageDraw.Draw(glass)
    g.rounded_rectangle((x0, y0, x1, y1), 56, fill=(30, 38, 58, 150), outline=(255, 255, 255, 46), width=3)
    g.line([(x0 + 70, y1 - 1), (x1 - 70, y1 - 1)], fill=accent + (255,), width=5)
    g.line([(x0 + 60, y0 + 270), (x1 - 60, y0 + 270)], fill=(255, 255, 255, 34), width=2)  # separador
    img.alpha_composite(glass)
    d = ImageDraw.Draw(img)

    # Fila del activo: icono circular con dos mitades (bandera combinada)
    cx, cy, r = x0 + 120, y0 + 140, 58
    d.pieslice((cx - r, cy - r, cx + r, cy + r), 90, 270, fill=(0, 51, 153))
    d.pieslice((cx - r, cy - r, cx + r, cy + r), 270, 90, fill=(178, 34, 52))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 255, 180), width=4)
    asset_font = _fit_font(d, asset, 'bold', 76, x1 - (cx + r + 40) - 60)
    d.text((cx + r + 36, cy - 12), asset, font=asset_font, fill=WHITE, anchor='ls')
    d.text((cx + r + 38, cy + 44), 'Asset', font=_font('regular', 38), fill=GREY, anchor='ls')

    # Métricas
    my = y0 + 360
    col = (x1 - x0) // 3
    metric_font = _font('semibold', 36)
    value_font = _font('bold', 40)
    items = [(_icon_clock, 'Duration', duration), (_icon_calendar, 'Day', day), (_icon_pulse, '', '')]
    for i, (icon, label, value) in enumerate(items):
        mx = x0 + col * i + col // 2
        icon(d, mx, my - 20, 30, accent)
        if label:
            d.text((mx, my + 50), label, font=metric_font, fill=GREY, anchor='mm')
            vf = _fit_font(d, value, 'bold', 40, col - 30)
            d.text((mx, my + 102), value, font=vf, fill=WHITE, anchor='mm')
        else:
            d.text((mx, my + 50), 'Status', font=metric_font, fill=GREY, anchor='mm')
            d.text((mx, my + 102), 'Closed', font=value_font, fill=WHITE, anchor='mm')

    # Total profit
    ty = y0 + 640
    label_font = _font('semibold', 40)
    tw = d.textlength('TOTAL PROFIT', font=label_font)
    d.text((W // 2 - 22, ty), 'TOTAL PROFIT', font=label_font, fill=GREY, anchor='mm')
    ix = W // 2 + tw / 2 + 8
    d.ellipse((ix - 17, ty - 17, ix + 17, ty + 17), outline=GREY, width=4)
    d.text((ix, ty + 1), 'i', font=_font('bold', 26), fill=GREY, anchor='mm')
    profit_font = _fit_font(d, profit, 'black', 170, x1 - x0 - 100)
    _glow_text(img, (W // 2, ty + 175), profit, profit_font, accent, radius=26, strength=2)

    out = io.BytesIO()
    img.convert('RGB').save(out, 'PNG', optimize=True)
    return out.getvalue()
