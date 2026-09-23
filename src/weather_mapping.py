import logging
import pandas as pd
import numpy as np
# from .config import TARGET_MINUTES, BPM

#Class takes cleaned weather data and converts it into musical values
class WeatherMapper():
    logger = logging.getLogger(__name__)

    def __init__ (self, dataframe):
        self.dataframe = dataframe
        # self.target_minutes = TARGET_MINUTES
        # self.bpm = BPM

    # Map weather into music    
    def map(self):
        self.logger.info("Starting weather-to-music mapping")
        df = self.dataframe 

        # Define weather ranges
        ranges = {
            "temperature": (-5, 25),
            "rain": (0,10),
            "wind": (0,40),
            "humidity": (0,100),
            "pressure": (970, 1045)
        }

        # ----------------------------------------------------------------------------------------------------
        # Step 1: Normalise data: convert each weather value into a 0-1 scale to map units to musical values
        # ----------------------------------------------------------------------------------------------------
        def normalise(series, low, high):
            # Convert values into a 0-1 range
            norm = (series - low) / (high - low)
            return norm.clip(0, 1) # clip in case data exceeds chosen range

        # Go through each column normalising it and creating a new normalised column for each df.columns
        for col, (low, high) in ranges.items():
            # Checks if column exists and normalises it + creates a new column
            if col in df.columns:
                df[f"{col}_norm"] = normalise(df[col], low, high)

        # Takes square root of rain to define the rain rythm
        df["rain_norm"] = normalise(np.sqrt(df["rain"]), 0, np.sqrt(10))

        # Print stats for all normalised columns
        self.logger.debug(
            "Normalised weather statistics:\n%s",
            df[[c for c in df.columns if c.endswith("_norm")]].describe()
        )


        # Musical scale using MIDI note number
        temperature_scale = np.array([60, 62, 64, 67, 69, 72, 74, 76]) # C4–E5, wide range for melodic movement
        # Convert normalised temperature into a note index (a value between 0-1 to an index from 0-7)
        df["temperature_note_index"] = (
            df["temperature_norm"] * (len(temperature_scale) - 1)
        ).round().astype(int)
        # Get the actual MIDI note from index
        df["temperature_midi"] = temperature_scale[
            df["temperature_note_index"]
        ]

        humidity_scale = np.array([48, 50, 52, 55, 57, 60, 62, 64]) # C3–E4
        df["humidity_note_index"] = (
            df["humidity_norm"] * (len(humidity_scale) - 1)
        ).round().astype(int)
        df["humidity_midi"] = humidity_scale[
            df["humidity_note_index"]
        ]

        wind_scale = np.array([43, 45, 48, 50, 52, 55, 57, 60]) # G2–C4
        df["wind_note_index"] = (
            df["wind_norm"] * (len(wind_scale) - 1)
        ).round().astype(int)
        df["wind_midi"] = wind_scale[
            df["wind_note_index"]
        ]

        pressure_scale = np.array([24, 26, 29, 31, 33, 36, 38, 41]) # C1–F2
        df["pressure_note_index"] = (
            df["pressure_norm"] * (len(pressure_scale) - 1)
        ).round().astype(int)
        df["pressure_midi"] = pressure_scale[
            df["pressure_note_index"]
        ]

        # Mapping rain to number of musical hits rather than a musical note
        df["rain_hits"] = (
            df["rain_norm"] * 4
        ).round().astype(int)

        '''
        # ----------------------------------------------------------------------------
        # Step 2: Compress data
        #
        #  Hourly data gets averaged, which
        # compresses time and smooths noise.
        # ----------------------------------------------------------------------------

        required_cols = [
            "temperature_midi", "humidity_midi", "wind_midi", "wind_norm",
            "pressure_midi", "rain_hits"
        ]

        df = df.sort_values("datetime").reset_index(drop=True) # Sort by time
        df = df.dropna(subset=required_cols).reset_index(drop=True) # remove missing data

        target_beats = round(self.target_minutes * self.bpm) # calculates how many beats final piece should have
        bucket_size = max(1, len(df) // target_beats) # calculates bucket size (number of hours that get compressedd) for each musical event

        # Print info
        self.logger.info(
            "%d hourly rows -> bucketing every %d hours -> ~%d notes -> ~%.1f min at %d BPM",
            len(df),
            bucket_size,
            len(df) // bucket_size,
            (len(df) // bucket_size) / self.bpm,
            self.bpm
        )
        # Create the buckets
        df["bucket"] = np.arange(len(df)) // bucket_size
        # Group data and calculate average or sum
        df = (
            df.groupby("bucket")
            .agg({
                "temperature_midi": "mean",
                "humidity_midi": "mean",
                "wind_midi": "mean",
                "wind_norm": "max",     
                "pressure_midi": "mean",
                "rain_hits": "sum",    
            })
            .reset_index(drop=True)
        )
        '''

        # Save final dataframe
        self.dataframe = df

        self.logger.info(
            "Weather-to-music mapping complete: %d musical events generated",
            len(df)
        )
        return df
    