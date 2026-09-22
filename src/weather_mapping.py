import pandas as pd
import numpy as np
from .config import TARGET_MINUTES, BPM

#Class takes cleaned weather data and converts it into musical values
class WeatherMapper():

    def __init__ (self, dataframe):
        self.dataframe = dataframe
        self.target_minutes = TARGET_MINUTES
        self.bpm = BPM

    # Map weather into music    
    def map(self):
        df = self.dataframe 

        # Define weather ranges
        ranges = {
            "temperature": (-5, 25),
            "rain": (0,10),
            "wind": (0,40),
            "humidity": (0,100),
            "pressure": (970, 1045)
        }

        # ----------------------------------------------------------------------------
        # Step 1: Normalise data
        # ----------------------------------------------------------------------------
        def normalise(series, low, high):
            # Conver values into a 0-1 range
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
        print(df[[c for c in df.columns if c.endswith("_norm")]].describe())


        # Musical scale using MIDI note number
        temperature_scale = np.array([60, 62, 64, 65, 67, 69, 71, 72])
        # Convert normalised temperature into a note index (a value between 0-1 to an index from 0-7)
        df["temperature_note_index"] = (
            df["temperature_norm"] * (len(temperature_scale) - 1)
        ).round().astype(int)
        # Get the actual MIDI note from index
        df["temperature_midi"] = temperature_scale[
            df["temperature_note_index"]
        ]

        humidity_scale = np.array([48, 50, 52, 53, 55, 57, 59, 60])
        df["humidity_note_index"] = (
            df["humidity_norm"] * (len(humidity_scale) - 1)
        ).round().astype(int)
        df["humidity_midi"] = humidity_scale[
            df["humidity_note_index"]
        ]

        wind_scale = np.array([36, 38, 40, 43, 45, 47, 50, 52])
        df["wind_note_index"] = (
            df["wind_norm"] * (len(wind_scale) - 1)
        ).round().astype(int)
        df["wind_midi"] = wind_scale[
            df["wind_note_index"]
        ]

        pressure_scale = np.array([36, 38, 40, 43, 45, 47, 50, 52])
        df["pressure_note_index"] = (
            df["pressure_norm"] * (len(pressure_scale) - 1)
        ).round().astype(int)
        df["pressure_midi"] = pressure_scale[
            df["pressure_note_index"]
        ]

        # Mapping rain to number of musical hits rather than a musical note
        df["rain_hits"] = (
            df["rain_norm"] * 2
        ).round().astype(int)

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
        print(f"{len(df)} hourly rows -> bucketing every {bucket_size} hours "
            f"-> ~{len(df) // bucket_size} notes -> "
            f"~{(len(df) // bucket_size) / self.bpm:.1f} min at {self.bpm} BPM")

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

        # Save final dataframe
        self.dataframe = df
        return df
    