"""정적(보기 전용) 사이트용 데이터 생성: data/*.csv → web_static/state.json (+ 도면 복사).

GitHub Pages 배포용 파일을 갱신하려면 이 스크립트를 실행한 뒤 push하면 됩니다:
    python3 build_static.py && git add web_static/ && git push
"""
from __future__ import annotations

import csv
import json
import os
import shutil
from datetime import datetime

from models import Floor, Device, Evaluation, DEVICE_TYPES, summarize
from web_server import BRAND, DEVICE_PHOTOS, STATUS_COLORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
OUT_DIR = os.path.join(BASE_DIR, "web_static")


def _read_csv(path: str) -> list:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    floors = [
        Floor(int(r["floor_id"]), r["name"], r.get("image_file", ""))
        for r in _read_csv(os.path.join(DATA_DIR, "floors.csv"))
    ]
    devices = [
        Device(int(r["device_id"]), int(r["floor_id"]), r["type"],
               r["name"], float(r["x"]), float(r["y"]))
        for r in _read_csv(os.path.join(DATA_DIR, "devices.csv"))
    ]
    evals = [
        Evaluation(int(r["eval_id"]), int(r["device_id"]), r["status"],
                   int(r["rating"]), r["comment"], r["created_at"])
        for r in _read_csv(os.path.join(DATA_DIR, "evaluations.csv"))
    ]

    dev_json = []
    for d in devices:
        s = summarize(d, evals)
        dev_json.append({
            "device_id": d.device_id, "floor_id": d.floor_id,
            "type": d.dtype, "name": d.name, "x": d.x, "y": d.y,
            "status": s.latest_status, "color": s.color,
            "avg": s.avg_rating, "count": s.count,
            "recent": [
                {"rating": e.rating, "comment": e.comment, "created_at": e.created_at}
                for e in s.recent
            ],
            "photo": DEVICE_PHOTOS.get(d.name, ""),
        })

    state = {
        "brand": BRAND,
        "floors": [
            {"floor_id": f.floor_id, "name": f.name, "image_file": f.image_file}
            for f in floors
        ],
        "devices": dev_json,
        "statuses": list(STATUS_COLORS.keys())[:3],
        "device_types": DEVICE_TYPES,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "state.json"), "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    with open(os.path.join(BASE_DIR, "web", "index.html"), encoding="utf-8") as f:
        html = f.read()
    static_config = (
        "<script>\n"
        "window.OUTLET_MAP_STATE_URL = 'state.json';\n"
        "window.OUTLET_MAP_IMAGE_PREFIX = 'images/';\n"
        "window.OUTLET_MAP_READ_ONLY = true;\n"
        "</script>\n"
    )
    html = html.replace("<script>\nconst STATE_URL", static_config + "<script>\nconst STATE_URL", 1)
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    img_out = os.path.join(OUT_DIR, "images")
    os.makedirs(img_out, exist_ok=True)
    copied = 0
    if os.path.isdir(IMAGES_DIR):
        for name in os.listdir(IMAGES_DIR):
            src = os.path.join(IMAGES_DIR, name)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(img_out, name))
                copied += 1

    print(f"state.json 생성 완료 (기기 {len(dev_json)}개, 도면 {copied}개)")
    print(f"배포할 폴더: {OUT_DIR}")


if __name__ == "__main__":
    main()
