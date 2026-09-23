# Weather Sonification

A Python project that transforms hourly weather data from Newcastle into a musical composition.

The project downloads around nine months of weather observations, cleans and validates the data, maps weather variables to musical properties, compresses the data into approximately five minutes, and generates a multi-track MIDI file.

## Architecture

The project follows a modular data-to-music pipeline:

```text
                 ┌─────────────────┐
                 │    Meteostat    │
                 └────────┬────────┘
                          ↓
                 ┌─────────────────┐
                 │ WeatherFetcher  │
                 └────────┬────────┘
                          ↓
                 ┌─────────────────┐
                 │ WeatherCleaner  │
                 └────────┬────────┘
                          ↓
                 ┌─────────────────┐
                 │ WeatherMapper   │
                 └────────┬────────┘
                          ↓
                 ┌─────────────────┐
                 │ Sonification    │
                 │    Engine       │
                 └────────┬────────┘
                          ↓
                 ┌─────────────────┐
                 │    MIDI file    │
                 └─────────────────┘
```

Each component has a specific responsibility:

* **WeatherFetcher** — retrieves hourly weather data from Meteostat.
* **WeatherCleaner** — validates, cleans and prepares the data.
* **WeatherMapper** — converts weather measurements into musical values.
* **SonificationEngine** — generates the final MIDI composition.

This separation makes the pipeline easier to test, maintain and extend. For example, the cleaning process can be changed without modifying the MIDI generation code.

## Weather → Music

| Weather variable | Musical element | Mapping                            |
| ---------------- | --------------- | ---------------------------------- |
| Temperature      | Piano           | Higher temperatures → higher notes |
| Humidity         | Slow strings    | Controls harmonic movement         |
| Wind             | Flute           | Controls pitch and intensity       |
| Air pressure     | Cello           | Creates a slower, lower layer      |
| Rain             | Vibraphone      | Creates rhythmic hits              |

Notes are constrained to a major pentatonic scale to keep the different layers musically compatible.

## Data Processing

```text
Meteostat
    ↓
Raw hourly data
    ↓
Cleaning + validation
    ↓
Normalisation + musical mapping
    ↓
Time compression
    ↓
Multi-track MIDI
```

The weather data currently covers:

**29 September 2025 → 15 June 2026**

The cleaning stage handles missing values, short gaps and out-of-range values. The mapping stage normalises weather values and groups hourly observations into larger time buckets so the complete dataset fits into an approximately five-minute composition.

## Project Structure

```text
weather_sonification/
├── src/
│   ├── main.py
│   ├── config.py
│   ├── get_weather.py
│   ├── clean_weather_file.py
│   ├── weather_mapping.py
│   └── create_midi.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── output/
│
├── .gitignore
└── requirements.txt
```

## Configuration

Shared settings are stored in `config.py`, keeping configuration separate from implementation.

Current settings include:

* **Target duration:** 5 minutes
* **Tempo:** 96 BPM
* **Root note:** MIDI 60 (C4)
* **Scale:** Major pentatonic
* MIDI timing values
* Wind octave shift

This allows musical parameters to be changed without modifying the logic.

## Code Quality

### Testing

Unit tests using `pytest` verify important parts of the cleaning pipeline, including:

* required output columns
* missing rainfall handling
* invalid/out-of-range values
* expected cleaned data structure

### Validation

The pipeline validates data at multiple stages. The cleaner checks required columns, handles missing values, detects unrealistic measurements and removes rows where data cannot be recovered.

The mapping and MIDI stages also check for missing required columns and empty DataFrames.

### Error Handling

Clear exceptions are used when something goes wrong. For example, `WeatherFetcher` handles Meteostat retrieval failures and empty responses rather than allowing confusing downstream errors.

### Logging

Python's `logging` module is used to track important pipeline events, including:

* data retrieval
* cleaning progress
* invalid values
* records removed
* mapping progress
* MIDI generation
* errors

Logging is configured centrally in `main.py`, while individual classes use module-level loggers.

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Main dependencies:

```text
meteostat
pandas
numpy
mido
pytest
```

## Running

From the project root:

```bash
python -m src.main
```

The generated MIDI and processed data are saved in the `data` directory.

## Musical Approach

The project treats weather as a source of musical structure rather than simply converting every measurement into a note.

* **Temperature** provides melodic movement.
* **Humidity** provides harmony.
* **Wind** adds movement and intensity.
* **Pressure** provides a lower, stable layer.
* **Rain** creates rhythmic events.

Changes in weather are therefore represented through changes in pitch, harmony, intensity and rhythm.

## Further Improvements

### Make It Extensible 

Future versions could support different sonification strategies:

```text
SonificationStrategy
       │
       ├── WeatherMelodyStrategy
       ├── AmbientStrategy
       └── RhythmStrategy
```

Polymorphism could be introduced if multiple strategies are implemented. It was not added to the current version because there is currently only one concrete strategy.

### Concurrent Data Fetching

The current project retrieves data for one location, so concurrency is unnecessary. If multiple independent locations were added, concurrent network requests could be considered because the workload is primarily I/O-bound.

### SQLite 

A future version could store weather observations in SQLite:

```text
Meteostat
    ↓
  SQLite
    ↓
WeatherCleaner
    ↓
WeatherMapper
    ↓
SonificationEngine
    ↓
   MIDI
```

This would allow previously downloaded data to be reused and make it easier to query and compare weather data from different dates or locations.
