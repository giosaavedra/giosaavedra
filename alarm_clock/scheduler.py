"""Async alarm scheduler."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Dict
import contextlib

from .models import Alarm, AlarmCollection
from .players import PlayerRegistry
from .storage import AlarmStore


class AlarmScheduler:
    """Schedules alarms and dispatches playback events."""

    def __init__(self, store: AlarmStore, players: PlayerRegistry) -> None:
        self._store = store
        self._players = players
        self._alarms: AlarmCollection = {}
        self._tasks: Dict[str, asyncio.Task[None]] = {}
        self._lock = asyncio.Lock()
        self._started = False

    async def start(self) -> None:
        async with self._lock:
            if self._started:
                return
            alarms = await self._store.load()
            self._alarms = {alarm.id: alarm for alarm in alarms}
            self._started = True
            for alarm in alarms:
                if alarm.enabled:
                    self._tasks[alarm.id] = asyncio.create_task(self._run_alarm(alarm.id))

    async def stop(self) -> None:
        async with self._lock:
            tasks = list(self._tasks.values())
            for task in tasks:
                task.cancel()
            for task in tasks:
                with contextlib.suppress(asyncio.CancelledError):
                    await task
            self._tasks.clear()
            self._started = False

    async def add_alarm(self, alarm: Alarm) -> None:
        async with self._lock:
            if alarm.id in self._alarms:
                raise ValueError(f"Alarm with id '{alarm.id}' already exists")
            self._alarms[alarm.id] = alarm
            await self._store.save(self._alarms.values())
            if self._started and alarm.enabled:
                self._tasks[alarm.id] = asyncio.create_task(self._run_alarm(alarm.id))

    async def update_alarm(self, alarm: Alarm) -> None:
        async with self._lock:
            if alarm.id not in self._alarms:
                raise KeyError(f"Alarm '{alarm.id}' not found")
            self._alarms[alarm.id] = alarm
            await self._store.save(self._alarms.values())
            await self._reschedule(alarm.id)

    async def remove_alarm(self, alarm_id: str) -> None:
        async with self._lock:
            if alarm_id not in self._alarms:
                raise KeyError(f"Alarm '{alarm_id}' not found")
            self._alarms.pop(alarm_id)
            await self._store.save(self._alarms.values())
            await self._cancel(alarm_id)

    async def enable(self, alarm_id: str) -> None:
        async with self._lock:
            alarm = self._alarms.get(alarm_id)
            if not alarm:
                raise KeyError(f"Alarm '{alarm_id}' not found")
            if alarm.enabled:
                return
            alarm.enabled = True
            await self._store.save(self._alarms.values())
            if self._started:
                self._tasks[alarm_id] = asyncio.create_task(self._run_alarm(alarm_id))

    async def disable(self, alarm_id: str) -> None:
        async with self._lock:
            alarm = self._alarms.get(alarm_id)
            if not alarm:
                raise KeyError(f"Alarm '{alarm_id}' not found")
            if not alarm.enabled:
                return
            alarm.enabled = False
            await self._store.save(self._alarms.values())
            await self._cancel(alarm_id)

    async def trigger_now(self, alarm_id: str) -> None:
        alarm = self._alarms.get(alarm_id)
        if not alarm:
            raise KeyError(f"Alarm '{alarm_id}' not found")
        await self._players.play(alarm)

    async def _cancel(self, alarm_id: str) -> None:
        task = self._tasks.pop(alarm_id, None)
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    async def _reschedule(self, alarm_id: str) -> None:
        await self._cancel(alarm_id)
        alarm = self._alarms[alarm_id]
        if self._started and alarm.enabled:
            self._tasks[alarm_id] = asyncio.create_task(self._run_alarm(alarm_id))

    async def _run_alarm(self, alarm_id: str) -> None:
        try:
            while True:
                alarm = self._alarms.get(alarm_id)
                if alarm is None or not alarm.enabled:
                    return
                now_utc = datetime.now(tz=timezone.utc)
                next_time = alarm.next_occurrence(now=now_utc)
                if next_time is None:
                    alarm.enabled = False
                    await self._store.save(self._alarms.values())
                    return
                wait_seconds = max(0.0, (next_time - now_utc).total_seconds())
                if wait_seconds:
                    await asyncio.sleep(wait_seconds)
                await self._players.play(alarm)
                if not alarm.repeat_days:
                    alarm.enabled = False
                    await self._store.save(self._alarms.values())
                    return
        except asyncio.CancelledError:
            return

    def snapshot(self) -> AlarmCollection:
        return dict(self._alarms)
