import sys
import pandas as pd
import numpy as np
from datetime import datetime 
from WeatherFetcher import WeatherFetcher
from WeatherCleaner import WeatherCleaner
from weather_mapping import weather_mapping
from create_midi import create_midi

def main():
    fetcher = WeatherFetcher(
        station_id="03245",
        start=datetime(2025, 9, 29),
        end=datetime(2026, 6, 15, 23, 59)
    )
    df = fetcher.fetch()

    cleaner = WeatherCleaner(df)
    cleaned_df = cleaner.clean()
    
    
    # clean_weather_file()
    # weather_mapping()
    # create_midi()

if __name__ == '__main__':
    main()