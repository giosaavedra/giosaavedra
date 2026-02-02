"""Persistence layer for alarms."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Iterable, List, Protocol

from .models import Alarm


class AlarmStore(Protocol):
    async def load(self) -> List[Alarm]:
        ...

    async def save(self, alarms: Iterable[Alarm]) -> None:
        ...


class JsonAlarmStore:
    """Store alarms inside a JSON file."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = asyncio.Lock()

    async def load(self) -> List[Alarm]:
        async with self._lock:
            if not self._path.exists():
                return []
            content = await asyncio.to_thread(self._path.read_text)
            if not content.strip():
                return []
            data = json.loads(content)
            return [Alarm.from_dict(item) for item in data]

    async def save(self, alarms: Iterable[Alarm]) -> None:
        async with self._lock:
            data = [alarm.to_dict() for alarm in alarms]
            await asyncio.to_thread(self._path.parent.mkdir, parents=True, exist_ok=True)
            await asyncio.to_thread(self._path.write_text, json.dumps(data, indent=2))
