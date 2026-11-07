#!/usr/bin/env python3
"""ESP32 Batch Flasher: board flashing with user-supplied firmware.

Uses Espressif esptool and pySerial, without bundled firmware or credentials.
"""
from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path


FLASH_OPTION_VALUES = {
    "--flash-mode": {"qio", "qout", "dio", "dout", "keep"},
    "--flash-freq": {"keep", "20m", "26m", "40m", "80m"},
    "--flash-size": None,  # Let esptool validate flash size for target chip.
}


def read_manifest(firmware_dir: Path, manifest_name: str = "flash_args") -> list[str]:
    """Validate an esptool-style flash_args file; reject unsafe/unexpected flags."""
    root = firmware_dir.resolve()
    manifest = (root / manifest_name).resolve()
    if not manifest.is_relative_to(root):
        raise ValueError("Manifest must be inside the firmware directory")
    if not manifest.is_file():
        raise FileNotFoundError(f"Firmware manifest missing: {manifest}")
    words = shlex.split(manifest.read_text(encoding="utf-8"), comments=True)
    if not words:
        raise ValueError("Firmware manifest is empty")
    result: list[str] = []
    offsets: set[int] = set()
    image_count = 0
    i = 0
    while i < len(words):
        token = words[i]
        canonical_option = token.replace("_", "-")
        if canonical_option in FLASH_OPTION_VALUES:
            if i + 1 >= len(words):
                raise ValueError(f"Missing value for {token}")
            val = words[i + 1]
            allowed = FLASH_OPTION_VALUES[canonical_option]
            if allowed is not None and val.lower() not in allowed:
                raise ValueError(f"Unsupported value for {token}: {val}")
            if canonical_option == "--flash-size" and not re.fullmatch(r"(?:keep|detect|\d+(?:KB|MB|B|k|m)?)", val, re.IGNORECASE):
                raise ValueError(f"Invalid flash size: {val}")
            result.extend((canonical_option, val))
            i += 2
            continue
        if token.startswith("-"):
            raise ValueError(f"Unsupported manifest flag: {token}")
        if not re.fullmatch(r"(?:0[xX][0-9a-fA-F]+|\d+)", token):
            raise ValueError(f"Expected flash offset, got: {token}")
        if i + 1 >= len(words):
            raise ValueError(f"Missing firmware filename after offset {token}")
        off = int(token, 0) if token.lower().startswith("0x") else int(token)
        if off in offsets:
            raise ValueError(f"Duplicate flash offset: {token}")
        offsets.add(off)
        file_token = words[i + 1]
        binary = (root / file_token).resolve()
        if Path(file_token).is_absolute() or not binary.is_relative_to(root):
            raise ValueError(f"Firmware path escapes firmware directory: {file_token}")
        if binary.suffix.lower() != ".bin" or not binary.is_file():
            raise FileNotFoundError(f"Firmware .bin missing: {file_token}")
        result.extend((token, str(binary)))
        image_count += 1
        i += 2
    if not image_count:
        raise ValueError("Manifest requires at least one flash offset and .bin file")
    return result


def available_ports():
    try:
        from serial.tools import list_ports
    except ImportError as exc:
        raise RuntimeError("Install requirements first: python -m pip install -r requirements.txt") from exc
    return sorted(list_ports.comports(), key=lambda p: p.device)


def show_ports() -> None:
    ports = available_ports()
    if not ports:
        print("No serial ports found. Check USB data cable, driver and Device Manager/permissions.")
        return
    print("Detected serial ports:")
    for i, p in enumerate(ports, 1):
        print(f"  {i}: {p.device} - {p.description}")


def choose_port(explicit: str | None) -> str:
    if explicit:
        return explicit
    ports = available_ports()
    if not ports:
        raise RuntimeError("No serial ports detected. Try --list-ports after connecting the ESP32.")
    show_ports()
    choice = input("Choose the serial port number (Enter to cancel): ").strip()
    if not choice:
        raise RuntimeError("Port selection cancelled")
    if not choice.isdigit() or not 1 <= int(choice) <= len(ports):
        raise ValueError("Invalid serial port number")
    return ports[int(choice) - 1].device


