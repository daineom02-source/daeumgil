"""상호명으로 프랜차이즈 브랜드를 찾는다 (상호명 기준 추정)
- 지점 표시: 지점명 칸이 있거나 상호명이 '~점/~호점/DT'로 끝남
- 브랜드: 같은 업종 대분류에서 같은 앞글자로 시작하는 가게가 8곳 이상, 그중 지점 표시가 45% 이상,
  그리고 그 앞글자 뒤에 오는 글자(지점 이름)가 제각각인 지점에서 끊는다 (스타 → 스타벅스)
사용: python find_brands.py <상가정보 CSV ...> <출력 brands.json>
"""
import sys, re, json, collections
import pandas as pd
srcs = sys.argv[1:-1]; out = sys.argv[-1]
cols = ['상호명', '지점명', '상권업종대분류명']
a = pd.concat([pd.read_csv(f, dtype=str, usecols=cols) for f in srcs])
a['nm'] = a['상호명'].fillna('').str.replace(r'\s+|\(.*?\)|㈜', '', regex=True)
a['sig'] = (a['지점명'].fillna('').str.strip() != '') | a['nm'].str.contains(r'.{2,}(?:점|호점|DT)$')
cnt = collections.Counter(); sig = collections.Counter(); nxt = collections.defaultdict(collections.Counter)
for nm, big, s in zip(a['nm'], a['상권업종대분류명'], a['sig']):
    for L in range(2, min(len(nm), 12) + 1):
        k = (nm[:L], big); cnt[k] += 1; sig[k] += s
        if len(nm) > L: nxt[k][nm[L:L + 2]] += 1
GENERIC = re.compile(r'공인중개|부동산|업소명|청소|수리|컨설팅|노래|식당|밥상|떡집|상회|교회|약국|의원|치과|병원|학원|교습|미용실|철물|정육|반찬|옛날|시골|원조|할매|엄마|가마솥|^(치킨|피자|커피|카페|국밥|족발|김밥|분식|떡볶|버거|샐러|디저|빵|베이|제과|헤어|네일|세탁|마트|슈퍼|편의|한국|대한|서울|경기|우리|행복|미래|하나|제일|중앙|신세|현대|삼성|24|더|뉴|해피|굿|그린|스타$)')
BAD = re.compile(r'셀프빨래|빨래방|휴대폰|파스타|샤브|스팀|무인|정육|김치')
def is_brand(k):
    n = cnt[k]
    if n < 8 or sig[k] / n < (0.75 if len(k[0]) <= 3 else 0.45) or GENERIC.search(k[0]) or BAD.search(k[0]): return False
    rest = sum(nxt[k].values())
    if rest < 5: return True  # 거의 모두 같은 이름 (지점은 지점명 칸에)
    return max(nxt[k].values()) / rest <= 0.25  # 뒤에 오는 이름이 제각각 → 여기서 브랜드가 끝남
brands = collections.defaultdict(set)
for k in cnt:
    if is_brand(k): brands[k[1]].add(k[0])
# 짧은 브랜드에 포함되는 긴 후보는 정리
for big in brands:
    ps = sorted(brands[big], key=len); keep = []
    for p in ps:
        if not any(p.startswith(q) for q in keep): keep.append(p)
    brands[big] = keep
# 지점 표시가 적어 놓치기 쉬운 잘 알려진 브랜드
EXTRA = {'음식': ['김밥천국', '투다리', '신전떡볶이', '페리카나', '네네치킨', '파리바게뜨', '뚜레쥬르', '배스킨라빈스', '맥도날드', '롯데리아', '버거킹', 'KFC'],
         '소매': ['GS25', 'CU', '씨유', '세븐일레븐', '이마트24', '다이소', '올리브영', '아모레', '이니스프리', '롯데마트', '홈플러스', '노브랜드'],
         '수리·개인': ['크린토피아', '준오헤어', '박승철헤어', '리안헤어', '이가자헤어', '블루클럽', '월드크리닝']}
for big, ps in EXTRA.items():
    for p in ps:
        if not any(p.startswith(q) for q in brands[big]): brands[big].append(p)
full = collections.defaultdict(collections.Counter)
pre = {big: sorted(ps, key=len) for big, ps in brands.items()}
for nm, big in zip(a['nm'], a['상권업종대분류명']):
    for p in pre.get(big, []):
        if nm.startswith(p):
            if not re.search(r'(?:점|호점|DT)$', nm) and len(nm) <= len(p) + 4: full[(p, big)][nm] += 1
            break
disp = {big: {p: (full[(p, big)].most_common(1)[0][0] if full[(p, big)] else p) for p in ps} for big, ps in brands.items()}
json.dump(disp, open(out, 'w', encoding='utf-8'), ensure_ascii=False)
print({b: len(ps) for b, ps in brands.items()})
food = sorted(brands['음식'], key=lambda p: -cnt[(p, '음식')])
print('음식', [(disp['음식'][p], cnt[(p, '음식')]) for p in food[:80]])
print('소매', sorted(brands['소매'], key=lambda p: -cnt[(p, '소매')])[:60])
print('수리', sorted(brands['수리·개인'], key=lambda p: -cnt[(p, '수리·개인')])[:40])
