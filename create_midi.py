import pandas as pd
from mido import MidiFile, MidiTrack, Message, MetaMessage

df = pd.read_csv("ncl_weather_mapped.csv")
df = df.sort_values("datetime").reset_index(drop=True)

# Create MIDI file
mid = MidiFile(ticks_per_beat=480)

# One weather observation = one MIDI beat
HOUR = 480

def clamp(value, low=0, high=127):
    return max(low, min(high, int(value)))

# Temperature track
temperature_track = MidiTrack()
mid.tracks.append(temperature_track)
temperature_track.append(MetaMessage("track_name", name="Temperature"))
temperature_track.append(Message("program_change", channel=0, program=0)) # Acoustic Grand Piano

for note in df["temperature_midi"]:
    note = clamp(note)
    temperature_track.append(
        Message(
            "note_on",
            note=int(note),
            velocity=80,
            time=0
        )
    )

    temperature_track.append(
        Message(
            "note_off",
            note=int(note),
            velocity=0,
            time=HOUR
        )
    )


# Humidity track
humidity_track = MidiTrack()
mid.tracks.append(humidity_track)
humidity_track.append(MetaMessage("track_name", name="Humidity"))
humidity_track.append(Message("program_change", channel=1, program=4)) # Electric piano

for root in df["humidity_midi"]:
    root = clamp(root)

    chord = [clamp(root), clamp(root + 4), clamp(root + 7)]

    # Play chord
    for note in chord:
        humidity_track.append(Message("note_on", channel=1, note=note, velocity=50, time=0))

     # Stop chord after HOUR ticks total, not HOUR per note
    for i, note in enumerate(chord):
        humidity_track.append(
            Message(
                "note_off",
                channel=1,
                note=note,
                velocity=0,
                time=HOUR if i == 0 else 0,
            )
        )


# Wind track

wind_track = MidiTrack()
mid.tracks.append(wind_track)
wind_track.append(MetaMessage("track_name", name="Wind"))
wind_track.append(Message("program_change", channel=2, program=73)) # Flute

for _, row in df.iterrows():

    note = clamp(row["wind_midi"])

    # Stronger wind = louder note
    velocity = clamp(
        30 + row["wind_norm"] * 90
    )

    wind_track.append(Message("note_on", channel=2, note=note, velocity=velocity, time=0))
    wind_track.append(Message("note_off", channel=2, note=note, velocity=0, time=HOUR))

# Pressure track

pressure_track = MidiTrack()
mid.tracks.append(pressure_track)
pressure_track.append(
    MetaMessage("track_name", name="Pressure")
)
pressure_track.append(Message("program_change", channel=3, program=42))  # Cello

for note in df["pressure_midi"]:
    note = clamp(note)
    pressure_track.append(Message("note_on", channel=3, note=note, velocity=70, time=0))
    pressure_track.append(Message("note_off", channel=3, note=note, velocity=0, time=HOUR))

# Rain track
RAIN_NOTE = 42

rain_track = MidiTrack()
mid.tracks.append(rain_track)
rain_track.append(
    MetaMessage("track_name", name="Rain")
)
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

        rain_track.append(
            Message("note_on", channel=4, note=RAIN_NOTE, velocity=80, time=on_time)
        )

        off_time = note_dur if i < hits - 1 else note_dur + leftover
        rain_track.append(
            Message("note_off", channel=4, note=RAIN_NOTE, velocity=0, time=off_time)
        )       

# Save MIDI file
mid.save("newcastle_weather.mid")

print("MIDI file created!")