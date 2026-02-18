from fastapi import FastAPI
from pydantic import BaseModel
from ota_package.dfu_service import run_dfu


app = FastAPI()


class UpdateRequest(BaseModel):
    mac: str
    zipfile: str
    ruuvitag: str


@app.post("/update")
def update_device(data: UpdateRequest):
    try:
        result = run_dfu(
            address=data.mac,
            zipfile=data.zipfile,
            ruuvitag=data.ruuvitag
        )
        return {"success": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
