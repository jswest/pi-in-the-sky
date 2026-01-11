# Pi in the sky

This project aims to use on-device models to detect the presence of birds in images taken from a USB webcam attached to a Raspberry Pi v4.

## Setup

Install the package:

```bash
uv pip install -e .
```

Or install globally:

```bash
uv tool install -e .
```

The TFLite model (SSD MobileNet V1, ~4MB) is automatically downloaded on first run from Google's official storage.

## Usage

List available cameras:

```bash
pisky list
```

Capture and detect birds:

```bash
pisky shoot                     # Use default camera (index 0)
pisky shoot --camera 1          # Use specific camera
pisky shoot --keep-all          # Keep images even if no birds detected
```

Show configuration and model source:

```bash
pisky info
```

## Configuration

By default, `pisky` stores data in `~/.pisky/` (models, images, and database). To use a different location, set the `PISKY_DATA_DIR` environment variable:

```bash
export PISKY_DATA_DIR=/path/to/data
pisky shoot
```
