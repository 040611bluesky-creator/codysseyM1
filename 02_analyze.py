"""
02_analyze.py
data/seongsu_daily.csv 를 읽어서
1) 시계열 분석 (이동평균, 변화율, 요일별/월별 집계, 변동성, 이상치 표시)
2) 그래프 4개를 images/ 폴더에 저장
3) 리포트에 쓸 숫자 요약을 data/summary.txt 에 저장

실행:  python 02_analyze.py
"""

import os

import matplotlib.pyplot as plt
import pandas as pd

# ---------- 설정 ----------
DATA_PATH = "data/seongsu_daily.csv"
IMG_DIR = "images"
SUMMARY_PATH = "data/summary.txt"
OUTLIER_RATIO = 0.30  # 같은 요일 평균보다 30% 이상 높거나 낮으면 '이상치'로 표시
WEEKDAY_KR = ["월", "화", "수", "목", "금", "토", "일"]

# 한글 폰트 (윈도우: 맑은 고딕 / 맥: AppleGothic / 기타: 나눔고딕)
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

os.makedirs(IMG_DIR, exist_ok=True)
summary_lines = []


def out(text=""):
    """화면에 출력하고, 요약 파일용으로도 저장"""
    print(text)
    summary_lines.append(str(text))


# ---------- 1. 데이터 읽기 ----------
df = pd.read_csv(DATA_PATH, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
df["weekday"] = df["date"].dt.dayofweek  # 0=월 ... 6=일
df["weekday_kr"] = df["weekday"].map(lambda x: WEEKDAY_KR[x])
df["is_weekend"] = df["weekday"] >= 5
df["month"] = df["date"].dt.to_period("M")

out("=" * 50)
out("[1] 기본 정보")
out("=" * 50)
out(f"기간: {df['date'].min().date()} ~ {df['date'].max().date()}")
out(f"데이터 개수: {len(df)}개 (일 단위)")
out(f"하루 총 이용객(승차+하차) 평균: {df['total'].mean():,.0f}명")
out(f"최대: {df['total'].max():,.0f}명 ({df.loc[df['total'].idxmax(), 'date'].date()})")
out(f"최소: {df['total'].min():,.0f}명 ({df.loc[df['total'].idxmin(), 'date'].date()})")

# ---------- 2. 시계열 분석 ----------
# (기법 1) 이동평균: 요일 효과를 없애려면 7일, 큰 흐름은 30일
df["ma7"] = df["total"].rolling(7).mean()
df["ma30"] = df["total"].rolling(30).mean()

# (기법 2) 변화율: 전일 대비(%) / 전월 대비(%)
df["daily_pct"] = df["total"].pct_change() * 100
monthly = df.groupby("month")["total"].mean().to_frame("avg_total")
monthly["mom_pct"] = monthly["avg_total"].pct_change() * 100

# (기법 3) 요일별 집계
weekday_avg = df.groupby("weekday")["total"].mean()

# (기법 4) 변동성(표준편차)
daily_std = df["total"].std()

# (이상치) 같은 요일 평균과 비교
df["weekday_mean"] = df.groupby("weekday")["total"].transform("mean")
df["gap_ratio"] = (df["total"] - df["weekday_mean"]) / df["weekday_mean"]
outliers = df[df["gap_ratio"].abs() >= OUTLIER_RATIO].copy()

out("")
out("=" * 50)
out("[2] 추세 (질문1: 전체적으로 오르는가, 내리는가?)")
out("=" * 50)
half = len(df) // 2
first_half = df.iloc[:half]["total"].mean()
second_half = df.iloc[half:]["total"].mean()
out(f"1년차(앞 절반) 일평균: {first_half:,.0f}명")
out(f"2년차(뒤 절반) 일평균: {second_half:,.0f}명")
out(f"2년차 vs 1년차 변화: {(second_half / first_half - 1) * 100:+.1f}%")
first90 = df.iloc[:90]["total"].mean()
last90 = df.iloc[-90:]["total"].mean()
out(f"처음 90일 평균: {first90:,.0f}명 → 마지막 90일 평균: {last90:,.0f}명 ({(last90 / first90 - 1) * 100:+.1f}%)")

out("")
out("월별 일평균 이용객과 전월 대비 변화율")
for m, row in monthly.iterrows():
    mom = "" if pd.isna(row["mom_pct"]) else f"({row['mom_pct']:+.1f}%)"
    out(f"  {m}: {row['avg_total']:,.0f}명 {mom}")
top_up = monthly["mom_pct"].nlargest(3)
top_down = monthly["mom_pct"].nsmallest(3)
out("전월 대비 가장 많이 늘어난 달 TOP3: " + ", ".join(f"{m}({v:+.1f}%)" for m, v in top_up.items()))
out("전월 대비 가장 많이 줄어든 달 TOP3: " + ", ".join(f"{m}({v:+.1f}%)" for m, v in top_down.items()))

out("")
out("=" * 50)
out("[3] 요일별 패턴 (질문2: 평일과 주말이 얼마나 다른가?)")
out("=" * 50)
for i, v in weekday_avg.items():
    out(f"  {WEEKDAY_KR[i]}요일 평균: {v:,.0f}명")
wd = df.loc[~df["is_weekend"], "total"].mean()
we = df.loc[df["is_weekend"], "total"].mean()
out(f"평일 평균: {wd:,.0f}명 / 주말 평균: {we:,.0f}명 (주말은 평일의 {we / wd * 100:.0f}%)")
out(f"가장 붐비는 요일: {WEEKDAY_KR[weekday_avg.idxmax()]} / 가장 한산한 요일: {WEEKDAY_KR[weekday_avg.idxmin()]}")

out("")
out("=" * 50)
out("[4] 이상치 (질문3: 갑자기 늘거나 줄어든 날은 언제인가?)")
out("=" * 50)
out(f"기준: 같은 요일 평균보다 {OUTLIER_RATIO * 100:.0f}% 이상 높거나 낮은 날 (삭제하지 않고 표시만 함)")
out(f"해당 날짜: {len(outliers)}일")
low = outliers.sort_values("gap_ratio").head(10)
high = outliers.sort_values("gap_ratio", ascending=False).head(10)
out("[평소보다 크게 줄어든 날 TOP10]")
for _, r in low.iterrows():
    out(f"  {r['date'].date()} ({r['weekday_kr']}): {r['total']:,.0f}명 (같은 요일 평균 대비 {r['gap_ratio'] * 100:+.0f}%)")
out("[평소보다 크게 늘어난 날 TOP10]")
for _, r in high.iterrows():
    if r["gap_ratio"] > 0:
        out(f"  {r['date'].date()} ({r['weekday_kr']}): {r['total']:,.0f}명 (같은 요일 평균 대비 {r['gap_ratio'] * 100:+.0f}%)")

out("")
out("=" * 50)
out("[5] 변동성")
out("=" * 50)
out(f"하루 이용객 표준편차: {daily_std:,.0f}명 (평균의 {daily_std / df['total'].mean() * 100:.0f}%)")
out(f"전일 대비 변화율 표준편차: {df['daily_pct'].std():.1f}%p")

# ---------- 3. 그래프 ----------
# 그래프 1: 일별 추세
fig, ax = plt.subplots(figsize=(11, 4.5))
ax.plot(df["date"], df["total"], color="#7a9cc6", linewidth=0.9)
ax.set_title("성수역 일별 총 이용객 추이 (승차+하차)")
ax.set_xlabel("날짜")
ax.set_ylabel("이용객 수(명)")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(IMG_DIR, "01_daily_trend.png"), dpi=150)
plt.close(fig)

