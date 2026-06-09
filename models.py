"""데이터 모델과 집계 로직 (순수 로직 - 화면과 분리되어 단위 테스트 가능)."""
from __future__ import annotations

from dataclasses import dataclass

# 사용 가능한 상태 목록과 마커 색상 규칙
STATUSES = ["사용가능", "고장", "점유"]

STATUS_COLORS = {
    "사용가능": "#1f9d55",  # 초록
    "고장": "#e02424",      # 빨강
    "점유": "#ff9f1c",      # 주황
    None: "#9aa0a6",        # 미평가(회색)
}

# 기기 종류
TYPE_OUTLET = "콘센트"
TYPE_AIRCON = "에어컨"
DEVICE_TYPES = [TYPE_OUTLET, TYPE_AIRCON]


@dataclass
class Floor:
    floor_id: int
    name: str
    image_file: str = ""  # 도면 PNG 파일명 (없으면 placeholder 사용)


@dataclass
class Device:
    device_id: int
    floor_id: int
    dtype: str        # "콘센트" 또는 "에어컨"
    name: str
    x: float          # 0.0~1.0 비율 좌표 (도면 가로 기준)
    y: float          # 0.0~1.0 비율 좌표 (도면 세로 기준)


@dataclass
class Evaluation:
    eval_id: int
    device_id: int
    status: str
    rating: int       # 1~5
    comment: str
    created_at: str   # ISO 형식 문자열


@dataclass
class DeviceSummary:
    """한 기기에 대한 평가들을 요약한 결과."""
    latest_status: str | None
    avg_rating: float | None
    count: int
    recent: list  # 최근 평가 리스트 (Evaluation, 최신순)

    @property
    def color(self) -> str:
        return STATUS_COLORS.get(self.latest_status, STATUS_COLORS[None])


@dataclass
class Classroom:
    classroom_id: int
    name: str
    floor: str
    room_label: str


@dataclass
class Schedule:
    schedule_id: int
    classroom_id: int
    day_of_week: int   # 0=월 1=화 2=수 3=목 4=금
    start_time: str    # "HH:MM"
    end_time: str      # "HH:MM"
    course_name: str
    professor: str


def compute_today_status(schedules: list, now_hhmm: str) -> dict:
    """오늘 시간표 목록과 현재 시각(HH:MM)으로 강의실 상태를 계산한다."""
    sorted_s = sorted(schedules, key=lambda s: s.start_time)
    current = next(
        (s for s in sorted_s if s.start_time <= now_hhmm < s.end_time),
        None,
    )
    if current:
        # 연속 수업 블록의 마지막 종료 시각 계산
        end = current.end_time
        while True:
            chained = next((s for s in sorted_s if s.start_time == end), None)
            if chained:
                end = chained.end_time
            else:
                break
        return {
            "status": "수업 중",
            "current_course": current.course_name,
            "current_professor": current.professor,
            "next_free": end,
        }
    return {
        "status": "빈 강의실",
        "current_course": None,
        "current_professor": None,
        "next_free": None,
    }


def summarize(device: Device, evaluations: list) -> DeviceSummary:
    """device에 해당하는 평가들만 모아 상태/평균별점/최근평가를 계산한다."""
    mine = [e for e in evaluations if e.device_id == device.device_id]
    if not mine:
        return DeviceSummary(latest_status=None, avg_rating=None, count=0, recent=[])

    # eval_id가 클수록 최신 (append 순서)
    ordered = sorted(mine, key=lambda e: e.eval_id, reverse=True)
    latest_status = ordered[0].status
    avg = round(sum(e.rating for e in mine) / len(mine), 1)
    return DeviceSummary(
        latest_status=latest_status,
        avg_rating=avg,
        count=len(mine),
        recent=ordered[:5],
    )


def validate_rating(value) -> int:
    """별점 입력값을 1~5 정수로 검증한다. 실패 시 ValueError."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        raise ValueError("별점은 숫자여야 합니다.")
    if not 1 <= n <= 5:
        raise ValueError("별점은 1~5 사이여야 합니다.")
    return n


def validate_status(value) -> str:
    if value not in STATUSES:
        raise ValueError(f"상태는 {STATUSES} 중 하나여야 합니다.")
    return value
