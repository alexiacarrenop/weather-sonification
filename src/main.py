import sys
import pandas as pd
import numpy as np
from datetime import datetime 
from get_weather import WeatherFetcher
from clean_weather import WeatherCleaner
from weather_mapping import WeatherMapper
from sonification import SonificationEngine

def main():
    fetcher = WeatherFetcher(
        station_id="03245",
        start=datetime(2025, 9, 29),
        end=datetime(2026, 6, 15, 23, 59)
    )

    df = fetcher.fetch()

    cleaner = WeatherCleaner(df)
    cleaned_df = cleaner.clean()

    mapper = WeatherMapper(cleaned_df)
    mapped_df = mapper.map()

    engine = SonificationEngine(mapped_df)
    midi = engine.generate()

    midi.save("newcastle_weather.mid")
    
    # clean_weather_file()
    # weather_mapping()
    # create_midi()

if __name__ == '__main__':
    main()