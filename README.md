# RuuviTag OTA Update Service

This repository provides a **Dockerized FastAPI service** to perform Over-The-Air (OTA) firmware updates on RuuviTags via Bluetooth.

## Features
- Dockerized Python service for easy deployment.
- OTA firmware update via FastAPI endpoint.
- Simple HTTP API to trigger updates with required parameters.
- Supports multiple RuuviTags by specifying MAC address and passcode.

## Quick Start
### 1. Run the Docker Container

```bash
docker compose up --build
```

This will start the FastAPI service accessible at http://localhost:8000.

### 2. Trigger an Update
Send a **POST request** to the `/update` endpoint with JSON data:
```json
{
  "url": "<FIRMWARE_URL>",
  "mac": "<DEVICE_MAC>",
  "ruuvitag": "<RUUVITAG_ID>"
}
```
Parameters:
- `url` – The URL to download the firmware from.
- `mac` – The MAC address of the RuuviTag to update.
- `ruuvitag` – Passcode required by the device to authorize the update.