# Alarm Clock App Requirements

## Vision
Create a modern mobile alarm clock experience that works reliably in the background, supports streaming services such as Spotify (as well as local tones), and provides smart wake-up features without requiring the app to stay open.

## Target Platforms
- **Android (initial focus):** Native implementation using Kotlin and Jetpack libraries.
- **iOS (future roadmap):** SwiftUI implementation leveraging `UNUserNotificationCenter` and background tasks.

## Personas
- **Daily Commuter:** Needs dependable alarms with backup tones even when streaming fails.
- **Music Enthusiast:** Wants to wake up to curated playlists from Spotify or Apple Music.
- **Heavy Sleeper:** Requires escalating volume, multiple alarms, and optional challenge-based dismissal.

## Functional Requirements
1. **Alarm Scheduling**
   - Users can create, edit, enable, disable, and delete alarms.
   - Supports recurring alarms by weekday pattern and one-off alarms.
   - Alarms fire even when the app is closed or the device is locked.
2. **Audio Sources**
   - Local tone library shipped with the app.
   - Spotify integration via the Spotify Android SDK (play playlist, album, track, or podcast).
   - Fallback to local tone if streaming app is unavailable or offline.
3. **Pre-wake Smart Features**
   - Optional gentle wake-up (fade-in) 5–30 minutes before the main alarm using ambient sounds.
   - Sleep tracking hooks for future integrations (e.g., Health Connect, wearable data).
4. **Alarm Experience**
   - Full-screen alarm UI with dismiss and snooze actions.
   - Customizable snooze duration (default 10 minutes).
   - Escalating volume option and vibration toggle.
5. **Background Behavior**
   - Schedule alarms using `AlarmManager` with `setExactAndAllowWhileIdle`.
   - Use a foreground service when playing alarm audio to ensure it continues under Doze mode.
   - Persist alarms in Room database and reschedule after device reboot via `BOOT_COMPLETED`.
6. **User Settings**
   - Global settings for default alarm tone, snooze duration, vibration, Spotify account linking, and Wi-Fi-only streaming.
7. **Notifications**
   - Upcoming alarm reminders (e.g., 10 minutes before).
   - Persistent notification while an alarm is active, allowing quick snooze/dismiss.
8. **Accessibility & Localization**
   - VoiceOver/TalkBack accessible.
   - Support for left-to-right and right-to-left locales.

## Non-functional Requirements
- **Reliability:** >99% alarm success rate validated through instrumentation tests.
- **Performance:** Alarm scheduling operations complete within 200 ms on mid-tier devices.
- **Security:** OAuth tokens for Spotify stored using `EncryptedSharedPreferences`.
- **Maintainability:** Feature modules separated to keep Spotify integration optional.
- **Testing:** Unit tests for scheduling logic, integration tests using `AlarmManager` shadows, UI tests for alarm flow.

## External Integrations
- Spotify Android SDK (`com.spotify.android:auth` and `com.spotify.android:app-remote`) for authentication and playback control.
- Android media session APIs for controlling playback across different music providers.
- Optional: Sleep tracking API integrations via Health Connect.

## Roadmap
1. **MVP (Sprint 1–2)**
   - Alarm CRUD with local tones.
   - Background scheduling with AlarmManager + foreground service.
   - Simple UI for listing alarms.
2. **Streaming Support (Sprint 3–4)**
   - Spotify authentication and playback fallback logic.
   - Volume ramp-up and snooze customization.
3. **Delight (Sprint 5+)**
   - Sleep analytics dashboard.
   - Smart device integration (smart lights, IoT triggers).
   - Shareable alarm presets.

