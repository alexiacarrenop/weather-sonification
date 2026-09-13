from config import BPM, ROOT, PENTATONIC, HOUR
from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo

class SonificationEngine:

    def __init__(self, dataframe):
        self.dataframe = dataframe
        self.bpm = BPM
        self.root = ROOT
        self.scale = PENTATONIC

    def clamp(self, value, low=0, high=127):
        return max(low, min(high, int(value)))

    def snap_to_scale(self, note):
        note = self.clamp(note)

        rel = (note - self.root) % 12
        best = min(self.scale, key=lambda s: min(abs(rel - s), 12 - abs(rel - s)))

        delta = best - rel

        if delta > 6:
            delta -= 12
        elif delta < -6:
            delta += 12

        return self.clamp(note + delta)

    def scale_degree_up(self, note, steps):
        """Move `note` up `steps` positions WITHIN the scale (not semitones),
            used to build chords that stay inside the scale."""
        snapped = self.snap_to_scale(note)
        rel = (snapped - self.root) % 12
        octave = (snapped - self.root - rel) // 12
        idx = self.scale.index(rel)
        new_idx = idx + steps
        oct_shift, new_idx = divmod(new_idx, len(self.scale))
        return self.clamp(self.root + (octave + oct_shift) * 12 + self.scale[new_idx])

    def generate(self):

        df = self.dataframe

        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")
    
        required_cols = [
                    "temperature_midi", "humidity_midi", "wind_midi", "wind_norm",
                    "pressure_midi", "rain_hits"
                ]

        if df.empty:
            raise ValueError("Cannot generate MIDI from an empty dataframe")
    
                # ----------------------------------------------------------------------------
                # Step 1: Scale quantization helpers
                #
                # Every track gets snapped onto the same pentatonic scale so tracks can't 
                # clash regardless of what the raw weather data does.
                # ----------------------------------------------------------------------------
                # ----------------------------------------------------------------------------
                # Step 2: Build MIDI
                # ----------------------------------------------------------------------------
        mid = MidiFile(ticks_per_beat=480)

                # Temperature (piano) 
        temperature_track = MidiTrack()
        mid.tracks.append(temperature_track)
        temperature_track.append(MetaMessage("track_name", name="Temperature"))
        temperature_track.append(MetaMessage("set_tempo", tempo=bpm2tempo(self.bpm)))
        temperature_track.append(Message("program_change", channel=0, program=0))  # Grand Piano

        for note in df["temperature_midi"]:
            note = self.snap_to_scale(note)
            temperature_track.append(Message("note_on", note=note, velocity=80, time=0))
            temperature_track.append(Message("note_off", note=note, velocity=0, time=HOUR))

                # Humidity (Slow strings) 
        humidity_track = MidiTrack()
        mid.tracks.append(humidity_track)
        humidity_track.append(MetaMessage("track_name", name="Humidity"))
        humidity_track.append(Message("program_change", channel=0, program=49))  # Slow strings

        for root in df["humidity_midi"]:
            root_note = self.snap_to_scale(root)
            chord = [
                root_note,
                        self.scale_degree_up(root_note, 2),
                        self.scale_degree_up(root_note, 4),
                    ]
            for note in chord:
                humidity_track.append(Message("note_on", channel=1, note=note, velocity=50, time=0))
            for i, note in enumerate(chord):
                humidity_track.append(
                            Message("note_off", channel=1, note=note, velocity=0,
                                    time=HOUR if i == 0 else 0)
                        )

                # Wind (flute, shifted up 2 octaves into a real flute register and away
                #     from Pressure's range) 
        WIND_OCTAVE_SHIFT = 24

        wind_track = MidiTrack()
        mid.tracks.append(wind_track)
        wind_track.append(MetaMessage("track_name", name="Wind"))
        wind_track.append(Message("program_change", channel=2, program=73))  # Flute

        for _, row in df.iterrows():
            note = self.snap_to_scale(row["wind_midi"] + WIND_OCTAVE_SHIFT)
            velocity = self.clamp(30 + row["wind_norm"] * 90)
            wind_track.append(Message("note_on", channel=2, note=note, velocity=velocity, time=0))
            wind_track.append(Message("note_off", channel=2, note=note, velocity=0, time=HOUR))

                # Pressure (cello) 
        pressure_track = MidiTrack()
        mid.tracks.append(pressure_track)
        pressure_track.append(MetaMessage("track_name", name="Pressure"))
        pressure_track.append(Message("program_change", channel=3, program=42))  # Cello

        for i, note in enumerate(df["pressure_midi"]):
            note = self.snap_to_scale(note)
            velocity = self.clamp(70 + (i % 5) - 2)  # small variation so it's not a dead-flat drone
            pressure_track.append(Message("note_on", channel=3, note=note, velocity=velocity, time=0))
            pressure_track.append(Message("note_off", channel=3, note=note, velocity=0, time=HOUR))

                # Rain (vibraphone) 
        RAIN_NOTE = self.snap_to_scale(42)

        rain_track = MidiTrack()
        mid.tracks.append(rain_track)
        rain_track.append(MetaMessage("track_name", name="Rain"))
        rain_track.append(Message("program_change", channel=0, program=11))  # Vibraphone
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

        return mid

