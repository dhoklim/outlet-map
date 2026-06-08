# Render + PostgreSQL 배포 설계

**날짜:** 2026-06-07  
**목표:** 콘센트맵 웹 앱을 Render + PostgreSQL로 영구 배포해 외부에서 접근 가능하게 한다.

---

## 1. 아키텍처 개요

```
GitHub push → Render 자동 배포 → web_server.py 실행
                                        ↓
                              PostgreSQL (Render 제공, 무료)
```

### 변경 파일 목록

| 파일 | 변경 내용 |
|---|---|
| `storage.py` | CSV 읽기/쓰기 → psycopg2 PostgreSQL 쿼리로 교체 |
| `web_server.py` | 바인드 주소 `127.0.0.1` → `0.0.0.0`, 포트를 `PORT` 환경변수에서 읽기 |
| `requirements.txt` (신규) | `psycopg2-binary` |
| `render.yaml` (신규) | Render 서비스 + DB 선언 |

변경하지 않는 파일: `models.py`, `main.py`, `map_view.py`, `detail_panel.py`, `web/`

---

## 2. 데이터 레이어

### DB 스키마

```sql
CREATE TABLE IF NOT EXISTS floors (
    floor_id SERIAL PRIMARY KEY,
    name     TEXT NOT NULL,
    image_file TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS devices (
    device_id SERIAL PRIMARY KEY,
    floor_id  INT  NOT NULL,
    type      TEXT NOT NULL,
    name      TEXT NOT NULL,
    x         REAL NOT NULL,
    y         REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS evaluations (
    eval_id    SERIAL PRIMARY KEY,
    device_id  INT  NOT NULL,
    status     TEXT NOT NULL,
    rating     INT  NOT NULL,
    comment    TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
```

### storage.py 인터페이스 유지

모든 public 함수의 시그니처와 반환 타입은 기존과 동일하게 유지한다.  
`web_server.py`와 `main.py`(tkinter)는 수정 불필요.

| 함수 | 변경 내용 |
|---|---|
| `ensure_data_files()` | 함수명 유지, 내부 구현만 교체. 테이블 생성 + floors가 비면 샘플 데이터 삽입 |
| `load_floors()` | `SELECT * FROM floors` |
| `load_devices()` | `SELECT * FROM devices` |
| `load_evaluations()` | `SELECT * FROM evaluations` |
| `add_device()` | `INSERT INTO devices ... RETURNING device_id` |
| `add_evaluation()` | `INSERT INTO evaluations ... RETURNING eval_id` |

DB 연결: `os.environ["DATABASE_URL"]`을 사용. 연결은 요청마다 열고 닫는다 (간단한 구현, 커넥션 풀 불필요).

---

## 3. 서버 변경 (web_server.py)

```python
PORT = int(os.environ.get("PORT", 8000))
server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
```

로컬 실행 시에도 동일하게 동작 (`PORT` 미설정 시 8000 사용).

---

## 4. 배포 설정 (render.yaml)

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

---

## 5. 배포 절차

1. 코드 변경 후 GitHub에 push
2. [render.com](https://render.com) → "New Project from Git" → 저장소 연결
3. `render.yaml` 자동 감지 → DB + 웹 서비스 동시 생성
4. 공개 URL 발급 (예: `https://outlet-map.onrender.com`)

---

## 6. 제약사항

- Render 무료 웹 서비스: 15분 비활성 시 슬립 → 첫 접속 시 ~30초 재시작
- Render 무료 PostgreSQL: **90일 후 만료** → 이후 유료 전환(월 $7) 또는 재생성 필요
- `main.py`(tkinter 앱)는 배포 환경에서 실행 안 됨 (로컬 전용)
