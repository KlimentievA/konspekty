"""Hub — логотип 2.0: классическая антиква «H» по центру, плоско, без точки и теней; изумрудный фон."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glyph import placed
SER = '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'
CREAM = '#F4F1E8'
def defs(u):
    return (f'<defs><linearGradient id="g{u}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#13A06E"/><stop offset="1" stop-color="#04452F"/></linearGradient>'
            f'<radialGradient id="l{u}" cx=".28" cy=".22" r=".75"><stop offset="0" stop-color="#3FE0A6" stop-opacity=".45"/><stop offset="1" stop-color="#3FE0A6" stop-opacity="0"/></radialGradient></defs>')
def bg(u, rx): return f'<rect width="512" height="512" rx="{rx}" fill="url(#g{u})"/><rect width="512" height="512" rx="{rx}" fill="url(#l{u})"/>'
def mark(color=CREAM, h=218): return placed(SER, h=h, color=color)
def svg(body, size=512): return f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 512 512">{body}</svg>'
def scaled(inner, k): return f'<g transform="translate(256 256) scale({k}) translate(-256 -256)">{inner}</g>'
U = 'h'
ROUNDED = svg(defs(U) + bg(U, 113) + mark())
FULL = svg(defs(U) + bg(U, 0) + mark())
MASKABLE = svg(defs(U) + bg(U, 0) + scaled(mark(), 0.8))
ANDROID_BG = svg(defs(U) + bg(U, 0))
ANDROID_FG = svg(scaled(mark(), 0.7))          # видимая часть адаптивной иконки — 72 из 108 dp
ANDROID_MONO = svg(scaled(mark('#FFFFFF'), 0.7))
CIRCLE = svg(defs(U) + '<circle cx="256" cy="256" r="256" fill="url(#gh)"/><circle cx="256" cy="256" r="256" fill="url(#lh)"/>' + scaled(mark(), 0.9))
if __name__ == '__main__':
    for n, s in [('rounded', ROUNDED), ('full', FULL), ('maskable', MASKABLE), ('a_bg', ANDROID_BG), ('a_fg', ANDROID_FG), ('a_mono', ANDROID_MONO), ('circle', CIRCLE)]:
        open(n + '.svg', 'w').write(s)
