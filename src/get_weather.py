import logging
import meteostat as ms
from abc import abstractmethod
from base import PipelineStage

class WeatherSource(PipelineStage):
    # Every class that inherits from weather source must implement it's own way to fetch.
    @abstractmethod
    def fetch(self):
        """Retrieve weather data"""

    def run(self, data=None):
        df = self.fetch()
        if df.empty:
            self.logger.warning("Source returned no weather data")
            raise ValueError("No weather data for the requested period.")
        return df

class MeteostatSource(WeatherSource):
    def __init__(self, station_id, start, end):
        # Initialise the parent PipelineStage
        super().__init__()
        
        self.station_id = station_id
        self.start = start
        self.end = end

    def fetch(self):
        self.logger.info("Fetching weather data from Meteostat")
        station = ms.Station(id=self.station_id)
    
        try:
            return ms.hourly(
                station,
                self.start,
                self.end,
                timezone="Europe/London"
                ).fetch()
        except Exception as e:
            self.logger.error("Failed to retrieve weather data from Meteostat")
            raise RuntimeError(f"Failed to retrieve weather data from Meteostat: {e}") from e
