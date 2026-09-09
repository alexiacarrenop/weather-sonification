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

# --------------------------------
# Step 5: Create musical mappings
# --------------------------------

# D minor pentatonic scale
scale = ["D3", "F3", "G3", "A3", "C4",
         "D4", "F4", "G4", "A4", "C5"]

# Temperature (strings)
# Low temperature = lower notes
# High temperature # higher notes

#Convert normalised temperature into a note index within the musical scale
df_music["strings_note"] = (
    df_music["temperature_norm"] * (len(scale) - 1)
).round().astype(int)

# Ensure note index stays within range 
df_music["strings_note"] = df_music["strings_note"].clip(
    0, len(scale) - 1
)

# Humidity (analog pad)
# Low humidity = quiet/thin 
# High humidity = louder/atmospheric

df_music["pad_volume"] = df_music["humidity_norm"]

# More humidity = more reverb
df_music["pad_reverb"] = df_music["humidity_norm"]

# Wind (organ)
# Low wind = longer notes
# High wind = shorter notes

df_music["organ_duration"] = ( 1.0 - df_music["wind_norm"])

df_music["organ_density"] = df_music["wind_norm"]

# Pressure (bass)
# Low pressure = deeper bass
# High pressure = higher bass

bass_scale = ["D2", "F2", "G2", "A2", "C3"]

df_music["bass_note"] = ( df_music["pressure_norm"] * (len(bass_scale) - 1)
).round().astype(int)

df_music["bass_note"] = df_music["bass_note"].clip(0, len(bass_scale) -1)

# Rain (soft synth)
# No rain = silence
# Light rain = occasional notes
# Heavy rain = dense notes

df_music["rain_density"] = df_music["rain_norm"]

print(df_music.head())

# df_music.to_csv("sonic_pi_weather.csv", index=False)

# print("Exported musical events to sonic_pi_weather.csv")

# Expert temperature notes for Sonic Pi
with open("rain_values.txt", "w") as file:
    file.write(str(df_music["rain_norm"].tolist()))