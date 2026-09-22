import pandas as pd

from src.weather_mapping import WeatherMapper

def test_weather_mapping_creates_midi_columns():
    data = pd.DataFrame({
        "datetime": pd.to_datetime([
            "2026-01-01 10:00",
            "2026-01-01 11:00",
        ]),
        "temperature": [10.0, 15.0],
        "rain": [0.0, 5.0],
        "wind": [10.0, 20.0],
        "humidity": [50.0, 75.0],
        "pressure": [1000.0, 1020.0],
    })

    mapper = WeatherMapper(data)
    mapped = mapper.map()

    assert "temperature_midi" in mapped.columns
    assert "humidity_midi" in mapped.columns
    assert "wind_midi" in mapped.columns
    assert "pressure_midi" in mapped.columns
    assert "rain_hits" in mapped.columns


def test_weather_mapping_midi_values_are_valid():
    data = pd.DataFrame({
        "datetime": pd.to_datetime([
            "2026-01-01 10:00",
            "2026-01-01 11:00",
        ]),
        "temperature": [10.0, 15.0],
        "rain": [0.0, 5.0],
        "wind": [10.0, 20.0],
        "humidity": [50.0, 75.0],
        "pressure": [1000.0, 1020.0],
    })

    mapper = WeatherMapper(data)
    mapped = mapper.map()

    for column in [
        "temperature_midi",
        "humidity_midi",
        "wind_midi",
        "pressure_midi",
    ]:
        assert mapped[column].between(0, 127).all()

    assert mapped["rain_hits"].between(0, 4).all()


def test_weather_mapping_creates_midi_columns():
    data = pd.DataFrame({
        "datetime": pd.to_datetime([
                "2026-01-01 10:00",
                "2026-01-01 11:00",
                ]),
        "temperature": [10.0, 15.0],
        "rain": [0.0, 5.0],
        "wind": [10.0, 20.0],
        "humidity": [50.0, 75.0],
        "pressure": [1000.0, 1020.0],
    })

    mapper = WeatherMapper(data)
    mapped = mapper.map()

    assert "temperature_midi" in mapped.columns
    assert "humidity_midi" in mapped.columns
    assert "wind_midi" in mapped.columns
    assert "pressure_midi" in mapped.columns
    assert "rain_hits" in mapped.columns

def test_rain_is_mapped_to_rain_hits():
    data = pd.DataFrame({
        "datetime": pd.to_datetime([
            "2026-01-01 10:00",
            "2026-01-01 11:00",
        ]),
        "temperature": [10.0, 15.0],
        "rain": [0.0, 10.0],
        "wind": [10.0, 20.0],
        "humidity": [50.0, 75.0],
        "pressure": [1000.0, 1020.0],
    })

    mapper = WeatherMapper(data)
    mapped = mapper.map()

    assert mapped["rain_hits"].iloc[0] == 0
    assert mapped["rain_hits"].iloc[1] == 4