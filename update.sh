!/bin/bash

# Function to show help message
show_help() {
  echo "Usage: $0 <url> <mac> <id>"
  echo ""
  echo "Update RuuviTag firmware using OTA DFU with Python script."
  echo ""
  echo "Arguments:"
  echo "  url      The URL to download the firmware zip file (e.g. https://github.com/ruuvi/ruuvi.firmware.c/releases/download/v3.34.1/ruuvitag_b_armgcc_ruuvifw_test_v3.34.1_dfu_app.zip)"
  echo ""
  echo "Options:"
  echo "  -h, --help    Show this help message and exit"
}

# Handle help flag
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
  show_help
  exit 0
fi

# Check if one argument are passed
if [ "$#" -ne 1 ]; then
  echo "Error: Invalid number of arguments"
  show_help
  exit 1
fi

cd /var/lib/ota-dfu-python

URL="$1"
MAC="$(cat /usr/share/mender/identity/mac)"
ID="$(cat /usr/share/mender/identity/ruuvi-id)"

# Get current timestamp in milliseconds
DATE=$(date +%s%3N)

# Set output filename with millisecond timestamp
FIRMWARE_FILE="ruuvitag_firmware_${DATE}.zip"

wget "$URL" -O "$FIRMWARE_FILE"

python3 dfu.py --address="$MAC" --zip="$FIRMWARE_FILE" --ruuvitag="$ID"
return_code=$?

rm -f "$FIRMWARE_FILE"

exit $return_code