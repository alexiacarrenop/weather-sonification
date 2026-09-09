import pandas as pd
import numpy as np
from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo

# ===========================================================================
# SETTINGS
# ===========================================================================
TARGET_MINUTES = 5      # roughly how long the final track should be
BPM = 96                # tempo
ROOT = 60                # scale root (60 = C). Change to transpose the piece.
PENTATONIC = [0, 2, 4, 7, 9]  # major pentatonic scale degrees (no clashes possible)
HOUR = 480               # ticks per "beat" / per compressed data-row

required_cols = [
    "temperature_midi", "humidity_midi", "wind_midi", "wind_norm",
    "pressure_midi", "rain_hits"
]

# ===========================================================================
# STEP 1: LOAD + COMPRESS DATA
#
# ~10 months of hourly data is way too many rows to map 1 row = 1 note in
# a 5-minute track (that'd be ~40ms/note -- inaudible as distinct pitches).
# Instead we bucket consecutive hours together and average them, which
# compresses time AND smooths hourly noise into real trends.
# ===========================================================================
df = pd.read_csv("ncl_weather_mapped.csv")
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
        "wind_norm": "max",     # keep gusts as accents, don't average them away
        "pressure_midi": "mean",
        "rain_hits": "sum",     # keep storm bursts intact
    })
    .reset_index(drop=True)
)

# ===========================================================================
# STEP 2: SCALE QUANTIZATION HELPERS
#
# Every track gets snapped onto the same pentatonic scale. A major
# pentatonic scale has no minor-2nd or tritone interval between ANY two of
# its notes, in any octave -- so tracks can't clash regardless of what the
# raw weather data does.
# ===========================================================================
def clamp(value, low=0, high=127):
    return max(low, min(high, int(value)))

def snap_to_scale(note, scale=PENTATONIC, root=ROOT):
    note = clamp(note)
    rel = (note - root) % 12
    best = min(scale, key=lambda s: min(abs(rel - s), 12 - abs(rel - s)))
    delta = best - rel
    if delta > 6:
        delta -= 12
    elif delta < -6:
        delta += 12
    return clamp(note + delta)

def scale_degree_up(note, steps, scale=PENTATONIC, root=ROOT):
    """Move `note` up `steps` positions WITHIN the scale (not semitones) --
    used to build chords that stay inside the scale."""
    snapped = snap_to_scale(note, scale, root)
    rel = (snapped - root) % 12
    octave = (snapped - root - rel) // 12
    idx = scale.index(rel)
    new_idx = idx + steps
    oct_shift, new_idx = divmod(new_idx, len(scale))
    return clamp(root + (octave + oct_shift) * 12 + scale[new_idx])


# ===========================================================================
# STEP 3: BUILD MIDI
# ===========================================================================
mid = MidiFile(ticks_per_beat=480)

# --- Temperature (piano) ---------------------------------------------------
temperature_track = MidiTrack()
mid.tracks.append(temperature_track)
temperature_track.append(MetaMessage("track_name", name="Temperature"))
temperature_track.append(MetaMessage("set_tempo", tempo=bpm2tempo(BPM)))
temperature_track.append(Message("program_change", channel=0, program=0))  # Acoustic Grand Piano

for note in df["temperature_midi"]:
    note = snap_to_scale(note)
    temperature_track.append(Message("note_on", note=note, velocity=80, time=0))
    temperature_track.append(Message("note_off", note=note, velocity=0, time=HOUR))

# --- Humidity (electric piano, in-scale chords) ----------------------------
humidity_track = MidiTrack()
mid.tracks.append(humidity_track)
humidity_track.append(MetaMessage("track_name", name="Humidity"))
humidity_track.append(Message("program_change", channel=1, program=4))  # Electric piano

for root in df["humidity_midi"]:
    root_note = snap_to_scale(root)
    chord = [
        root_note,
        scale_degree_up(root_note, 2),
        scale_degree_up(root_note, 4),
    ]
    for note in chord:
        humidity_track.append(Message("note_on", channel=1, note=note, velocity=50, time=0))
    for i, note in enumerate(chord):
        humidity_track.append(
            Message("note_off", channel=1, note=note, velocity=0,
                    time=HOUR if i == 0 else 0)
        )

# --- Wind (flute, shifted up 2 octaves into a real flute register and away
#     from Pressure's range) ------------------------------------------------
WIND_OCTAVE_SHIFT = 24

wind_track = MidiTrack()
mid.tracks.append(wind_track)
wind_track.append(MetaMessage("track_name", name="Wind"))
wind_track.append(Message("program_change", channel=2, program=73))  # Flute

for _, row in df.iterrows():
    note = snap_to_scale(row["wind_midi"] + WIND_OCTAVE_SHIFT)
    velocity = clamp(30 + row["wind_norm"] * 90)
    wind_track.append(Message("note_on", channel=2, note=note, velocity=velocity, time=0))
    wind_track.append(Message("note_off", channel=2, note=note, velocity=0, time=HOUR))

# --- Pressure (cello, bass register) ---------------------------------------
pressure_track = MidiTrack()
mid.tracks.append(pressure_track)
pressure_track.append(MetaMessage("track_name", name="Pressure"))
pressure_track.append(Message("program_change", channel=3, program=42))  # Cello

for i, note in enumerate(df["pressure_midi"]):
    note = snap_to_scale(note)
    velocity = clamp(70 + (i % 5) - 2)  # small variation so it's not a dead-flat drone
    pressure_track.append(Message("note_on", channel=3, note=note, velocity=velocity, time=0))
    pressure_track.append(Message("note_off", channel=3, note=note, velocity=0, time=HOUR))

# --- Rain (steel drums / percussive hits) -----------------------------------
RAIN_NOTE = snap_to_scale(42)

rain_track = MidiTrack()
mid.tracks.append(rain_track)
rain_track.append(MetaMessage("track_name", name="Rain"))
rain_track.append(Message("program_change", channel=4, program=115))  # Steel Drums

pending_time = 0

for hits in df["rain_hits"]:
    hits = int(hits)

    if hits == 0:
        pending_time += HOUR
        continue

    spacing = HOUR // hits
    note_dur = min(60, spacing)
    leftover = HOUR - (note_dur + spacing * (hits - 1))

    for i in range(hits):
        on_time = pending_time if i == 0 else (spacing - note_dur)
        pending_time = 0

        rain_track.append(Message("note_on", channel=4, note=RAIN_NOTE, velocity=80, time=on_time))

        off_time = note_dur if i < hits - 1 else note_dur + leftover
        rain_track.append(Message("note_off", channel=4, note=RAIN_NOTE, velocity=0, time=off_time))

mid.save("newcastle_weather.mid")
print("MIDI file created!")