# 그래프 2: 이동평균
fig, ax = plt.subplots(figsize=(11, 4.5))
ax.plot(df["date"], df["total"], color="#c9d6e8", linewidth=0.8, label="일별")
ax.plot(df["date"], df["ma7"], color="#2b7bba", linewidth=1.6, label="7일 이동평균")
ax.plot(df["date"], df["ma30"], color="#d9534f", linewidth=2.2, label="30일 이동평균")
ax.set_title("성수역 이용객: 이동평균으로 본 큰 흐름")
ax.set_xlabel("날짜")
ax.set_ylabel("이용객 수(명)")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.legend()
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(IMG_DIR, "02_moving_average.png"), dpi=150)
plt.close(fig)

# 그래프 3: 요일별 평균
fig, ax = plt.subplots(figsize=(7, 4.5))
colors = ["#2b7bba"] * 5 + ["#d9534f"] * 2
bars = ax.bar(WEEKDAY_KR, weekday_avg.values, color=colors)
ax.set_title("성수역 요일별 평균 이용객")
ax.set_ylabel("이용객 수(명)")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
for b, v in zip(bars, weekday_avg.values):
    ax.text(b.get_x() + b.get_width() / 2, v, f"{v:,.0f}", ha="center", va="bottom", fontsize=8)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(IMG_DIR, "03_weekday_avg.png"), dpi=150)
plt.close(fig)

# 그래프 4: 월별 일평균 + 이상치 표시
fig, axes = plt.subplots(2, 1, figsize=(11, 8))
ax = axes[0]
labels = [str(m) for m in monthly.index]
ax.bar(labels, monthly["avg_total"].values, color="#2b7bba")
ax.set_title("성수역 월별 일평균 이용객")
ax.set_ylabel("이용객 수(명)")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.tick_params(axis="x", rotation=60)
ax.grid(axis="y", alpha=0.3)

ax = axes[1]
ax.plot(df["date"], df["total"], color="#c9d6e8", linewidth=0.8)
ax.scatter(outliers["date"], outliers["total"], color="#d9534f", s=18, label=f"이상치 {len(outliers)}일")
ax.set_title("같은 요일 평균과 크게 다른 날 (빨간 점)")
ax.set_ylabel("이용객 수(명)")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.legend()
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(IMG_DIR, "04_monthly_and_outliers.png"), dpi=150)
plt.close(fig)

out("")
out(f"그래프 4개 저장 완료 → {IMG_DIR}/ 폴더")

with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(summary_lines))
print(f"요약 저장 완료 → {SUMMARY_PATH}")
