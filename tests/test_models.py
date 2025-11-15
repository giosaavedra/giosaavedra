from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from alarm_clock.models import Alarm, MusicSettings


def test_next_occurrence_once_moves_to_next_day_when_time_passed():
    tz = ZoneInfo("UTC")
    now = datetime(2024, 1, 1, 10, 0, tzinfo=tz)
    alarm = Alarm(
        id="morning",
        label="Morning Alarm",
        hour=9,
        minute=30,
        second=0,
        timezone="UTC",
        repeat_days=(),
        music=MusicSettings.tone(),
    )

    next_time = alarm.next_occurrence(now=now)
    assert next_time.date() == datetime(2024, 1, 2, tzinfo=tz).date()


def test_next_occurrence_respects_start_date_once():
    tz = ZoneInfo("UTC")
    now = datetime(2024, 1, 2, 8, 0, tzinfo=tz)
    alarm = Alarm(
        id="doctor",
        label="Doctor",
        hour=7,
        minute=0,
        timezone="UTC",
        repeat_days=(),
        start_date=datetime(2024, 1, 1, tzinfo=tz).date(),
        music=MusicSettings.tone(),
    )

    assert alarm.next_occurrence(now=now) is None


def test_next_occurrence_repeating_advances_to_next_valid_day():
    tz = ZoneInfo("UTC")
    now = datetime(2024, 1, 1, 6, 0, tzinfo=tz)  # Monday
    alarm = Alarm(
        id="gym",
        label="Gym",
        hour=7,
        minute=30,
        timezone="UTC",
        repeat_days=(1, 3),  # Tuesday and Thursday
        music=MusicSettings.tone(),
    )

    next_time = alarm.next_occurrence(now=now)
    assert next_time.astimezone(tz).date().weekday() == 1
