# Alarm Clock App Architecture

## High-Level Overview
The app is structured around modular layers so background scheduling remains robust while optional integrations (Spotify, sleep tracking) can evolve independently.

```
┌─────────────────────────────┐
│           UI Layer          │
│ Jetpack Compose screens     │
│ ViewModels (AlarmList, ... )│
└─────────────▲───────────────┘
              │
┌─────────────┴───────────────┐
│        Domain Layer          │
│ Use cases (ScheduleAlarm,    │
│ CancelAlarm, SnoozeAlarm)    │
│ Kotlin coroutines + Flow     │
└─────────────▲───────────────┘
              │
┌─────────────┴───────────────┐
│        Data Layer            │
│ Room database, repositories  │
│ Spotify service API client   │
└─────────────▲───────────────┘
              │
┌─────────────┴───────────────┐
│ Platform Services            │
│ AlarmManager, Foreground     │
│ Service, MediaSession,       │
│ WorkManager (reschedule)     │
└──────────────────────────────┘
```

## Key Modules
- `core-model`: Data classes for alarms, audio sources, recurrence patterns.
- `core-database`: Room entities/DAO for persistence.
- `feature-scheduler`: Contains the scheduling use cases and a wrapper around `AlarmManager`.
- `feature-alarmplayer`: Foreground service, audio routing, Spotify integration.
- `feature-ui`: Jetpack Compose screens and navigation graphs.

Each module exposes a clean API and depends only on lower layers to keep background behavior testable.

## Background Scheduling Flow
1. User creates or updates an alarm via UI.
2. `ScheduleAlarmUseCase` validates user input and writes to the repository.
3. Repository saves the alarm and triggers `AlarmScheduler`.
4. `AlarmScheduler` calls `AlarmManager.setExactAndAllowWhileIdle` with a `PendingIntent` targeting `AlarmReceiver`.
5. When the alarm fires, `AlarmReceiver` launches `AlarmService` as a foreground service.
6. `AlarmService` resolves the preferred `MusicSource` (Spotify vs. local tone) and begins playback.
7. A full-screen activity displays the alarm UI while the service handles snooze/dismiss actions.

## Handling Spotify and Fallbacks
- Spotify sessions are managed by `SpotifyMusicSource`, which uses the Spotify App Remote SDK to control playback.
- If Spotify fails to connect within a configurable timeout (default 5 seconds), the system falls back to a bundled tone through `LocalToneMusicSource`.
- The currently active `MusicSource` publishes state via a `StateFlow` so the UI can reflect playback status.

## Offline & Edge Cases
- All alarms persist locally; Spotify is optional per alarm.
- If network is unavailable at the trigger time, the fallback tone starts immediately while Spotify reconnect attempts continue in the background.
- A watchdog `WorkManager` task verifies the alarm fired and re-schedules if the device restarted during playback.

## Data Model Snapshot
```kotlin
data class Alarm(
    val id: Long,
    val label: String,
    val time: LocalTime,
    val recurrence: RecurrencePattern,
    val audioPreference: AudioPreference,
    val snoozeMinutes: Int,
    val volumeRampMinutes: Int?,
    val vibrationEnabled: Boolean,
    val enabled: Boolean
)

data sealed interface AudioPreference {
    data class LocalTone(val resName: String) : AudioPreference
    data class SpotifyTrack(
        val uri: String,
        val fallbackTone: LocalTone,
        val startOffsetMs: Int = 0
    ) : AudioPreference
}
```

## Persistence Strategy
- Room database storing `AlarmEntity`, `RecurrenceEntity`, and `AudioPreferenceEntity` tables.
- Database migrations versioned to support future analytics data.
- Repository exposes `Flow<List<Alarm>>` to keep UI reactive.

## Dependency Injection
- Use Hilt for DI, with modules for scheduling, Spotify, repository, and use cases.
- Foreground service obtains dependencies via entry points.

## Testing Approach
- Use `AlarmManager` shadow (Robolectric) for unit testing scheduling logic.
- Integration tests verifying Spotify fallback by mocking `MusicSource` implementations.
- UI tests with Compose Test framework simulating create/edit alarm flows.

## Security Considerations
- Store OAuth refresh tokens with `EncryptedSharedPreferences`.
- Ask for exact alarm permission (`SCHEDULE_EXACT_ALARM`) on Android 12+.
- Provide opt-in analytics with clear privacy controls.

## Future Enhancements
- Shared alarm presets synced via cloud backend (Firebase/Amplify).
- Integrate wearable data to adjust smart wake time automatically.
- Use `Media3` for unified playback management across providers.

