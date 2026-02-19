import os
import httpx
import aiofiles
from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from ota_package.dfu_service import run_dfu

app = FastAPI()
firmware_path = "ruuvi.zip"

class UpdateRequest(BaseModel):
    mac: str
    url: str
    ruuvitag: str


async def download_firmware(url):
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                async with aiofiles.open(firmware_path, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        await f.write(chunk)
    except Exception as e:
        raise RuntimeError(f"Failed to download firmware: {e}")


@app.post("/update")
async def update_device(data: UpdateRequest):
    try:
        await download_firmware(data.url)

        result = await run_in_threadpool(
            run_dfu,
            data.mac,
            firmware_path,
            data.ruuvitag
        )

        return {"success": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        if os.path.exists(firmware_path):
            os.remove(firmware_path)