#!/bin/bash

DEVICE_TYPE="ruuvitag"
UPDATE_SCRIPT="ruuvitag-updater.sh"

# EDIT THESE AS NEEDED
NAME="ruuvi-firmware"
VERSION="3.41.1"

# Create the update script
cat <<'EOF' > "$UPDATE_SCRIPT"
#!/bin/bash

# EDIT THIS AS NEEDED
URL="https://github.com/ruuvi/ruuvi.firmware.c/releases/download/v3.34.1/ruuvitag_b_armgcc_ruuvifw_default_v3.34.1_dfu_app.zip"

/bin/bash /usr/ota-dfu-python/update.sh "$URL"
EOF

# Make the update script executable
chmod +x "$UPDATE_SCRIPT"

# Generate the Mender artifact
mender-artifact write module-image \
  -T script \
  -n "${NAME}-${VERSION}" \
  -t "$DEVICE_TYPE" \
  -o "${NAME}-${VERSION}.mender" \
  -f "$UPDATE_SCRIPT" \
  --software-name "$NAME" \
  --software-version "$VERSION"

rm "$UPDATE_SCRIPT"

echo "Mender artifact '${NAME}-${VERSION}.mender' generated successfully."