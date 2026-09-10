# Weather Sonification

A Python project that transforms hourly weather data into a musical composition.

The project takes real weather observations, cleans and normalises the data, maps different weather variables to musical properties, compresses around nine months of hourly data into a roughly five-minute composition, and generates a MIDI file.

## How it works

The project follows a simple data-to-music pipeline:

```text
Meteostat weather data
        ↓
   get_weather.py
        ↓
   Raw weather CSV
        ↓
 clean_weather_file.py
        ↓
   Cleaned weather data
        ↓
   weather_mapping.py
        ↓
 Normalised + musical data
        ↓
    create_midi.py
        ↓
 Newcastle weather MIDI
```

## Weather → Music

Each weather variable controls a different musical element:

| Weather variable | Musical element | How it is used                                   |
| ---------------- | --------------- | ------------------------------------------------ |
| Temperature      | Piano           | Higher temperatures produce higher notes         |
| Humidity         | Slow strings    | Controls the harmonic/chord movement             |
| Wind             | Flute           | Controls pitch and playing intensity             |
| Air pressure     | Cello           | Creates a slower, lower layer                    |
| Rain             | Vibraphone      | Creates individual hits when rain occurs |

All notes are constrained to a **major pentatonic scale**. This helps the different weather layers work together without creating harsh dissonance.

## Project structure

```text
weather_sonification/
│
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

### `main.py`

It runs the different stages of the pipeline in order:

1. Get the weather data
2. Clean the data
3. Map weather values to musical values
4. Generate the MIDI file

### `config.py`

Contains shared settings used by different parts of the project.

Settings include:

* Target composition length: **5 minutes**
* Tempo: **96 BPM**
* Root note: **MIDI note 60 (C4)**
* Major pentatonic scale
* MIDI timing settings

Keeping these values in one file makes it easier to experiment with the composition without changing multiple scripts.

### `get_weather.py`

Uses the **Meteostat** Python library to retrieve hourly weather observations for Newcastle.

The data currently covers:

**29 September 2025 → 15 June 2026**

The following variables are collected:

* Temperature
* Precipitation
* Wind speed
* Relative humidity
* Atmospheric pressure

### `clean_weather_file.py`

Cleans and prepares the raw weather data.

The script:

* Converts timestamps to UK local time
* Selects the weather variables needed for the project
* Renames columns to clearer names
* Sorts the data chronologically
* Treats missing rainfall values as zero
* Interpolates short gaps in weather measurements
* Removes rows with larger unfillable gaps
* Checks for unusual/out-of-range values
* Interpolates values that were identified as errors
* Saves the cleaned dataset

### `weather_mapping.py`

Converts the cleaned numerical weather data into musical values.

First, each weather variable is normalised to a value between 0 and 1. These values are then mapped to MIDI notes.

The script also compresses the hourly dataset so that around nine months of weather can be represented by a composition of approximately five minutes.

For most variables, values within each time bucket are averaged. Wind intensity uses the maximum value so that stronger gusts are not completely smoothed out, while rainfall events are summed to preserve bursts of rain.

### `create_midi.py`

Turns the mapped weather data into a multi-track MIDI composition.

The MIDI file contains separate tracks for:

* Temperature — piano
* Humidity — slow strings
* Wind — flute
* Pressure — cello
* Rain — vibraphone

The script also quantises notes to the shared pentatonic scale.

## Data processing

The project uses a number of different stages of data transformation:

### 1. Raw data

The hourly weather observations are downloaded from Meteostat.

```text
ncl_weather.csv
```

### 2. Cleaning

Missing values and unusual measurements are handled.

```text
ncl_weather_clean.csv
```

### 3. Normalisation and mapping

Weather values are converted into normalised values and MIDI notes.

```text
ncl_weather_mapped.csv
```

### 4. Compression

The hourly data is grouped into larger time buckets so that the complete dataset can fit into a roughly five-minute musical composition.

### 5. MIDI generation

The mapped data is converted into a multi-track MIDI file.

```text
newcastle_weather.mid
```

## Installation

Clone or download the project and create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

The project currently requires:

```text
meteostat
pandas
numpy
mido
```

## Running the project

From the project directory:

```bash
python src/main.py
```

This runs the complete pipeline.

The generated files are saved inside the `data` directory.

## Musical approach

The aim of the project is not to directly turn every weather measurement into a note. Instead, the weather data is treated as a source of musical structure.

Different variables represent different layers of the composition:

* **Temperature** provides the main melodic movement.
* **Humidity** provides harmony through slow-moving chords.
* **Wind** adds movement and intensity.
* **Pressure** provides a lower, more stable layer.
* **Rain** creates short rhythmic events.

The composition therefore represents changes in weather through changes in pitch, harmony, intensity and rhythm.
