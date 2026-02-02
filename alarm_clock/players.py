"""Playback helpers for the alarm scheduler."""
from __future__ import annotations

import asyncio
import math
import os
import struct
import sys
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
import shutil

from .models import Alarm, MusicSettings

try:  # pragma: no-cover - optional dependency
    import simpleaudio  # type: ignore
except Exception:  # pragma: no-cover - optional dependency
    simpleaudio = None


class PlayerError(RuntimeError):
    """Raised when playback fails."""


class BasePlayer:
    """Base interface for audio players."""

    async def play(self, alarm: Alarm, settings: MusicSettings) -> None:
        raise NotImplementedError


@dataclass
class PlayerRegistry:
    """Registry mapping music sources to a playback implementation."""

    players: Dict[str, BasePlayer]

    def register(self, source: str, player: BasePlayer) -> None:
        self.players[source] = player

    async def play(self, alarm: Alarm) -> None:
        settings = alarm.music
        player = self.players.get(settings.source)
        if not player:
            raise PlayerError(f"No player registered for source '{settings.source}'")
        await player.play(alarm, settings)


class TonePlayer(BasePlayer):
    """Generate a simple sine wave tone when the alarm fires."""

    def __init__(self, *, sample_rate: int = 44_100) -> None:
        self.sample_rate = sample_rate

    async def play(self, alarm: Alarm, settings: MusicSettings) -> None:  # pragma: no-cover - heavily time based
        duration = max(1, int(settings.tone_duration_seconds))
        frequency = max(100, int(settings.tone_frequency_hz))
        if simpleaudio is None:
            # Fall back to the terminal bell. It is crude but works across environments.
            for _ in range(duration):
                sys.stdout.write("\a")
                sys.stdout.flush()
                await asyncio.sleep(1)
            return

        num_samples = int(self.sample_rate * duration)
        amplitude = 32_000
        sine_wave = bytearray()
        for i in range(num_samples):
            sample = amplitude * math.sin(2 * math.pi * frequency * (i / self.sample_rate))
            sine_wave.extend(struct.pack("<h", int(sample)))

        wave_obj = simpleaudio.WaveObject(bytes(sine_wave), 1, 2, self.sample_rate)
        play_obj = wave_obj.play()
        while play_obj.is_playing():
            await asyncio.sleep(0.1)


class SpotifyPlayer(BasePlayer):
    """Launch Spotify with the configured URI."""

    def __init__(self, *, open_browser: bool = True, command: Optional[str] = None) -> None:
        self.open_browser = open_browser
        self.command = command

    async def play(self, alarm: Alarm, settings: MusicSettings) -> None:  # pragma: no-cover - requires Spotify
        uri = settings.resource
        if not uri:
            raise PlayerError("Spotify URI missing")

        if self.command:
            process = await asyncio.create_subprocess_exec(self.command, uri)
            await process.communicate()
            return

        if self.open_browser:
            if not webbrowser.open(f"spotify:{uri}"):
                raise PlayerError("Could not open Spotify URI via default handler")
            return

        raise PlayerError("No mechanism to open Spotify URI configured")



class AppLauncherPlayer(BasePlayer):
    """Open a local application or file using the operating system handler."""

    async def play(self, alarm: Alarm, settings: MusicSettings) -> None:  # pragma: no-cover - depends on OS integration
        resource = settings.resource
        if not resource:
            raise PlayerError("Application resource is required")
        if sys.platform.startswith('win'):
            os.startfile(resource)  # type: ignore[attr-defined]
            return
        if sys.platform == 'darwin':
            process = await asyncio.create_subprocess_exec('open', resource)
            await process.communicate()
            return
        command = shutil.which('xdg-open')
        if command:
            process = await asyncio.create_subprocess_exec(command, resource)
            await process.communicate()
            return
        raise PlayerError('No mechanism to open application resources found')


class CommandPlayer(BasePlayer):
    """Invoke an arbitrary command to handle playback."""

    def __init__(self, command: str, *, cwd: Optional[Path] = None, env: Optional[Dict[str, str]] = None) -> None:
        if not command:
            raise ValueError("CommandPlayer requires a command")
        self.command = command
        self.cwd = cwd
        self.env = env

    async def play(self, alarm: Alarm, settings: MusicSettings) -> None:
        resource = settings.resource or ""
        command = self.command.format(resource=resource, label=alarm.label)
        process = await asyncio.create_subprocess_shell(command, cwd=self.cwd, env={**os.environ, **(self.env or {})})
        await process.communicate()
        if process.returncode not in (0, None):
            raise PlayerError(f"Command '{command}' exited with status {process.returncode}")
