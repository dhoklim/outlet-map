"""SQLite 읽기/쓰기. data/outlet_map.db 파일에 저장."""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime

from models import Floor, Device, Evaluation, Classroom, Schedule

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
DB_PATH = os.path.join(DATA_DIR, "outlet_map.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


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


def _seed(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT INTO floors (name, image_file) VALUES (?, ?)",
        ("8706-1707호", "room_8706_1707_map.png"),
    )
    sample_devices = [
        (1, "콘센트", "칠판 왼쪽 콘센트",           0.27, 0.13),
        (1, "콘센트", "칠판 오른쪽 콘센트",          0.75, 0.13),
        (1, "콘센트", "왼쪽 출입문 콘센트",          0.18, 0.92),
        (1, "콘센트", "왼쪽 출입문 안쪽 콘센트",     0.27, 0.92),
        (1, "콘센트", "오른쪽 출입문 왼편 콘센트",   0.76, 0.92),
        (1, "콘센트", "오른쪽 출입문 오른편 콘센트", 0.86, 0.92),
        (1, "에어컨", "중앙 벽면 에어컨",            0.53, 0.55),
        (1, "에어컨", "창가 에어컨",                 0.91, 0.55),
    ]
    conn.executemany(
        "INSERT INTO devices (floor_id, type, name, x, y) VALUES (?, ?, ?, ?, ?)",
        sample_devices,
    )
    sample_evals = [
        (1, "사용가능", 5, "칠판 앞이라 발표 준비할 때 쓰기 좋아요"),
        (2, "사용가능", 4, "교탁 쪽에서 접근하기 쉬움"),
        (3, "점유",    3, "문 근처라 사람이 자주 지나가요"),
        (4, "사용가능", 4, "창가 자리에서 쓰기 무난함"),
        (7, "사용가능", 4, "강의실 중앙 냉방이 잘 됩니다"),
        (8, "사용가능", 3, "창가 쪽은 햇빛 때문에 조금 더워요"),
    ]
    conn.executemany(
        "INSERT INTO evaluations (device_id, status, rating, comment, created_at)"
        " VALUES (?, ?, ?, ?, ?)",
        [(d, s, r, c, "2026-06-01 12:00") for d, s, r, c in sample_evals],
    )


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


def load_floors() -> list:
    with _get_conn() as conn:
        rows = conn.execute("SELECT floor_id, name, image_file FROM floors ORDER BY floor_id").fetchall()
        return [Floor(r["floor_id"], r["name"], r["image_file"]) for r in rows]


def load_devices() -> list:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT device_id, floor_id, type, name, x, y FROM devices ORDER BY device_id"
        ).fetchall()
        return [Device(r["device_id"], r["floor_id"], r["type"], r["name"], r["x"], r["y"]) for r in rows]


def load_evaluations() -> list:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT eval_id, device_id, status, rating, comment, created_at"
            " FROM evaluations ORDER BY eval_id"
        ).fetchall()
        return [
            Evaluation(r["eval_id"], r["device_id"], r["status"],
                       r["rating"], r["comment"], r["created_at"])
            for r in rows
        ]


def add_device(floor_id: int, dtype: str, name: str, x: float, y: float) -> Device:
    with _get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO devices (floor_id, type, name, x, y) VALUES (?, ?, ?, ?, ?)",
            (floor_id, dtype, name, round(x, 4), round(y, 4)),
        )
        return Device(cur.lastrowid, floor_id, dtype, name, round(x, 4), round(y, 4))


def add_evaluation(device_id: int, status: str, rating: int, comment: str) -> Evaluation:
    created = datetime.now().strftime("%Y-%m-%d %H:%M")
    with _get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO evaluations (device_id, status, rating, comment, created_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (device_id, status, rating, comment, created),
        )
        return Evaluation(cur.lastrowid, device_id, status, rating, comment, created)
