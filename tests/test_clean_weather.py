import pandas as pd

from src.clean_weather import WeatherCleaner

def test_clean_weather_keeps_required_columns():
    data = pd.DataFrame({
    "temp": [10.0, 100.0],
    "prcp": [None, 1.0],
    "wspd": [10.0, 12.0],
    "rhum": [70.0, 75.0],
    "pres": [1010.0, 1012.0],
    }, index=pd.to_datetime([
        "2026-01-01 10:00",
        "2026-01-01 11:00",
    ]))

    cleaner = WeatherCleaner(data)
    cleaned = cleaner.clean()

    assert list(cleaned.columns) == [
        "index",
        "temperature",
        "rain",
        "wind",
        "humidity",
        "pressure",
    ]

def test_clean_weather_fills_rain_nan_with_zero():
    data = pd.DataFrame({
    "temp": [10.0, 100.0],
    "prcp": [None, 1.0],
    "wspd": [10.0, 12.0],
    "rhum": [70.0, 75.0],
    "pres": [1010.0, 1012.0],
    }, index=pd.to_datetime([
        "2026-01-01 10:00",
        "2026-01-01 11:00",
    ]))

    cleaner = WeatherCleaner(data)
    cleaned = cleaner.clean()

    assert cleaned["rain"].iloc[0] == 0

def test_clean_weather_handles_out_of_range_values():
    data = pd.DataFrame({
    "temp": [10.0, 100.0],
    "prcp": [None, 1.0],
    "wspd": [10.0, 12.0],
    "rhum": [70.0, 75.0],
    "pres": [1010.0, 1012.0],
    }, index=pd.to_datetime([
        "2026-01-01 10:00",
        "2026-01-01 11:00",
    ]))

    cleaner = WeatherCleaner(data)
    cleaned = cleaner.clean()

    assert cleaned["temperature"].max() <= 40