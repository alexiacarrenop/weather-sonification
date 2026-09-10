import pandas as pd
import numpy as np
from config import TARGET_MINUTES, BPM

df = pd.read_csv("ncl_weather_clean.csv", parse_dates=["datetime"])

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
    norm = (series - low) / (high - low)
    return norm.clip(0, 1) # clip in case data exceeds chosen range

# Go through each column normalising it and creating a new normalised column for each df.columns
for col, (low, high) in ranges.items():
    if col in df.columns:
        df[f"{col}_norm"] = normalise(df[col], low, high)

df["rain_norm"] = normalise(np.sqrt(df["rain"]), 0, np.sqrt(10))

print(df[[c for c in df.columns if c.endswith("_norm")]].describe())

# df.to_csv("ncl_weather_normalised.csv", index=False)

# Musical scale using MIDI note number
temperature_scale = np.array([60, 62, 64, 65, 67, 69, 71, 72])

# Convert normalised temperature into a note index
df["temperature_note_index"] = (
    df["temperature_norm"] * (len(temperature_scale) - 1)
).round().astype(int)

# Get the actual MIDI note
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

df["rain_hits"] = (
    df["rain_norm"] * 4
).round().astype(int)

# ----------------------------------------------------------------------------
# Step 2: Compress data
#
#  Hourly data get averaged, which
# compresses time and smooths noise.
# ----------------------------------------------------------------------------

required_cols = [
    "temperature_midi", "humidity_midi", "wind_midi", "wind_norm",
    "pressure_midi", "rain_hits"
]

df = df.sort_values("datetime").reset_index(drop=True)
df = df.dropna(subset=required_cols).reset_index(drop=True)

target_beats = round(TARGET_MINUTES * BPM)
bucket_size = max(1, len(df) // target_beats)

print(f"{len(df)} hourly rows -> bucketing every {bucket_size} hours "
      f"-> ~{len(df) // bucket_size} notes -> "
      f"~{(len(df) // bucket_size) / BPM:.1f} min at {BPM} BPM")

df["bucket"] = np.arange(len(df)) // bucket_size

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

df.to_csv("ncl_weather_mapped.csv", index=False)