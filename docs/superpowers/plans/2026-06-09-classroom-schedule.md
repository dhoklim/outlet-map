# 강의실 시간표 기능 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 콘센트맵 웹앱 헤더에 "시간표" 탭을 추가하여 614호·706호·707호의 오늘 시간표와 현재 수업 상태(수업 중/빈 강의실)를 표시한다.

**Architecture:** SQLite에 classrooms·schedules 테이블을 추가하고 3개 강의실 전체 시간표를 시드 데이터로 초기화한다. Python 웹서버에 `/api/classrooms/*` 라우트를 추가하고, 프론트엔드는 헤더에 "시간표" 버튼을 붙여 클릭 시 지도 대신 시간표 패널을 표시한다. 상태 계산(수업 중/빈 강의실, 다음 빈 시간)은 순수 함수 `compute_today_status`로 분리해 단위 테스트한다.

**Tech Stack:** Python 3 stdlib (sqlite3, http.server, datetime), Vanilla JS, HTML/CSS

---

## 파일 구조

| 파일 | 변경 내용 |
|------|-----------|
| `outlet_map/models.py` | `Classroom`, `Schedule` 데이터클래스 + `compute_today_status()` 추가 |
| `outlet_map/storage.py` | classrooms/schedules 테이블 + `_seed_classrooms()` + 5개 함수 추가 |
| `outlet_map/web_server.py` | `datetime` import + `do_GET`/`do_POST` 라우트 추가 + `do_DELETE` 추가 |
| `outlet_map/web/index.html` | 시간표 탭 버튼 + 패널 HTML + CSS + JS 함수 추가 |
| `outlet_map/tests/test_logic.py` | 새 모델/스토리지 테스트 추가 |
| `outlet_map/tests/test_web_assets.py` | HTML 구조 테스트 추가 |

---

### Task 1: models.py — Classroom/Schedule 데이터클래스 + compute_today_status

**Files:**
- Modify: `outlet_map/models.py` (현재 95줄)
- Test: `outlet_map/tests/test_logic.py`

- [ ] **Step 1: Write the failing tests**

`outlet_map/tests/test_logic.py` 파일 끝에 추가 (기존 코드 뒤에):

```python
def test_compute_today_status_during_class():
    from models import Schedule, compute_today_status
    schedules = [
        Schedule(1, 1, 1, "09:00", "10:30", "고급프로그래밍", "홍길동"),
        Schedule(2, 1, 1, "11:00", "12:30", "알고리즘",     "이순신"),
    ]
    result = compute_today_status(schedules, "09:45")
    assert result["status"] == "수업 중"
    assert result["current_course"] == "고급프로그래밍"
    assert result["current_professor"] == "홍길동"
    assert result["next_free"] == "10:30"


def test_compute_today_status_free():
    from models import Schedule, compute_today_status
    schedules = [
        Schedule(1, 1, 1, "09:00", "10:30", "고급프로그래밍", "홍길동"),
        Schedule(2, 1, 1, "11:00", "12:30", "알고리즘",     "이순신"),
    ]
    result = compute_today_status(schedules, "10:45")
    assert result["status"] == "빈 강의실"
    assert result["current_course"] is None
    assert result["next_free"] is None


def test_compute_today_status_chained_classes():
    from models import Schedule, compute_today_status
    # 10:30 종료 즉시 10:30 시작 → 연속 블록
    schedules = [
        Schedule(1, 1, 1, "09:00", "10:30", "과목A", "교수A"),
        Schedule(2, 1, 1, "10:30", "12:00", "과목B", "교수B"),
    ]
    result = compute_today_status(schedules, "09:30")
    assert result["status"] == "수업 중"
    assert result["next_free"] == "12:00"  # 연속 블록 전체 끝 시간


def test_compute_today_status_empty():
    from models import compute_today_status
    result = compute_today_status([], "10:00")
    assert result["status"] == "빈 강의실"
    assert result["current_course"] is None
    assert result["next_free"] is None
```

