"""시·군별 가게 이름 목록 (가게 이름으로 위치 찾기용)
사용: python build_names.py <경기 상가정보 CSV> <docs/data/gg>
출력: nm/gNN.json [상호(지점), ...]  (gNN.json 점포 순서와 같음)
"""
import sys, json, os
import pandas as pd
src, out = sys.argv[1:3]
COLS = ["상호명", "지점명", "상권업종대분류명", "상권업종중분류명", "상권업종소분류명", "시군구명", "행정동명", "경도", "위도"]
df = pd.read_csv(src, dtype=str, usecols=COLS).dropna(subset=["경도", "위도", "상권업종소분류명"])
df["시군"] = df["시군구명"].str.strip().str.split().str[0]
df["경도"] = df["경도"].astype(float).round(5)
nm = df["상호명"].fillna('').str.strip()
br = df["지점명"].fillna('').str.strip()
df["n"] = [a + (' ' + b if b and b not in a else '') for a, b in zip(nm, br)]
idx = {e['name']: e['file'] for e in json.load(open(os.path.join(out, 'index.json'), encoding='utf-8'))}
os.makedirs(os.path.join(out, 'nm'), exist_ok=True)
for sg, g in df.groupby("시군"):
    chk = json.load(open(os.path.join(out, idx[sg] + '.json'), encoding='utf-8'))
    assert len(chk['lon']) == len(g) and chk['lon'][:30] == g['경도'].tolist()[:30], sg
    json.dump(g['n'].tolist(), open(os.path.join(out, 'nm', idx[sg] + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('ok')
