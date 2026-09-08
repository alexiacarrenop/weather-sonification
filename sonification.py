import pandas as pd
import numpy as np

df = pd.read_csv("ncl_weather_normalised.csv")

# ---------------------------
# Step 1: load weather data
# ---------------------------

# Convert datetime column to Pandas datetime
df["datetime"] = pd.to_datetime(df["datetime"])

print(df.head())
print(df.dtypes)
print("Number of rows and columns: ", df.shape)

# ----------------------------
# Step 2: check the timeline
# ----------------------------

# Check first and last observation
print("First observation:", df["datetime"].min())
print("Last observation:", df["datetime"].max())

# Check number of observations
print("Number of observations:", len(df))

# Check if it's chronological
print("Data is sorted: ", df["datetime"].is_monotonic_increasing)

#Check time difference between observations
time_diff = df["datetime"].diff()

print("\nTime differences between observations: ")
print(time_diff.value_counts().head())

# --------------------------------------
# Step 3: Aggregate into 6-hour windows
# --------------------------------------

# Select only normalised weather variables
weather_columns = [
    "temperature_norm",
    "humidity_norm",
    "wind_norm",
    "pressure_norm",
    "rain_norm"
]

# Use datetime as the DataFrame index
df = df.set_index("datetime")

# Keep only normalised variables
weather_df = df[weather_columns]

# Group data into 6-hour windows
df_6h = weather_df.resample("6h").mean()

print(df_6h.head())
print("\nNumber of 6-hour observations: ", len(df_6h))
print("Number of rows and columns: ", df_6h.shape)

# -----------------------------
# Step 4: Smooth weather data
# -----------------------------

# Apply a moving average to smooth out
df_smooth = df_6h.rolling(window=3, center=True).mean()

#Remove NaN rows
df_smooth = df_smooth.dropna()

# Check result
print(df_smooth.head())
print("Shape:", df_smooth.shape)

# ---------------------------------------
# Step 5: Resample to 400 musical events
# ---------------------------------------

# Number of musical events needed for the 5-minute track
num_events = 400

old_positions = np.linspace(0, 1, len(df_smooth))

new_positions = np.linspace(0, 1, num_events)

# Interpolate
df_music = pd.DataFrame()

for column in df_smooth.columns:
    df_music[column] = np.interp(
        new_positions,
        old_positions,
        df_smooth[column]
    )

    print(df_music.head())
    print("\nShape:", df_music.shape)