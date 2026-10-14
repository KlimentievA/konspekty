BG='#F4F1E8';RED='#A93D28';GRN='#1F6B57';INK='#25221C';GOLD='#C9A227';DARK='#171611'
def serifH(c, x=136, y=136, h=240, sw=54, w=200):
    """H с засечками: две стойки, перекладина, засечки сверху и снизу (рисуется фигурами, без шрифта)."""
    xr = x + w - sw; s = 30; t = 16
    r = ''
    for xs in (x, xr):
        r += f'<rect x="{xs}" y="{y}" width="{sw}" height="{h}" fill="{c}"/>'
        r += f'<rect x="{xs-s}" y="{y}" width="{sw+2*s}" height="{t}" rx="3" fill="{c}"/>'
        r += f'<rect x="{xs-s}" y="{y+h-t}" width="{sw+2*s}" height="{t}" rx="3" fill="{c}"/>'
    r += f'<rect x="{x+sw-2}" y="{y+h*0.45}" width="{w-2*sw+4}" height="{h*0.11}" fill="{c}"/>'
    return r
def sansH(c1, c2, cb, x=150, y=136, h=240, sw=60, w=196):
    xr = x + w - sw
    return (f'<rect x="{x}" y="{y}" width="{sw}" height="{h}" rx="{sw/2}" fill="{c1}"/>'
            f'<rect x="{xr}" y="{y}" width="{sw}" height="{h}" rx="{sw/2}" fill="{c2}"/>'
            f'<rect x="{x+sw/2}" y="{y+h/2-26}" width="{w-sw}" height="52" rx="26" fill="{cb}"/>')
L = {}
# A: классика — H с засечками и красная точка, бежевый фон
L['A · Классика'] = (BG, serifH(INK, x=118) + f'<circle cx="378" cy="352" r="30" fill="{RED}"/>')
# B: тёмная — светлая H и красная точка на тёмном фоне
L['B · Тёмная'] = (DARK, serifH('#F4F1E8', x=118) + f'<circle cx="378" cy="352" r="30" fill="#E8886B"/>')
# C: зелёная — бежевая H и золотая точка на зелёном (финансовый «банк»)
L['C · Зелёная'] = (GRN, serifH('#F4F1E8', x=118) + f'<circle cx="378" cy="352" r="30" fill="{GOLD}"/>')
# D: в круге — H в тонком кольце, точка на кольце
L['D · В круге'] = (BG, f'<circle cx="256" cy="256" r="178" fill="none" stroke="{INK}" stroke-width="16"/>' + serifH(INK, x=146, y=166, h=180, sw=42, w=200) + f'<circle cx="382" cy="382" r="26" fill="{RED}"/>')
# E: мягкая — округлая H из двух цветов (учёба + финансы) и точка
L['E · Мягкая'] = (BG, sansH(RED, GRN, INK, x=128) + f'<circle cx="384" cy="350" r="32" fill="{INK}"/>')
# F: точка-узел — перекладина H стала точкой-центром
L['F · Точка-узел'] = (BG, f'<rect x="148" y="136" width="56" height="240" rx="28" fill="{INK}"/><rect x="308" y="136" width="56" height="240" rx="28" fill="{INK}"/>'
                       f'<rect x="176" y="243" width="160" height="26" rx="13" fill="{INK}"/><circle cx="256" cy="256" r="42" fill="{RED}" stroke="{BG}" stroke-width="12"/>')
