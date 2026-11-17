"""
상가(상권)정보 시도별 CSV → 웹앱용 시·군별 JSON 변환 스크립트

사용법:
    python aggregate.py <경기 CSV 경로> <출력 폴더> [<1년 전 경기 CSV 경로>]

출력:
    cats.json            업종 소분류 목록 [[대분류, 중분류, 소분류], ...]
    sigungu.json         시·군 목록과 점포 수
    stores/<시군>.json    {"cats": 업종 번호, "lon": [...], "lat": [...], "dong": [...], "dongs": [행정동명...]}
    change.json          (이전 파일을 줄 때만) 시·군 × 행정동 × 소분류 점포 수 증감
"""
import json
import os
import sys

import pandas as pd

COLS = ["상권업종대분류명", "상권업종중분류명", "상권업종소분류명",
        "시군구명", "행정동명", "경도", "위도"]


def load(path):
    df = pd.read_csv(path, dtype=str, usecols=COLS)
    df = df.dropna(subset=["경도", "위도", "상권업종소분류명"])
    for c in COLS[:5]:
        df[c] = df[c].str.strip()
    # '성남시 분당구' → '성남시' 처럼 시 단위로 묶는다
    df["시군"] = df["시군구명"].str.split().str[0]
    df["경도"] = df["경도"].astype(float).round(5)
    df["위도"] = df["위도"].astype(float).round(5)
    return df


def main():
    src, out = sys.argv[1], sys.argv[2]
    prev = sys.argv[3] if len(sys.argv) > 3 else None
    os.makedirs(os.path.join(out, "stores"), exist_ok=True)

    df = load(src)
    cats = (df[["상권업종대분류명", "상권업종중분류명", "상권업종소분류명"]]
            .drop_duplicates().sort_values(["상권업종대분류명", "상권업종중분류명", "상권업종소분류명"])
            .values.tolist())
    cat_idx = {c[2]: i for i, c in enumerate(cats)}
    with open(os.path.join(out, "cats.json"), "w", encoding="utf-8") as f:
        json.dump(cats, f, ensure_ascii=False)

    summary = []
    for sigun, g in df.groupby("시군"):
        dongs = sorted(g["행정동명"].unique().tolist())
        d_idx = {d: i for i, d in enumerate(dongs)}
        data = {
            "sigun": sigun,
            "dongs": dongs,
            "cat": [cat_idx[c] for c in g["상권업종소분류명"]],
            "dong": [d_idx[d] for d in g["행정동명"]],
            "lon": g["경도"].tolist(),
            "lat": g["위도"].tolist(),
        }
        with open(os.path.join(out, "stores", f"{sigun}.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        summary.append({"sigun": sigun, "stores": len(g), "dongs": len(dongs)})

    with open(os.path.join(out, "sigungu.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False)

    if prev:
        p = load(prev)
        key = ["시군", "행정동명", "상권업종소분류명"]
        now_c = df.groupby(key).size().rename("now")
        prev_c = p.groupby(key).size().rename("prev")
        ch = pd.concat([now_c, prev_c], axis=1).fillna(0).astype(int).reset_index()
        ch.columns = ["sigun", "dong", "cat", "now", "prev"]
        ch.to_json(os.path.join(out, "change.json"), orient="records", force_ascii=False)

    print(f"업종 {len(cats)}개, 시·군 {len(summary)}곳, 점포 {len(df):,}곳 변환 완료")


if __name__ == "__main__":
    main()
