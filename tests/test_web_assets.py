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


def test_mobile_html_structure():
    html_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "web", "index.html")
    html = open(html_path, encoding="utf-8").read()
    assert 'class="sheet-handle"' in html, "시트 핸들 div 없음"
    assert 'id="starRating"' in html, "별점 버튼 컨테이너 없음"
    assert 'class="star-btn"' in html, "별점 버튼 없음"
    assert 'data-val="5"' in html, "별점 5 버튼 없음"


def _run():
    passed = 0
    test_mobile_html_structure()
    passed += 1
    print("  ok  test_mobile_html_structure")
    test_image_content_type_matches_extension()
    passed += 1
    print("  ok  test_image_content_type_matches_extension")
    print(f"\n{passed}개 테스트 통과 (DB 필요 테스트는 DATABASE_URL 설정 후 pytest로 실행)")


if __name__ == "__main__":
    _run()
