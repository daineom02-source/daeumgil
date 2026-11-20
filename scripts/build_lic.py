# 일반음식점 인허가(경기) → 시·군별 개업·폐업 기록 JSON
# 사용: python scripts/build_lic.py <일반음식점현황.csv> docs/data/gg
import sys, json, math, os
import pandas as pd
src, out = sys.argv[1], sys.argv[2]
idx = json.load(open(os.path.join(out, 'index.json')))
d = pd.read_csv(src, encoding='cp949', dtype=str, low_memory=False)
d['sg'] = d['소재지지번주소'].fillna(d['소재지도로명주소']).fillna('').str.split().str[1]
d['lat'] = pd.to_numeric(d['위도'], errors='coerce'); d['lon'] = pd.to_numeric(d['경도'], errors='coerce')
d = d[d.lat.between(36.8, 38.4) & d.lon.between(126.3, 127.9)]
def mon(s):
    s = str(s)
    if len(s) < 6 or not s[:6].isdigit(): return 0
    y, m = int(s[:4]), int(s[4:6])
    return (y - 2000) * 12 + m if 1950 < y < 2100 and 1 <= m <= 12 else 0
d['o'] = d['인허가일자'].map(mon); d['c'] = d['폐업일자'].map(mon)
d.loc[d['영업상태명'] == '영업', 'c'] = 0
d = d[(d.o > 0) & ((d.c == 0) | (d.c >= (2019 - 2000) * 12 + 1))]
TYPES = sorted(d['업태구분명정보'].fillna('기타').unique().tolist())
tix = {t: i for i, t in enumerate(TYPES)}
M_LAT = 110540
tot = 0
for e in idx:
    sub = d[d.sg == e['name']]
    city = json.load(open(os.path.join(out, e['file'] + '.json')))
    # 가장 가까운 상가 점포의 행정동을 빌린다 (300m 안)
    k = 111320 * math.cos(math.radians(37.5)); G = 150
    grid = {}
    for i, (x, y) in enumerate(zip(city['lon'], city['lat'])):
        grid.setdefault((int(x * k // G), int(y * M_LAT // G)), []).append(i)
    dongs = []
    for x, y in zip(sub.lon, sub.lat):
        gx, gy = int(x * k // G), int(y * M_LAT // G); best, bd = -1, 300.0
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                for i in grid.get((gx + dx, gy + dy), ()):
                    dd = math.hypot((city['lon'][i] - x) * k, (city['lat'][i] - y) * M_LAT)
                    if dd < bd: bd, best = dd, i
        dongs.append(city['dong'][best] if best >= 0 else -1)
    res = {'t': [tix[t] for t in sub['업태구분명정보'].fillna('기타')],
           'lon': [round(v, 5) for v in sub.lon], 'lat': [round(v, 5) for v in sub.lat],
           'o': sub.o.astype(int).tolist(), 'c': sub.c.astype(int).tolist(), 'd': dongs}
    os.makedirs(os.path.join(out, 'lic'), exist_ok=True)
    json.dump(res, open(os.path.join(out, 'lic', e['file'] + '.json'), 'w'), separators=(',', ':'), ensure_ascii=False)
    tot += len(sub); print(e['name'], len(sub), sum(1 for v in dongs if v < 0))
json.dump({'types': TYPES, 'asof': '2026.11', 'total': tot}, open(os.path.join(out, 'lic', 'meta.json'), 'w'), ensure_ascii=False)
print('total', tot)
