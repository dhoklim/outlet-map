# Render + PostgreSQL 배포 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 콘센트맵 웹 앱을 Render + PostgreSQL로 영구 배포해 누구나 접속 가능한 URL을 발급한다.

**Architecture:** `storage.py`의 CSV 읽기/쓰기를 psycopg2 PostgreSQL로 교체한다. `web_server.py`는 `0.0.0.0`과 `PORT` 환경변수를 사용하도록 수정한다. `render.yaml`로 Render가 DB와 웹 서비스를 자동 생성한다.

**Tech Stack:** Python 3, psycopg2-binary, Render (Web Service + PostgreSQL free tier)

---

## 파일 변경 목록

| 파일 | 작업 |
|---|---|
| `requirements.txt` | 신규 생성 |
| `render.yaml` | 신규 생성 |
| `storage.py` | 전체 교체 (CSV → PostgreSQL) |
| `web_server.py` | 2줄 수정 (host, port) |
| `tests/test_logic.py` | storage 테스트 DB 환경변수 조건부 처리 |
| `tests/test_web_assets.py` | 동일 |

---

## Task 1: requirements.txt 생성

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: 파일 생성**

```
psycopg2-binary
```

- [ ] **Step 2: 설치 확인**

```bash
pip install -r requirements.txt
```

Expected: `Successfully installed psycopg2-binary-...`

- [ ] **Step 3: 커밋**

```bash
git add requirements.txt
git commit -m "chore: add psycopg2-binary dependency"
```

---

## Task 2: render.yaml 생성

**Files:**
- Create: `render.yaml`

- [ ] **Step 1: 파일 생성**

```yaml
services:
  - type: web
    name: outlet-map
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: python web_server.py
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: outlet-map-db
          property: connectionString

databases:
  - name: outlet-map-db
    plan: free
```

- [ ] **Step 2: 커밋**

```bash
git add render.yaml
git commit -m "chore: add Render deployment config"
```

---

## Task 3: web_server.py 수정

**Files:**
- Modify: `web_server.py` (PORT 상수 및 서버 바인드 주소)

- [ ] **Step 1: 실패 테스트 확인 (현재 동작 기록)**

```bash
python3 -c "
import web_server, inspect
src = inspect.getsource(web_server.main)
assert '127.0.0.1' in src, 'already patched?'
print('FAIL (expected) - still binds to 127.0.0.1')
"
```

Expected: `FAIL (expected) - still binds to 127.0.0.1`

- [ ] **Step 2: PORT 상수와 바인드 주소 수정**

`web_server.py` 161~163행을:

```python
def main():
    storage.ensure_data_files()
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"콘센트맵 웹 데모 실행 중 →  http://localhost:{PORT}")
```

아래로 교체:

```python
def main():
    storage.ensure_data_files()
    port = int(os.environ.get("PORT", 8000))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"콘센트맵 웹 데모 실행 중 →  http://localhost:{port}")
```

그리고 파일 상단의 `PORT = 8000` 상수 줄을 삭제한다.

- [ ] **Step 3: 수정 확인**

```bash
python3 -c "
import web_server, inspect
src = inspect.getsource(web_server.main)
assert '0.0.0.0' in src
assert 'PORT' not in src or 'os.environ' in src
print('PASS')
"
```

Expected: `PASS`

- [ ] **Step 4: 커밋**

```bash
git add web_server.py
git commit -m "fix: bind to 0.0.0.0 and read PORT from env for Render"
```

---

## Task 4: storage.py 교체 (CSV → PostgreSQL)

**Files:**
- Modify: `storage.py` (전체 교체)

- [ ] **Step 1: 현재 테스트가 통과하는지 확인**

```bash
cd /Users/dhoklim/Documents/AdvPrograming/outlet_map
python3 tests/test_logic.py
```

Expected: `4개 테스트 통과`

- [ ] **Step 2: storage.py 전체 교체**

