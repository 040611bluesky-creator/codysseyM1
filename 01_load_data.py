import pandas as pd
from pathlib import Path

# ==========================================
# 1. 폴더 설정
# ==========================================
PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
OUTPUT_DIR = PROJECT_DIR / "data"
OUTPUT_FILE = OUTPUT_DIR / "seongsu_daily.csv"

# ==========================================
# 2. CSV 파일 찾기
# ==========================================
files = sorted(RAW_DIR.glob("CARD_SUBWAY_MONTH_*.csv"))

if not files:
    print("오류: data/raw 폴더에 CSV 파일이 없습니다.")
    print(f"확인할 폴더: {RAW_DIR}")
    raise SystemExit

print(f"발견한 CSV 파일: {len(files)}개")

# ==========================================
# 3. CSV 파일 불러오기
# ==========================================
data_list = []

for file in files:
    try:
        df = pd.read_csv(file, encoding="cp949")
    except UnicodeDecodeError:
        df = pd.read_csv(file, encoding="utf-8-sig")

    # 성수역만 선택
    df["역명"] = df["역명"].astype(str).str.strip()
    seongsu = df[df["역명"] == "성수"].copy()

    if not seongsu.empty:
        data_list.append(seongsu)

# ==========================================
# 4. 데이터 합치기
# ==========================================
if not data_list:
    print("오류: CSV 파일에서 성수역 데이터를 찾지 못했습니다.")
    raise SystemExit

data = pd.concat(data_list, ignore_index=True)

# ==========================================
# 5. 필요한 열만 선택
# ==========================================
data = data[
    ["사용일자", "노선명", "역명", "승차총승객수", "하차총승객수"]
].copy()

# ==========================================
# 6. 날짜 변환
# CSV의 날짜 형식: YYYYMMDD
# 예: 20241201 → 2024-12-01
# ==========================================
data["사용일자"] = pd.to_datetime(
    data["사용일자"].astype(str).str.strip(),
    format="%Y%m%d",
    errors="coerce"
)

# ==========================================
# 7. 승차/하차 인원 숫자로 변환
# ==========================================
data["승차총승객수"] = pd.to_numeric(
    data["승차총승객수"],
    errors="coerce"
)

data["하차총승객수"] = pd.to_numeric(
    data["하차총승객수"],
    errors="coerce"
)

# ==========================================
# 8. 승하차 합계 계산
# ==========================================
data["승하차합계"] = (
    data["승차총승객수"] +
    data["하차총승객수"]
)

# ==========================================
# 9. 날짜순 정렬
# ==========================================
data = data.sort_values("사용일자").reset_index(drop=True)

# ==========================================
# 10. 결측치 확인
# ==========================================
missing_count = int(data.isnull().sum().sum())

# ==========================================
# 11. 기간 확인
# ==========================================
start_date = data["사용일자"].min()
end_date = data["사용일자"].max()

# ==========================================
# 12. 빠진 날짜 확인
# ==========================================
valid_dates = data["사용일자"].dropna()

if not valid_dates.empty:
    all_dates = pd.date_range(
        start=start_date,
        end=end_date,
        freq="D"
    )

    existing_dates = pd.DatetimeIndex(
        valid_dates.unique()
    )

    missing_dates = all_dates.difference(existing_dates)
else:
    missing_dates = pd.DatetimeIndex([])

# ==========================================
# 13. 결과 저장
# ==========================================
OUTPUT_DIR.mkdir(exist_ok=True)

data.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

# ==========================================
# 14. 실행 결과 출력
# ==========================================
print()
print("==========================================")
print("          데이터 처리 결과")
print("==========================================")

if pd.notna(start_date) and pd.notna(end_date):
    print(f"기간: {start_date.date()} ~ {end_date.date()}")
else:
    print("기간: 확인할 수 없음")

print(f"데이터 개수: {len(data):,}개")
print(f"결측치: {missing_count:,}개")
print(f"빠진 날짜: {len(missing_dates):,}일")
print(f"저장 위치: {OUTPUT_FILE}")

if len(missing_dates) > 0:
    print()
    print("빠진 날짜 목록:")

    for date in missing_dates:
        print(date.date())

print()
print("처리가 완료되었습니다.")