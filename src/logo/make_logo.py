import sys, os
sys.path.insert(0, '.')
from logos import serifH
CREAM = '#F4F1E8'
def defs(u):
    return (f'<defs><linearGradient id="g{u}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#13A06E"/><stop offset="1" stop-color="#04452F"/></linearGradient>'
            f'<radialGradient id="l{u}" cx=".28" cy=".22" r=".75"><stop offset="0" stop-color="#3FE0A6" stop-opacity=".55"/><stop offset="1" stop-color="#3FE0A6" stop-opacity="0"/></radialGradient>'
            f'<radialGradient id="d{u}" cx=".35" cy=".35"><stop offset="0" stop-color="#FFF0B8"/><stop offset=".55" stop-color="#E2B53E"/><stop offset="1" stop-color="#A47A12"/></radialGradient>'
            f'<filter id="b{u}" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="14"/></filter>'
            f'<filter id="s{u}" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="9" stdDeviation="11" flood-color="#00140C" flood-opacity=".55"/></filter></defs>')
def bg(u, rx): return f'<rect width="512" height="512" rx="{rx}" fill="url(#g{u})"/><rect width="512" height="512" rx="{rx}" fill="url(#l{u})"/>'
def mark(u, color=CREAM, dot=True, shadow=True, mono=False):
    h = serifH(color, x=118)
    out = f'<g filter="url(#s{u})">{h}</g>' if shadow else h
    if dot:
        out += (f'<circle cx="378" cy="352" r="30" fill="{color}"/>' if mono else
                f'<circle cx="378" cy="352" r="34" fill="#E2B53E" opacity=".5" filter="url(#b{u})"/><circle cx="378" cy="352" r="30" fill="url(#d{u})"/>')
    return out
def svg(body, size=512, vb='0 0 512 512'):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="{vb}">{body}</svg>'
def scaled(inner, k):   # уменьшить содержимое к центру (безопасная зона маскируемых иконок)
    return f'<g transform="translate(256 256) scale({k}) translate(-256 -256)">{inner}</g>'
U = 'h'
ROUNDED = svg(defs(U) + bg(U, 113) + mark(U))
FULL = svg(defs(U) + bg(U, 0) + mark(U))
MASKABLE = svg(defs(U) + bg(U, 0) + scaled(mark(U), 0.8))
ANDROID_BG = svg(defs(U) + bg(U, 0))
ANDROID_FG = svg(defs(U) + scaled(mark(U), 0.92))
ANDROID_MONO = svg(defs(U) + scaled(mark(U, '#FFFFFF', shadow=False, mono=True), 0.92))
CIRCLE = svg(defs(U) + '<circle cx="256" cy="256" r="256" fill="url(#gh)"/><circle cx="256" cy="256" r="256" fill="url(#lh)"/>' + scaled(mark(U), 0.86))
if __name__ == '__main__':
    for n, s in [('rounded', ROUNDED), ('full', FULL), ('maskable', MASKABLE), ('a_bg', ANDROID_BG), ('a_fg', ANDROID_FG), ('a_mono', ANDROID_MONO), ('circle', CIRCLE)]:
        open(n + '.svg', 'w').write(s)
