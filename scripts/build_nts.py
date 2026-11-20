"""국세청 100대 생활업종 사업자 현황(시군구별, 월별) → 시·군별 요약
사용: python build_nts.py <TASIS 우리동네가게 엑셀> <docs/data/gg>
출력: nts.json {asof, types:[업종], g:{시군:[[당월, 전년동월], ...]}}  ('경기도'는 도 합계)
"""
import sys, json, os, openpyxl, collections
src, out = sys.argv[1:3]
ws = openpyxl.load_workbook(src, read_only=True)['100대 생활업종']
asof = None; types = []; acc = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
for i, r in enumerate(ws.iter_rows(values_only=True)):
    if r[0] == '*조회년월': asof = r[3]
    if i < 6 or r[1] != '경기도' or r[0] == '업종전체' or not isinstance(r[3], (int, float)): continue
    t = r[0]
    if t not in types: types.append(t)
    sg = '경기도' if r[2] == '경기도 합계' else r[2].split()[0]
    a = acc[sg][t]; a[0] += r[3]; a[1] += r[6] if isinstance(r[6], (int, float)) else 0
g = {sg: [acc[sg][t] if t in acc[sg] else [0, 0] for t in types] for sg in acc}
json.dump({'asof': asof, 'types': types, 'g': g}, open(os.path.join(out, 'nts.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(asof, len(types), len(g), sorted(g)[:5])
k = types.index('커피음료점'); print('수원 커피', g['수원시'][k], '경기', g['경기도'][k])
