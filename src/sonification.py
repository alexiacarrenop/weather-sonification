import logging
import random
from .config import (
    BPM,
    ROOT,
    PENTATONIC,
    TICKS_PER_BEAT,
    TICKS_PER_ROW,
    WIND_OCTAVE_SHIFT,
)
from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo

# Takes mapped weather data and turns it into MIDI composition
class SonificationEngine:
    logger = logging.getLogger(__name__)

    
    # ----------------------------------------------------------------------------
    # Ambient tuning knobs
    #
    # 1 row = 1 data point = TICKS_PER_ROW ticks (one beat).
    #   BLOCK_ROWS   : how many rows get averaged into one note. 
    #   OVERLAP_ROWS : how long a note keeps ringing after its slot ends, so it
    #                  blends into the next note.
    # ----------------------------------------------------------------------------
    TEMPERATURE_BLOCK_ROWS = 4
    TEMPERATURE_OVERLAP_ROWS = 0
 
    HUMIDITY_BLOCK_ROWS = 8
    HUMIDITY_OVERLAP_ROWS = 0
    HUMIDITY_CHORD_STEPS = (0, 2)       # scale steps above the root; was (0, 2, 4)
 
    WIND_BLOCK_ROWS = 3
    WIND_OVERLAP_ROWS = 0
 
    PRESSURE_BLOCK_ROWS = 8
    PRESSURE_OVERLAP_ROWS = 0
 
    RAIN_KEEP_PROBABILITY = 0.5         # chance each raindrop is actually played
    RAIN_NOTE_TICKS = 120               # length of one drop
    RAIN_NOTES = (72, 74, 76, 79, 81, 84)  # C5-C6 pentatonic; drops pick randomly from these
 
    HUMANIZE_TICKS = 40                 # random +/- shift of note starts
    VELOCITY_JITTER = 4                 # random +/- velocity
    RANDOM_SEED = 7                     # same data -> same MIDI every run

    def __init__(self, dataframe):
        self.dataframe = dataframe
        self.bpm = BPM
        self.root = ROOT
        self.scale = PENTATONIC
        self.rng = random.Random(self.RANDOM_SEED)

    # Keeps MIDI values within valid range
    def clamp(self, value, low=0, high=127):
        return max(low, min(high, int(value)))
    
    # ----------------------------------------------------------------------------
    # Step 1: Scale quantization helpers
    #
    # Every track gets snapped onto the same pentatonic scale so tracks can't 
    # clash regardless of what the raw weather data does.
    # ----------------------------------------------------------------------------
    
    # Takes a MIDI note and moves it to the nearest note in scale
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

    # ----------------------------------------------------------------------------
    # Step 2: Ambient helpers
    #
    # Each track works in three stages:
    #   1. _block_notes = average rows into blocks, merge repeated pitches
    #   2. build intervals = (start_tick, end_tick, note, velocity), with overlap
    #   3. _write_intervals = turn intervals into MIDI events with delta times
    # ----------------------------------------------------------------------------
 
    def _jitter_velocity(self, velocity):
        return self.clamp(
            velocity + self.rng.randint(-self.VELOCITY_JITTER, self.VELOCITY_JITTER), 1, 127
        )
 
    # Groups rows into blocks of `block_rows`, snaps each block's average pitch to the
    # scale, and  merges neighbouring blocks with the same pitch into one
    # long note. aux_values (e.g. wind_norm) get averaged per run.
    def _block_notes(self, midi_values, block_rows, merge_same=True, aux_values=None, shift=0):
        runs = []
        for start in range(0, len(midi_values), block_rows):
            chunk = midi_values[start:start + block_rows]
            note = self.snap_to_scale(round(sum(chunk) / len(chunk)) + shift)
            aux_sum = sum(aux_values[start:start + block_rows]) if aux_values is not None else 0.0
 
            if merge_same and runs and runs[-1]["note"] == note:
                runs[-1]["length"] += len(chunk)
                runs[-1]["aux_sum"] += aux_sum
            else:
                runs.append({"start": start, "length": len(chunk), "note": note, "aux_sum": aux_sum})
 
        for run in runs:
            run["aux"] = run["aux_sum"] / run["length"]
        return runs
 
    # Start/end ticks for a run: nudged start, end extended by the overlap tail
    def _span(self, run, overlap_rows):
        start = max(0, run["start"] * TICKS_PER_ROW
                    + self.rng.randint(-self.HUMANIZE_TICKS, self.HUMANIZE_TICKS))
        end = (run["start"] + run["length"] + overlap_rows) * TICKS_PER_ROW
        return start, end
 
    # Converts start, end, note, velocity intervals into MIDI.
    # If the same pitch would be triggered while it is still ringing, the earlier
    # note is cut off at the moment the later one starts.
    def _write_intervals(self, track, channel, intervals):
        by_note = {}
        for start, end, note, velocity in intervals:
            by_note.setdefault(note, []).append([start, end, velocity])
 
        events = []  # (tick, order, type, note, velocity); order 0 = note_off first
        for note, spans in by_note.items():
            spans.sort()
            for i, span in enumerate(spans):
                if i + 1 < len(spans) and span[1] > spans[i + 1][0]:
                    span[1] = spans[i + 1][0]
                if span[1] <= span[0]:
                    continue
                events.append((span[0], 1, "note_on", note, span[2]))
                events.append((span[1], 0, "note_off", note, 0))
 
        events.sort(key=lambda e: (e[0], e[1]))
 
        last_tick = 0
        for tick, _, kind, note, velocity in events:
            track.append(Message(kind, channel=channel, note=note,
                                 velocity=velocity, time=int(tick - last_tick)))
            last_tick = tick
    
    # ----------------------------------------------------------------------------
    # Step 3: Build MIDI
    # ----------------------------------------------------------------------------
    
    # Main function that creates the MIDI
    def generate(self):
        self.logger.info("Starting MIDI generation")

        df = self.dataframe

        required_cols = [
                            "temperature_midi", "humidity_midi", "wind_midi", "wind_norm",
                            "pressure_midi", "rain_hits"
                        ]

        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            self.logger.error(
                "Missing required columns: %s",
                ", ".join(missing_cols)
            )
            raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

        if df.empty:
            self.logger.error("Cannot generate MIDI from an empty dataframe")
            raise ValueError("Cannot generate MIDI from an empty dataframe")

        # Reseed so calling generate() twice gives identical output
        self.rng = random.Random(self.RANDOM_SEED)
    
        mid = MidiFile(ticks_per_beat=TICKS_PER_BEAT)

        self.logger.info("Creating MIDI tracks for temperature, humidity, wind, pressure and rain")

        # Temperature (strings):  slow melody, one note per block, merged when pitch repeats
        temperature_track = MidiTrack()
        mid.tracks.append(temperature_track)
        temperature_track.append(MetaMessage("track_name", name="Temperature"))
        temperature_track.append(MetaMessage("set_tempo", tempo=bpm2tempo(self.bpm)))
        temperature_track.append(Message("program_change", channel=0, program=48))  # String Ensemble 1

        intervals = []
        for run in self._block_notes(df["temperature_midi"].tolist(), self.TEMPERATURE_BLOCK_ROWS):
            start, end = self._span(run, self.TEMPERATURE_OVERLAP_ROWS)
            intervals.append((start, end, run["note"], self._jitter_velocity(70)))
        self._write_intervals(temperature_track, 0, intervals)


        '''for note in df["temperature_midi"]:
            note = self.snap_to_scale(note)
            temperature_track.append(Message("note_on", note=note, velocity=80, time=0))
            temperature_track.append(Message("note_off", note=note, velocity=0, time=TICKS_PER_ROW))'''

        # Humidity (warm pad): thinner, longer chords (root + one scale step pair)
        humidity_track = MidiTrack()
        mid.tracks.append(humidity_track)
        humidity_track.append(MetaMessage("track_name", name="Humidity"))
        humidity_track.append(Message("program_change", channel=1, program=89))  # Pad 2 (warm) = analog pad

        intervals = []
        for run in self._block_notes(df["humidity_midi"].tolist(), self.HUMIDITY_BLOCK_ROWS):
            start, end = self._span(run, self.HUMIDITY_OVERLAP_ROWS)
            for steps in self.HUMIDITY_CHORD_STEPS:
                note = self.scale_degree_up(run["note"], steps)
                intervals.append((start, end, note, self._jitter_velocity(50)))
        self._write_intervals(humidity_track, 1, intervals)

        # Wind (flute, shifted up 2 octaves into a real flute register and away from pressure's range) 
        

        wind_track = MidiTrack()
        mid.tracks.append(wind_track)
        wind_track.append(MetaMessage("track_name", name="Wind"))
        wind_track.append(Message("program_change", channel=2, program=19))  # Church organ

        intervals = []
        wind_runs = self._block_notes(
            df["wind_midi"].tolist(),
            self.WIND_BLOCK_ROWS,
            merge_same=False,
            aux_values=df["wind_norm"].tolist(),
            shift=WIND_OCTAVE_SHIFT,
        )
        for run in wind_runs:
            start, end = self._span(run, self.WIND_OVERLAP_ROWS)
            velocity = self._jitter_velocity(30 + run["aux"] * 90)
            intervals.append((start, end, run["note"], velocity))
        self._write_intervals(wind_track, 2, intervals)

        # Pressure (cello) 
        pressure_track = MidiTrack()
        mid.tracks.append(pressure_track)
        pressure_track.append(MetaMessage("track_name", name="Pressure"))
        pressure_track.append(Message("program_change", channel=3, program=38))  # Synth bass 1

        intervals = []
        for run in self._block_notes(df["pressure_midi"].tolist(), self.PRESSURE_BLOCK_ROWS):
            start, end = self._span(run, self.PRESSURE_OVERLAP_ROWS)
            intervals.append((start, end, run["note"], self._jitter_velocity(64)))
        self._write_intervals(pressure_track, 3, intervals)

        # Rain (vibraphone) 
        rain_track = MidiTrack()
        mid.tracks.append(rain_track)
        rain_track.append(MetaMessage("track_name", name="Rain"))
        rain_track.append(Message("program_change", channel=4, program=11))  # Vibraphone

        rain_notes = [self.snap_to_scale(n) for n in self.RAIN_NOTES]
        intervals = []
        for row, hits in enumerate(df["rain_hits"].tolist()):
            hits = int(hits)
            if hits <= 0:
                continue
 
            spacing = TICKS_PER_ROW // hits
            note_dur = min(self.RAIN_NOTE_TICKS, spacing)
 
            for i in range(hits):
                if self.rng.random() > self.RAIN_KEEP_PROBABILITY:
                    continue
                start = row * TICKS_PER_ROW + i * spacing + self.rng.randint(0, spacing - note_dur)
                note = self.rng.choice(rain_notes)
                velocity = self.clamp(35 + hits * 6 + self.rng.randint(0, 15), 1, 127)
                intervals.append((start, start + note_dur, note, velocity))
        self._write_intervals(rain_track, 4, intervals)

        self.logger.info(
            "MIDI generation complete: %d musical events processed",
            len(df)
        )
        return mid

