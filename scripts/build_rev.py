"""국세청 '통계로 보는 생활업종' 화면에서 옮겨 적은 평균 연매출 → rev.json
사용: python build_rev.py <rev_*.csv ...> <docs/data/gg/rev.json>
"""
import sys, csv, json
srcs, out = sys.argv[1:-1], sys.argv[-1]
g, life = {}, {}
for f in srcs:
    for r in csv.DictReader(open(f, encoding='utf-8')):
        life[r['업종']] = r['평균존속연수']
        if not r['평균연매출_만원']: continue  # 사업자 20명 이하: 국세청이 평균을 공개하지 않음
        g.setdefault(r['시군'], {})[r['업종']] = [int(r['평균연매출_만원']), float(r['전년대비_pct'] or 0)]
json.dump({'asof': '2024년 귀속', 'src': '국세청 통계로 보는 생활업종', 'g': g, 'life': life}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print({k: len(v) for k, v in g.items()})
