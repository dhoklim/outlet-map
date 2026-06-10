# 강의실 시간표 기능 설계

## 개요

콘센트맵 웹앱에 강의실 시간표 조회 기능을 추가한다. 헤더에 "지도 / 시간표" 탭을 추가하고, 시간표 탭에서 강의실별 오늘 시간표와 현재 수업 상태(수업 중 / 빈 강의실)를 표시한다.

---

## 요구사항

- 강의실 3개 지원: 614호, 706호, 707호
- 각 강의실별 요일·시간대 시간표 저장 (수동 입력, 이후 수정 가능)
- 오늘 요일 기준으로 시간표 필터링
- 현재 시각 기준으로 "수업 중 / 빈 강의실" 상태 자동 계산
- 다음 빈 시간 표시
- 교수명 표시
- 기존 지도 기능은 그대로 유지

---

## 데이터 모델

### 새 테이블: `classrooms`

```sql
CREATE TABLE IF NOT EXISTS classrooms (
    classroom_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,       -- "614호"
    floor        TEXT DEFAULT '',     -- "6층"
    room_label   TEXT DEFAULT ''      -- "Lecture Room 02"
);
```

### 새 테이블: `schedules`

```sql
CREATE TABLE IF NOT EXISTS schedules (
    schedule_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    classroom_id INTEGER NOT NULL,
    day_of_week  INTEGER NOT NULL,    -- 0=월 1=화 2=수 3=목 4=금
    start_time   TEXT NOT NULL,       -- "10:30"
    end_time     TEXT NOT NULL,       -- "12:30"
    course_name  TEXT NOT NULL,       -- "모바일 컴퓨팅"
    professor    TEXT DEFAULT ''      -- "김윤지"
);
```

**화/목 같은 복합 요일은 두 개의 행으로 분리 저장.** 예: 화/목 09:30–10:30 → day_of_week=1 행 + day_of_week=3 행.

### 시드 데이터

아래 3개 강의실 데이터를 `_seed()` 에서 함께 초기화:

**614호 (6층, Lecture Room 02)**
| 요일 | 시간 | 과목명 | 교수 |
|------|------|--------|------|
| 화(1) | 10:30–12:30 | 모바일 컴퓨팅 | 김윤지 |
| 화(1) | 14:30–16:30 | 모바일 컴퓨팅 | 김윤지 |
| 수(2) | 10:30–12:00 | 캡스톤 디자인 프로젝트 II | 정재필 |
| 수(2) | 15:30–17:30 | 메타버스와 디지털변환 | 서상현 |
| 목(3) | 10:30–12:30 | 고급 인터랙티브 미디어디자인 | 김윤지 |
| 금(4) | 13:00–14:30 | 지능형영상비전 | 김영빈 |
| 금(4) | 17:30–18:30 | CAU세미나(1) | 서상현 |
| 금(4) | 18:30–19:30 | CAU세미나(1) | 임상순 |

**706호 (7층, Lecture Room 03)**
| 요일 | 시간 | 과목명 | 교수 |
|------|------|--------|------|
| 월(0) | 11:30–13:30 | 영상처리 및 비전 | 최종원 |
| 월(0) | 14:30–16:30 | 영상처리 및 비전 | 김학구 |
| 화(1) | 10:30–12:00 | 기초 프로그래밍 | 서상현 |
| 목(3) | 10:30–12:00 | 기초 프로그래밍 | 서상현 |
| 화(1) | 14:30–16:00 | 기초 프로그래밍 | 서상현 |
| 목(3) | 14:30–16:00 | 기초 프로그래밍 | 서상현 |
| 수(2) | 10:30–12:00 | 라이팅 테크놀로지 | 이설의 |
| 수(2) | 13:00–14:30 | 라이팅 테크놀로지 | 이설의 |
| 수(2) | 15:30–17:30 | 라이팅 테크놀로지 | 이설의 |
| 금(4) | 18:30–19:30 | CAU세미나(1) | 이대론 |

**707호 (7층, Lecture Room 04)**
| 요일 | 시간 | 과목명 | 교수 |
|------|------|--------|------|
| 월(0) | 11:30–13:30 | 게임엔진 2 | 김정호 |
| 월(0) | 14:30–16:30 | 게임엔진 2 | 김정호 |
| 화(1) | 09:30–10:30 | 기초 프로그래밍 | 임상순 |
| 목(3) | 09:30–10:30 | 기초 프로그래밍 | 임상순 |
| 화(1) | 09:30–10:30 | 표준웹테크놀로지 | 김관희 |
| 목(3) | 09:30–10:30 | 표준웹테크놀로지 | 김관희 |
| 화(1) | 11:30–13:00 | 표준웹테크놀로지 | 김관희 |
| 목(3) | 11:30–13:00 | 표준웹테크놀로지 | 김관희 |
| 화(1) | 13:00–16:30 | 기초 프로그래밍 | 임상순 |
| 목(3) | 13:00–16:30 | 기초 프로그래밍 | 임상순 |
| 수(2) | 09:30–11:30 | 콘텐츠 빅데이터 처리 | 임상순 |
| 수(2) | 13:00–15:00 | 시각효과 프로덕션 | 유태경 |
| 수(2) | 15:30–17:30 | 시각효과 프로덕션 | 유태경 |
| 금(4) | 10:30–12:30 | 크리에이티브 테크놀로지 | 정재필 |
| 금(4) | 14:30–16:30 | 크리에이티브 테크놀로지 | 정재필 |
| 금(4) | 17:30–18:30 | CAU세미나(1) | 김관지 |
| 금(4) | 18:30–19:30 | CAU세미나(1) | 신태일 |

