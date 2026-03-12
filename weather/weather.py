"""
weather - Deterministic weather generation for games and simulations.

A single function `weather()` produces a complete weather report for any moment in time,
with optional location and climate parameters. All randomness is seeded by the time input,
making every call reproducible.

Example:
    from weather import weather
    from datetime import datetime

    # Current weather at default location (all disasters possible)
    w = weather()

    # Weather at a specific game minute
    w = weather(game_minutes=123456)

    # Weather in Paris (latitude 48.9, elevation 35m) using real time
    w = weather(real_time=datetime(2025, 6, 1, 12, 0), latitude=48.9, longitude=2.3, elevation=35)

    # Weather using Köppen code for Siberian climate, with time scaling (1 real minute = 12 game minutes)
    w = weather(real_time=datetime.now(), real_time_scale=12, koppen="Dfd")

    print(w.temperature, w.condition, w.ascii_art)
"""

import math
import random
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple, Union
from dataclasses import dataclass

# ----------------------------------------------------------------------
# Time constants (game minutes)
# ----------------------------------------------------------------------
MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
MINUTES_PER_DAY = MINUTES_PER_HOUR * HOURS_PER_DAY
DAYS_PER_YEAR = 365
MINUTES_PER_YEAR = MINUTES_PER_DAY * DAYS_PER_YEAR

