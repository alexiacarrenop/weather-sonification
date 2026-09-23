import meteostat as ms

class WeatherFetcher:

    # Newcastle
    # station_id = ms.Station(id="03245")
    
    # Time frame
    # start = datetime(2025, 9, 29)
    # end = datetime(2026, 6, 15, 23, 59)

    def __init__(self, station_id, start, end):
        self.station_id = station_id
        self.start = start
        self.end = end

    def fetch(self):
        station = ms.Station(id=self.station_id)

        try:
            data = ms.hourly(
                station,
                self.start,
                self.end,
                timezone="Europe/London"
            ).fetch()
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve weather data from Meteostat: {e}")

        if data.empty:
            raise ValueError("Meteostat returned no weather data for the requested period.")

        return data
        
        
        