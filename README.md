# ESP32 Batch Flasher

A small, open-source Python command-line utility for flashing **user-provided** ESP32-family firmware to serial-connected development boards, one device at a time. It wraps [Espressif esptool](https://github.com/espressif/esptool) and [pySerial](https://github.com/pyserial/pyserial).

> **Development status:** Initial code release. Manifest parsing is unit-tested; Windows/Linux hardware flashing has **not yet been independently validated** in this release. Please report your board, operating system, serial adapter, and test results.

## Features

- Works with Python on Windows and Linux (platform support requires hardware testing).
- Lists serial devices and lets you explicitly select the target port.
- Reads an esptool-style `flash_args` manifest with safe, validated firmware paths.
- Offers a `--dry-run` validation mode that does not contact hardware.
- Checks board connectivity with `esptool chip-id` before writing.
- Supports repeated one-board-at-a-time flashing with `--batch`.
- Optional serial monitor, with an explicit confirmation prompt before flashing.
- Does **not** bundle compiled firmware, internal deployments, or credentials.

## Requirements

- Python 3.10 or newer and a USB data cable
- A working serial driver (often CP210x or CH340/CH341, depending on your board)
- Your own compiled firmware, including the correct `flash_args` manifest
- A compatible ESP32 development board

## Install

Clone the repository and enter it:

```bash
git clone https://github.com/vipin-commit/esp32-batch-flasher.git
cd esp32-batch-flasher
python -m pip install -r requirements.txt
```

On Windows, replace `python` with `py -3` if needed, or run `setup_windows.bat`. A virtual environment is recommended for dependency isolation.

On Linux, your user may need serial-port permissions (for example membership in `uucp` or `dialout`, depending on distribution). Do not use `sudo` unless necessary and understood.

## Add your own firmware

Copy your compiled `.bin` files and the **matching** build-generated `flash_args` to the `firmware/` directory. See [`firmware/README.md`](firmware/README.md). All firmware files are excluded from version control to avoid accidentally publishing private binaries.

## Use

```bash
python flasher.py --list-ports
python flasher.py --dry-run
python flasher.py --port COM5
python flasher.py --port COM5 --batch --monitor
```

Linux example:

```bash
python flasher.py --port /dev/ttyUSB0 --batch
```

In interactive use, type **YES** before each board is flashed. Use `--yes` only if you are intentionally authorizing unattended repeated flashes with a trusted port/device. To change firmware directory, pass `--firmware-dir /path/to/firmware`.

Exit the serial monitor with `Ctrl+]` when finished. In batch mode, unplug each board and connect the next one. Stop with `Ctrl+C`.

**Firmware must be compiled for the precise target board and flash layout.** Writing an incompatible image may make the board fail to boot; recovery may require re-flashing the correct image.

## Tests

```bash
python -m unittest discover -s tests -v
python -m compileall -q flasher.py tests
```

Hardware verification checklist: confirm port listing, dry-run manifest, board probe, firmware flash, boot, serial monitor, unplug/replug, and multiple-board loop on both Windows and Linux where available.

## Open-source usage

This repository contains the **generic flashing tool**, not any project-specific firmware. See the MIT `LICENSE` in the repository. Contributions and hardware test reports are welcome; open an issue with your board model, OS and esptool version.

## Attribution

Flashing is performed by Espressif's `esptool` under its own license. Serial-port discovery and monitoring use `pySerial` under its own license. This utility does not incorporate or redistribute either project's source code.
