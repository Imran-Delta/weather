# weather

A deterministic weather generation library for games and simulations.  
Given a single time input (and optional location/climate parameters), it returns a complete, reproducible weather report.

## Features

- Fully deterministic – same input always yields same output.
- Supports game minutes, real‑time, or current UTC.
- Optional latitude, longitude, elevation for fine‑tuning.
- Built‑in Köppen climate profiles (extensible).
- Includes:
  - Temperature, pressure, humidity, dew point, wind (speed/direction/cardinal)
  - Precipitation probability, cloud cover, instability (CAPE‑like)
  - 20+ weather conditions (clear, rain, snow, thunderstorm, blizzard, etc.)
  - Special atmospheric phenomena: aurora, rainbow, sun dog, halo
  - Moon phase (with year drift) and seasonal events (equinoxes/solstices)
  - Flavor text and ASCII art for every condition
- All disasters can be enabled/disabled per profile.

## Installation

Copy `weather.py` into your project and import:

```python
from weather import weather, WeatherData, list_koppen_codes
```

(No external dependencies – only the Python standard library.)

## Usage

### Basic – current weather at default location

```python
w = weather()
print(f"{w.condition} at {w.temperature}°C")
print(w.ascii_art)
print(w.flavor)
```

### Specify game minutes

```python
w = weather(game_minutes=123456)
```

### Use real time (UTC)

```python
from datetime import datetime

w = weather(real_time=datetime(2025, 6, 1, 12, 0))
```

### Scale time (e.g., 1 real minute = 12 game minutes)

```python
w = weather(real_time=datetime.now(), real_time_scale=12)
```

### Set location (latitude affects aurora; elevation applies lapse rate)

```python
w = weather(latitude=60.0, elevation=200, koppen="Dfd")
```

### List available Köppen codes

```python
print(list_koppen_codes())
```

### Allow all disasters (overrides profile)

```python
w = weather(koppen="Cfb", allow_all_disasters=True)
```

## WeatherData fields

| Field                | Type     | Description                                |
|----------------------|----------|--------------------------------------------|
| game_minutes         | int      | Internal game minute count                 |
| datetime_str         | str      | Formatted "Year X, Day Y, HH:MM"           |
| temperature          | float    | Air temperature (°C)                        |
| feels_like           | float    | Apparent temperature (°C)                   |
| pressure             | float    | Atmospheric pressure (hPa)                  |
| humidity             | float    | Relative humidity (%)                       |
| dew_point            | float    | Dew point (°C)                              |
| wind_speed           | float    | Wind speed (m/s)                            |
| wind_direction       | float    | Wind direction (degrees)                    |
| wind_cardinal        | str      | Cardinal direction (N, NNE, etc.)           |
| condition            | str      | Weather condition (e.g., "light rain")      |
| cloud_cover          | int      | Cloud cover (%)                             |
| precipitation_prob   | float    | Precipitation probability (%)                |
| instability          | float    | CAPE‑like instability (J/kg)                 |
| moon_phase           | str      | Moon phase name                             |
| moon_emoji           | str      | Moon phase emoji                            |
| season_event         | str\|None| Solstice/equinox if within ±2 days          |
| flavor               | str      | Descriptive flavor text                     |
| ascii_art            | str      | ASCII art representing the condition        |


# `- Update LOGS -`
# -Update 0.0.1-
* Bro, this is 0.0.1. Why you even looking here?