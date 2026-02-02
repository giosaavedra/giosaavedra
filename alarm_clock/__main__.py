"""Command line interface for the alarm clock service."""
from __future__ import annotations

import argparse
import asyncio
from datetime import date
from pathlib import Path
from typing import Iterable, List

from . import (
    Alarm,
    AlarmScheduler,
    AppLauncherPlayer,
    JsonAlarmStore,
    MusicSettings,
    PlayerRegistry,
    SpotifyPlayer,
    TonePlayer,
)

DEFAULT_STORE = Path.home() / ".alarm_clock" / "alarms.json"
DAY_ALIASES = {
    "mon": 0,
    "monday": 0,
    "tue": 1,
    "tuesday": 1,
    "wed": 2,
    "wednesday": 2,
    "thu": 3,
    "thursday": 3,
    "fri": 4,
    "friday": 4,
    "sat": 5,
    "saturday": 5,
    "sun": 6,
    "sunday": 6,
}


def parse_repeat_days(values: Iterable[str]) -> List[int]:
    days = []
    for value in values:
        key = value.strip().lower()
        if key not in DAY_ALIASES:
            raise SystemExit(f"Unknown weekday: {value}")
        days.append(DAY_ALIASES[key])
    return days


def build_registry() -> PlayerRegistry:
    registry = PlayerRegistry(players={})
    registry.register("tone", TonePlayer())
    registry.register("spotify", SpotifyPlayer())
    registry.register("app", AppLauncherPlayer())
    return registry


def create_alarm_from_args(args: argparse.Namespace) -> Alarm:
    repeat_days = parse_repeat_days(args.repeat or [])
    music_source = args.music_source
    if music_source == "tone":
        music = MusicSettings.tone(frequency_hz=args.frequency, duration_seconds=args.duration)
    elif music_source == "spotify":
        if not args.music_resource:
            raise SystemExit("--music-resource is required for Spotify alarms")
        music = MusicSettings.spotify(args.music_resource, duration_seconds=args.duration)
    elif music_source == "app":
        if not args.music_resource:
            raise SystemExit("--music-resource must point to an application or URI")
        music = MusicSettings.app(args.music_resource, duration_seconds=args.duration)
    else:
        music = MusicSettings.custom(music_source, args.music_resource or "", duration_seconds=args.duration)

    start_date = date.fromisoformat(args.start_date) if args.start_date else None
    return Alarm(
        id=args.id,
        label=args.label or args.id,
        hour=args.hour,
        minute=args.minute,
        second=args.second,
        timezone=args.timezone,
        repeat_days=repeat_days,
        start_date=start_date,
        music=music,
        enabled=not args.disabled,
        volume=args.volume,
    )


def load_scheduler(store_path: Path) -> AlarmScheduler:
    store = JsonAlarmStore(store_path)
    registry = build_registry()
    return AlarmScheduler(store, registry)


def cmd_list(args: argparse.Namespace) -> None:
    scheduler = load_scheduler(args.store)
    async def _run() -> None:
        await scheduler.start()
        for alarm in scheduler.snapshot().values():
            repeat = ",".join(str(day) for day in alarm.repeat_days) or "once"
            print(f"{alarm.id}: {alarm.label} @ {alarm.hour:02d}:{alarm.minute:02d}:{alarm.second:02d} {alarm.timezone} [{repeat}] -> {alarm.music.source}")
        await scheduler.stop()
    asyncio.run(_run())


def cmd_add(args: argparse.Namespace) -> None:
    alarm = create_alarm_from_args(args)
    scheduler = load_scheduler(args.store)

    async def _run() -> None:
        await scheduler.start()
        await scheduler.add_alarm(alarm)
        await scheduler.stop()

    asyncio.run(_run())


def cmd_remove(args: argparse.Namespace) -> None:
    scheduler = load_scheduler(args.store)

    async def _run() -> None:
        await scheduler.start()
        await scheduler.remove_alarm(args.id)
        await scheduler.stop()

    asyncio.run(_run())


def cmd_enable(args: argparse.Namespace) -> None:
    scheduler = load_scheduler(args.store)

    async def _run() -> None:
        await scheduler.start()
        await scheduler.enable(args.id)
        await scheduler.stop()

    asyncio.run(_run())


def cmd_disable(args: argparse.Namespace) -> None:
    scheduler = load_scheduler(args.store)

    async def _run() -> None:
        await scheduler.start()
        await scheduler.disable(args.id)
        await scheduler.stop()

    asyncio.run(_run())


def cmd_trigger(args: argparse.Namespace) -> None:
    scheduler = load_scheduler(args.store)

    async def _run() -> None:
        await scheduler.start()
        await scheduler.trigger_now(args.id)
        await scheduler.stop()

    asyncio.run(_run())


def cmd_run(args: argparse.Namespace) -> None:
    scheduler = load_scheduler(args.store)

    async def _run() -> None:
        await scheduler.start()
        try:
            while True:
                await asyncio.sleep(args.heartbeat)
        except KeyboardInterrupt:
            pass
        finally:
            await scheduler.stop()

    asyncio.run(_run())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="alarm-clock", description="Alarm clock daemon with Spotify and tone support")
    parser.add_argument("--store", type=Path, default=DEFAULT_STORE, help="Path to the alarm storage file")

    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--hour", type=int, required=True)
    common.add_argument("--minute", type=int, required=True)
    common.add_argument("--second", type=int, default=0)
    common.add_argument("--timezone", default="UTC")
    common.add_argument("--repeat", nargs="*", help="Weekdays to repeat (mon, tue, ...)")
    common.add_argument("--start-date", help="First date to trigger (YYYY-MM-DD)")
    common.add_argument("--music-source", default="tone")
    common.add_argument("--music-resource")
    common.add_argument("--frequency", type=int, default=440)
    common.add_argument("--duration", type=int, default=30)
    common.add_argument("--volume", type=float, default=1.0)
    common.add_argument("--label")
    common.add_argument("--disabled", action="store_true")

    add_parser = subparsers.add_parser("add", parents=[common])
    add_parser.add_argument("id")
    add_parser.set_defaults(func=cmd_add)

    remove_parser = subparsers.add_parser("remove")
    remove_parser.add_argument("id")
    remove_parser.set_defaults(func=cmd_remove)

    enable_parser = subparsers.add_parser("enable")
    enable_parser.add_argument("id")
    enable_parser.set_defaults(func=cmd_enable)

    disable_parser = subparsers.add_parser("disable")
    disable_parser.add_argument("id")
    disable_parser.set_defaults(func=cmd_disable)

    trigger_parser = subparsers.add_parser("trigger")
    trigger_parser.add_argument("id")
    trigger_parser.set_defaults(func=cmd_trigger)

    list_parser = subparsers.add_parser("list")
    list_parser.set_defaults(func=cmd_list)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--heartbeat", type=float, default=30.0, help="How frequently to wake the loop while idle")
    run_parser.set_defaults(func=cmd_run)

    return parser


def main(argv: Iterable[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    args.func(args)


if __name__ == "__main__":
    main()
