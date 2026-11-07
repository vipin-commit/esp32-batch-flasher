# Your firmware goes here (local only)

Put your **own compiled firmware** and its matching `flash_args` file here. This directory is intentionally excluded from Git, except for this README.

Example structure (file names and offsets are illustrative; use those generated for **your board/build**):

```
firmware/
  flash_args
  bootloader.bin
  partitions.bin
  application.bin
```

A possible `flash_args` file for a particular ESP32 build might contain:

```
--flash-mode dio --flash-freq 40m --flash-size 4MB
0x1000 bootloader.bin
0x8000 partitions.bin
0x10000 application.bin
```

**Do not copy these offsets blindly.** Firmware layouts vary between boards, build systems, and partition tables. See Espressif's [flashing guide](https://docs.espressif.com/projects/esptool/en/latest/esp32/esptool/flashing-firmware.html).

Never commit proprietary binaries, credentials, API endpoints, device identifiers, or personal records. The `.gitignore` excludes `firmware/*`; check `git status` before publishing.