```python
"""PostgreSQL 읽기/쓰기. DATABASE_URL 환경변수로 연결."""
from __future__ import annotations

import os
from datetime import datetime

import psycopg2
import psycopg2.extras

from models import Floor, Device, Evaluation

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")


def _get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def ensure_data_files() -> None:
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS floors (
                    floor_id   SERIAL PRIMARY KEY,
                    name       TEXT NOT NULL,
                    image_file TEXT NOT NULL DEFAULT ''
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    device_id SERIAL PRIMARY KEY,
                    floor_id  INT  NOT NULL,
                    type      TEXT NOT NULL,
                    name      TEXT NOT NULL,
                    x         REAL NOT NULL,
                    y         REAL NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS evaluations (
                    eval_id    SERIAL PRIMARY KEY,
                    device_id  INT  NOT NULL,
                    status     TEXT NOT NULL,
                    rating     INT  NOT NULL,
                    comment    TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                )
            """)
            cur.execute("SELECT COUNT(*) FROM floors")
            if cur.fetchone()[0] == 0:
                _seed(cur)
        conn.commit()


def _seed(cur) -> None:
    cur.execute(
        "INSERT INTO floors (name, image_file) VALUES (%s, %s)",
        ("8706-1707호", "room_8706_1707_map.png"),
    )
    sample_devices = [
        (1, "콘센트", "칠판 왼쪽 콘센트",         0.27, 0.13),
        (1, "콘센트", "칠판 오른쪽 콘센트",        0.75, 0.13),
        (1, "콘센트", "왼쪽 출입문 콘센트",        0.18, 0.92),
        (1, "콘센트", "왼쪽 출입문 안쪽 콘센트",   0.27, 0.92),
        (1, "콘센트", "오른쪽 출입문 왼편 콘센트", 0.76, 0.92),
        (1, "콘센트", "오른쪽 출입문 오른편 콘센트", 0.86, 0.92),
        (1, "에어컨", "중앙 벽면 에어컨",          0.53, 0.55),
        (1, "에어컨", "창가 에어컨",               0.91, 0.55),
    ]
    for floor_id, dtype, name, x, y in sample_devices:
        cur.execute(
            "INSERT INTO devices (floor_id, type, name, x, y) VALUES (%s, %s, %s, %s, %s)",
            (floor_id, dtype, name, x, y),
        )
    sample_evals = [
        (1, "사용가능", 5, "칠판 앞이라 발표 준비할 때 쓰기 좋아요"),
        (2, "사용가능", 4, "교탁 쪽에서 접근하기 쉬움"),
        (3, "점유",    3, "문 근처라 사람이 자주 지나가요"),
        (4, "사용가능", 4, "창가 자리에서 쓰기 무난함"),
        (7, "사용가능", 4, "강의실 중앙 냉방이 잘 됩니다"),
        (8, "사용가능", 3, "창가 쪽은 햇빛 때문에 조금 더워요"),
    ]
    for device_id, status, rating, comment in sample_evals:
        cur.execute(
            "INSERT INTO evaluations (device_id, status, rating, comment, created_at)"
            " VALUES (%s, %s, %s, %s, %s)",
            (device_id, status, rating, comment, "2026-06-01 12:00"),
        )


def load_floors() -> list:
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT floor_id, name, image_file FROM floors ORDER BY floor_id")
            return [Floor(r["floor_id"], r["name"], r["image_file"]) for r in cur.fetchall()]


def load_devices() -> list:
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                "SELECT device_id, floor_id, type, name, x, y FROM devices ORDER BY device_id"
            )
            return [
                Device(r["device_id"], r["floor_id"], r["type"], r["name"], r["x"], r["y"])
                for r in cur.fetchall()
            ]


def load_evaluations() -> list:
    with _get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                "SELECT eval_id, device_id, status, rating, comment, created_at"
                " FROM evaluations ORDER BY eval_id"
            )
            return [
                Evaluation(r["eval_id"], r["device_id"], r["status"],
                           r["rating"], r["comment"], r["created_at"])
                for r in cur.fetchall()
            ]


def add_device(floor_id: int, dtype: str, name: str, x: float, y: float) -> Device:
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO devices (floor_id, type, name, x, y)"
                " VALUES (%s, %s, %s, %s, %s) RETURNING device_id",
                (floor_id, dtype, name, round(x, 4), round(y, 4)),
            )
            device_id = cur.fetchone()[0]
        conn.commit()
    return Device(device_id, floor_id, dtype, name, round(x, 4), round(y, 4))


def add_evaluation(device_id: int, status: str, rating: int, comment: str) -> Evaluation:
    created = datetime.now().strftime("%Y-%m-%d %H:%M")
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO evaluations (device_id, status, rating, comment, created_at)"
                " VALUES (%s, %s, %s, %s, %s) RETURNING eval_id",
                (device_id, status, rating, comment, created),
            )
            eval_id = cur.fetchone()[0]
        conn.commit()
    return Evaluation(eval_id, device_id, status, rating, comment, created)
```

