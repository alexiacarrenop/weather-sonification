import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# COMPRESS 10 MONTHS OF HOURLY DATA INTO ~5 MINUTES OF MUSIC
#
# Idea: don't just shrink note durations to cram more data into less time --
# at ~7200 hourly rows into 5 minutes that's ~40ms/note, which is too short
# to hear as distinct pitches and just turns into a blur.
#
# Instead, average groups of consecutive hours into single "super-notes".
# This both compresses time AND smooths hourly noise into real trends
# (daily warm-up/cool-down, multi-day pressure systems, etc.), which
# sounds far more musical than raw hour-by-hour jitter.
#
# Target math: at BPM beats per minute, TARGET_MINUTES of music = 
#   TARGET_MINUTES * BPM  quarter-note beats total.
# One row -> one beat (matching HOUR = 480 ticks = 1 beat in your script),
# so we need the compressed dataframe to have that many rows.
# ---------------------------------------------------------------------------

TARGET_MINUTES = 5
BPM = 96

df = pd.read_csv("ncl_weather_mapped.csv")
df = df.sort_values("datetime").reset_index(drop=True)

required_cols = [
    "temperature_midi", "humidity_midi", "wind_midi", "wind_norm",
    "pressure_midi", "rain_hits"
]
df = df.dropna(subset=required_cols).reset_index(drop=True)

target_beats = round(TARGET_MINUTES * BPM)
bucket_size = max(1, len(df) // target_beats)

print(f"{len(df)} hourly rows -> bucketing every {bucket_size} hours "
      f"-> ~{len(df) // bucket_size} notes -> "
      f"~{(len(df) // bucket_size) / BPM:.1f} min at {BPM} BPM")

df["bucket"] = np.arange(len(df)) // bucket_size

# Aggregate each variable sensibly:
# - continuous readings (temp/humidity/pressure/wind pitch): mean, so the
#   note represents the "average conditions" over that window
# - wind_norm (drives velocity/loudness): max, so gusts still register as
#   an accent rather than getting averaged away
# - rain_hits: sum, so a stormy window still produces a burst of hits
#   rather than a diluted average
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

# `df` now has ~target_beats rows and is a drop-in replacement for the
# original hourly dataframe -- feed it straight into the MIDI-building
# code from create_midi_reworked.py unchanged (still one row = one HOUR
# of ticks = one beat).