# Library Top Level Folder
"""
LibTest.py – Interactive test harness for the weather library.

This script exercises all public functions of the weather library,
including the new WeatherArchive for persistent, smooth weather trends.
"""

import json
import sys
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Try/Except for weather library imports
# ----------------------------------------------------------------------
try:
    from weather.weather import (
        weather,
        WeatherData,
        list_koppen_codes,
        WeatherArchive,
    )
except ImportError:
    print("❌ Error: `weather` not found. Please ensure weather.py is in the same directory.")
    sys.exit(1)

# ----------------------------------------------------------------------
# Global test objects
# ----------------------------------------------------------------------
# A single archive instance for all trend tests
archive = WeatherArchive("test_weather.db")

# We'll store created trend IDs for later use
trend_ids = []

# ----------------------------------------------------------------------
# Helper: pretty print WeatherData
# ----------------------------------------------------------------------
def print_weather(w: WeatherData):
    print(f"\n--- Weather at game minute {w.game_minutes} ---")
    print(f"Datetime: {w.datetime_str}")
    print(f"Condition: {w.condition}")
    print(f"Temperature: {w.temperature}°C (feels like {w.feels_like}°C)")
    print(f"Pressure: {w.pressure} hPa")
    print(f"Humidity: {w.humidity}%")
    print(f"Dew Point: {w.dew_point}°C")
    print(f"Wind: {w.wind_speed} m/s from {w.wind_cardinal} ({w.wind_direction}°)")
    print(f"Cloud cover: {w.cloud_cover}%")
    print(f"Precip prob: {w.precipitation_prob}%")
    print(f"Instability: {w.instability}")
    print(f"Moon: {w.moon_phase} {w.moon_emoji}")
    if w.season_event:
        print(f"Season event: {w.season_event}")
    print(f"Flavor: {w.flavor}")
    print("ASCII art:")
    print(w.ascii_art)

# ----------------------------------------------------------------------
# Simulation functions (each corresponds to a menu option)
# ----------------------------------------------------------------------
def test_basic_weather():
    """Generate weather with current time (default parameters)."""
    print("\n--- Basic weather() call (current UTC) ---")
    w = weather()
    print_weather(w)

def test_game_minutes():
    """Generate weather with explicit game minutes."""
    try:
        gm = int(input("Enter game minutes: "))
    except ValueError:
        print("Invalid input, using 0")
        gm = 0
    w = weather(game_minutes=gm)
    print_weather(w)

def test_real_time():
    """Generate weather with a real datetime."""
    dt_str = input("Enter datetime (YYYY-MM-DD HH:MM) or leave empty for now: ").strip()
    if dt_str:
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        except ValueError:
            print("Invalid format, using current time")
            dt = datetime.now()
    else:
        dt = datetime.now()
    scale = input("Time scale (game minutes per real minute, default 1): ").strip()
    scale = float(scale) if scale else 1.0
    w = weather(real_time=dt, real_time_scale=scale)
    print_weather(w)

def test_koppen_codes():
    """List all available Köppen codes."""
    codes = list_koppen_codes()
    print("\n--- Available Köppen codes ---")
    for code in codes:
        print(f"  {code}")

def test_custom_location():
    """Weather with custom latitude/longitude/elevation."""
    lat = float(input("Latitude (-90..90): ") or "45.0")
    lon = float(input("Longitude: ") or "0.0")
    elev = float(input("Elevation (m): ") or "0.0")
    koppen = input("Köppen code (optional): ") or None
    allow_all = input("Allow all disasters? (y/n): ").lower() == 'y'
    gm = int(input("Game minutes (default 0): ") or "0")
    w = weather(
        game_minutes=gm,
        latitude=lat,
        longitude=lon,
        elevation=elev,
        koppen=koppen,
        allow_all_disasters=allow_all
    )
    print_weather(w)

def test_smoothing():
    """Request several consecutive minutes to see smoothing in action."""
    start = int(input("Start minute: ") or "1000")
    count = int(input("How many consecutive minutes: ") or "5")
    print(f"\n--- Smoothing test from minute {start} to {start+count-1} ---")
    for gm in range(start, start + count):
        w = weather(game_minutes=gm)
        print(f"{gm}: {w.condition}")

def test_trend_id():
    """Generate weather with a trend ID (isolated memory)."""
    tid = input("Trend ID (any string/integer): ") or "test1"
    gm = int(input("Game minutes: ") or "0")
    w = weather(game_minutes=gm, trend_id=tid)
    print_weather(w)

# ----------------------------------------------------------------------
# Archive-related tests
# ----------------------------------------------------------------------
def archive_add_trend():
    """Add a new trend to the archive."""
    name = input("Trend name: ") or "Test Trend"
    lat = float(input("Latitude: ") or "45.0")
    lon = float(input("Longitude: ") or "0.0")
    elev = float(input("Elevation (m): ") or "0.0")
    koppen = input("Köppen code (optional): ") or None
    allow_all = input("Allow all disasters? (y/n): ").lower() == 'y'
    tid = archive.add_trend(name, lat, lon, elev, koppen, allow_all)
    trend_ids.append(tid)
    print(f"✅ Trend added with ID: {tid}")

