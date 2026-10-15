"""Hub — логотип 3.1. Знак — строчная «h» в тонком мятном кольце; сама h, нарисованная одной толщиной линии (стойка + арка), без шрифтов.
Те же правила строят «u» и «b», так что значок + «ub» читаются как hub."""
W = 58          # толщина линии
R = 68          # радиус арки (по средней линии)
XT, BASE, ASC = 203, 392, 99      # верх строчных, базовая линия, верх выносных
def _st(d, c, cap='butt'): return f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{W}" stroke-linecap="{cap}"/>'
def _dot(x, y, c): return f'<circle cx="{x}" cy="{y}" r="{W/2}" fill="{c}"/>'
def h(c, x=0):
    s = x + W/2; cy = XT + W/2 + R
    return (_st(f'M{s} {ASC+W/2}V{BASE}', c) + _dot(s, ASC+W/2, c) +
            _st(f'M{s} {cy}A{R} {R} 0 0 1 {s+2*R} {cy}V{BASE}', c)), W + 2*R
def u(c, x=0):
    s = x + W/2; cy = BASE - W/2 - R; top = XT + W/2
    return (_st(f'M{s} {top}V{cy}A{R} {R} 0 0 0 {s+2*R} {cy}', c) + _st(f'M{s+2*R} {top}V{BASE}', c) +
            _dot(s, top, c) + _dot(s+2*R, top, c)), W + 2*R
def b(c, x=0):
    s = x + W/2; r = (BASE - XT - W)/2; cy = XT + W/2 + r
    return (_st(f'M{s} {ASC+W/2}V{BASE}', c) + _dot(s, ASC+W/2, c) +
            f'<circle cx="{s+r}" cy="{cy}" r="{r}" fill="none" stroke="{c}" stroke-width="{W}"/>'), W + r*2 + 0
GAP = 34
def word(c, letters='hub'):
    """слово целиком; возвращает (svg-фрагмент, ширина) в координатах высоты ASC…BASE"""
    out, x = '', 0
    for ch in letters:
        f, w = {'h': h, 'u': u, 'b': b}[ch](c, x); out += f; x += w + GAP
    return out, x - GAP
RING = '#BDF7DF'   # мятное кольцо вокруг h: hub — точка, где всё сходится
def mark(c='#FFFFFF', ring=None):
    """знак для значка: h в тонком кольце, по центру 512×512 (h чуть правее — у неё тяжёлая левая стойка)"""
    f, w = h(c)
    k = 0.68
    glyph = f'<g transform="translate({256 + 5} 256) scale({k}) translate({-w/2} {-(ASC + BASE)/2})">{f}</g>'
    return f'<circle cx="256" cy="256" r="148" fill="none" stroke="{ring or RING}" stroke-width="20"/>' + glyph
GRAD = ('#22D39A', '#05704C')
def defs(u):
    a, b_ = GRAD
    return (f'<defs><linearGradient id="g{u}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b_}"/></linearGradient>'
            f'<radialGradient id="l{u}" cx=".5" cy="0" r=".9"><stop offset="0" stop-color="#fff" stop-opacity=".18"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient></defs>')
def bg(u, rx): return f'<rect width="512" height="512" rx="{rx}" fill="url(#g{u})"/><rect width="512" height="512" rx="{rx}" fill="url(#l{u})"/>'
def svg(body, size=512): return f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 512 512">{body}</svg>'
def scaled(inner, k): return f'<g transform="translate(256 256) scale({k}) translate(-256 -256)">{inner}</g>'
U = 'h'
ROUNDED = svg(defs(U) + bg(U, 113) + mark())
FULL = svg(defs(U) + bg(U, 0) + mark())
MASKABLE = svg(defs(U) + bg(U, 0) + scaled(mark(), 0.86))
ANDROID_BG = svg(defs(U) + bg(U, 0))
ANDROID_FG = svg(scaled(mark(), 0.66))          # видимая часть адаптивной иконки — 72 из 108 dp
ANDROID_MONO = svg(scaled(mark('#FFFFFF', '#FFFFFF'), 0.66))
CIRCLE = svg(defs(U) + '<circle cx="256" cy="256" r="256" fill="url(#gh)"/><circle cx="256" cy="256" r="256" fill="url(#lh)"/>' + scaled(mark(), 0.96))
def wordmark(c='#25221C', letters='ub', first=None):
    """first — цвет первой буквы (h в фирменном изумруде)"""
    f, w = word(c, letters); H = BASE - ASC
    if first:
        f0, _ = word(first, letters[0]); f1, _ = word(c, letters)
        f = f0 + f1[len(word(c, letters[0])[0]):]
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {ASC} {w:.0f} {H}" width="{w:.0f}" height="{H}">{f}</svg>'
if __name__ == '__main__':
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    for n, s in [('rounded', ROUNDED), ('full', FULL), ('maskable', MASKABLE), ('a_bg', ANDROID_BG), ('a_fg', ANDROID_FG),
                 ('a_mono', ANDROID_MONO), ('circle', CIRCLE), ('ub', wordmark()), ('ub-light', wordmark('#ECE8DD')), ('hub-word', wordmark(letters='hub', first='#0A9466')), ('hub-word-dark', wordmark('#ECE8DD', letters='hub', first='#2FD69C'))]:
        open(f'{out}/{n}.svg', 'w').write(s)
