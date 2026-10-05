import glob
import os

import pandas as pd

RAW_DIR = "data/raw"
OUT_PATH = "data/seongsu_daily.csv"
LINE_NAME = "2호선"
STATION_NAME = "성수"


def read_csv_safely(path):
    for enc in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            # index_col=False: 줄 끝 쉼표 때문에 컬럼이 밀리는 문제 방지
            # dtype=str: 일단 전부 글자로 읽고 나중에 숫자로 변환
            return pd.read_csv(path, encoding=enc, index_col=False, dtype=str)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"인코딩 오류: {path}")


def find_col(df, keywords):
    for c in df.columns:
        if any(k in str(c) for k in keywords):
            return c
    return None


def to_number(series):
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False).str.strip(),

        errors="coerce",
    )


def main():
    files = sorted(glob.glob(os.path.join(RAW_DIR, "*.csv")))
    print(f"발견한 CSV 파일: {len(files)}개\n")
    if not files:
        raise SystemExit("data/raw 폴더에 CSV가 없습니다.")

    frames = []
    print("[파일별 점검]")
    for f in files:
        name = os.path.basename(f)
        df = read_csv_safely(f)

        date_c = find_col(df, ["사용일자", "YMD"])
        line_c = find_col(df, ["노선명", "LN_NM"])
        stn_c = find_col(df, ["역명", "STNS_NM"])
        on_c = find_col(df, ["승차", "GTON"])
        off_c = find_col(df, ["하차", "GTOFF"])

        if None in (date_c, line_c, stn_c, on_c, off_c):
            print(f"- {name}: 필요한 컬럼 없음 → 건너뜀 (컬럼: {list(df.columns)})")
            continue

        sub = df[[date_c, line_c, stn_c, on_c, off_c]].copy()
        sub.columns = ["date", "line", "station", "boarding", "alighting"]

        # 날짜: 숫자만 남기고 앞 8자리(YYYYMMDD)만 사용
        digits = sub["date"].astype(str).str.replace(r"\D", "", regex=True).str[:8]
        sub["date"] = pd.to_datetime(digits, format="%Y%m%d", errors="coerce")

        sub["line"] = sub["line"].astype(str).str.strip()
        sub["station"] = sub["station"].astype(str).str.strip()
        sub["boarding"] = to_number(sub["boarding"])
        sub["alighting"] = to_number(sub["alighting"])

        if sub["date"].isna().all():
            print(f"- {name}: 날짜를 못 읽음! 첫 행 내용: {df.iloc[0].tolist()}")
            continue

        hit = sub[(sub["line"] == LINE_NAME) & (sub["station"] == STATION_NAME)]
        print(
            f"- {name}: 전체 {len(sub)}행, "
            f"기간 {sub['date'].min().date()}~{sub['date'].max().date()}, "
            f"성수역 {len(hit)}행"
        )
        frames.append(hit)

    if not frames:
        raise SystemExit("사용할 수 있는 파일이 없습니다. 위 점검 결과를 알려주세요.")

    result = pd.concat(frames, ignore_index=True)
    if result.empty:
        raise SystemExit("성수역 데이터를 찾지 못했습니다. 위 점검 결과를 알려주세요.")

    result = (
        result.dropna(subset=["date"])
        .groupby("date", as_index=False)[["boarding", "alighting"]]
        .sum()
        .sort_values("date")
        .reset_index(drop=True)
    )
    result["total"] = result["boarding"] + result["alighting"]


    full = pd.date_range(result["date"].min(), result["date"].max(), freq="D")
    missing = full.difference(result["date"])

    print("\n" + "=" * 40)
    print("데이터 처리 결과")
    print("=" * 40)
    print(f"기간: {result['date'].min().date()} ~ {result['date'].max().date()}")
    print(f"데이터 개수: {len(result)}개")
    print(f"결측치: {int(result.isna().sum().sum())}개")
    print(f"빠진 날짜: {len(missing)}일")
    if len(missing) > 0:
        print("  빠진 날짜 예시:", [d.date().isoformat() for d in missing[:10]])
    print("100개 이상 조건:", "충족 ✅" if len(result) >= 100 else "부족 ❌ (CSV를 더 받아야 함)")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    result.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    print(f"\n저장 위치: {OUT_PATH}")


if __name__ == "__main__":
    main()