import sys
import pandas as pd
import numpy as np
from get_weather import get_weather
from clean_weather_file import clean_weather_file
from weather_mapping import weather_mapping
from create_midi import create_midi

def main():
    get_weather()
    clean_weather_file()
    weather_mapping()
    create_midi()

if __name__ == '__main__':
    main()