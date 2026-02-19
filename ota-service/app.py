from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from ota_package.dfu_service import run_dfu
from bleak import BleakScanner

app = FastAPI()


class UpdateRequest(BaseModel):
    mac: str
    zipfile: str
    ruuvitag: str


@app.post("/update")
async def update_device(data: UpdateRequest):
    try:
        result = await run_in_threadpool(
            run_dfu,
            data.mac,
            data.zipfile,
            data.ruuvitag
        )
        return {"success": result}
    except Exception as e:
        return {"success": False, "error": str(e)}