# ----------------------------------------------------------------------
# Deterministic random (seeded)
# ----------------------------------------------------------------------
def _deterministic_random(seed: int, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Return a deterministic float in [min_val, max_val] using a seeded RNG."""
    rng = random.Random(seed)
    return rng.uniform(min_val, max_val)

# ----------------------------------------------------------------------
# Climate profiles
# ----------------------------------------------------------------------
# List of all possible disaster conditions (used for the DEFAULT profile)
ALL_DISASTERS = [
    "hurricane", "tropical storm", "gale", "blizzard",
    "dust storm", "tornado", "ice fog", "squall",
    "heat burst", "downburst", "polar low"
]

# Base profile: original Brandenton constants (all disasters possible)
DEFAULT_PROFILE = {
    "temp_annual_mean": 10.0,
    "temp_annual_amplitude": 15.0,
    "temp_daily_amplitude": 5.0,
    "pressure_mean": 1013.0,
    "pressure_annual_amplitude": 10.0,
    "pressure_daily_amplitude": 2.0,
    "humidity_base": 70.0,
    "wind_base": 3.0,
    "cape_base": 500.0,
    "cape_annual_amplitude": 300.0,
    "cape_daily_amplitude": 400.0,
    "cape_noise_amplitude": 150.0,
    "hurricane_temp_min": 26.0,
    "hurricane_pressure_max": 980.0,
    "hurricane_wind_min": 30.0,
    "hurricane_humidity_min": 80.0,
    "storm_temp_min": 24.0,
    "storm_pressure_max": 995.0,
    "storm_wind_min": 18.0,
    "storm_humidity_min": 70.0,
    "disasters_allowed": ALL_DISASTERS,
}

# Köppen climate profiles (only a few examples; extend as needed)
KOPPEN_PROFILES = {
    "Dfb": {  # Humid continental
        "temp_annual_mean": 8.0,
        "temp_annual_amplitude": 16.0,
        "temp_daily_amplitude": 6.0,
        "pressure_mean": 1013.0,
        "pressure_annual_amplitude": 9.0,
        "pressure_daily_amplitude": 2.0,
        "humidity_base": 70.0,
        "wind_base": 3.5,
        "cape_base": 500.0,
        "cape_annual_amplitude": 250.0,
        "cape_daily_amplitude": 350.0,
        "cape_noise_amplitude": 100.0,
        "hurricane_temp_min": 26.0,      # same thresholds, rarely met
        "hurricane_pressure_max": 980.0,
        "hurricane_wind_min": 30.0,
        "hurricane_humidity_min": 80.0,
        "storm_temp_min": 24.0,
        "storm_pressure_max": 995.0,
        "storm_wind_min": 18.0,
        "storm_humidity_min": 70.0,
        "disasters_allowed": ["thunderstorm", "tornado", "blizzard", "gale"],
    },
    "Dfd": {  # Extreme subarctic (Siberia)
        "temp_annual_mean": -5.0,
        "temp_annual_amplitude": 25.0,
        "temp_daily_amplitude": 4.0,
        "pressure_mean": 1015.0,
        "pressure_annual_amplitude": 12.0,
        "pressure_daily_amplitude": 1.5,
        "humidity_base": 60.0,
        "wind_base": 3.0,
        "cape_base": 50.0,
        "cape_annual_amplitude": 50.0,
        "cape_daily_amplitude": 80.0,
        "cape_noise_amplitude": 30.0,
        "hurricane_temp_min": 26.0,
        "hurricane_pressure_max": 980.0,
        "hurricane_wind_min": 30.0,
        "hurricane_humidity_min": 80.0,
        "storm_temp_min": 24.0,
        "storm_pressure_max": 995.0,
        "storm_wind_min": 18.0,
        "storm_humidity_min": 70.0,
        "disasters_allowed": ["blizzard", "ice fog", "gale"],
    },
    "BWh": {  # Hot desert
        "temp_annual_mean": 28.0,
        "temp_annual_amplitude": 12.0,
        "temp_daily_amplitude": 15.0,
        "pressure_mean": 1015.0,
        "pressure_annual_amplitude": 8.0,
        "pressure_daily_amplitude": 4.0,
        "humidity_base": 20.0,
        "wind_base": 5.0,
        "cape_base": 100.0,
        "cape_annual_amplitude": 50.0,
        "cape_daily_amplitude": 100.0,
        "cape_noise_amplitude": 40.0,
        "hurricane_temp_min": 26.0,
        "hurricane_pressure_max": 980.0,
        "hurricane_wind_min": 30.0,
        "hurricane_humidity_min": 80.0,
        "storm_temp_min": 24.0,
        "storm_pressure_max": 995.0,
        "storm_wind_min": 18.0,
        "storm_humidity_min": 70.0,
        "disasters_allowed": ["dust storm", "gale"],
    },
    "Cfb": {  # Oceanic (e.g., UK)
        "temp_annual_mean": 12.0,
        "temp_annual_amplitude": 6.0,
        "temp_daily_amplitude": 5.0,
        "pressure_mean": 1012.0,
        "pressure_annual_amplitude": 8.0,
        "pressure_daily_amplitude": 2.0,
        "humidity_base": 80.0,
        "wind_base": 4.0,
        "cape_base": 300.0,
        "cape_annual_amplitude": 150.0,
        "cape_daily_amplitude": 200.0,
        "cape_noise_amplitude": 60.0,
        "hurricane_temp_min": 26.0,
        "hurricane_pressure_max": 980.0,
        "hurricane_wind_min": 30.0,
        "hurricane_humidity_min": 80.0,
        "storm_temp_min": 24.0,
        "storm_pressure_max": 995.0,
        "storm_wind_min": 18.0,
        "storm_humidity_min": 70.0,
        "disasters_allowed": ["gale", "thunderstorm"],
    },
    "Af": {  # Tropical rainforest
        "temp_annual_mean": 26.0,
        "temp_annual_amplitude": 2.0,
        "temp_daily_amplitude": 8.0,
        "pressure_mean": 1010.0,
        "pressure_annual_amplitude": 5.0,
        "pressure_daily_amplitude": 3.0,
        "humidity_base": 85.0,
        "wind_base": 2.0,
        "cape_base": 1200.0,
        "cape_annual_amplitude": 200.0,
        "cape_daily_amplitude": 500.0,
        "cape_noise_amplitude": 200.0,
        "hurricane_temp_min": 26.0,
        "hurricane_pressure_max": 980.0,
        "hurricane_wind_min": 30.0,
        "hurricane_humidity_min": 80.0,
        "storm_temp_min": 24.0,
        "storm_pressure_max": 995.0,
        "storm_wind_min": 18.0,
        "storm_humidity_min": 70.0,
        "disasters_allowed": ["thunderstorm", "tropical storm", "hurricane"],
    },
}

# ----------------------------------------------------------------------
# Helper functions (dew point, apparent temp, etc.)
# ----------------------------------------------------------------------
def _calculate_dew_point(temperature: float, humidity: float) -> float:
    """Magnus-Tetens dew point formula."""
    a = 17.27
    b = 237.7
    alpha = (a * temperature) / (b + temperature) + math.log(humidity / 100.0)
    # Prevent division by zero
    if abs(a - alpha) < 1e-9:
        return -100.0
    return (b * alpha) / (a - alpha)

def _calculate_apparent_temperature(temp: float, humidity: float, wind_speed: float) -> float:
    """Feels‑like temperature (wind chill or heat index)."""
    # Wind chill (temp < 10°C, wind > 1.5 m/s)
    if temp < 10 and wind_speed > 1.5:
        v_kmh = wind_speed * 3.6
        wc = 13.12 + 0.6215 * temp - 11.37 * (v_kmh ** 0.16) + 0.3965 * temp * (v_kmh ** 0.16)
        return round(wc, 1)
    # Heat index (temp > 20°C, humidity > 40%)
    if temp > 20 and humidity > 40:
        hi = (-8.78469475556 + 1.61139411 * temp + 2.33854883889 * humidity
              - 0.14611605 * temp * humidity - 0.012308094 * temp * temp
              - 0.016424828 * humidity * humidity + 0.002211732 * temp * temp * humidity
              + 0.00072546 * temp * humidity * humidity - 0.000003582 * temp * temp * humidity * humidity)
        return round(max(temp, hi), 1)
    return round(temp, 1)

def _calculate_instability(game_minutes: int, params: dict) -> float:
    """CAPE‑like instability with cycles and noise."""
    minute_of_day = game_minutes % MINUTES_PER_DAY
    day_of_year = (game_minutes // MINUTES_PER_DAY) % DAYS_PER_YEAR
    t_year = day_of_year / DAYS_PER_YEAR
    t_day = minute_of_day / MINUTES_PER_DAY

    annual = params["cape_annual_amplitude"] * math.sin(2 * math.pi * t_year - math.pi / 2)
    daily = params["cape_daily_amplitude"] * math.cos(2 * math.pi * (t_day - 14 / 24))
    noise_seed = game_minutes * 4000
    noise = _deterministic_random(noise_seed, -1.0, 1.0) * params["cape_noise_amplitude"]
    cape = params["cape_base"] + annual + daily + noise
    return max(0, cape)

def _smooth_wind_direction(game_minutes: int) -> float:
    """
    Improved wind direction: slow seasonal rotation + small diurnal + noise.
    Returns degrees 0–360.
    """
    minute_of_day = game_minutes % MINUTES_PER_DAY
    day_of_year = (game_minutes // MINUTES_PER_DAY) % DAYS_PER_YEAR
    # Two full cycles per year
    base_dir = (360.0 * day_of_year / DAYS_PER_YEAR) * 2
    # Diurnal variation (±10°)
    diurnal = 10.0 * math.sin(2 * math.pi * minute_of_day / MINUTES_PER_DAY)
    # Random noise (±5°)
    noise_seed = game_minutes * 2000
    noise = _deterministic_random(noise_seed, -5.0, 5.0)
    return (base_dir + diurnal + noise) % 360.0

def _degrees_to_cardinal(deg: float) -> str:
    """Convert wind direction in degrees to cardinal point (N, NNE, etc.)."""
    cardinals = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                 "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    ix = round(deg / (360.0 / len(cardinals))) % len(cardinals)
    return cardinals[ix]

# ----------------------------------------------------------------------
# Moon phase with year drift
# ----------------------------------------------------------------------
def _get_moon_phase(day_of_year: int, year: int) -> Tuple[str, str]:
    """
    Return (phase_name, emoji) with an annual drift to avoid exact repetition.
    Approximate synodic month = 29.530588 days; drift ~11 days/year.
    """
    total_days = day_of_year + year * 11
    lunar_day = total_days % 29.530588
    if lunar_day < 1.8:
        return "New Moon", "🌑"
    if lunar_day < 5.1:
        return "Waxing Crescent", "🌒"
    if lunar_day < 8.8:
        return "First Quarter", "🌓"
    if lunar_day < 12.3:
        return "Waxing Gibbous", "🌔"
    if lunar_day < 16.1:
        return "Full Moon", "🌕"
    if lunar_day < 19.8:
        return "Waning Gibbous", "🌖"
    if lunar_day < 23.5:
        return "Last Quarter", "🌗"
    if lunar_day < 27.2:
        return "Waning Crescent", "🌘"
    return "New Moon", "🌑"

# ----------------------------------------------------------------------
# Seasonal events (solstices/equinoxes)
# ----------------------------------------------------------------------
def _get_season_event(day_of_year: int) -> Optional[str]:
    spring = 80   # March 21
    summer = 172  # June 21
    autumn = 265  # September 23
    winter = 355  # December 21
    if abs(day_of_year - spring) <= 2:
        return "🌸 Spring Equinox"
    if abs(day_of_year - summer) <= 2:
        return "☀️ Summer Solstice"
    if abs(day_of_year - autumn) <= 2:
        return "🍂 Autumn Equinox"
    if abs(day_of_year - winter) <= 2:
        return "❄️ Winter Solstice"
    return None

# ----------------------------------------------------------------------
# Flavor text dictionary
# ----------------------------------------------------------------------
_FLAVORS = {
    "clear": [
        "The sky is a brilliant blue.",
        "Perfect weather for a stroll.",
        "Birds are singing in the distance.",
    ],
    "partly cloudy": [
        "Fluffy clouds drift lazily.",
        "Sun and clouds share the sky.",
        "A pleasant mix of sun and shade.",
    ],
    "cloudy": [
        "A gray blanket covers the sky.",
        "The sun is hidden behind clouds.",
        "It's a bit gloomy today.",
    ],
    "light rain": [
        "A gentle drizzle falls.",
        "Pitter-patter on the rooftops.",
        "The air smells fresh and clean.",
    ],
    "rain": [
        "Rain taps against the windows.",
        "Puddles are forming on the ground.",
        "The rhythm of rainfall is soothing.",
    ],
    "heavy rain": [
        "Sheets of rain obscure the view.",
        "Gutters are overflowing.",
        "Best to stay indoors today.",
    ],
    "light snow": [
        "A few snowflakes dance in the air.",
        "A dusting of snow covers the ground.",
        "Winter's first kiss.",
    ],
    "snow": [
        "Snowfall creates a winter wonderland.",
        "Footprints are quickly covered.",
        "The world is silent under snow.",
    ],
    "heavy snow": [
        "A blizzard rages outside.",
        "Visibility is near zero.",
        "Drifts pile high against the walls.",
    ],
    "light freezing rain": [
        "A thin glaze of ice forms on surfaces.",
        "Slick patches appear on walkways.",
        "Ice crystals sparkle in the light.",
    ],
    "freezing rain": [
        "Ice coats every surface.",
        "Walk carefully – it's slippery.",
        "Trees glisten with ice.",
    ],
    "heavy freezing rain": [
        "A dangerous ice storm is underway.",
        "Branches bend under the weight of ice.",
        "Travel is nearly impossible.",
    ],
    "thunderstorm": [
        "Lightning splits the sky!",
        "Thunder shakes the windows.",
        "Seek shelter from the storm.",
    ],
    "fog": [
        "The world disappears into mist.",
        "Shapes loom out of the fog.",
        "An eerie silence pervades.",
    ],
    "mist": [
        "A soft mist hangs in the air.",
        "Dew glistens on every leaf.",
        "Morning mist rises from the ground.",
    ],
    "haze": [
        "The sky has a milky veil.",
        "Heat shimmers on the horizon.",
        "The air feels thick and still.",
    ],
    "gale": [
        "Trees bend in the fierce wind.",
        "Hold onto your hat!",
        "The wind howls like a wolf.",
    ],
    "blizzard": [
        "Snow and wind rage together.",
        "A true whiteout condition.",
        "Stay warm and safe inside.",
    ],
    "drizzle": [
        "A fine, persistent drizzle.",
        "Everything is damp but not soaked.",
        "Mizzle – mist and drizzle combined.",
    ],
    "hurricane": [
        "CATEGORY 5 HURRICANE!",
        "Winds tear at the landscape.",
        "Seek immediate shelter!",
    ],
    "tropical storm": [
        "Tropical storm conditions.",
        "Heavy rain and strong winds.",
        "Stay alert for updates.",
    ],
    "dust storm": [
        "A wall of dust advances across the plain.",
        "Sand stings your skin as the wind howls.",
        "The sky turns orange-brown.",
    ],
    "tornado": [
        "A funnel cloud touches down!",
        "Debris flies through the air.",
        "Take cover immediately!",
    ],
    "ice fog": [
        "Tiny ice crystals hang in the air.",
        "Sun dogs appear around the sun.",
        "The world shimmers with frozen mist.",
    ],
    "squall": [
        "A sudden, violent wind accompanies the rain.",
        "The squall line passes with fury.",
        "Waves build rapidly on the lake.",
    ],
    "heat burst": [
        "The temperature jumps unexpectedly!",
        "Scorching wind rushes down.",
        "It feels like an oven outside.",
    ],
    "downburst": [
        "A powerful gust slams into the ground.",
        "Trees bend as if bowing.",
        "Straight-line winds cause damage.",
    ],
    "polar low": [
        "An arctic hurricane spins offshore.",
        "Snow and wind rage in a tight vortex.",
        "The polar low brings extreme cold and snow.",
    ],
    "aurora": [
        "The northern lights dance across the sky.",
        "Green and purple curtains shimmer overhead.",
        "Aurora borealis illuminates the night.",
    ],
    "rainbow": [
        "A brilliant rainbow arcs across the sky.",
        "Colors bend after the rain.",
        "A double rainbow appears!",
    ],
    "sun dog": [
        "Bright spots of light flank the sun.",
        "Ice crystals create a stunning sun dog.",
        "A prismatic display in the cold air.",
    ],
    "halo": [
        "A luminous ring surrounds the sun.",
        "Ice crystals form a halo around the light.",
        "A perfect circle of light in the sky.",
    ],
}

def _get_flavor_text(condition: str, seed: int) -> str:
    lst = _FLAVORS.get(condition, ["Unusual weather today."])
    idx = _deterministic_random(seed, 0, len(lst) - 0.999)
    return lst[int(idx)]

# ----------------------------------------------------------------------
# ASCII art dictionary
# ----------------------------------------------------------------------
_ASCII_ART = {
    "clear": "```\n    \\   |   /\n     \\  |  /\n      \\ | /\n    --- ☀️ ---\n      / | \\\n     /  |  \\\n    /   |   \\\n```",
    "partly cloudy": "```\n      .--.\n   .-(    ).\n  (___.__)__)\n     ☁️ ☀️\n```",
    "cloudy": "```\n      .--.\n   .-(    ).\n  (___.__)__)\n     ☁️☁️☁️\n```",
    "light rain": "```\n      .--.\n   .-(    ).\n  (___.__)__)\n     /  /  /\n```",
    "rain": "```\n      .--.\n   .-(    ).\n  (___.__)__)\n     /  /  /\n    /  /  /\n```",
    "heavy rain": "```\n      .--.\n   .-(    ).\n  (___.__)__)\n     /  /  /\n    /  /  /\n   /  /  /\n```",
    "light snow": "```\n      .--.\n   .-(    ).\n  (___.__)__)\n     *  *  *\n```",
    "snow": "```\n      .--.\n   .-(    ).\n  (___.__)__)\n     * * * *\n```",
    "heavy snow": "```\n      .--.\n   .-(    ).\n  (___.__)__)\n    * * * *\n   * * * *\n```",
    "light freezing rain": "```\n      .--.\n   .-(    ).\n  (___.__)__)\n     ❄️\n```",
    "freezing rain": "```\n      .--.\n   .-(    ).\n  (___.__)__)\n     ❄️❄️❄️\n```",
    "heavy freezing rain": "```\n      .--.\n   .-(    ).\n  (___.__)__)\n     ❄️❄️❄️\n    ❄️❄️❄️\n```",
    "thunderstorm": "```\n      .--.\n   .-(    ).\n  (___.__)__)\n     ⚡⚡⚡\n    /  /  /\n```",
    "fog": "```\n      .--.\n   .-(    ).\n  (___.__)__)\n     🌫️🌫️🌫️\n```",
    "mist": "```\n      .--.\n   .-(    ).\n  (___.__)__)\n     🌫️ ☁️\n```",
    "haze": "```\n      .--.\n   .-(    ).\n  (___.__)__)\n     🌫️☀️\n```",
    "gale": "```\n      .--.\n   .-(    ).\n  (___.__)__)\n     💨💨💨\n```",
    "blizzard": "```\n      .--.\n   .-(    ).\n  (___.__)__)\n    ❄️💨❄️\n   ❄️  ❄️\n```",
    "drizzle": "```\n      .--.\n   .-(    ).\n  (___.__)__)\n     .  .  .\n```",
    "hurricane": "```\n      .--.\n   .-(    ).\n  (___.__)__)\n     🌀🌀🌀\n    /  /  /\n```",
    "tropical storm": "```\n      .--.\n   .-(    ).\n  (___.__)__)\n     🌊🌀🌊\n```",
    "dust storm": "```\n   ~~~~\n  ~~~~~~\n  ~~~~~~\n   ~~~~\n    🌪️\n```",
    "tornado": "```\n    ╭╮\n   ╭╯╰╮\n   ╰╮╭╯\n    ╰╯\n   🌪️🌪️\n```",
    "ice fog": "```\n   .-.-.\n  (  🌫️ )\n   `-'-'\n```",
    "squall": "```\n   ⛈️💨\n  /  /  /\n /  /  /\n```",
    "heat burst": "```\n   🔥🔥🔥\n  🔥  🔥\n   🔥🔥🔥\n```",
    "downburst": "```\n    ↓↓↓\n   ↓↓↓↓\n  ↓↓↓↓↓\n```",
    "polar low": "```\n   ❄️🌀❄️\n  ❄️  ❄️\n   ❄️🌀❄️\n```",
    "aurora": "```\n    ✨  ✨\n  ✨    ✨\n ✨  ✨  ✨\n   🌌\n```",
    "rainbow": "```\n     🌈\n   🌈   🌈\n 🌈     🌈\n```",
    "sun dog": "```\n   ☀️  ✨\n  ✨  ☀️  ✨\n   ☀️  ✨\n```",
    "halo": "```\n     ⭕\n    ☀️⭕\n     ⭕\n```",
}

# ----------------------------------------------------------------------
# Weather smoothing (small memory)
# ----------------------------------------------------------------------
_weather_memory: Dict[int, str] = {}

def _smooth_condition(raw_condition: str, game_minutes: int) -> str:
    global _weather_memory
    prev = _weather_memory.get(game_minutes - 1)

    if not prev:
        _weather_memory[game_minutes] = raw_condition
        if len(_weather_memory) > 5:
            oldest = min(_weather_memory.keys())
            del _weather_memory[oldest]
        return raw_condition

    # Simple transition rules
    if "heavy" in raw_condition and "light" not in prev and "clear" in prev:
        raw_condition = raw_condition.replace("heavy", "light")
    if "rain" in raw_condition and "rain" not in prev and "heavy" not in prev:
        if "heavy" in raw_condition:
            raw_condition = raw_condition.replace("heavy", "light")
        elif raw_condition == "rain":
            raw_condition = "light rain"
    if "light rain" in prev and raw_condition == "clear":
        raw_condition = "partly cloudy"

    _weather_memory[game_minutes] = raw_condition
    if len(_weather_memory) > 5:
        oldest = min(_weather_memory.keys())
        del _weather_memory[oldest]
    return raw_condition

# ----------------------------------------------------------------------
# Main weather generation function (internal)
# ----------------------------------------------------------------------
def _generate_weather(
    game_minutes: int,
    params: dict,
    latitude: float,
    longitude: float,
    elevation: float,
    allow_all_disasters: bool
) -> "WeatherData":
    """Core deterministic weather generator."""
    # Time components
    minute_of_day = game_minutes % MINUTES_PER_DAY
    day_of_year = (game_minutes // MINUTES_PER_DAY) % DAYS_PER_YEAR
    year = game_minutes // MINUTES_PER_YEAR
    hour = minute_of_day // 60
    minute = minute_of_day % 60
    t_year = day_of_year / DAYS_PER_YEAR
    t_day = minute_of_day / MINUTES_PER_DAY

    # Elevation lapse rate (standard -6.5°C per km)
    elev_factor = (elevation / 1000.0) * 6.5

    # --- Temperature ---
    annual_temp = params["temp_annual_mean"] + params["temp_annual_amplitude"] * math.sin(2 * math.pi * t_year - math.pi / 2)
    daily_phase = 2 * math.pi * (t_day - 14 / 24)
    daily_temp = params["temp_daily_amplitude"] * math.cos(daily_phase)
    noise_seed = game_minutes * 1000
    noise = _deterministic_random(noise_seed, -1.0, 1.0) * 1.5
    temperature = annual_temp + daily_temp + noise - elev_factor

    # --- Pressure ---
    pressure_annual = params["pressure_annual_amplitude"] * math.sin(2 * math.pi * t_year + 0.2)
    pressure_daily = params["pressure_daily_amplitude"] * math.cos(2 * math.pi * t_day - 0.5)
    pressure_noise = _deterministic_random(noise_seed + 1, -2.0, 2.0)
    pressure = params["pressure_mean"] + pressure_annual + pressure_daily + pressure_noise

    # --- Humidity ---
    humidity_base = params["humidity_base"] - 0.2 * (temperature - params["temp_annual_mean"])
    humidity_base = max(30.0, min(95.0, humidity_base))
    pressure_anomaly = pressure - params["pressure_mean"]
    humidity = humidity_base - 0.1 * pressure_anomaly
    humidity = max(20.0, min(100.0, humidity))

    # --- Dew point ---
    dew_point = _calculate_dew_point(temperature, humidity)

    # --- Wind ---
    wind_dir = _smooth_wind_direction(game_minutes)
    wind_speed_base = params["wind_base"] + 2.0 * math.sin(2 * math.pi * t_year) + 0.5 * math.cos(2 * math.pi * t_day)
    wind_gust = _deterministic_random(noise_seed + 2, -1.0, 1.0) * 2.0
    wind_speed = max(0, wind_speed_base + wind_gust)
    wind_cardinal = _degrees_to_cardinal(wind_dir)

    # --- Instability ---
    instability = _calculate_instability(game_minutes, params)

    # --- Precipitation probability ---
    precip_prob = (humidity - 50) / 50 * 0.8 + (params["pressure_mean"] - pressure) / 20 * 0.2
    precip_prob = max(0, min(1, precip_prob))

    # --- Apparent temperature ---
    feels_like = _calculate_apparent_temperature(temperature, humidity, wind_speed)

    # --- Day/night flag (simple) ---
    is_day = 6 <= hour < 18

    # --- Condition determination (priority order) ---
    allowed = params["disasters_allowed"] if not allow_all_disasters else ALL_DISASTERS

    # Start with a default condition
    condition = "clear"

    # 0. Hurricane / Tropical Storm
    if (temperature > params["hurricane_temp_min"] and pressure < params["hurricane_pressure_max"] and
        wind_speed > params["hurricane_wind_min"] and humidity > params["hurricane_humidity_min"]):
        if "hurricane" in allowed:
            condition = "hurricane"
    elif (temperature > params["storm_temp_min"] and pressure < params["storm_pressure_max"] and
          wind_speed > params["storm_wind_min"] and humidity > params["storm_humidity_min"]):
        if "tropical storm" in allowed:
            condition = "tropical storm"
    # 1. Gale
    elif wind_speed > 15.0 and "gale" in allowed:
        condition = "gale"
    # 2. Dust storm (if allowed)
    elif humidity < 30 and wind_speed > 12 and "dust storm" in allowed:
        condition = "dust storm"
    # 3. Tornado (extreme)
    elif instability > 2000 and wind_speed > 15 and temperature > 15 and "tornado" in allowed:
        condition = "tornado"
    # 4. Ice fog
    elif temperature < -15 and humidity > 85 and wind_speed < 2 and "ice fog" in allowed:
        condition = "ice fog"
    # 5. Squall
    elif precip_prob > 0.6 and wind_speed > 10 and "squall" in allowed:
        condition = "squall"
    # 6. Heat burst
    elif temperature > 35 and humidity < 20 and wind_speed > 8 and "heat burst" in allowed:
        condition = "heat burst"
    # 7. Polar low
    elif temperature < -10 and wind_speed > 20 and pressure < 980 and "polar low" in allowed:
        condition = "polar low"
    # 8. Fog / Mist / Haze
    elif (temperature - dew_point) < 2.0 and humidity > 95 and wind_speed < 2.0:
        condition = "fog"
    elif (temperature - dew_point) < 4.0 and humidity > 85 and wind_speed < 5.0:
        condition = "mist"
    elif pressure > 1020 and humidity < 40 and wind_speed < 2.0:
        condition = "haze"
    # 9. Thunderstorm / Blizzard
    elif precip_prob > 0.7:
        if instability > 800 and temperature > 15:
            if "thunderstorm" in allowed:
                condition = "thunderstorm"
            else:
                condition = "heavy rain"  # fallback
        elif temperature < -5 and wind_speed > 10:
            if "blizzard" in allowed:
                condition = "blizzard"
            else:
                condition = "heavy snow"
        else:
            if temperature < 0:
                base = "snow"
            elif temperature < 5:
                base = "freezing rain"
            else:
                base = "rain"
            intensity = _deterministic_random(noise_seed + 3, 0.5, 1.5)
            if intensity < 0.8:
                condition = "light " + base
            elif intensity > 1.2:
                condition = "heavy " + base
            else:
                condition = base
    # 10. Drizzle
    elif 0.3 < precip_prob < 0.5 and humidity > 80:
        condition = "drizzle"
    # 11. Regular sky cover
    elif precip_prob < 0.2:
        condition = "clear"
    elif precip_prob < 0.5:
        condition = "partly cloudy"
    elif precip_prob < 0.7:
        condition = "cloudy"
    else:
        # Fallback
        if temperature < 0:
            base = "snow"
        elif temperature < 5:
            base = "freezing rain"
        else:
            base = "rain"
        intensity = _deterministic_random(noise_seed + 3, 0.5, 1.5)
        if intensity < 0.8:
            condition = "light " + base
        elif intensity > 1.2:
            condition = "heavy " + base
        else:
            condition = base

    # --- Atmospheric phenomena (non‑hazardous, only when not severe) ---
    # Aurora (high latitudes, night, clear/partly cloudy)
    if (latitude > 55 or latitude < -55) and not is_day and condition in ["clear", "partly cloudy"]:
        if _deterministic_random(game_minutes * 7000, 0, 1) > 0.7:
            condition = "aurora"
    # Rainbow (after light rain, day) – avoid overwriting severe weather
    elif condition in ["light rain", "drizzle"] and is_day:
        if _deterministic_random(game_minutes * 8000, 0, 1) > 0.5:
            condition = "rainbow"
    # Sun dog (cold, high clouds, day)
    elif temperature < -5 and condition in ["partly cloudy", "cloudy"] and is_day:
        if _deterministic_random(game_minutes * 9000, 0, 1) > 0.6:
            condition = "sun dog"
    # Halo (thin clouds)
    elif condition in ["partly cloudy", "cloudy"] and 20 <= precip_prob*100 <= 60:
        if _deterministic_random(game_minutes * 10000, 0, 1) > 0.8:
            condition = "halo"

    # --- Downburst (special: only if thunderstorm and high wind) ---
    if condition == "thunderstorm" and wind_speed > 20 and "downburst" in allowed:
        condition = "downburst"

    # --- Apply smoothing ---
    condition = _smooth_condition(condition, game_minutes)

    cloud_cover = int(precip_prob * 100)

    # --- Moon phase and seasonal event ---
    moon_phase, moon_emoji = _get_moon_phase(day_of_year, year)
    season_event = _get_season_event(day_of_year)

    # --- Flavor text ---
    flavor = _get_flavor_text(condition, game_minutes * 5000)

    # --- ASCII art ---
    ascii_art = _ASCII_ART.get(condition, _ASCII_ART["clear"])

    # Build datetime string
    datetime_str = f"Year {year+1}, Day {day_of_year+1}, {hour:02d}:{minute:02d}"

    return WeatherData(
        game_minutes=game_minutes,
        datetime_str=datetime_str,
        temperature=round(temperature, 1),
        feels_like=feels_like,
        pressure=round(pressure, 1),
        humidity=round(humidity, 1),
        dew_point=round(dew_point, 1),
        wind_speed=round(wind_speed, 1),
        wind_direction=round(wind_dir, 0),
        wind_cardinal=wind_cardinal,
        condition=condition,
        cloud_cover=cloud_cover,
        precipitation_prob=round(precip_prob * 100, 1),
        instability=round(instability, 0),
        moon_phase=moon_phase,
        moon_emoji=moon_emoji,
        season_event=season_event,
        flavor=flavor,
        ascii_art=ascii_art,
    )

# ----------------------------------------------------------------------
# Public interface
# ----------------------------------------------------------------------
@dataclass
class WeatherData:
    """Complete weather report for a specific moment."""
    game_minutes: int
    datetime_str: str
    temperature: float
    feels_like: float
    pressure: float
    humidity: float
    dew_point: float
    wind_speed: float
    wind_direction: float
    wind_cardinal: str
    condition: str
    cloud_cover: int
    precipitation_prob: float
    instability: float
    moon_phase: str
    moon_emoji: str
    season_event: Optional[str]
    flavor: str
    ascii_art: str

def weather(
    game_minutes: Optional[int] = None,
    *,
    real_time: Optional[datetime] = None,
    real_time_scale: float = 1.0,
    latitude: float = 45.0,
    longitude: float = 0.0,
    elevation: float = 0.0,
    koppen: Optional[str] = None,
    allow_all_disasters: bool = False,
) -> WeatherData:
    """
    Generate deterministic weather for a given time and location.

    Args:
        game_minutes: Direct game minute count. If None, real_time is used.
        real_time: A datetime object (assumed UTC). If None and game_minutes is None,
                   uses current UTC time.
        real_time_scale: Number of game minutes per real minute. Default 1.0.
        latitude: Latitude in degrees (-90 to 90). Used for aurora and day length.
        longitude: Longitude (unused currently, reserved).
        elevation: Elevation in meters. Applies temperature lapse rate.
        koppen: Köppen climate code (e.g., "Dfb"). If None, uses default profile
                (all disasters possible).
        allow_all_disasters: If True, overrides the profile's disaster list to allow
                             every disaster type.

    Returns:
        WeatherData object with all weather fields.
    """
    # Resolve time to game minutes
    if game_minutes is not None:
        gm = game_minutes
    else:
        if real_time is None:
            real_time = datetime.now(timezone.utc)
        # Convert to UTC timestamp (seconds) then to game minutes
        gm = int(real_time.timestamp() * real_time_scale)

    # Choose profile
    if koppen is None:
        params = DEFAULT_PROFILE.copy()
    else:
        if koppen not in KOPPEN_PROFILES:
            raise ValueError(f"Unknown Köppen code: {koppen}")
        params = KOPPEN_PROFILES[koppen].copy()

    # If allow_all_disasters, override the allowed list
    if allow_all_disasters:
        params["disasters_allowed"] = ALL_DISASTERS

    return _generate_weather(gm, params, latitude, longitude, elevation, allow_all_disasters)

# ----------------------------------------------------------------------
# Optional: convenience function to list available Köppen codes
# ----------------------------------------------------------------------
def list_koppen_codes() -> List[str]:
    """Return a list of all defined Köppen codes."""
    return list(KOPPEN_PROFILES.keys())