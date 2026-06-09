"""웹 데모 서버 (파이썬 기본 http.server만 사용).

앱(main.py)과 **같은 data/*.csv 파일**을 읽고 쓰므로 둘은 자동으로 연동된다.

실행:  python3 web_server.py   →  브라우저에서 http://localhost:8000
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from urllib.parse import unquote
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

import storage
from models import (
    STATUS_COLORS, summarize, validate_rating, validate_status, DEVICE_TYPES,
    compute_today_status,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")

BRAND = {
    "logo": "utility_logo.png",
    "icon": "utility_icon.png",
}

DEVICE_PHOTOS = {
    "칠판 왼쪽 콘센트": "room_front_wall.jpeg",
    "칠판 오른쪽 콘센트": "room_front_wall.jpeg",
    "왼쪽 출입문 콘센트": "room_outlet_wall.jpeg",
    "왼쪽 출입문 안쪽 콘센트": "room_outlet_wall.jpeg",
    "오른쪽 출입문 왼편 콘센트": "room_window_column.jpeg",
    "오른쪽 출입문 오른편 콘센트": "room_windows_overview.jpeg",
    "중앙 벽면 에어컨": "room_front_wall.jpeg",
    "창가 에어컨": "room_windows_overview.jpeg",
}


def image_content_type(name: str) -> str:
    ext = os.path.splitext(name.lower())[1]
    if ext == ".png":
        return "image/png"
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext == ".webp":
        return "image/webp"
    return "application/octet-stream"


def build_state() -> dict:
    """현재 CSV 상태를 웹이 쓰기 좋은 JSON 구조로 만든다."""
    floors = storage.load_floors()
    devices = storage.load_devices()
    evals = storage.load_evaluations()

    dev_json = []
    for d in devices:
        s = summarize(d, evals)
        dev_json.append({
            "device_id": d.device_id,
            "floor_id": d.floor_id,
            "type": d.dtype,
            "name": d.name,
            "x": d.x, "y": d.y,
            "status": s.latest_status,
            "color": s.color,
            "avg": s.avg_rating,
            "count": s.count,
            "recent": [
                {"rating": e.rating, "comment": e.comment, "created_at": e.created_at}
                for e in s.recent
            ],
            "photo": DEVICE_PHOTOS.get(d.name, ""),
        })
    return {
        "brand": BRAND,
        "floors": [
            {"floor_id": f.floor_id, "name": f.name, "image_file": f.image_file}
            for f in floors
        ],
        "devices": dev_json,
        "statuses": list(STATUS_COLORS.keys())[:3],
        "device_types": DEVICE_TYPES,
    }


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path, content_type):
        with open(path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    # ---- GET ----
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send_file(os.path.join(WEB_DIR, "index.html"),
                            "text/html; charset=utf-8")
        elif self.path == "/api/state":
            self._send_json(build_state())
        elif self.path == "/api/classrooms":
            classrooms = storage.load_classrooms()
            self._send_json([
                {"classroom_id": c.classroom_id, "name": c.name,
                 "floor": c.floor, "room_label": c.room_label}
                for c in classrooms
            ])
        elif self.path.startswith("/api/classrooms/") and self.path.endswith("/today"):
            try:
                parts = self.path.split("/")  # ['', 'api', 'classrooms', '{id}', 'today']
                if len(parts) < 5:
                    raise ValueError("invalid path")
                classroom_id = int(parts[3])
            except (ValueError, IndexError):
                self._send_json({"error": "invalid classroom id"}, 400)
                return
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
        elif self.path.startswith("/data/images/"):
            # 학교 도면, 로고, 위치 참고 사진 제공
            name = os.path.basename(unquote(self.path))
            fpath = os.path.join(storage.IMAGES_DIR, name)
            if os.path.exists(fpath):
                self._send_file(fpath, image_content_type(name))
            else:
                self._send_json({"error": "not found"}, 404)
        else:
            self._send_json({"error": "not found"}, 404)

    # ---- POST ----
    def do_POST(self):
        try:
            data = self._read_json()
            if self.path == "/api/evaluation":
                device_id = int(data["device_id"])
                status = validate_status(data["status"])
                rating = validate_rating(data["rating"])
                comment = str(data.get("comment", "")).strip()
                ev = storage.add_evaluation(device_id, status, rating, comment)
                self._send_json({"ok": True, "eval_id": ev.eval_id})
            elif self.path == "/api/device":
                floor_id = int(data["floor_id"])
                dtype = data["type"]
                if dtype not in DEVICE_TYPES:
                    raise ValueError("기기 종류가 올바르지 않습니다.")
                name = str(data["name"]).strip()
                if not name:
                    raise ValueError("이름을 입력하세요.")
                x, y = float(data["x"]), float(data["y"])
                dev = storage.add_device(floor_id, dtype, name, x, y)
                self._send_json({"ok": True, "device_id": dev.device_id})
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
            else:
                self._send_json({"error": "not found"}, 404)
        except (KeyError, ValueError) as e:
            self._send_json({"ok": False, "error": str(e)}, 400)

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

    def log_message(self, *args):  # 콘솔 로그 최소화
        pass


def main():
    storage.ensure_data_files()
    port = int(os.environ.get("PORT", 8000))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"콘센트맵 웹 데모 실행 중 →  http://localhost:{port}")
    print("종료하려면 Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n서버를 종료합니다.")
        server.shutdown()


if __name__ == "__main__":
    main()