- [ ] **Step 2: Run to confirm FAIL**

```bash
cd /Users/dhoklim/Documents/AdvPrograming/outlet_map
python3 -m pytest tests/test_logic.py::test_compute_today_status_during_class -v
```

Expected output: `FAILED` — `ImportError: cannot import name 'Schedule' from 'models'`

- [ ] **Step 3: Add dataclasses and compute_today_status to models.py**

`outlet_map/models.py` 에서 `class DeviceSummary:` 블록 이후(line 55 부근), `def summarize(` 바로 앞에 삽입:

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
    day_of_week: int   # 0=월 1=화 2=수 3=목 4=금
    start_time: str    # "HH:MM"
    end_time: str      # "HH:MM"
    course_name: str
    professor: str


def compute_today_status(schedules: list, now_hhmm: str) -> dict:
    """오늘 시간표 목록과 현재 시각(HH:MM)으로 강의실 상태를 계산한다."""
    sorted_s = sorted(schedules, key=lambda s: s.start_time)
    current = next(
        (s for s in sorted_s if s.start_time <= now_hhmm < s.end_time),
        None,
    )
    if current:
        # 연속 수업 블록의 마지막 종료 시각 계산
        end = current.end_time
        while True:
            chained = next((s for s in sorted_s if s.start_time == end), None)
            if chained:
                end = chained.end_time
            else:
                break
        return {
            "status": "수업 중",
            "current_course": current.course_name,
            "current_professor": current.professor,
            "next_free": end,
        }
    return {
        "status": "빈 강의실",
        "current_course": None,
        "current_professor": None,
        "next_free": None,
    }
```

- [ ] **Step 4: Run to confirm PASS**

```bash
python3 -m pytest tests/test_logic.py::test_compute_today_status_during_class \
  tests/test_logic.py::test_compute_today_status_free \
  tests/test_logic.py::test_compute_today_status_chained_classes \
  tests/test_logic.py::test_compute_today_status_empty -v
```

Expected: `4 passed`

- [ ] **Step 5: Run existing tests — no regression**

```bash
python3 tests/test_logic.py
```

Expected: `3개 테스트 통과`

- [ ] **Step 6: Commit**

```bash
git -C /Users/dhoklim/Documents/AdvPrograming/outlet_map add models.py tests/test_logic.py
git -C /Users/dhoklim/Documents/AdvPrograming/outlet_map commit -m "feat: add Classroom/Schedule models and compute_today_status"
```

---

### Task 2: storage.py — classrooms/schedules 테이블 + 시드 + 스토리지 함수

**Files:**
- Modify: `outlet_map/storage.py`
- Test: `outlet_map/tests/test_logic.py`

**Note:** storage.py를 읽고 시작. `ensure_data_files()`의 `executescript` 블록을 교체하고, `_seed_classrooms()` 함수와 5개 스토리지 함수를 추가한다.

- [ ] **Step 1: Write the failing tests**

`outlet_map/tests/test_logic.py` 파일 끝에 추가:

```python
def test_load_classrooms_returns_seeded_data():
    storage.ensure_data_files()
    classrooms = storage.load_classrooms()
    assert len(classrooms) == 3
    names = [c.name for c in classrooms]
    assert "614호" in names
    assert "706호" in names
    assert "707호" in names


def test_load_today_schedules_filters_by_day():
    storage.ensure_data_files()
    classrooms = storage.load_classrooms()
    cls_614 = next(c for c in classrooms if c.name == "614호")
    # 화요일(1): 614호에 2개 수업
    tue = storage.load_today_schedules(cls_614.classroom_id, 1)
    assert len(tue) >= 2
    assert all(s.day_of_week == 1 for s in tue)
    # 월요일(0): 614호에 수업 없음
    mon = storage.load_today_schedules(cls_614.classroom_id, 0)
    assert len(mon) == 0


