import requests

url = "http://localhost:8000/update"

data = {
    "mac": "FD:A0:1D:27:3C:11",
    "zipfile": "firmware.zip",
    "ruuvitag": "E9:34:DA:74:0D:6C:5B:43"
}

response = requests.post(url, json=data)
print(response.json())