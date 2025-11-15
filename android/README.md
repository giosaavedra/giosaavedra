# Android Alarm Clock Prototype

This module contains Kotlin source files that illustrate how to implement the background alarm workflow described in the documentation. The code is organized to highlight core concepts:

- **Scheduling:** Wrapper around `AlarmManager` that keeps alarms exact and resilient to device restarts.
- **Foreground service:** Plays alarm audio while respecting Android's background execution limits.
- **Music sources:** Strategy pattern that allows Spotify playback with fallbacks to local tones.

> **Note:** The files are provided as reference-quality code snippets. To convert this into a runnable project, drop the sources into a standard Android Studio project, add Gradle configuration (Compose, Hilt, Spotify SDK), and wire up the missing UI resources.

## Key Files
- [`AlarmScheduler.kt`](src/main/java/com/example/alarmclock/AlarmScheduler.kt) — Schedules and cancels alarms.
- [`AlarmReceiver.kt`](src/main/java/com/example/alarmclock/AlarmReceiver.kt) — Broadcast receiver that launches the foreground service.
- [`AlarmService.kt`](src/main/java/com/example/alarmclock/AlarmService.kt) — Foreground service responsible for audio playback and notifications.
- [`MusicSource.kt`](src/main/java/com/example/alarmclock/MusicSource.kt) — Strategy interface plus local tone implementation.
- [`SpotifyMusicSource.kt`](src/main/java/com/example/alarmclock/SpotifyMusicSource.kt) — Spotify integration with timeout fallback.
- [`MainActivity.kt`](src/main/java/com/example/alarmclock/MainActivity.kt) — Jetpack Compose UI stub for managing alarms.
- [`AndroidManifest.xml`](src/main/AndroidManifest.xml) — Declares permissions, receivers, and services.

## Additional Setup Notes
1. Request `SCHEDULE_EXACT_ALARM` permission for Android 12+ devices.
2. Provide the Spotify client ID and redirect URI in your Gradle secrets or manifest placeholders.
3. Include at least one local alarm tone under `res/raw` and reference it in `LocalToneMusicSource`.
4. Implement actual persistence using Room; in these samples, an in-memory repository is used for brevity.

