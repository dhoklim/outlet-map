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
