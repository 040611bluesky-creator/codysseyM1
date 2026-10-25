# 성수역 일별 이용객 추세 분석

서울 지하철 2호선 성수역의 일별 승차·하차 자료를 정리하고, 추세·요일별 차이·이상치를 분석하는 프로젝트입니다. 분석 결과와 그래프는 `REPORT.md`와 `images/`에서 확인할 수 있습니다.

## 폴더 구조

```text
성수역 데이터 분석/
├── data/
│   ├── raw/                  # 내려받은 월별 원본 CSV
│   ├── seongsu_daily.csv     # 분석에 사용하는 성수역 일별 데이터
│   └── summary.txt           # 분석 결과 숫자 요약
├── images/                   # 분석 스크립트가 만든 그래프
├── 01_load_data_v2.py        # 월별 CSV를 합쳐 성수역 일별 데이터 생성
├── 02_analyze.py             # 분석, 그래프, summary.txt 생성
├── app.py                    # 대시보드
├── requirements.txt          # Python 라이브러리 목록
├── REPORT.md                 # 분석 리포트
├── docs/
│   └── dashboard_scenarios.md # 대시보드 스크린샷 시나리오
└── README.md                 # 이 안내서
```

## 설치와 실행

현재 고정한 라이브러리 버전은 Python 3.11 이상이 필요합니다. Windows PowerShell에서 프로젝트 폴더로 이동한 뒤 아래 명령을 한 줄씩 실행합니다.

```powershell
python -m venv .venv
```

```powershell
.\.venv\Scripts\Activate.ps1
```

```powershell
python -m pip install -r requirements.txt
```

```powershell
python -X utf8 01_load_data_v2.py
```

```powershell
python -X utf8 02_analyze.py
```

```powershell
streamlit run app.py
```

브라우저에서 대시보드가 열립니다. PowerShell에서 가상환경 활성화가 차단되면 현재 사용자에 대한 실행 정책 설정이 필요할 수 있습니다. VS Code에서 프로젝트 폴더를 연 뒤 Python 인터프리터로 `.venv`를 선택하면 해당 환경에서 실행할 수 있습니다.

`-X utf8`은 Windows 콘솔이 한글이나 체크 표시를 출력할 때 생길 수 있는 문자 인코딩 오류를 피하기 위한 설정입니다. 분석 계산이나 저장 결과에는 영향을 주지 않습니다.

## 데이터 출처와 수집 방법

- 출처: 서울 열린데이터광장, 「서울시 지하철호선별 역별 승하차 인원 정보」
- 다운로드할 파일: `CARD_SUBWAY_MONTH_YYYYMM.csv` 형식의 월별 CSV
- 수집 기간과 파일: 2024년 9월~2026년 8월, 월별 CSV 24개(`CARD_SUBWAY_MONTH_202409.csv` ~ `CARD_SUBWAY_MONTH_202608.csv`)를 받아 `data/raw/`에 넣는다.
- 수집 방법: 서울 열린데이터광장에서 분석 대상 월의 CSV를 내려받아 `data/raw/` 폴더에 넣습니다. 파일명을 바꾸지 않고 월별 원본 파일을 보관한 뒤 `01_load_data_v2.py`를 실행하면 성수역 자료를 모아 `data/seongsu_daily.csv`를 만듭니다.
- 분석 대상: 노선명 `2호선`, 역명 `성수`
- 라이선스: **TODO: 다운로드 페이지에서 이용 조건과 라이선스를 확인해 기록하세요.**

원본 데이터의 재배포 여부는 다운로드 페이지의 이용 조건을 확인한 뒤 결정하세요.

## Streamlit Community Cloud 배포 준비

이 프로젝트는 GitHub 저장소를 연결해 Streamlit Community Cloud에 배포할 수 있습니다. Streamlit 안내에 따르면 새 앱을 만들 때 저장소, 브랜치, 실행 파일 경로를 지정합니다. 자세한 내용은 [Streamlit 공식 배포 안내](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)를 참고하세요.

1. GitHub에서 새 저장소를 만들거나, 사용할 저장소를 준비합니다.
2. VS Code의 **소스 제어** 화면에서 변경 파일을 살펴봅니다. `data/seongsu_daily.csv`, `app.py`, `requirements.txt`는 저장소에 포함되어야 합니다. `data/raw/`는 현재 `.gitignore`에서 제외되어 있어 업로드되지 않습니다. (원본 월별 CSV는 GitHub에서 제외하기로 결정했습니다.)
3. 변경 파일을 스테이지에 올리고 커밋합니다. 터미널에서 올릴 파일을 직접 지정하려면 다음 명령을 사용할 수 있습니다.

   ```powershell
   git add .gitignore README.md REPORT.md requirements.txt app.py data/seongsu_daily.csv data/summary.txt 01_load_data_v2.py 02_analyze.py images docs
   ```

   ```powershell
   git commit -m "Add Seongsu Station analysis and dashboard"
   ```

4. 프로젝트의 현재 브랜치는 `main`이며 원격 저장소 `origin`이 설정되어 있습니다. 커밋을 GitHub에 올립니다.

   ```powershell
   git push -u origin main
   ```

5. Streamlit Community Cloud에 로그인하고 **Create app**을 선택합니다.
6. 다음 항목을 지정하고 **Deploy**를 누릅니다.
   - Repository: 본인의 GitHub 저장소
   - Branch: `main`
   - Main file path: `app.py`
7. 배포가 끝나면 표시된 앱 주소를 열어 동작을 확인하고, 그 주소를 `REPORT.md`의 배포 URL TODO에 적습니다.

Community Cloud의 배포 설정에는 Python 버전 선택이 있습니다. 현재 안내상 기본값은 Python 3.12이며, 이 프로젝트의 고정 라이브러리 버전은 Python 3.11 이상이 필요합니다. [Python 버전 및 배포 설정 안내](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)를 참고하세요.

GitHub 계정과 Streamlit 서비스의 저장소 접근 권한이 필요합니다. 저장소 공개 범위와 원본 CSV 포함 여부는 데이터 이용 조건을 확인해 결정하세요.
