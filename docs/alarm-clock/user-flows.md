# User Flows

## Create a New Alarm
1. User taps **Add Alarm**.
2. Selects time via time picker.
3. Chooses recurrence (single, weekdays, custom days).
4. Picks audio source:
   - Select default tone.
   - Or link Spotify account (if not already) and pick playlist/track.
5. Configures options: snooze duration, vibration, volume ramp.
6. Saves alarm → repository writes to database and scheduler programs `AlarmManager`.

## Alarm Trigger
1. `AlarmReceiver` starts `AlarmService` as a foreground service.
2. Service resolves Spotify authentication; if not available, plays local tone.
3. Full-screen alarm activity appears with current track info.
4. User either snoozes (service schedules new alarm after snooze duration) or dismisses (service stops playback and clears notification).

## Spotify Authentication Flow
1. User opens **Music Sources** settings.
2. Taps **Connect Spotify** → OAuth web login using Spotify Auth SDK.
3. Receives access + refresh token stored securely.
4. `SpotifyMusicSource` uses tokens to connect via App Remote.
5. User selects Spotify content for alarms.

## Background Reschedule After Reboot
1. Device reboots.
2. `BootCompletedReceiver` starts `RescheduleWorker`.
3. Worker reads enabled alarms and re-registers them with `AlarmManager`.
4. Confirmation notification informs user that alarms are ready.

## Gentle Wake Flow
1. Alarm configured with a 15-minute volume ramp.
2. `AlarmScheduler` schedules both the main alarm and a pre-alarm service.
3. Pre-alarm uses ambient sound at low volume and gradually increases.
4. At main alarm time, service transitions to the selected music source at configured volume.

