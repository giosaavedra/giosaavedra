import asyncio
from datetime import datetime, timedelta, timezone

from alarm_clock.models import Alarm, MusicSettings
from alarm_clock.players import BasePlayer, PlayerRegistry
from alarm_clock.scheduler import AlarmScheduler


class DummyStore:
    def __init__(self) -> None:
        self.alarms = []

    async def load(self):
        return list(self.alarms)

    async def save(self, alarms):
        self.alarms = list(alarms)


class DummyPlayer(BasePlayer):
    def __init__(self) -> None:
        self.events: asyncio.Queue[str] = asyncio.Queue()

    async def play(self, alarm, settings):
        await self.events.put(alarm.id)


def test_scheduler_triggers_alarm_once():
    async def scenario():
        store = DummyStore()
        player = DummyPlayer()
        registry = PlayerRegistry(players={"tone": player})
        scheduler = AlarmScheduler(store, registry)

        now = datetime.now(timezone.utc) + timedelta(seconds=2)
        alarm = Alarm(
            id="wake",
            label="Wake",
            hour=now.hour,
            minute=now.minute,
            second=now.second,
            timezone="UTC",
            repeat_days=(),
            music=MusicSettings.tone(),
        )

        await scheduler.start()
        try:
            await scheduler.add_alarm(alarm)
            fired = await asyncio.wait_for(player.events.get(), timeout=5)
            assert fired == "wake"
        finally:
            await scheduler.stop()

    asyncio.run(scenario())


def test_scheduler_persists_changes_on_trigger():
    async def scenario():
        store = DummyStore()
        player = DummyPlayer()
        registry = PlayerRegistry(players={"tone": player})
        scheduler = AlarmScheduler(store, registry)

        now = datetime.now(timezone.utc) + timedelta(seconds=1)
        alarm = Alarm(
            id="meeting",
            label="Meeting",
            hour=now.hour,
            minute=now.minute,
            second=now.second,
            timezone="UTC",
            repeat_days=(),
            music=MusicSettings.tone(),
        )

        await scheduler.start()
        try:
            await scheduler.add_alarm(alarm)
            await asyncio.wait_for(player.events.get(), timeout=5)
            assert not scheduler.snapshot()["meeting"].enabled
        finally:
            await scheduler.stop()

    asyncio.run(scenario())
