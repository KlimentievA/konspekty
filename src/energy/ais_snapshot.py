#!/usr/bin/env python3
"""Снимок положения танкеров из AIS (aisstream.io, бесплатный ключ) → tankers.json.
Ключ берётся из переменной окружения AISSTREAM_KEY (в GitHub: Settings → Secrets → Actions). Нет ключа — тихо выходим.
Запуск: AISSTREAM_KEY=... python3 src/energy/ais_snapshot.py [секунд_прослушивания]
Тип судна приходит отдельным сообщением (ShipStaticData, раз в ~6 минут), поэтому типы копятся в data/ais_static.json,
а положения сливаются с прошлым снимком: судно живёт на карте, пока не старше MAXAGE."""
import asyncio, json, os, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KEY = os.environ.get('AISSTREAM_KEY', '').strip()
LISTEN = int(sys.argv[1]) if len(sys.argv) > 1 else 240
MAXAGE = 3 * 3600            # положение старше 3 часов не показываем
STATIC_TTL = 14 * 86400
OUT, STATIC = os.path.join(ROOT, 'tankers.json'), os.path.join(ROOT, 'data', 'ais_static.json')

def load(p, d):
    try: return json.load(open(p, encoding='utf-8'))
    except Exception: return d

async def listen(static, pos):
    import websockets
    sub = {'APIKey': KEY, 'BoundingBoxes': [[[-90, -180], [90, 180]]], 'FilterMessageTypes': ['PositionReport', 'ShipStaticData']}
    end, n = time.time() + LISTEN, 0
    async with websockets.connect('wss://stream.aisstream.io/v0/stream', open_timeout=30, max_size=2**22) as ws:
        await ws.send(json.dumps(sub))
        while time.time() < end:
            try: raw = await asyncio.wait_for(ws.recv(), timeout=30)
            except asyncio.TimeoutError: continue
            try: m = json.loads(raw)
            except Exception: continue
            if 'error' in m: sys.exit('AIS: ' + str(m['error']))
            md, t, now = m.get('MetaData') or {}, m.get('MessageType'), int(time.time())
            mmsi = str(md.get('MMSI') or '')
            if not mmsi: continue
            n += 1
            if t == 'ShipStaticData':
                s = (m.get('Message') or {}).get('ShipStaticData') or {}
                ty = s.get('Type')
                if isinstance(ty, int): static[mmsi] = [(s.get('Name') or md.get('ShipName') or '').strip(), ty, (s.get('Destination') or '').strip(), now]
            elif t == 'PositionReport':
                p = (m.get('Message') or {}).get('PositionReport') or {}
                la, lo = md.get('latitude', p.get('Latitude')), md.get('longitude', p.get('Longitude'))
                if la is None or lo is None or abs(la) > 90 or abs(lo) > 180: continue
                pos[mmsi] = [round(la, 3), round(lo, 3), round(p.get('Sog') or 0, 1), round(p.get('Cog') or 0), now, (md.get('ShipName') or '').strip()]
    return n

def main():
    if not KEY:
        print('нет AISSTREAM_KEY — пропуск'); return
    static = load(STATIC, {}); now = int(time.time())
    static = {k: v for k, v in static.items() if now - v[3] < STATIC_TTL}
    pos = {}
    try: n = asyncio.run(listen(static, pos))
    except SystemExit: raise
    except Exception as e:
        print('AIS: сбой соединения —', e); n = 0
    old = {str(s[0]): s for s in (load(OUT, {}).get('ships') or [])}
    ships = {}
    for k, s in old.items():                                      # прошлый снимок: [mmsi,name,lat,lon,sog,cog,dest,type,ts]
        if now - s[8] < MAXAGE: ships[k] = s
    for k, p in pos.items():
        st = static.get(k)
        if not st or not (80 <= st[1] <= 89): continue          # только танкеры (AIS-тип 80–89)
        ships[k] = [int(k), st[0] or p[5], p[0], p[1], p[2], p[3], st[2], st[1], p[4]]
    os.makedirs(os.path.dirname(STATIC), exist_ok=True)
    json.dump(static, open(STATIC, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    out = {'updated': now, 'listened': LISTEN, 'msgs': n, 'ships': sorted(ships.values(), key=lambda s: s[0])}
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('сообщений', n, '· типов судов', len(static), '· танкеров на карте', len(ships))

if __name__ == '__main__':
    main()