def test_add_and_delete_schedule():
    storage.ensure_data_files()
    c = storage.add_classroom("테스트강의실", "1층", "Test Room")
    assert c.classroom_id > 0
    s = storage.add_schedule(c.classroom_id, 2, "09:00", "10:30", "테스트과목", "테스트교수")
    assert s.schedule_id > 0
    rows = storage.load_today_schedules(c.classroom_id, 2)
    assert any(r.schedule_id == s.schedule_id for r in rows)
    storage.delete_schedule(s.schedule_id)
    rows_after = storage.load_today_schedules(c.classroom_id, 2)
    assert not any(r.schedule_id == s.schedule_id for r in rows_after)
```

- [ ] **Step 2: Run to confirm FAIL**

```bash
python3 -m pytest tests/test_logic.py::test_load_classrooms_returns_seeded_data -v
```

Expected: `FAILED` — `AttributeError: module 'storage' has no attribute 'load_classrooms'`

- [ ] **Step 3: Update ensure_data_files() — executescript 블록 교체**

`outlet_map/storage.py` 의 `ensure_data_files()` 함수 전체를 아래로 교체:

```python
def ensure_data_files() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with _get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS floors (
                floor_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                image_file TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS devices (
                device_id INTEGER PRIMARY KEY AUTOINCREMENT,
                floor_id  INTEGER NOT NULL,
                type      TEXT NOT NULL,
                name      TEXT NOT NULL,
                x         REAL NOT NULL,
                y         REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS evaluations (
                eval_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id  INTEGER NOT NULL,
                status     TEXT NOT NULL,
                rating     INTEGER NOT NULL,
                comment    TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS classrooms (
                classroom_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT NOT NULL,
                floor        TEXT NOT NULL DEFAULT '',
                room_label   TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS schedules (
                schedule_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                classroom_id INTEGER NOT NULL,
                day_of_week  INTEGER NOT NULL,
                start_time   TEXT NOT NULL,
                end_time     TEXT NOT NULL,
                course_name  TEXT NOT NULL,
                professor    TEXT NOT NULL DEFAULT ''
            );
        """)
        if conn.execute("SELECT COUNT(*) FROM floors").fetchone()[0] == 0:
            _seed(conn)
        if conn.execute("SELECT COUNT(*) FROM classrooms").fetchone()[0] == 0:
            _seed_classrooms(conn)
```

- [ ] **Step 4: Add _seed_classrooms() function**

`outlet_map/storage.py` 에서 기존 `_seed()` 함수 바로 다음에 삽입:

```python
def _seed_classrooms(conn: sqlite3.Connection) -> None:
    classrooms = [
        ("614호", "6층", "Lecture Room 02"),
        ("706호", "7층", "Lecture Room 03"),
        ("707호", "7층", "Lecture Room 04"),
    ]
    for name, floor, label in classrooms:
        conn.execute(
            "INSERT INTO classrooms (name, floor, room_label) VALUES (?, ?, ?)",
            (name, floor, label),
        )
    # classroom_id 순서: 1=614호, 2=706호, 3=707호
    schedules = [
        # 614호 (id=1)
        (1, 1, "10:30", "12:30", "모바일 컴퓨팅",               "김윤지"),
        (1, 1, "14:30", "16:30", "모바일 컴퓨팅",               "김윤지"),
        (1, 2, "10:30", "12:00", "캡스톤 디자인 프로젝트 II",   "정재필"),
        (1, 2, "15:30", "17:30", "메타버스와 디지털변환",        "서상현"),
        (1, 3, "10:30", "12:30", "고급 인터랙티브 미디어디자인", "김윤지"),
        (1, 4, "13:00", "14:30", "지능형영상비전",               "김영빈"),
        (1, 4, "17:30", "18:30", "CAU세미나(1)",                 "서상현"),
        (1, 4, "18:30", "19:30", "CAU세미나(1)",                 "임상순"),
        # 706호 (id=2)
        (2, 0, "11:30", "13:30", "영상처리 및 비전",   "최종원"),
        (2, 0, "14:30", "16:30", "영상처리 및 비전",   "김학구"),
        (2, 1, "10:30", "12:00", "기초 프로그래밍",    "서상현"),
        (2, 3, "10:30", "12:00", "기초 프로그래밍",    "서상현"),
        (2, 1, "14:30", "16:00", "기초 프로그래밍",    "서상현"),
        (2, 3, "14:30", "16:00", "기초 프로그래밍",    "서상현"),
        (2, 2, "10:30", "12:00", "라이팅 테크놀로지",  "이설의"),
        (2, 2, "13:00", "14:30", "라이팅 테크놀로지",  "이설의"),
        (2, 2, "15:30", "17:30", "라이팅 테크놀로지",  "이설의"),
        (2, 4, "18:30", "19:30", "CAU세미나(1)",       "이대론"),
        # 707호 (id=3)
        (3, 0, "11:30", "13:30", "게임엔진 2",               "김정호"),
        (3, 0, "14:30", "16:30", "게임엔진 2",               "김정호"),
        (3, 1, "09:30", "10:30", "기초 프로그래밍",          "임상순"),
        (3, 3, "09:30", "10:30", "기초 프로그래밍",          "임상순"),
        (3, 1, "09:30", "10:30", "표준웹테크놀로지",         "김관희"),
        (3, 3, "09:30", "10:30", "표준웹테크놀로지",         "김관희"),
        (3, 1, "11:30", "13:00", "표준웹테크놀로지",         "김관희"),
        (3, 3, "11:30", "13:00", "표준웹테크놀로지",         "김관희"),
        (3, 1, "13:00", "16:30", "기초 프로그래밍",          "임상순"),
        (3, 3, "13:00", "16:30", "기초 프로그래밍",          "임상순"),
        (3, 2, "09:30", "11:30", "콘텐츠 빅데이터 처리",     "임상순"),
        (3, 2, "13:00", "15:00", "시각효과 프로덕션",        "유태경"),
        (3, 2, "15:30", "17:30", "시각효과 프로덕션",        "유태경"),
        (3, 4, "10:30", "12:30", "크리에이티브 테크놀로지",  "정재필"),
        (3, 4, "14:30", "16:30", "크리에이티브 테크놀로지",  "정재필"),
        (3, 4, "17:30", "18:30", "CAU세미나(1)",             "김관지"),
        (3, 4, "18:30", "19:30", "CAU세미나(1)",             "신태일"),
    ]
    conn.executemany(
        "INSERT INTO schedules"
        " (classroom_id, day_of_week, start_time, end_time, course_name, professor)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        schedules,
    )
```

- [ ] **Step 5: Add 5 storage functions**

`_seed_classrooms()` 바로 다음에 삽입:

```python
def load_classrooms() -> list:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT classroom_id, name, floor, room_label FROM classrooms ORDER BY classroom_id"
        ).fetchall()
        return [Classroom(r["classroom_id"], r["name"], r["floor"], r["room_label"]) for r in rows]


def load_today_schedules(classroom_id: int, day_of_week: int) -> list:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT schedule_id, classroom_id, day_of_week, start_time, end_time,"
            " course_name, professor FROM schedules"
            " WHERE classroom_id = ? AND day_of_week = ? ORDER BY start_time",
            (classroom_id, day_of_week),
        ).fetchall()
        return [
            Schedule(r["schedule_id"], r["classroom_id"], r["day_of_week"],
                     r["start_time"], r["end_time"], r["course_name"], r["professor"])
            for r in rows
        ]


def add_classroom(name: str, floor: str, room_label: str) -> Classroom:
    with _get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO classrooms (name, floor, room_label) VALUES (?, ?, ?)",
            (name, floor, room_label),
        )
        return Classroom(cur.lastrowid, name, floor, room_label)


def add_schedule(classroom_id: int, day_of_week: int, start_time: str,
                 end_time: str, course_name: str, professor: str) -> Schedule:
    with _get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO schedules"
            " (classroom_id, day_of_week, start_time, end_time, course_name, professor)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (classroom_id, day_of_week, start_time, end_time, course_name, professor),
        )
        return Schedule(cur.lastrowid, classroom_id, day_of_week,
                        start_time, end_time, course_name, professor)


def delete_schedule(schedule_id: int) -> None:
    with _get_conn() as conn:
        conn.execute("DELETE FROM schedules WHERE schedule_id = ?", (schedule_id,))
```

- [ ] **Step 6: Update models import in storage.py**

`storage.py` 상단의 import 라인을:

```python
from models import Floor, Device, Evaluation
```

아래로 교체:

```python
from models import Floor, Device, Evaluation, Classroom, Schedule
```

- [ ] **Step 7: Delete old DB to force re-seed**

```bash
rm -f /Users/dhoklim/Documents/AdvPrograming/outlet_map/data/outlet_map.db
```

- [ ] **Step 8: Run new tests**

```bash
cd /Users/dhoklim/Documents/AdvPrograming/outlet_map
python3 -m pytest tests/test_logic.py::test_load_classrooms_returns_seeded_data \
  tests/test_logic.py::test_load_today_schedules_filters_by_day \
  tests/test_logic.py::test_add_and_delete_schedule -v
```

Expected: `3 passed`

- [ ] **Step 9: Run full test suite**

```bash
python3 tests/test_logic.py && python3 tests/test_web_assets.py
```

Expected: 기존 모든 테스트 통과

- [ ] **Step 10: Commit**

```bash
git -C /Users/dhoklim/Documents/AdvPrograming/outlet_map add storage.py tests/test_logic.py
git -C /Users/dhoklim/Documents/AdvPrograming/outlet_map commit -m "feat: add classrooms/schedules storage with seed data for 614/706/707"
```

---

### Task 3: web_server.py — API 라우트 추가

**Files:**
- Modify: `outlet_map/web_server.py`
- Test: 수동 curl 검증

**Note:** web_server.py를 읽고 시작. `do_GET`/`do_POST`에 블록 추가, `do_DELETE` 메서드 신규 추가.

- [ ] **Step 1: Add datetime import and compute_today_status to web_server.py imports**

`web_server.py` 상단 import 섹션에서:

```python
from datetime import datetime
```

를 기존 import 목록에 추가하고, models import 라인을:

```python
from models import (
    STATUS_COLORS, summarize, validate_rating, validate_status, DEVICE_TYPES,
    compute_today_status,
)
```

으로 교체.

- [ ] **Step 2: Add GET /api/classrooms and GET /api/classrooms/{id}/today to do_GET**

`do_GET` 메서드에서 `elif self.path.startswith("/data/images/"):` 블록 바로 앞에 삽입:

```python
        elif self.path == "/api/classrooms":
            classrooms = storage.load_classrooms()
            self._send_json([
                {"classroom_id": c.classroom_id, "name": c.name,
                 "floor": c.floor, "room_label": c.room_label}
                for c in classrooms
            ])
        elif self.path.startswith("/api/classrooms/") and self.path.endswith("/today"):
            parts = self.path.split("/")  # ['', 'api', 'classrooms', '{id}', 'today']
            classroom_id = int(parts[3])
            day_of_week = datetime.now().weekday()  # 0=월 … 4=금
            schedules = storage.load_today_schedules(classroom_id, day_of_week)
            now_hhmm = datetime.now().strftime("%H:%M")
            status_info = compute_today_status(schedules, now_hhmm)
            classrooms = storage.load_classrooms()
            classroom = next((c for c in classrooms if c.classroom_id == classroom_id), None)
            self._send_json({
                "classroom_id": classroom_id,
                "name": classroom.name if classroom else "",
                "status": status_info["status"],
                "current_course": status_info["current_course"],
                "current_professor": status_info["current_professor"],
                "next_free": status_info["next_free"],
                "schedules": [
                    {
                        "schedule_id": s.schedule_id,
                        "start_time": s.start_time,
                        "end_time": s.end_time,
                        "course_name": s.course_name,
                        "professor": s.professor,
                        "is_now": s.start_time <= now_hhmm < s.end_time,
                    }
                    for s in schedules
                ],
            })
```

- [ ] **Step 3: Add POST /api/classrooms and POST /api/classrooms/{id}/schedules to do_POST**

`do_POST` 메서드에서 `elif self.path == "/api/device":` 블록 다음, `else:` 블록 바로 앞에 삽입:

```python
            elif self.path == "/api/classrooms":
                name = str(data["name"]).strip()
                if not name:
                    raise ValueError("강의실 이름을 입력하세요.")
                floor = str(data.get("floor", "")).strip()
                room_label = str(data.get("room_label", "")).strip()
                c = storage.add_classroom(name, floor, room_label)
                self._send_json({"ok": True, "classroom_id": c.classroom_id})
            elif self.path.startswith("/api/classrooms/") and self.path.endswith("/schedules"):
                parts = self.path.split("/")
                classroom_id = int(parts[3])
                day_of_week = int(data["day_of_week"])
                start_time = str(data["start_time"]).strip()
                end_time = str(data["end_time"]).strip()
                course_name = str(data["course_name"]).strip()
                professor = str(data.get("professor", "")).strip()
                s = storage.add_schedule(
                    classroom_id, day_of_week, start_time, end_time, course_name, professor
                )
                self._send_json({"ok": True, "schedule_id": s.schedule_id})
```

- [ ] **Step 4: Add do_DELETE method to Handler class**

`Handler` 클래스에서 `do_POST` 메서드 다음, `log_message` 메서드 앞에 삽입:

```python
    def do_DELETE(self):
        try:
            if self.path.startswith("/api/schedules/"):
                schedule_id = int(self.path.split("/")[-1])
                storage.delete_schedule(schedule_id)
                self._send_json({"ok": True})
            else:
                self._send_json({"error": "not found"}, 404)
        except (ValueError, IndexError):
            self._send_json({"ok": False, "error": "잘못된 요청"}, 400)
```

- [ ] **Step 5: Smoke-test the new routes**

```bash
cd /Users/dhoklim/Documents/AdvPrograming/outlet_map
python3 web_server.py &
sleep 1
curl -s http://localhost:8000/api/classrooms | python3 -m json.tool
```

Expected: `[{"classroom_id": 1, "name": "614호", ...}, ...]` 3개 항목

```bash
curl -s "http://localhost:8000/api/classrooms/1/today" | python3 -m json.tool
```

Expected: `{"classroom_id": 1, "name": "614호", "status": "수업 중" or "빈 강의실", "schedules": [...]}` 구조

```bash
kill %1
```

- [ ] **Step 6: Commit**

```bash
git -C /Users/dhoklim/Documents/AdvPrograming/outlet_map add web_server.py
git -C /Users/dhoklim/Documents/AdvPrograming/outlet_map commit -m "feat: add /api/classrooms/* REST routes"
```

---

### Task 4: web/index.html — 시간표 탭 UI

**Files:**
- Modify: `outlet_map/web/index.html`
- Test: `outlet_map/tests/test_web_assets.py`

**Note:** index.html을 읽고 시작. 파일이 크므로 (`~831줄`) 삽입 위치를 정확히 찾을 것.
- CSS 삽입 위치: `</style>` 바로 앞
- 헤더 버튼: `<div id="tabs"></div>` 바로 다음
- 패널 HTML: `</main>` 바로 다음
- JS 삽입 위치: `initStarRating();` 바로 앞

- [ ] **Step 1: Write the failing test**

`outlet_map/tests/test_web_assets.py` 끝에 추가:

```python
def test_schedule_tab_html_structure():
    html_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "web", "index.html")
    html = open(html_path, encoding="utf-8").read()
    assert 'id="schedule-panel"' in html,   "시간표 패널 없음"
    assert 'id="classroom-chips"' in html,  "강의실 칩 컨테이너 없음"
    assert 'id="schedule-tab-btn"' in html, "시간표 탭 버튼 없음"
    assert 'switchMainTab' in html,         "탭 전환 함수 없음"
    assert 'loadClassrooms' in html,        "강의실 로드 함수 없음"
```

- [ ] **Step 2: Run to confirm FAIL**

```bash
cd /Users/dhoklim/Documents/AdvPrograming/outlet_map
python3 -m pytest tests/test_web_assets.py::test_schedule_tab_html_structure -v
```

Expected: `FAILED` — `AssertionError: 시간표 패널 없음`

- [ ] **Step 3: Add CSS to index.html**

`web/index.html` 에서 `</style>` 바로 앞에 삽입:

```css
  /* ── 시간표 탭 ── */
  #schedule-panel {
    padding: 18px;
    max-width: 600px;
    margin: 0 auto;
  }
  .classroom-chips {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 14px;
    overflow-x: auto;
  }
  .classroom-chip {
    border: 1px solid var(--line);
    background: var(--panel);
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 14px;
    white-space: nowrap;
  }
  .classroom-chip.active {
    background: var(--accent-dark);
    color: var(--accent);
    border-color: var(--accent-dark);
  }
  .schedule-status-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--panel);
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 12px;
    border: 1px solid var(--line);
  }
  .status-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
  .status-text { font-weight: 700; font-size: 14px; }
  .status-next { color: var(--muted); font-size: 13px; }
  .schedule-list { display: flex; flex-direction: column; gap: 8px; }
  .schedule-row {
    background: var(--panel);
    border-radius: 10px;
    padding: 12px 16px;
    border: 1px solid var(--line);
    display: flex;
    gap: 14px;
    align-items: flex-start;
  }
  .schedule-row.now { border-color: var(--green); background: #f0faf4; }
  .sched-time {
    color: var(--muted);
    font-size: 12px;
    white-space: nowrap;
    min-width: 110px;
    margin-top: 2px;
  }
  .sched-course {
    font-weight: 700;
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }
  .sched-prof { color: var(--muted); font-size: 12px; margin-top: 3px; }
  .now-badge {
    background: var(--green);
    color: #fff;
    font-size: 10px;
    padding: 2px 7px;
    border-radius: 10px;
    font-weight: 700;
  }
  .no-schedule { color: var(--muted); text-align: center; padding: 40px 0; }
```

- [ ] **Step 4: Add schedule tab button to header**

`web/index.html` 에서:
```html
  <div id="tabs"></div>
```
를 찾아:
```html
  <div id="tabs"></div>
  <button id="schedule-tab-btn" class="tab" onclick="switchMainTab('schedule')">시간표</button>
```
로 교체.

- [ ] **Step 5: Add schedule panel HTML after </main>**

`web/index.html` 에서 `</main>` 태그 바로 다음 줄에 삽입:

```html
<div id="schedule-panel" style="display:none;">
  <div class="classroom-chips" id="classroom-chips"></div>
  <div class="schedule-status-bar" id="schedule-status-bar">
    <span class="status-dot" id="status-dot" style="background:var(--gray)"></span>
    <span class="status-text" id="status-text">강의실을 선택하세요</span>
  </div>
  <div class="schedule-list" id="schedule-list"></div>
</div>
```

- [ ] **Step 6: Add JS functions before initStarRating()**

`web/index.html` 의 `<script>` 블록에서 `initStarRating();` 바로 앞에 삽입:

```javascript
let classroomList = [];
let scheduleClassroomId = null;

async function switchMainTab(tab) {
  const mainEl = document.querySelector('main');
  const schedPanel = document.getElementById('schedule-panel');
  const schedBtn = document.getElementById('schedule-tab-btn');
  if (tab === 'schedule') {
    mainEl.style.display = 'none';
    schedPanel.style.display = 'block';
    schedBtn.classList.add('active');
    if (classroomList.length === 0) await loadClassrooms();
  } else {
    mainEl.style.display = '';
    schedPanel.style.display = 'none';
    schedBtn.classList.remove('active');
  }
}

async function loadClassrooms() {
  const r = await fetch('/api/classrooms');
  classroomList = await r.json();
  if (classroomList.length) {
    scheduleClassroomId = classroomList[0].classroom_id;
    renderClassroomChips();
    await loadTodaySchedule(scheduleClassroomId);
  }
}

function renderClassroomChips() {
  const el = document.getElementById('classroom-chips');
  el.innerHTML = classroomList.map(c =>
    `<button class="classroom-chip${c.classroom_id === scheduleClassroomId ? ' active' : ''}"
      onclick="selectClassroom(${c.classroom_id})">${c.name}</button>`
  ).join('');
}

async function selectClassroom(id) {
  scheduleClassroomId = id;
  renderClassroomChips();
  await loadTodaySchedule(id);
}

async function loadTodaySchedule(classroomId) {
  const r = await fetch(`/api/classrooms/${classroomId}/today`);
  const data = await r.json();
  const isClass = data.status === '수업 중';
  document.getElementById('status-dot').style.background =
    isClass ? 'var(--red)' : 'var(--green)';
  document.getElementById('status-text').textContent = data.status;
  const statusBar = document.getElementById('schedule-status-bar');
  let nextSpan = statusBar.querySelector('.status-next');
  if (!nextSpan) {
    nextSpan = document.createElement('span');
    nextSpan.className = 'status-next';
    statusBar.appendChild(nextSpan);
  }
  nextSpan.textContent =
    isClass && data.next_free ? `· 다음 빈 시간: ${data.next_free}` : '';
  const listEl = document.getElementById('schedule-list');
  if (!data.schedules.length) {
    listEl.innerHTML = '<p class="no-schedule">오늘 수업 없음</p>';
    return;
  }
  listEl.innerHTML = data.schedules.map(s =>
    `<div class="schedule-row${s.is_now ? ' now' : ''}">
      <div class="sched-time">${s.start_time} – ${s.end_time}</div>
      <div>
        <div class="sched-course">${s.course_name}${s.is_now ? '<span class="now-badge">지금</span>' : ''}</div>
        <div class="sched-prof">${s.professor}</div>
      </div>
    </div>`
  ).join('');
}
```

- [ ] **Step 7: Run the test**

```bash
python3 -m pytest tests/test_web_assets.py::test_schedule_tab_html_structure -v
```

Expected: `PASSED`

- [ ] **Step 8: Run full test suite**

```bash
python3 tests/test_web_assets.py && python3 tests/test_logic.py
```

Expected: 모든 테스트 통과

- [ ] **Step 9: Verify in browser**

```bash
cd /Users/dhoklim/Documents/AdvPrograming/outlet_map
python3 web_server.py &
sleep 1
open http://localhost:8000
```

확인 체크리스트:
- [ ] 헤더에 "시간표" 버튼 표시됨
- [ ] "시간표" 클릭 → 지도 숨김, 시간표 패널 표시됨
- [ ] 614호 / 706호 / 707호 칩 표시됨
- [ ] 강의실 칩 클릭 시 해당 강의실 시간표로 전환됨
- [ ] 상태 바에 수업 중/빈 강의실 + 색상 표시됨
- [ ] 수업 행에 시간·과목명·교수 표시됨
- [ ] 현재 수업 행에 초록 테두리 + "지금" 배지 표시됨
- [ ] 지도 탭(floor 버튼) 클릭 시 지도로 복귀됨

```bash
kill %1
```

- [ ] **Step 10: Commit**

```bash
git -C /Users/dhoklim/Documents/AdvPrograming/outlet_map add web/index.html tests/test_web_assets.py
git -C /Users/dhoklim/Documents/AdvPrograming/outlet_map commit -m "feat: add classroom schedule tab UI with status and timetable"
```
