"""시·군별 프랜차이즈(상호명 기준 추정) 표시 파일 만들기
사용: python build_fr.py <경기 상가정보 CSV> <brands.json> <docs/data/gg>
출력: fr/gNN.json {"i":[점포 번호], "b":[브랜드 번호]}  (gNN.json 점포 순서와 같음)
      fr/meta.json {"brands":[표시 이름...], "asof":"2026.9.30", "method":"상호명 기준 추정"}
"""
import sys, json, os, re
import pandas as pd
src, bj, out = sys.argv[1:4]
COLS = ["상호명", "상권업종대분류명", "상권업종중분류명", "상권업종소분류명", "시군구명", "행정동명", "경도", "위도"]
df = pd.read_csv(src, dtype=str, usecols=COLS).dropna(subset=["경도", "위도", "상권업종소분류명"])
for c in ["상권업종대분류명", "상권업종중분류명", "상권업종소분류명", "시군구명", "행정동명"]: df[c] = df[c].str.strip()
df["시군"] = df["시군구명"].str.split().str[0]
df["경도"] = df["경도"].astype(float).round(5)
df["nm"] = df["상호명"].fillna('').str.replace(r'\s+|\(.*?\)|㈜', '', regex=True)
B = json.load(open(bj, encoding='utf-8'))
names, bidx = [], {}
pre = {big: sorted(d.keys(), key=len) for big, d in B.items()}
def brand(nm, big):
    for p in pre.get(big, []):
        if nm.startswith(p):
            disp = B[big][p]
            if disp not in bidx: bidx[disp] = len(names); names.append(disp)
            return bidx[disp]
    return -1
idx = {e['name']: e['file'] for e in json.load(open(os.path.join(out, 'index.json'), encoding='utf-8'))}
os.makedirs(os.path.join(out, 'fr'), exist_ok=True)
tot = fr = 0
for sigun, g in df.groupby("시군"):
    f = idx[sigun]
    chk = json.load(open(os.path.join(out, f + '.json'), encoding='utf-8'))
    assert len(chk['lon']) == len(g) and chk['lon'][:50] == g['경도'].tolist()[:50], sigun
    I, Bn = [], []
    for k, (nm, big) in enumerate(zip(g['nm'], g['상권업종대분류명'])):
        b = brand(nm, big)
        if b >= 0: I.append(k); Bn.append(b)
    json.dump({'i': I, 'b': Bn}, open(os.path.join(out, 'fr', f + '.json'), 'w', encoding='utf-8'), separators=(',', ':'))
    tot += len(g); fr += len(I)
json.dump({'brands': names, 'asof': '2026.9.30', 'method': '상호명 기준 추정'}, open(os.path.join(out, 'fr', 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('점포', tot, '프랜차이즈 추정', fr, f'{fr/tot:.1%}', '브랜드', len(names))
