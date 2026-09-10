from datetime import datetime 
import meteostat as ms

def get_weather():

    print("Meteostat works!")

    # Newcastle
    station = ms.Station(id="03245")

    # Time frame
    start = datetime(2025, 9, 29)
    end = datetime(2026, 6, 15, 23, 59)

    # Get hourly weather 
    data = ms.hourly(
        station,
        start,
        end,
        timezone="Europe/London"
    )

    df = data.fetch()

    print(df)

    df.to_csv("ncl_weather.csv")