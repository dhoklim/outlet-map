"""정적(보기 전용) 사이트용 데이터 생성: data/*.csv → web_static/state.json (+ 도면 복사).

Netlify에 올릴 공개 데이터를 갱신하려면 이 스크립트를 다시 실행한 뒤
web_static/ 폴더를 재배포하면 됩니다.

실행:  python3 build_static.py
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime

import storage
from web_server import build_state

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "web_static")


def main():
    storage.ensure_data_files()
    os.makedirs(OUT_DIR, exist_ok=True)

    state = build_state()
    state["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(os.path.join(OUT_DIR, "state.json"), "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    # 로컬 웹 UI를 그대로 쓰되, 정적 배포에서는 API 대신 state.json/images를 보게 한다.
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

    # 도면 이미지가 있으면 함께 복사
    img_out = os.path.join(OUT_DIR, "images")
    os.makedirs(img_out, exist_ok=True)
    copied = 0
    if os.path.isdir(storage.IMAGES_DIR):
        for name in os.listdir(storage.IMAGES_DIR):
            src = os.path.join(storage.IMAGES_DIR, name)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(img_out, name))
                copied += 1

    print(f"state.json 생성 완료 (기기 {len(state['devices'])}개, 도면 {copied}개)")
    print(f"배포할 폴더: {OUT_DIR}")


if __name__ == "__main__":
    main()
