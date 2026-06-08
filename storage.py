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
        (1, "콘센트", "칠판 왼쪽 콘센트",           0.27, 0.13),
        (1, "콘센트", "칠판 오른쪽 콘센트",          0.75, 0.13),
        (1, "콘센트", "왼쪽 출입문 콘센트",          0.18, 0.92),
        (1, "콘센트", "왼쪽 출입문 안쪽 콘센트",     0.27, 0.92),
        (1, "콘센트", "오른쪽 출입문 왼편 콘센트",   0.76, 0.92),
        (1, "콘센트", "오른쪽 출입문 오른편 콘센트", 0.86, 0.92),
        (1, "에어컨", "중앙 벽면 에어컨",            0.53, 0.55),
        (1, "에어컨", "창가 에어컨",                 0.91, 0.55),
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
