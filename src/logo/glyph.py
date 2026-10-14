from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
def glyph(path, ch='H'):
    f = TTFont(path); gs = f.getGlyphSet(); n = f.getBestCmap()[ord(ch)]
    p = SVGPathPen(gs); gs[n].draw(p); b = BoundsPen(gs); gs[n].draw(b)
    return p.getCommands(), b.bounds
def placed(path, cx=256, cy=256, h=200, color='#F4F1E8', ch='H'):
    d, (x0, y0, x1, y1) = glyph(path, ch)
    k = h / (y1 - y0); w = (x1 - x0) * k
    # шрифт: y вверх → переворачиваем
    return f'<path d="{d}" fill="{color}" transform="translate({cx - w/2 - x0*k:.2f} {cy + h/2 + y0*k:.2f}) scale({k:.5f} {-k:.5f})"/>'