- [ ] **Step 3: 순수 모델 테스트 여전히 통과하는지 확인**

```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from models import Device, Evaluation, summarize, validate_rating, validate_status

dev = Device(1, 1, '콘센트', 'test', 0.1, 0.1)
evals = [Evaluation(1, 1, '고장', 1, 'x', '2026-06-01'), Evaluation(2, 1, '사용가능', 5, 'ok', '2026-06-01')]
s = summarize(dev, evals)
assert s.count == 2 and s.avg_rating == 3.0 and s.latest_status == '사용가능'
assert validate_rating('3') == 3
assert validate_status('고장') == '고장'
print('PASS: 모델 단위 테스트')
"
```

Expected: `PASS: 모델 단위 테스트`

- [ ] **Step 4: 커밋**

```bash
git add storage.py
git commit -m "feat: migrate storage from CSV to PostgreSQL"
```

---

## Task 5: 테스트 파일 업데이트

**Files:**
- Modify: `tests/test_logic.py`
- Modify: `tests/test_web_assets.py`

- [ ] **Step 1: test_logic.py 교체**

```python
"""storage/models 순수 로직 검증.

순수 모델 테스트(test_summarize_*, test_validators)는 DB 없이 실행 가능.
storage 통합 테스트는 DATABASE_URL 환경변수가 필요하다:
    DATABASE_URL=postgres://... pytest tests/test_logic.py -v
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import storage  # noqa: E402
from models import (  # noqa: E402
    Device, Evaluation, summarize, validate_rating, validate_status,
)

_NEED_DB = os.getenv("DATABASE_URL") is None


def _truncate():
    import psycopg2
    with psycopg2.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "TRUNCATE floors, devices, evaluations RESTART IDENTITY CASCADE"
            )
        conn.commit()


def test_summarize_average_and_latest():
    dev = Device(1, 1, "콘센트", "test", 0.1, 0.1)
    evals = [
        Evaluation(1, 1, "고장",    1, "x",     "2026-06-01 10:00"),
        Evaluation(2, 1, "사용가능", 5, "ok",    "2026-06-01 11:00"),
        Evaluation(3, 2, "점유",    2, "other", "2026-06-01 12:00"),
    ]
    s = summarize(dev, evals)
    assert s.count == 2
    assert s.avg_rating == 3.0
    assert s.latest_status == "사용가능"
    assert s.color == "#1f9d55"


def test_summarize_empty():
    dev = Device(9, 1, "에어컨", "none", 0.5, 0.5)
    s = summarize(dev, [])
    assert s.count == 0 and s.avg_rating is None
    assert s.latest_status is None and s.color == "#9aa0a6"


def test_validators():
    assert validate_rating("3") == 3
    assert validate_status("고장") == "고장"
    for bad in ("0", "6", "abc", None):
        try:
            validate_rating(bad)
            assert False, f"{bad} should fail"
        except ValueError:
            pass
    try:
        validate_status("이상한값")
        assert False
    except ValueError:
        pass


def test_storage_roundtrip():
    if _NEED_DB:
        import pytest
        pytest.skip("DATABASE_URL 미설정 — 통합 테스트 건너뜀")

    _truncate()
    storage.ensure_data_files()

    floors = storage.load_floors()
    devices = storage.load_devices()
    evals = storage.load_evaluations()
    assert len(floors) == 1
    assert floors[0].name == "8706-1707호"
    assert floors[0].image_file == "room_8706_1707_map.png"
    assert len(devices) == 8
    assert len(evals) == 6

    new_dev = storage.add_device(1, "콘센트", "추가콘센트", 0.4, 0.4)
    assert new_dev.device_id > 0
    assert len(storage.load_devices()) == 9

    ev = storage.add_evaluation(new_dev.device_id, "사용가능", 4, "좋음")
    assert ev.eval_id > 0
    reloaded = storage.load_evaluations()
    assert len(reloaded) == 7
    s = summarize(new_dev, reloaded)
    assert s.count == 1 and s.avg_rating == 4.0


def _run():
    passed = 0
    for fn in (test_summarize_average_and_latest, test_summarize_empty, test_validators):
        fn()
        passed += 1
        print(f"  ok  {fn.__name__}")
    print(f"\n{passed}개 테스트 통과 (DB 필요 테스트는 DATABASE_URL 설정 후 pytest로 실행)")


if __name__ == "__main__":
    _run()
```

