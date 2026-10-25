from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


DATA_PATH = Path(__file__).resolve().parent / "data" / "seongsu_daily.csv"
WEEKDAY_NAMES = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
METRICS = {"총 이용객": "total", "승차": "boarding", "하차": "alighting"}


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    """일별 정제 데이터를 읽고 대시보드 계산에 필요한 열을 준비한다."""
    data = pd.read_csv(path, parse_dates=["date"])
    required = {"date", "boarding", "alighting", "total"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"필요한 열이 없습니다: {', '.join(sorted(missing))}")

    data = data.sort_values("date").reset_index(drop=True)
    data["weekday"] = data["date"].dt.dayofweek
    data["요일"] = data["weekday"].map(dict(enumerate(WEEKDAY_NAMES)))
    data["month"] = data["date"].dt.to_period("M").dt.to_timestamp()
    return data


st.set_page_config(page_title="성수역 이용객 대시보드", page_icon="🚇", layout="wide")
st.title("성수역 일별 이용객 대시보드")
st.caption("서울 지하철 2호선 성수역 · 승차와 하차 합계에는 환승객이 포함됩니다.")

try:
    df = load_data(str(DATA_PATH))
except FileNotFoundError:
    st.error("data/seongsu_daily.csv 파일을 찾을 수 없습니다. README의 데이터 준비 순서를 따라 주세요.")
    st.stop()
except (ValueError, pd.errors.ParserError) as exc:
    st.error(f"데이터 파일을 읽지 못했습니다: {exc}")
    st.stop()

min_date = df["date"].min().date()
max_date = df["date"].max().date()

with st.sidebar:
    st.header("조건 선택")
    chosen_range = st.date_input(
        "기간",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        help="시작일과 종료일을 선택하세요.",
    )
    metric_label = st.selectbox("지표", list(METRICS.keys()), index=0)
    moving_days = st.slider("이동평균 일수", min_value=1, max_value=60, value=30)
    selected_weekdays = st.multiselect("요일", WEEKDAY_NAMES, default=WEEKDAY_NAMES)
    outlier_threshold = st.slider("이상치 기준 (%)", min_value=10, max_value=50, value=30)

if not isinstance(chosen_range, (tuple, list)) or len(chosen_range) != 2:
    st.info("기간을 보려면 시작일과 종료일을 모두 선택해 주세요.")
    st.stop()

start_date, end_date = chosen_range
if start_date > end_date:
    st.info("시작일이 종료일보다 늦습니다. 기간을 다시 선택해 주세요.")
    st.stop()

metric = METRICS[metric_label]
all_data = df.copy()
all_data["moving_average"] = all_data[metric].rolling(moving_days, min_periods=1).mean()

start_ts = pd.Timestamp(start_date)
end_ts = pd.Timestamp(end_date)
date_mask = all_data["date"].between(start_ts, end_ts)
weekday_mask = all_data["요일"].isin(selected_weekdays)
view = all_data.loc[date_mask & weekday_mask].copy()

if view.empty:
    st.info("선택한 기간과 요일에 해당하는 데이터가 없습니다. 기간이나 요일 조건을 바꿔 주세요.")
    st.stop()

# 이상치 기준 평균은 선택 기간이 아닌 전체 기간의 같은 요일 평균이다.
weekday_means = all_data.groupby("weekday")[metric].mean()
all_data["weekday_mean"] = all_data["weekday"].map(weekday_means)
all_data["gap_pct"] = (all_data[metric] - all_data["weekday_mean"]) / all_data["weekday_mean"] * 100
outliers = all_data.loc[
    date_mask
    & weekday_mask
    & (all_data["gap_pct"].abs() >= outlier_threshold)
].copy()

st.subheader(f"{metric_label} 요약")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("선택한 데이터 일수", f"{len(view):,}일")
kpi2.metric("일평균", f"{view[metric].mean():,.0f}명")
max_idx = view[metric].idxmax()
min_idx = view[metric].idxmin()
kpi3.metric("최대", f"{view.loc[max_idx, metric]:,.0f}명", view.loc[max_idx, "date"].strftime("%Y-%m-%d"))
kpi4.metric("최소", f"{view.loc[min_idx, metric]:,.0f}명", view.loc[min_idx, "date"].strftime("%Y-%m-%d"))

st.subheader("① 일별 추세와 이동평균")
trend_fig = go.Figure()
trend_fig.add_trace(go.Scatter(x=view["date"], y=view[metric], mode="lines", name="일별", line={"color": "#9ab3d0", "width": 1}))
trend_fig.add_trace(go.Scatter(x=view["date"], y=view["moving_average"], mode="lines", name=f"{moving_days}일 이동평균", line={"color": "#d9534f", "width": 2.5}))
trend_fig.update_layout(xaxis_title="날짜", yaxis_title="이용객 수(명)", hovermode="x unified", legend_title="")
st.plotly_chart(trend_fig, width="stretch")
st.caption("이 그래프는 이렇게 읽으세요: 가는 선은 날짜별 값이고, 굵은 선은 선택한 일수만큼 평균해 단기 오르내림을 줄인 흐름입니다.")

st.subheader("② 요일별 평균")
weekday_avg = view.groupby("요일", as_index=False)[metric].mean()
weekday_avg["요일"] = pd.Categorical(weekday_avg["요일"], categories=WEEKDAY_NAMES, ordered=True)
weekday_avg = weekday_avg.sort_values("요일")
weekday_fig = px.bar(weekday_avg, x="요일", y=metric, labels={"요일": "요일", metric: "평균 이용객(명)"}, color="요일")
weekday_fig.update_layout(showlegend=False)
st.plotly_chart(weekday_fig, width="stretch")
st.caption("이 그래프는 이렇게 읽으세요: 선택한 기간과 요일 조건에 해당하는 날짜만 모아 요일별 하루 평균을 비교합니다.")

st.subheader("③ 월별 일평균")
monthly_avg = view.groupby("month", as_index=False)[metric].mean()
monthly_avg["월"] = monthly_avg["month"].dt.strftime("%Y-%m")
monthly_fig = px.bar(monthly_avg, x="월", y=metric, labels={"월": "월", metric: "일평균 이용객(명)"})
st.plotly_chart(monthly_fig, width="stretch")
st.caption("이 그래프는 이렇게 읽으세요: 선택한 조건에 속한 날짜만 월별로 묶어 하루 평균을 비교합니다.")

st.subheader(f"④ 이상치 ({outlier_threshold}% 기준)")
if outliers.empty:
    st.info("선택한 조건에서 기준을 넘는 이상치가 없습니다.")
else:
    outlier_table = outliers[["date", "요일", metric, "gap_pct"]].copy()
    outlier_table["date"] = outlier_table["date"].dt.strftime("%Y-%m-%d")
    outlier_table = outlier_table.rename(
        columns={"date": "날짜", "요일": "요일", metric: "이용객", "gap_pct": "같은 요일 평균 대비 %"}
    )
    outlier_table["이용객"] = outlier_table["이용객"].map(lambda value: f"{value:,.0f}")
    outlier_table["같은 요일 평균 대비 %"] = outlier_table["같은 요일 평균 대비 %"].map(lambda value: f"{value:+.1f}%")
    st.dataframe(outlier_table, hide_index=True, width="stretch")
st.caption("이 그래프는 이렇게 읽으세요: 같은 요일의 전체 기간 평균과 비교해 설정한 비율 이상 차이 나는 날짜를 보여줍니다. 실제 현상일 수 있어 삭제하지 않았습니다.")
