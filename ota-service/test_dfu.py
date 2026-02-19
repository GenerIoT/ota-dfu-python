#!/usr/bin/env python3

import sys
from ota_package.dfu_service import run_dfu

# -----------------------------
# Configuration
# -----------------------------
# Replace these with real values
MAC_ADDRESS = "FD:A0:1D:27:3C:11"
FIRMWARE_FILE = "ota_package/firmware.zip"  # must exist inside container/host
RUUVITAG_ID = "E9:34:DA:74:0D:6C:5B:43"

# -----------------------------
# Run DFU
# -----------------------------
try:
    print(f"Starting DFU for device {MAC_ADDRESS} using {FIRMWARE_FILE}")
    result = run_dfu(
        address=MAC_ADDRESS,
        zipfile=FIRMWARE_FILE,
        ruuvitag=RUUVITAG_ID
    )

    if result:
        print("DFU completed successfully!")
    else:
        print("DFU returned False")

except Exception as e:
    import traceback
    print("DFU failed with exception:")
    print(str(e))
    print(traceback.format_exc())
    sys.exit(1)
