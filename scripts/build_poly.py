"""폴리텍 재취업과정 CSV → web/data/poly.json
사용법: python build_poly.py <재취업과정 CSV> <출력 poly.json> [입시연도(기본: 가장 최근)]
캠퍼스 좌표는 상가(상권)정보에서 같은 도로명주소에 등록된 점포 좌표를 빌려 왔습니다.
"""
import json, sys
import pandas as pd

CAMPUS = {  # 이름: (위도, 경도, 주소)
    '성남캠퍼스': (37.45888, 127.15399, '성남시 수정구 수정로 398'),
    '분당융합기술교육원': (37.38581, 127.12129, '성남시 분당구 황새울로329번길 5'),
    '광명융합기술교육원': (37.47734, 126.86260, '광명시 오리로 904'),
    '서울정수캠퍼스': (37.52998, 126.99681, '서울 용산구 보광로 일대'),
    '인천캠퍼스': (37.47939, 126.75324, '인천 부평구 무네미로 478'),
    '남인천캠퍼스': (37.47265, 126.67734, '인천 미추홀구 염전로333번길 23'),
    '서울강서캠퍼스': (37.54924, 126.84244, '서울 강서구 우장산로10길 112'),
    '화성캠퍼스': (37.13155, 126.88968, '화성시 팔탄면 제암고주로 108'),
    '반도체융합캠퍼스': (37.00732, 127.17445, '안성시 공도읍 송원길 41-12'),
}

def main():
    src, out = sys.argv[1], sys.argv[2]
    df = pd.read_csv(src, dtype=str)
    year = sys.argv[3] if len(sys.argv) > 3 else df['입시연도'].max()
    d = df[(df['입시연도'] == year) & df['캠퍼스'].isin(CAMPUS)]
    res = []
    for name, (lat, lon, addr) in CAMPUS.items():
        rows = d[d['캠퍼스'] == name]
        res.append({'name': name, 'lat': lat, 'lon': lon, 'addr': addr, 'year': year,
                    'courses': [{'type': r['과정구분'].replace('(단기)', ''), 'name': r['전공직종'],
                                 'time': r['주간야간구분'], 'n': int(r['모집인원'])} for _, r in rows.iterrows()]})
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'{year}년 캠퍼스 {len(res)}곳, 과정 {sum(len(r["courses"]) for r in res)}개')

if __name__ == '__main__':
    main()