- [ ] **Step 2: test_web_assets.py 교체**

```python
"""웹 이미지 자산 상태를 검증한다.

DATABASE_URL 없이도 image_content_type 테스트는 실행 가능.
build_state 테스트는 DATABASE_URL 필요:
    DATABASE_URL=postgres://... pytest tests/test_web_assets.py -v
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import storage      # noqa: E402
import web_server   # noqa: E402

_NEED_DB = os.getenv("DATABASE_URL") is None


def _truncate():
    import psycopg2
    with psycopg2.connect(os.environ["DATABASE_URL"]) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "TRUNCATE floors, devices, evaluations RESTART IDENTITY CASCADE"
            )
        conn.commit()


def test_build_state_includes_room_visual_assets():
    if _NEED_DB:
        import pytest
        pytest.skip("DATABASE_URL 미설정 — 통합 테스트 건너뜀")

    _truncate()
    storage.ensure_data_files()
    state = web_server.build_state()

    assert state["brand"]["logo"] == "utility_logo.png"
    assert state["brand"]["icon"] == "utility_icon.png"
    assert state["floors"][0]["image_file"] == "room_8706_1707_map.png"

    devices_with_photos = [d for d in state["devices"] if d.get("photo")]
    assert len(devices_with_photos) >= 4
    assert all(d["photo"].startswith("room_") for d in devices_with_photos)


def test_image_content_type_matches_extension():
    assert web_server.image_content_type("room_8706_1707_map.png") == "image/png"
    assert web_server.image_content_type("front_wall.jpeg") == "image/jpeg"
    assert web_server.image_content_type("front_wall.jpg") == "image/jpeg"
    assert web_server.image_content_type("unknown.bin") == "application/octet-stream"


def _run():
    passed = 0
    test_image_content_type_matches_extension()
    passed += 1
    print("  ok  test_image_content_type_matches_extension")
    print(f"\n{passed}개 테스트 통과 (DB 필요 테스트는 DATABASE_URL 설정 후 pytest로 실행)")


if __name__ == "__main__":
    _run()
```

- [ ] **Step 3: 순수 테스트 실행 확인**

```bash
cd /Users/dhoklim/Documents/AdvPrograming/outlet_map
python3 tests/test_logic.py
python3 tests/test_web_assets.py
```

Expected:
```
  ok  test_summarize_average_and_latest
  ok  test_summarize_empty
  ok  test_validators

3개 테스트 통과 (DB 필요 테스트는 DATABASE_URL 설정 후 pytest로 실행)
  ok  test_image_content_type_matches_extension

1개 테스트 통과 (DB 필요 테스트는 DATABASE_URL 설정 후 pytest로 실행)
```

- [ ] **Step 4: 커밋**

```bash
git add tests/test_logic.py tests/test_web_assets.py
git commit -m "test: adapt storage tests for PostgreSQL (skip without DATABASE_URL)"
```

---

## Task 6: GitHub push 및 Render 배포

- [ ] **Step 1: GitHub 저장소 초기화 (아직 git repo가 아닌 경우)**

```bash
cd /Users/dhoklim/Documents/AdvPrograming/outlet_map
git init
git add .
git commit -m "chore: initial commit"
```

- [ ] **Step 2: GitHub에 push**

```bash
git remote add origin https://github.com/<YOUR_USERNAME>/outlet-map.git
git push -u origin main
```

`<YOUR_USERNAME>`을 본인 GitHub 계정으로 교체.

- [ ] **Step 3: Render 배포**

1. [dashboard.render.com](https://dashboard.render.com) 접속 → "New +" → "Blueprint"
2. GitHub 계정 연결 → `outlet-map` 저장소 선택
3. `render.yaml` 자동 감지 → "Apply" 클릭
4. 빌드 완료 후 대시보드에서 공개 URL 확인 (`https://outlet-map.onrender.com` 형태)

- [ ] **Step 4: 접속 테스트**

```bash
curl -s https://<YOUR-APP>.onrender.com/api/state | python3 -m json.tool | head -20
```

Expected: floors, devices, statuses 키를 포함한 JSON 응답
