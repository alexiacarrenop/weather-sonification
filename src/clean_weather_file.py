import pandas as pd
import numpy as np

def clean_weather_file():

    # Get the CSV
    df = pd.read_csv("ncl_weather.csv", index_col="time", parse_dates=True)
    df.index = pd.to_datetime(df.index, utc=True).tz_convert("Europe/London").tz_localize(None)

    # Select only variables needed
    df = df[["temp", "prcp", "wspd", "rhum", "pres"]].copy()
    df.columns = ["temperature", "rain", "wind", "humidity", "pressure"]

    # Sort chronologically (Meteostat usually does this, but just in case.)
    df = df.sort_index()

    # Handle 'no rain' values (NaN) by filling the NaNs with 0s - rather than 'unknown'.
    df["rain"] = df["rain"].fillna(0)

    # Treat genuine missing data with interpolation instead of zero, with a limit of 6 hours with no data
    for col in ["temperature", "wind", "humidity", "pressure"]:
        df[col] = df[col].interpolate(method="time", limit=6)

    # If gap is bigger than 6 hours = gap is too large to interpolate. Drop rows with missing data instead.
    before = len(df)
    df = df.dropna(subset=["temperature", "wind", "humidity"])
    print(f"Dropped {before - len(df)} rows with unfillable gaps")

    # Check for strange values. Anything outside these ranges is unusual for a UK coastal city and almost certainly a reporting error, not the actual weather.
    checks = {"temperature": (-15, 40),
            "rain": (0, 100),
            "wind": (0, 150),
            "humidity": (0, 100),
    }

    for col, (low, high) in checks.items():
        mask = ~df[col]. between(low, high)
        n_bad = mask.sum()
        if n_bad:
            print(f"{col}: {n_bad} out-of-range values found, flagging as NaN")
            df.loc[mask, col] = np.nan

    # Interpolate values we just flagged as errors
    df[["temperature", "wind", "humidity", "pressure"]] = df[["temperature", "wind", "humidity", "pressure"]].interpolate(method="time")
    df["rain"] = df["rain"].fillna(0) # reapply rain rule

    # Final tidy-up
    df = df.reset_index().rename(columns={"time": "datetime"}) # turn time back into a column (i made it an index at the start) and rename it to 'datetime'

    print(df.head()) # first 5 rows to check that data looks correct
    print(df.describe()) # useful statistics

    df.to_csv("ncl_weather_clean.csv", index=False)