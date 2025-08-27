# Generate Mender Artifact

This repository contains a helper script, **`generate_mender_artifact.sh`**, which creates a [Mender](https://mender.io/) artifact for RuuviTag OTA (Over-the-Air) updates.
  
The script packages a mender update script into a `.mender` artifact that can be deployed via Mender. It utilizes ota-dfu-python to deploy the update from gateway to RuuviTag.

## Configuration

Before running the script, open **`generate_mender_artifact.sh`** and edit the following variables as needed:

1. **NAME** -- The name of this update, displayed in Mender UI
2. **VERSION** -- The version of this update package, displayed in Mender UI
3. **URL** -- URL where gateway downloads the deployed update package for RuuviTag

## Usage
After configuration script can be runned on terminal, e.g.

 ```bash
 ./generate_mender_artifact
 ```
 
This will create `${ARTIFACT_NAME}-${ARTIFACT_VERSION}.mender` file. Copy this to your Mender Server using website UI. The script has set the artifact to only target RuuviTags device, even if it's used in heterogeneous device group.