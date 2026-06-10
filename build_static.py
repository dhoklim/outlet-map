"""정적(보기 전용) 사이트용 데이터 생성: SQLite → web_static/

Cloudflare Pages / GitHub Pages 배포용:
    python3 build_static.py && git add web_static/ && git push
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime

import storage
from models import DEVICE_TYPES, summarize
from web_server import BRAND, DEVICE_PHOTOS, STATUS_COLORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "data", "images")
OUT_DIR = os.path.join(BASE_DIR, "web_static")

STATIC_PATCH_HEAD = """\
<script>
window.OUTLET_MAP_STATE_URL = 'state.json';
window.OUTLET_MAP_IMAGE_PREFIX = 'images/';
window.OUTLET_MAP_READ_ONLY = true;
"""

STATIC_PATCH_TAIL = """\
const __origFetch = window.fetch.bind(window);
window.fetch = function(url, opts) {
  if (url === '/api/classrooms') {
    return Promise.resolve({ok:true, json:()=>Promise.resolve(window.__SC__)});
  }
  const m = String(url).match(/^\\/api\\/classrooms\\/(\\d+)\\/week$/);
  if (m) {
    return Promise.resolve({ok:true, json:()=>Promise.resolve(_computeWeek(parseInt(m[1])))});
  }
  return __origFetch(url, opts);
};

function _computeWeek(cid) {
  const now = new Date();
  const jsd = now.getDay();
  const today = jsd === 0 ? 6 : jsd - 1;
  const hhmm = String(now.getHours()).padStart(2,'0') + ':' + String(now.getMinutes()).padStart(2,'0');
  const cls = (window.__SC__ || []).find(c => c.classroom_id === cid);
  const all = (window.__SS__ || []).filter(s => s.classroom_id === cid);
  const todayS = all.filter(s => s.day_of_week === today);
  let status = '빈 강의실', cc = '', cp = '', nf = '';
  for (const s of todayS) {
    if (s.start_time <= hhmm && hhmm < s.end_time) { status='수업 중'; cc=s.course_name; cp=s.professor; }
  }
  if (status === '수업 중') {
    const sorted = [...todayS].sort((a,b)=>a.start_time.localeCompare(b.start_time));
    for (const s of sorted) { if (s.start_time <= hhmm && hhmm < s.end_time) nf = s.end_time; }
  }
  const week = [0,1,2,3,4].map(day => ({
    day, day_name: ['월','화','수','목','금'][day], is_today: day===today,
    schedules: all.filter(s=>s.day_of_week===day)
      .sort((a,b)=>a.start_time.localeCompare(b.start_time))
      .map(s=>({...s, is_now: day===today && s.start_time<=hhmm && hhmm<s.end_time}))
  }));
  return {classroom_id:cid, name:cls?cls.name:'', status, current_course:cc,
          current_professor:cp, next_free:nf, today, week};
}
</script>
"""


def main():
    storage.ensure_data_files()

    floors   = storage.load_floors()
    devices  = storage.load_devices()
    evals    = storage.load_evaluations()
    classrooms = storage.load_classrooms()

    # all schedules across all classrooms
    all_schedules = []
    for c in classrooms:
        for s in storage.load_week_schedules(c.classroom_id):
            all_schedules.append({
                "schedule_id": s.schedule_id,
                "classroom_id": s.classroom_id,
                "day_of_week": s.day_of_week,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "course_name": s.course_name,
                "professor": s.professor,
            })

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
        "floors": [{"floor_id": f.floor_id, "name": f.name, "image_file": f.image_file} for f in floors],
        "devices": dev_json,
        "statuses": list(STATUS_COLORS.keys())[:3],
        "device_types": DEVICE_TYPES,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "state.json"), "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    classrooms_json = [
        {"classroom_id": c.classroom_id, "name": c.name, "floor": c.floor, "room_label": c.room_label}
        for c in classrooms
    ]
    with open(os.path.join(BASE_DIR, "web", "index.html"), encoding="utf-8") as f:
        html = f.read()

    sc_data = json.dumps(classrooms_json, ensure_ascii=False)
    ss_data = json.dumps(all_schedules, ensure_ascii=False)
    inject = (
        STATIC_PATCH_HEAD +
        f"window.__SC__ = {sc_data};\nwindow.__SS__ = {ss_data};\n" +
        STATIC_PATCH_TAIL
    )
    html = html.replace("\n<script>\nconst isMobile", "\n" + inject + "<script>\nconst isMobile", 1)

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

    print(f"완료: 기기 {len(dev_json)}개, 강의실 {len(classrooms_json)}개, 도면 이미지 {copied}개")
    print(f"배포 폴더: {OUT_DIR}")


if __name__ == "__main__":
    main()