---

## 백엔드 API

`web_server.py` 에 라우트 추가.

### `GET /api/classrooms`

전체 강의실 목록 반환.

```json
[
  {"classroom_id": 1, "name": "614호", "floor": "6층", "room_label": "Lecture Room 02"},
  {"classroom_id": 2, "name": "706호", "floor": "7층", "room_label": "Lecture Room 03"},
  {"classroom_id": 3, "name": "707호", "floor": "7층", "room_label": "Lecture Room 04"}
]
```

### `GET /api/classrooms/{classroom_id}/today`

오늘 요일(파이썬 `datetime.weekday()` 0=월~4=금)로 시간표 조회 후, 현재 시각 기준 상태 계산해서 반환.

```json
{
  "classroom_id": 1,
  "name": "614호",
  "status": "수업 중",
  "current_course": "모바일 컴퓨팅",
  "current_professor": "김윤지",
  "next_free": "12:30",
  "schedules": [
    {
      "schedule_id": 1,
      "start_time": "10:30",
      "end_time": "12:30",
      "course_name": "모바일 컴퓨팅",
      "professor": "김윤지",
      "is_now": true
    }
  ]
}
```

- `status`: `"수업 중"` | `"빈 강의실"`
- `current_course`: 현재 수업 중이면 과목명, 아니면 `null`
- `next_free`: 다음 빈 시간 시작 시각 (문자열, 없으면 `null`)
- `schedules`: 오늘 시간표 목록 (시작 시각 오름차순)
- `is_now`: 현재 시각이 해당 수업 시간 안에 있으면 `true`

`status`와 `next_free`는 서버에서 계산. 클라이언트는 표시만 한다.

### `POST /api/classrooms`

강의실 추가 (관리용).

Request body:
```json
{"name": "608호", "floor": "6층", "room_label": ""}
```

### `POST /api/classrooms/{classroom_id}/schedules`

수업 추가 (관리용).

Request body:
```json
{
  "day_of_week": 1,
  "start_time": "10:30",
  "end_time": "12:30",
  "course_name": "모바일 컴퓨팅",
  "professor": "김윤지"
}
```

### `DELETE /api/schedules/{schedule_id}`

수업 삭제 (관리용).

---

## 프론트엔드

`web/index.html` 수정.

### 헤더 탭 전환

헤더 오른쪽에 탭 두 개 추가:

```html
<div id="tab-map" class="tab active" onclick="switchTab('map')">지도</div>
<div id="tab-schedule" class="tab" onclick="switchTab('schedule')">시간표</div>
```

`switchTab('map')`: `#map-view` 표시, `#schedule-view` 숨김  
`switchTab('schedule')`: `#map-view` 숨김, `#schedule-view` 표시 + 첫 번째 강의실 로드

### 시간표 패널 구조 (`#schedule-view`)

```
┌─────────────────────────────┐
│ [614호]  [706호]  [707호]    │  ← 강의실 선택 칩 (가로 스크롤)
├─────────────────────────────┤
│ 🔴 수업 중 · 다음 빈 시간: 12:30│  ← 상태 바
├─────────────────────────────┤
│ 10:30 – 12:30               │
│ 모바일 컴퓨팅        [지금]   │  ← 시간표 행 (is_now=true면 배지)
│ 김윤지                       │
│──────────────────────────── │
│ 14:30 – 16:30               │
│ 모바일 컴퓨팅                │
│ 김윤지                       │
└─────────────────────────────┘
```

- 강의실 칩 클릭 → `GET /api/classrooms/{id}/today` 호출 → 패널 업데이트
- 오늘 수업 없으면 "오늘 수업 없음" 메시지 표시
- 빈 강의실 상태면 상태 바 초록색

### 기존 기능 영향 없음

- `#map-view` (지도, 마커, 바텀 시트)는 변경 없이 유지
- 탭 전환은 CSS `display` 토글로 처리

---

## storage.py 변경사항

- `ensure_data_files()`: classrooms, schedules 테이블 CREATE 추가
- `_seed()`: 위 3개 강의실 + 전체 시간표 데이터 삽입
- 새 함수 추가:
  - `load_classrooms() -> list[Classroom]`
  - `load_today_schedules(classroom_id, day_of_week) -> list[Schedule]`
  - `add_classroom(name, floor, room_label) -> Classroom`
  - `add_schedule(classroom_id, day_of_week, start_time, end_time, course_name, professor) -> Schedule`
  - `delete_schedule(schedule_id) -> None`

---

## models.py 변경사항

`Classroom`, `Schedule` 데이터클래스 추가:

```python
@dataclass
class Classroom:
    classroom_id: int
    name: str
    floor: str
    room_label: str

@dataclass
class Schedule:
    schedule_id: int
    classroom_id: int
    day_of_week: int
    start_time: str
    end_time: str
    course_name: str
    professor: str
```

---

## 범위 외 (구현 안 함)

- 강의실 관리 어드민 UI (데이터는 시드로 충분)
- 강의실 추가/삭제 (API는 있으나 UI는 없음)
- 주차별 시간표 차이 처리
- 공휴일/휴강 처리
