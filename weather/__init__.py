"""
Weather - Deterministic weather generation
Licensed under BSD 3-Clause
Copyright (c) 2026 Imran Bin Gifary (System Delta)
"""

__version__ = "0.0.1dev2"
__author__ = "Imran Bin Gifary (System Delta)"
__license__ = "BSD-3-Clause"

from .weather import weather, WeatherData, list_koppen_codes, WeatherArchive

__all__ = ["weather", "WeatherData", "list_koppen_codes"]
