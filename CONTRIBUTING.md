# Contributing

Thank you for considering a contribution to ESP32 Batch Flasher.

1. Open an issue explaining your improvement or bug before large changes.
2. Make changes on a branch and add unit tests where applicable.
3. Run `python -m unittest discover -s tests -v` and `python -m compileall -q flasher.py tests`.
4. Submit a pull request describing your changes and test environment.
5. Never include private firmware, API keys, personal data, production device identifiers, or proprietary customer code.

For hardware bug reports, include the board variant, serial adapter, operating system, Python/esptool versions and a redacted error log. Do not share device MAC addresses or secrets.
