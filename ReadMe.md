# Govee BLE Controller

Control Govee Bluetooth LED strips from a PC without the phone app. Built and tested against a Govee H617E (20 m RGBIC strip) on Windows, using [bleak](https://github.com/hbldh/bleak) for Bluetooth Low Energy.

> **Status:** early development. Unofficial, not affiliated with or endorsed by Govee. The protocol is reverse engineered and may differ between models and firmware versions.

## Features

- Finds the strip by scanning for a `Govee*` BLE name
- Persistent connection with lazy reconnect
- Power, brightness and colour commands
- Notification subscription for reading the strip's replies

Planned: CLI, GUI, state tracking, segment control, scenes and music-reactive lighting.

## Requirements

- Python 3.10+ (developed on 3.14)
- A Bluetooth LE adapter, switched on
- The Govee phone app **closed**: the strip only accepts one BLE connection at a time

## Setup

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

## Project structure

```
src/
  main.py               entry point
  govee_strip.py        GoveeStrip: scan, connect, send (transport layer)
  command_functions.py  on(), off(), brightness(), colour() -> payload bytes
  make_frame.py         checksum() and make_frame(): payload -> 20-byte frame
  constants.py          UUIDs, opcodes, frame length, tuning values
```

Layers, each using only the one beneath it:

```
UI / CLI        user input
Commands        on(), off(), brightness(n), colour(r, g, b)  -> payload bytes
Framing         make_frame(payload)                          -> 20-byte frame
Transport       GoveeStrip: find device, connect, write
```

## Usage

```python
from govee_strip import GoveeStrip
from command_functions import on, brightness, colour

async with GoveeStrip() as strip:
    await strip.send(on())
    await strip.send(brightness(50))
    await strip.send(colour(255, 0, 0))
```

## Protocol notes

- Commands are written, without response, to characteristic `00010203-0405-0607-0809-0a0b0c0d2b11`.
- The strip's replies arrive as notifications on `...2b10`.
- Frames are 20 bytes: payload, zero padding to 19 bytes, then an XOR checksum of those 19 bytes.
- Payload layout: `0x33` (control command), a packet type (`0x01` power, `0x04` brightness, `0x05` colour), then the value bytes.
- Brightness range and the colour sub-mode vary by model, so they are constants in `constants.py`.

Based on community reverse-engineering work for older Govee models, adapted and checked against the H617E.

## Troubleshooting

- **Strip not found:** it stops advertising while connected elsewhere. Close the Govee app, power-cycle the strip, and toggle Windows Bluetooth.
- **Service discovery errors:** the client skips Windows' GATT cache; if errors persist, remove the strip from Windows Bluetooth devices and retry.
- **Commands ignored:** try the other colour sub-mode or brightness range in `constants.py`.