def archive_list_trends():
    """List all trends in the archive."""
    trends = archive.list_trends()
    if not trends:
        print("No trends found.")
        return
    print("\n--- Trends in archive ---")
    for t in trends:
        print(f"ID {t['id']}: {t['name']} (lat={t['latitude']}, lon={t['longitude']}, "
              f"elev={t['elevation']}, koppen={t['koppen']}, last_checkpoint={t['last_checkpoint']})")

def archive_get_weather():
    """Retrieve weather for a trend using the archive (ensures smoothing)."""
    if not trend_ids:
        print("No trends available. Add one first (option 10).")
        return
    print("Available trend IDs:", trend_ids)
    try:
        tid = int(input("Trend ID: "))
    except ValueError:
        print("Invalid ID.")
        return
    target = int(input("Target game minute: ") or "0")
    read_only = input("Read‑only? (y/n): ").lower() == 'y'
    force = input("Force generate (ignore checkpoints)? (y/n): ").lower() == 'y'
    try:
        w = archive.get_weather(tid, target, read_only=read_only, force_generate=force)
        print_weather(w)
    except Exception as e:
        print(f"❌ Error: {e}")

def archive_test_smoothing():
    """Request consecutive minutes from archive to verify smoothing."""
    if not trend_ids:
        print("No trends available. Add one first (option 10).")
        return
    print("Available trend IDs:", trend_ids)
    try:
        tid = int(input("Trend ID: "))
    except ValueError:
        print("Invalid ID.")
        return
    start = int(input("Start minute: ") or "1000")
    count = int(input("How many consecutive minutes: ") or "5")
    print(f"\n--- Archive smoothing test from minute {start} to {start+count-1} ---")
    for gm in range(start, start + count):
        w = archive.get_weather(tid, gm, read_only=True)   # read‑only to avoid extra checkpoints
        print(f"{gm}: {w.condition}")

def archive_delete_all():
    """DANGER: delete all trends and checkpoints (for cleanup)."""
    confirm = input("This will DELETE ALL trends and checkpoints. Type 'YES' to confirm: ")
    if confirm == "YES":
        # Quick and dirty: remove the database file
        import os
        try:
            os.remove(archive.db_path)
            print(f"Removed {archive.db_path}. Reinitializing...")
            archive._init_db()
            trend_ids.clear()
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Cancelled.")

def archive_forecast_fast():
    """Retrieve archive weather using fast-forward for speed (exact=False)."""
    if not trend_ids:
        print("No trends available. Add one first (option 10).")
        return
    print("Available trend IDs:", trend_ids)
    try:
        tid = int(input("Trend ID: "))
    except ValueError:
        print("Invalid ID.")
        return
    target = int(input("Target game minute: ") or "0")
    w = archive.get_weather(tid, target, exact=False)
    print_weather(w)


def archive_forecast_custom_step():
    """Fast-forward with a user-chosen step size."""
    if not trend_ids:
        print("No trends available. Add one first (option 10).")
        return
    print("Available trend IDs:", trend_ids)
    try:
        tid = int(input("Trend ID: "))
    except ValueError:
        print("Invalid ID.")
        return
    target = int(input("Target game minute: ") or "0")
    step = int(input(f"Fast-forward step in minutes (default {archive.checkpoint_interval}): ")
               or str(archive.checkpoint_interval))
    w = archive.get_weather(tid, target, exact=False, fast_forward_step=step)
    print_weather(w)


# ----------------------------------------------------------------------
# Menu
# ----------------------------------------------------------------------
def print_menu():
    print("\n" + "="*50)
    print("WEATHER LIBRARY TEST HARNESS")
    print("="*50)
    print(" 1: Basic weather() (current time)")
    print(" 2: weather() with game minutes")
    print(" 3: weather() with real time & scale")
    print(" 4: List Köppen codes")
    print(" 5: Custom location / climate")
    print(" 6: Smoothing test (consecutive minutes)")
    print(" 7: weather() with trend_id (isolated memory)")
    print("\n--- WeatherArchive Tests ---")
    print("10: Add a new trend")
    print("11: List all trends")
    print("12: Get weather from archive (with smoothing)")
    print("13: Archive smoothing test (consecutive minutes)")
    print("14: Archive fast-forward forecast (exact=False)")
    print("15: Archive fast-forward with custom step")
    print("99: DANGER: Delete archive database")
    print(" 0: Exit")
    print("-"*50)

def main():
    print("Welcome to the Weather Library Test Harness")
    print("Some tests use the global archive at 'test_weather.db'.\n")

    while True:
        print_menu()
        choice = input("Enter your choice: ").strip()

        try:
            if choice == '1':
                test_basic_weather()
            elif choice == '2':
                test_game_minutes()
            elif choice == '3':
                test_real_time()
            elif choice == '4':
                test_koppen_codes()
            elif choice == '5':
                test_custom_location()
            elif choice == '6':
                test_smoothing()
            elif choice == '7':
                test_trend_id()
            elif choice == '10':
                archive_add_trend()
            elif choice == '11':
                archive_list_trends()
            elif choice == '12':
                archive_get_weather()
            elif choice == '13':
                archive_test_smoothing()
            elif choice == '14':
                archive_forecast_fast()
            elif choice == '15':
                archive_forecast_custom_step()
            elif choice == '99':
                archive_delete_all()
            elif choice == '0':
                print("Goodbye!")
                break
            else:
                print("Invalid choice.")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()