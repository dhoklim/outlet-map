# 콘센트맵 (데모)

학교 건물의 **콘센트·전자기기(에어컨 등) 위치를 도면에서 보여주고, 사용 평가를 남기는** 파이썬 프로그램입니다.
**데스크톱 앱(tkinter)** 과 **웹(브라우저)** 두 가지로 쓸 수 있고, 둘은 **같은 `data/*.csv` 파일을 공유**해서 자동으로 연동됩니다.

## 기능 (데모 버전)
- 층 선택 → 도면 위에 마커 표시 (🔵 콘센트 / 🟢 에어컨, 색은 상태)
- 마커 클릭 → 오른쪽 패널에 **상태 · 평균 별점 · 최근 한줄평** 표시
- **평가 등록**: 상태(사용가능/고장/점유) + 별점(1~5) + 한줄평 → CSV 저장
- **편집 모드**: 도면을 클릭해 새 콘센트/에어컨 위치 등록 (학교 도면을 받으면 바로 위치 찍기)
- 이름으로 기기 검색

> 아직 학교 도면 사진이 없어 **임시 도면**을 그려서 보여줍니다.
> 사진을 받으면 아래 "도면 교체" 참고.

## 실행 방법 ① 데스크톱 앱 (tkinter)
tkinter(Tk 9)가 포함된 파이썬이 필요합니다. 이 맥에는 다음으로 설치돼 있습니다:

```bash
# (최초 1회) Tk 설치 — 이미 설치돼 있으면 생략
brew install python-tk@3.14

# 실행
cd outlet_map
/opt/homebrew/bin/python3.14 main.py
```

또는 Finder에서 **`run.command`** 더블클릭으로 실행할 수 있습니다.

## 실행 방법 ② 웹 데모 (브라우저)
웹서버는 파이썬 기본 라이브러리만 쓰므로 tkinter가 없어도 됩니다.

```bash
cd outlet_map
/opt/homebrew/bin/python3.14 web_server.py   # 또는 python3 web_server.py
# → 브라우저에서 http://localhost:8000 접속
```

또는 Finder에서 **`run_web.command`** 더블클릭(브라우저 자동 실행). 종료는 터미널에서 Ctrl+C.

## 앱 ↔ 웹 연동
앱과 웹은 **같은 `data/*.csv` 텍스트 파일**을 읽고 씁니다. 한쪽에서 평가를 등록하면
다른 쪽에도 반영됩니다(웹은 3초마다 자동 새로고침, 앱은 다시 선택/실행 시 반영).
즉, CSV 파일이 곧 공유 상태 저장소입니다.

## 인터넷 공개 (Netlify, 보기 전용)
Netlify는 정적 사이트만 호스팅하므로(파이썬 서버·파일쓰기 불가), 현재 데이터를
`state.json` 스냅샷으로 굳혀 **보기 전용** 공개 사이트로 배포합니다.

```bash
cd outlet_map
python3 build_static.py     # data/*.csv → web_static/state.json (+ 도면) 생성
```

배포(둘 중 하나):
1. **드래그&드롭 (가장 쉬움)** — https://app.netlify.com/drop 접속(무료 가입) →
   `web_static` 폴더를 페이지에 끌어다 놓으면 `https://이름.netlify.app` 링크 생성.
2. **CLI** — `npx netlify-cli deploy --dir web_static --prod`

> 공개 사이트는 누구나 위치·상태·별점·한줄평을 **열람**만 합니다.
> 평가 등록은 로컬 앱/웹에서 하고, 공개 데이터를 갱신하려면 `build_static.py`를 다시
> 실행한 뒤 `web_static`를 재배포하세요.

## 테스트
```bash
/opt/homebrew/bin/python3.14 tests/test_logic.py   # 핵심 로직 검증
```

## 파일 구조
```
outlet_map/
├─ main.py          # [앱] 실행 + 화면 조립 (상단바·지도·패널 연결)
├─ models.py        # 데이터 모델 + 평균별점/상태 집계 (순수 로직, 앱·웹 공용)
├─ storage.py       # CSV 읽기/쓰기 (없으면 자동 생성 + 샘플 데이터, 앱·웹 공용)
├─ map_view.py      # [앱] 도면 캔버스: 배경/마커 그리기, 클릭 처리
├─ detail_panel.py  # [앱] 오른쪽 정보/평가 입력 패널
├─ web_server.py    # [웹] http.server 기반 서버 (storage·models 재사용)
├─ web/index.html   # [웹] 브라우저 화면 (HTML/CSS/JS)
├─ build_static.py  # [공개] data → web_static/state.json 스냅샷 생성
├─ web_static/      # [공개] Netlify 배포용 정적 사이트 (index.html + state.json)
├─ run.command      # 맥용 더블클릭 실행 (앱)
├─ run_web.command  # 맥용 더블클릭 실행 (웹)
├─ tests/test_logic.py
└─ data/            # ← 앱과 웹이 공유하는 텍스트(CSV) 저장소
   ├─ floors.csv        # 층 목록 (floor_id, name, image_file)
   ├─ devices.csv       # 기기 마커 (id, floor, type, name, x, y[0~1 비율])
   ├─ evaluations.csv   # 평가 기록 (id, device, status, rating, comment, time)
   └─ images/           # 층별 도면 PNG 를 여기에 넣습니다
```

## 학교 도면으로 교체하기
1. 도면 이미지를 `data/images/` 에 넣습니다 (예: `floor1.png`).
2. `data/floors.csv` 의 해당 층 `image_file` 칸에 파일명을 적습니다.
3. 프로그램을 실행하고 **편집 모드**로 도면을 클릭해 기기 위치를 등록합니다.
   - 좌표는 0~1 비율로 저장되어 창 크기가 바뀌어도 위치가 유지됩니다.
