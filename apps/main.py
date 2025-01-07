from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import os
import json
from apps.service.google_upload.upload import do_upload
from apps.service.market import get_market_data, export_to_excel
from typing import Dict
from pydantic import BaseModel
from functools import partial
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uvicorn


app = FastAPI(title="Market Data API")

# 建立線程池
thread_pool = ThreadPoolExecutor()


# 載入設定檔
def load_config() -> Dict:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, 'data.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Configuration file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid configuration file format")


class ProcessResponse(BaseModel):
    status: str
    message: str


async def run_in_thread(func, *args):
    """在線程池中運行同步函數"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, func, *args)


@app.post("/market", response_model=ProcessResponse)
async def process_market_data():
    """
    處理市場數據並上傳到 Google Drive
    """
    try:
        # 載入設定
        config = load_config()

        # 在線程池中運行同步函數
        market_data = await run_in_thread(get_market_data, config)
        await run_in_thread(export_to_excel, market_data)
        await run_in_thread(do_upload)

        return ProcessResponse(
            status="success",
            message="Market data processed and uploaded successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process market data: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """
    健康檢查端點
    """
    return {"status": "healthy"}


# 錯誤處理
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail}
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)