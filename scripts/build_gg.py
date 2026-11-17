"""경기 31개 시·군 프로토타입 데이터 생성
입력: out/stores/<시군>.json (aggregate.py 결과), 상권변화지표 CSV, 지원사업 공고 CSV
출력: proto/data/gg/index.json, proto/data/gg/gNN.json(시군별 점포), proto/data/gg/change.json, proto/data/gg/support.json
"""
import json, os, re, sys
import pandas as pd
STORES, CHG_CSV, SUP_CSV, OUT = sys.argv[1:5]
os.makedirs(OUT, exist_ok=True)
names = sorted(f[:-5] for f in os.listdir(STORES) if f.endswith('.json'))
index = []
for i, n in enumerate(names):
    fid = f"g{i:02d}"
    d = json.load(open(os.path.join(STORES, n + '.json'), encoding='utf-8'))
    json.dump(d, open(os.path.join(OUT, fid + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    index.append({'name': n, 'file': fid, 'stores': len(d['cat']), 'dongs': len(d['dongs'])})
json.dump(index, open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False)

# 상권변화지표: {시군: {_city: {...}, 행정동: {...}}}
c = pd.read_csv(CHG_CSV, encoding='cp949', dtype=str)
c = c[c['행정구역명'].str.startswith('경기도 ')]
chg = {}
gus = set()
for _, r in c.iterrows():
    t = r['행정구역명'].split()
    v = {'type': r['상권변동지표구분명'], 'open': float(r['운영점포평균영업기간']), 'closed': float(r['폐업점포평균영업기간'])}
    if len(t) == 2: chg.setdefault(t[1], {})['_city'] = v
    elif t[-1].endswith('구') and len(t) == 3: gus.add(r['행정구역명'])
    else: chg.setdefault(t[1], {})[t[-1]] = v
json.dump(chg, open(os.path.join(OUT, 'change.json'), 'w', encoding='utf-8'), ensure_ascii=False)

# 지역 지원사업: 공고명에 [경기]와 시군 이름이 함께 있는 소상공인 관련 공고
s = pd.read_csv(SUP_CSV, encoding='cp949', dtype=str)
s = s[s['공고명'].str.contains(r'\[경기\]', na=False)]
sup = {}
for _, r in s.iterrows():
    rel = r['지원대상'] == '소상공인' or '소상공인' in r['공고명'] or '자영업' in r['공고명']
    if not rel: continue
    item = {'title': re.sub(r'^\[경기\]\s*', '', r['공고명']).strip(), 'org': r['소관기관명'], 'start': r['신청기간시작일자'], 'end': r['신청기간종료일자']}
    hit = [n for n in names if n in r['공고명']]
    for n in (hit or ['_경기도']): sup.setdefault(n, []).append(item)
json.dump(sup, open(os.path.join(OUT, 'support.json'), 'w', encoding='utf-8'), ensure_ascii=False)

# 매칭률 보고
tot = ok = 0
for e in index:
    d = json.load(open(os.path.join(OUT, e['file'] + '.json'), encoding='utf-8'))
    m = chg.get(e['name'], {})
    hits = sum(1 for x in d['dongs'] if x in m); tot += len(d['dongs']); ok += hits
    e['chg_match'] = f"{hits}/{len(d['dongs'])}"
print('시군', len(index), '행정동 지표 연결', ok, '/', tot)
print({e['name']: e['chg_match'] for e in index})
print('지원사업', {k: len(v) for k, v in sup.items()})
