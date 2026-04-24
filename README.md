# weatherz
A deterministic weather generation library for games and simulations.
Given a single time input (and optional location/climate parameters), it returns a complete, reproducible weather report.

## Features
* Fully deterministic: Same input always yields the same output.
* Flexible Time: Supports game minutes, real-time, or current UTC.
* Geographic Context: Optional latitude, longitude, and elevation for fine-tuning.
* Climate Profiles: Built-in Köppen climate profiles (extensible).
* Comprehensive Data:
  * Temperature, pressure, humidity, dew point, wind (speed/direction/cardinal).
  * Precipitation probability, cloud cover, instability (CAPE-like).
  * 20+ weather conditions (clear, rain, snow, thunderstorm, blizzard, etc.).
  * Special atmospheric phenomena: aurora, rainbow, sun dog, halo.
  * Moon phase (with year drift) and seasonal events (equinoxes/solstices).
  * Flavor text and ASCII art for every condition.
* Customizable: All disasters can be enabled/disabled per profile.
* Per-trend memory isolation – pass a `trend_id` to keep smoothing separate for concurrent use.
* WeatherArchive – persistent SQLite storage of sparse checkpoints, ensuring smooth weather even when jumping to arbitrary times.
* Fast-forward generation – leap months or years in milliseconds instead of computing every intermediate minute.

## Installation
Copy `weather.py` into your project and import:
```python
from weather import weather, WeatherData, list_koppen_codes, WeatherArchive
```
No external dependencies — only the Python standard library.

## Usage

### Basic – current weather at default location
```python
w = weather()
print(f"{w.condition} at {w.temperature}°C")
print(w.ascii_art)
print(w.flavor)
```

### Advanced Time & Location
```python
# Specify game minutes
w = weather(game_minutes=123456)

# Use real time (UTC)
from datetime import datetime
w = weather(real_time=datetime(2025, 6, 1, 12, 0))

# Scale time (e.g., 1 real minute = 12 game minutes)
w = weather(real_time=datetime.now(), real_time_scale=12)

# Set location (latitude affects aurora; elevation applies lapse rate)
w = weather(latitude=60.0, elevation=200, koppen="Dfd")

# Isolate smoothing per trend
w1 = weather(game_minutes=1000, trend_id="siberia")
w2 = weather(game_minutes=1000, trend_id="desert")  # separate memory
```

## WeatherArchive – Persistent, Smooth Trends

`WeatherArchive` stores weather checkpoints in a local SQLite database. When you request a time, it generates forward from the nearest checkpoint, ensuring smooth transitions without storing every minute.

```python
archive = WeatherArchive("my_weather.db")

# Add a trend (location + climate)
trend_id = archive.add_trend(
    name="Siberian Outpost",
    latitude=60.0,
    longitude=120.0,
    elevation=200.0,
    koppen="Dfd"
)

# Get weather at game minute 5000
w = archive.get_weather(trend_id, 5000)

# Later, get minute 6000 (resumes from checkpoint at 5000)
w2 = archive.get_weather(trend_id, 6000)

# Read-only mode (no new checkpoints saved)
w3 = archive.get_weather(trend_id, 7000, read_only=True)
```

> **Thread Safety:** WeatherArchive is thread-safe. Concurrent requests for different trends run in parallel; requests for the same trend are serialized to preserve smoothing continuity.

### Fast-Forward Generation

By default, `get_weather` uses fast-forward mode when the gap between the nearest checkpoint and the target is large (≥ one game-day / 1440 minutes). Instead of computing every intermediate minute, it leaps forward in chunks and back-fills the smoothing memory so weather at the boundary is still plausible.

```python
# Default: fast-forward automatically kicks in for large gaps
w = archive.get_weather(trend_id, 525600)  # jump a whole game-year instantly

# Exact mode: minute-by-minute, fully faithful sequence (slower)
w = archive.get_weather(trend_id, 525600, exact=True)

# Custom step: control the leap size (in game minutes)
w = archive.get_weather(trend_id, 525600, fast_forward_step=720)  # leap every 12 hours
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `exact` | bool | `False` | Force minute-by-minute generation (full accuracy, slower) |
| `fast_forward_step` | int or None | `checkpoint_interval` (1440) | Leap size in game minutes when fast-forwarding |

**Trade-off:** Fast-forward skips subtle minute-to-minute variations inside each leap, so the weather at the target *may* differ slightly from a full exact run. For gameplay this is imperceptible; use `exact=True` only when you need a perfectly reproducible sequence (e.g. replay systems).

## WeatherData Fields
| Field | Type | Description |
|---|---|---|
| `game_minutes` | int | Internal game minute count |
| `datetime_str` | str | Formatted "Year X, Day Y, HH:MM" |
| `temperature` | float | Air temperature (°C) |
| `feels_like` | float | Apparent temperature (°C) |
| `pressure` | float | Atmospheric pressure (hPa) |
| `humidity` | float | Relative humidity (%) |
| `dew_point` | float | Dew point (°C) |
| `wind_speed` | float | Wind speed (m/s) |
| `wind_direction` | float | Wind direction (degrees) |
| `wind_cardinal` | str | Cardinal direction (N, NNE, etc.) |
| `condition` | str | Weather condition (e.g., "light rain") |
| `cloud_cover` | int | Cloud cover (%) |
| `precipitation_prob` | float | Precipitation probability (%) |
| `instability` | float | CAPE-like instability (J/kg) |
| `moon_phase` | str | Moon phase name |
| `moon_emoji` | str | Moon phase emoji |
| `season_event` | str/None | Solstice/equinox if within ±2 days |
| `flavor` | str | Descriptive flavor text |
| `ascii_art` | str | ASCII art representing the condition |

---

## Update Logs

### 0.0.1
* Added `trend_id` parameter to `weather()` for isolated smoothing memory per concurrent caller.
* Added `WeatherArchive` class for persistent, checkpoint-based storage.
* Thread-safe archive with per-trend locks.
* Added fast-forward generation to `WeatherArchive.get_weather` — large time jumps now leap in day-sized chunks instead of computing every minute, with smoothing memory back-filled to prevent jarring transitions. Use `exact=True` to restore the old minute-by-minute behaviour.

### 0.0.1dev1
* Bro, this is 0.0.1. Why you even looking here?
