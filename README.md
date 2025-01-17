# Racing Coach

An AI-powered sim racing coach that provides real-time feedback to improve your lap times. This project analyzes your driving telemetry against reference data to give actionable insights during your race sessions.

## Features

- Real-time telemetry collection from iRacing
- Track segmentation and corner analysis
- Performance comparison against reference lap data
- Real-time feedback during racing sessions

## Installation

1. Make sure you have Python 3.10+ and Poetry installed
2. Clone this repository:

```bash
git clone https://github.com/yourusername/racing-coach.git
cd racing-coach
```

3. Install dependencies:

```bash
poetry install
```

## Usage

1. Start iRacing
2. Activate the Poetry environment:

```bash
poetry shell
```

3. Run the telemetry collector:

```bash
python -m racing_coach.main
```

## Project Structure

```
racing_coach/
├── src/              # Source code
├── tests/            # Unit tests
├── data/             # Telemetry and reference data
└── notebooks/        # Development and analysis notebooks
```

## Development

This project uses Poetry for dependency management and packaging. To set up the development environment:

1. Install development dependencies:

```bash
poetry install --with dev
```

2. Run tests:

```bash
poetry run pytest
```
