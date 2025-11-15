"""Core data structures for the alarm clock service."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Dict, Iterable, Optional, Tuple
from zoneinfo import ZoneInfo


def _normalize_days(days: Optional[Iterable[int]]) -> Tuple[int, ...]:
    if not days:
        return tuple()
    seen = set()
    normalized = []
    for day in days:
        if day < 0 or day > 6:
            raise ValueError("Weekday indexes must be between 0 (Monday) and 6 (Sunday)")
        if day not in seen:
            seen.add(day)
            normalized.append(day)
    return tuple(sorted(normalized))


@dataclass(frozen=True)
class MusicSettings:
    """Describes how an alarm should start playback when triggered."""

    source: str
    resource: Optional[str] = None
    tone_frequency_hz: int = 440
    tone_duration_seconds: int = 30
    extra: Dict[str, str] = field(default_factory=dict)

    @staticmethod
    def tone(frequency_hz: int = 440, duration_seconds: int = 30) -> "MusicSettings":
        return MusicSettings(source="tone", resource=None, tone_frequency_hz=frequency_hz, tone_duration_seconds=duration_seconds)

    @staticmethod
    def spotify(uri: str, *, duration_seconds: int = 30) -> "MusicSettings":
        if not uri:
            raise ValueError("Spotify URI must be provided")
        return MusicSettings(source="spotify", resource=uri, tone_duration_seconds=duration_seconds)

    @staticmethod
    def app(command: str, *, duration_seconds: int = 30, extra: Optional[Dict[str, str]] = None) -> "MusicSettings":
        if not command:
            raise ValueError("Application command must be provided")
        return MusicSettings(source="app", resource=command, tone_duration_seconds=duration_seconds, extra=extra or {})

    @staticmethod
    def custom(source: str, resource: str, *, duration_seconds: int = 30, extra: Optional[Dict[str, str]] = None) -> "MusicSettings":
        if not source:
            raise ValueError("Custom source identifier must be provided")
        return MusicSettings(source=source, resource=resource, tone_duration_seconds=duration_seconds, extra=extra or {})

    def to_dict(self) -> Dict[str, object]:
        return {
            "source": self.source,
            "resource": self.resource,
            "tone_frequency_hz": self.tone_frequency_hz,
            "tone_duration_seconds": self.tone_duration_seconds,
            "extra": dict(self.extra),
        }

    @staticmethod
    def from_dict(payload: Dict[str, object]) -> "MusicSettings":
        return MusicSettings(
            source=str(payload.get("source")),
            resource=payload.get("resource") if payload.get("resource") is not None else None,
            tone_frequency_hz=int(payload.get("tone_frequency_hz", 440)),
            tone_duration_seconds=int(payload.get("tone_duration_seconds", 30)),
            extra={str(k): str(v) for k, v in dict(payload.get("extra", {})).items()},
        )


@dataclass
class Alarm:
    """Represents a single alarm configuration."""

    id: str
    label: str
    hour: int
    minute: int
    second: int = 0
    timezone: str = "UTC"
    repeat_days: Tuple[int, ...] = field(default_factory=tuple)
    start_date: Optional[date] = None
    music: MusicSettings = field(default_factory=MusicSettings.tone)
    enabled: bool = True
    volume: float = 1.0

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Alarm id must be provided")
        if not (0 <= self.hour <= 23 and 0 <= self.minute <= 59 and 0 <= self.second <= 59):
            raise ValueError("Time must be within a valid 24h clock range")
        object.__setattr__(self, "repeat_days", _normalize_days(self.repeat_days))
        if self.volume <= 0:
            raise ValueError("Volume must be positive")
        if not self.label:
            object.__setattr__(self, "label", self.id)

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "label": self.label,
            "hour": self.hour,
            "minute": self.minute,
            "second": self.second,
            "timezone": self.timezone,
            "repeat_days": list(self.repeat_days),
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "music": self.music.to_dict(),
            "enabled": self.enabled,
            "volume": self.volume,
        }

    @staticmethod
    def from_dict(payload: Dict[str, object]) -> "Alarm":
        start_date_value = payload.get("start_date")
        start_date_parsed = date.fromisoformat(start_date_value) if start_date_value else None
        return Alarm(
            id=str(payload["id"]),
            label=str(payload.get("label", payload["id"])),
            hour=int(payload.get("hour", 0)),
            minute=int(payload.get("minute", 0)),
            second=int(payload.get("second", 0)),
            timezone=str(payload.get("timezone", "UTC")),
            repeat_days=tuple(int(value) for value in payload.get("repeat_days", []) if value is not None),
            start_date=start_date_parsed,
            music=MusicSettings.from_dict(dict(payload.get("music", {}))),
            enabled=bool(payload.get("enabled", True)),
            volume=float(payload.get("volume", 1.0)),
        )

    def next_occurrence(self, *, now: Optional[datetime] = None) -> Optional[datetime]:
        now = now or datetime.now(tz=ZoneInfo("UTC"))
        tz = ZoneInfo(self.timezone)
        localized_now = now.astimezone(tz)
        alarm_time = time(self.hour, self.minute, self.second, tzinfo=tz)

        def combine(target_date: date) -> datetime:
            localized = datetime.combine(target_date, alarm_time)
            return localized.astimezone(ZoneInfo("UTC"))


        if not self.enabled:
            return None

        # Determine the earliest date the alarm may ring.
        candidate_date = self.start_date or localized_now.date()
        if self.start_date and self.start_date < localized_now.date() and not self.repeat_days:
            # One-off alarm already passed and should not trigger again.
            return None

        if self.repeat_days:
            for offset in range(0, 7):
                possible_date = localized_now.date() + timedelta(days=offset)
                if possible_date < candidate_date:
                    continue
                if possible_date.weekday() not in self.repeat_days:
                    continue
                occurrence = combine(possible_date)
                if occurrence > now + timedelta(seconds=0.5):
                    return occurrence
            # If none were found in the upcoming week, schedule for the next available day
            next_day = min(self.repeat_days)
            today_idx = (localized_now.date().weekday())
            delta = (next_day - today_idx) % 7 or 7
            possible_date = localized_now.date() + timedelta(days=delta)
            return combine(possible_date)

        occurrence = combine(candidate_date)
        if occurrence <= now + timedelta(seconds=0.5):
            # Move to the next day for non-repeating alarms that should trigger again tomorrow.
            if self.start_date:
                return None
            occurrence = combine(localized_now.date() + timedelta(days=1))
        return occurrence


AlarmCollection = Dict[str, Alarm]
