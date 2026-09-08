import pandas as pd
import numpy as np



df = pd.read_csv("ncl_weather_clean.csv", parse_dates=["datetime"])

ranges = {
    "temperature": (-5, 25),
    "rain": (0,10),
    "wind": (0,40),
    "humidity": (0,100),
    "pressure": (970, 1045)
}

def normalise(series, low, high):
    norm = (series - low) / (high - low)
    return norm.clip(0, 1) # clip in case data exceeds chosen range

# Go through each column normalising it and creating a new normalised column for each df.columns
for col, (low, high) in ranges.items():
    if col in df.columns:
        df[f"{col}_norm"] = normalise(df[col], low, high)

df["rain_norm"] = normalise(np.sqrt(df["rain"]), 0, np.sqrt(10))

print(df[[c for c in df.columns if c.endswith("_norm")]].describe())

df.to_csv("ncl_weather_normalised.csv", index=False)