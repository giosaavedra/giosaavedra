# Alarm Clock Toolkit

This repository provides working building blocks for an alarm clock that can trigger Spotify (or any installed music player) as well as bundled tones without leaving a UI open in the foreground.

## Components
- [`alarm_clock/`](alarm_clock/) – a Python background scheduler with a CLI for adding, enabling, or triggering alarms. It persists alarms to disk, plays tones out of the box, and can launch Spotify URIs or arbitrary applications.
- [`docs/alarm-clock`](docs/alarm-clock/) – requirements, user journeys, and architecture notes that guided the implementation.
- [`android/`](android/) – the original Android prototype sources kept for reference if you want to build a native mobile client.

## Quick start
1. Add an alarm:
   ```bash
   python -m alarm_clock add wake-up --hour 7 --minute 30 --timezone "America/New_York" --repeat mon tue wed thu fri --music-source spotify --music-resource spotify:playlist:YOUR_PLAYLIST
   ```
2. Run the scheduler as a background service (leave it running with systemd, pm2, or a simple `tmux` session):
   ```bash
   python -m alarm_clock run
   ```
3. List, enable/disable, trigger, or remove alarms:
   ```bash
   python -m alarm_clock list
   python -m alarm_clock disable wake-up
   python -m alarm_clock trigger wake-up
   ```

The CLI stores alarms in `~/.alarm_clock/alarms.json` by default. Use `--store` to point at a different location, or run multiple schedulers with different stores.

## Testing
Execute the automated suite with:

```bash
pytest
```

The tests cover both the recurrence calculations and the asynchronous scheduler loop that ensures alarms fire even when the UI is closed.
- 👋 Hi, I’m @giosaavedra
- 👀 I’m interested in information technology, gaming, and all that is tech.
- 🌱 I’m currently learning at Coursera
- 💞️ I’m looking to collaborate on any project that will help me understand code.
- 📫 How to reach me giosaavedra19@gmail.com

<!---
giosaavedra/giosaavedra is a ✨ special ✨ repository because its `README.md` (this file) appears on your GitHub profile.
You can click the Preview link to take a look at your changes.
--->
