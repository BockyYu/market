import os
import json
from apps.service.google_upload.upload import do_upload
from apps.service.market import get_market_data, export_to_excel
from typing import Dict
from pydantic import BaseModel
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

app = FastAPI(title="Market Data API")
scheduler = AsyncIOScheduler()
thread_pool = ThreadPoolExecutor()

async def scheduled_market_data_task():
    try:
        config = load_config()
        market_data = await run_in_thread(get_market_data, config)
        await run_in_thread(export_to_excel, market_data)
        await run_in_thread(do_upload)

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Task completed successfully at {current_time}")

    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Task failed at {current_time}: {str(e)}")


@app.on_event("startup")
async def setup_scheduler():
    # 21:00 到 23:59 每半小時執行一次
    scheduler.add_job(
        scheduled_market_data_task,
        'cron',
        hour='21-23',
        minute='0,30'
    )

    # 00:00 到 02:00 每半小時執行一次
    scheduler.add_job(
        scheduled_market_data_task,
        'cron',
        hour='0-2',
        minute='0,30'
    )

    # 09:00 到 20:59 每小時執行一次
    scheduler.add_job(
        scheduled_market_data_task,
        'cron',
        hour='9-20',
        minute='0'
    )

    scheduler.start()
    print("Scheduler started successfully")


@app.get("/next-run")
async def get_next_run():
    # 添加檢查下次執行時間的端點
    jobs = scheduler.get_jobs()
    next_runs = []
    for job in jobs:
        next_runs.append(job.next_run_time.strftime("%Y-%m-%d %H:%M:%S"))
    return {"next_run_times": sorted(next_runs)}

def load_config() -> Dict:
    # 載入設定檔
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