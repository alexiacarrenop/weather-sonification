import logging
import meteostat as ms

class WeatherFetcher:
    logger = logging.getLogger(__name__)

    def __init__(self, station_id, start, end):
        self.station_id = station_id
        self.start = start
        self.end = end

    def fetch(self):
        self.logger.info("Fetching weather data from Meteostat")
        station = ms.Station(id=self.station_id)

        try:
            data = ms.hourly(
                station,
                self.start,
                self.end,
                timezone="Europe/London"
            ).fetch()
        except Exception as e:
            self.logger.error("Failed to retrieve weather data from Meteostat")
            raise RuntimeError(f"Failed to retrieve weather data from Meteostat: {e}")

        if data.empty:
            self.logger.warning("Meteostat returned no weather data")
            raise ValueError("Meteostat returned no weather data for the requested period.")

        return data
        
        
        