def esptool_command(port: str, baud: int, manifest_args: list[str]) -> list[str]:
    return [
        sys.executable, "-m", "esptool", "--port", port, "--baud", str(baud),
        "--before", "default-reset", "--after", "hard-reset", "write-flash",
        *manifest_args,
    ]


def wait_for_port(port: str, present: bool, poll: float = 0.5) -> None:
    print(f"Waiting for port {port} to {'appear' if present else 'disconnect'}...")
    while True:
        if (port.upper() in {p.device.upper() for p in available_ports()}) == present:
            return
        time.sleep(poll)


def flash_board(port: str, baud: int, flash_args: list[str], monitor: bool, serial_baud: int) -> int:
    print(f"Checking ESP chip on {port}...")
    probe = subprocess.run([sys.executable, "-m", "esptool", "--port", port, "chip-id"], check=False)
    if probe.returncode:
        print("Probe failed; no firmware was written. Check port, cable, BOOT button, and drivers.")
        return probe.returncode
    print("Flashing using your supplied manifest...")
    rc = subprocess.run(esptool_command(port, baud, flash_args), check=False).returncode
    if rc:
        print("Flash failed. Check that the firmware matches this board and flash layout.")
        return rc
    print("Flash finished successfully (esptool exit code 0). Confirm the device boots as expected.")
    if monitor:
        print("Starting serial monitor; exit with Ctrl+].")
        subprocess.run([sys.executable, "-m", "serial.tools.miniterm", port, str(serial_baud)], check=False)
    return 0


def positive_int(value: str) -> int:
    num = int(value)
    if num <= 0:
        raise argparse.ArgumentTypeError("Must be a positive integer")
    return num


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Flash user-provided ESP32 firmware safely, one board at a time")
    ap.add_argument("--firmware-dir", type=Path, default=Path(__file__).parent / "firmware")
    ap.add_argument("--manifest", default="flash_args", help="Manifest filename inside firmware-dir")
    ap.add_argument("--port", help="Explicit serial port, e.g. COM5 or /dev/ttyUSB0")
    ap.add_argument("--baud", type=positive_int, default=115200, help="Flash speed (default: 115200)")
    ap.add_argument("--serial-baud", type=positive_int, default=115200)
    ap.add_argument("--list-ports", action="store_true", help="Print serial ports without flashing")
    ap.add_argument("--dry-run", action="store_true", help="Validate manifest and print planned command; no hardware required")
    ap.add_argument("--batch", action="store_true", help="Repeat on unplug/replug of one selected port")
    ap.add_argument("--monitor", action="store_true", help="Open serial monitor after successful flash")
    ap.add_argument("--yes", action="store_true", help="Skip per-board confirmation (use only with trusted hardware)")
    ns = ap.parse_args(argv)
    try:
        if ns.list_ports:
            show_ports()
            return 0
        args = read_manifest(ns.firmware_dir, ns.manifest)
        if ns.dry_run:
            cmd = esptool_command(ns.port or "<PORT>", ns.baud, args)
            print("Validated manifest. Planned command (not executed):")
            print(shlex.join(cmd))
            return 0
        port = choose_port(ns.port)
        n = 0
        while True:
            wait_for_port(port, present=True)
            n += 1
            if not ns.yes:
                answer = input(f"Flash board #{n} on {port}? Type YES to proceed: ").strip()
                if answer != "YES":
                    print("Cancelled; no firmware written.")
                    return 1
            rc = flash_board(port, ns.baud, args, ns.monitor, ns.serial_baud)
            if not ns.batch:
                return rc
            print(f"Board #{n} result: {'PASS' if rc == 0 else 'FAILED'}. Unplug it before the next board.")
            wait_for_port(port, present=False)
    except (ValueError, FileNotFoundError, RuntimeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nStopped by user")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
