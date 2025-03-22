import os
import asyncio
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

SCRAPY_PROJECT_PATH = "/usr/src/app/app"  # Scrapy プロジェクトのルート

class CrawlRequest(BaseModel):
    start_url: str
    target_class: str

@app.post("/crawl/")
async def run_scrapy(request: CrawlRequest):
    os.chdir(SCRAPY_PROJECT_PATH)  # Scrapy のプロジェクトディレクトリに移動

    # Scrapy コマンドの準備
    cmd = [
        "scrapy", "crawl", "internallinks",
        "-a", f"start_url={request.start_url}",
        "-a", f"target_class={request.target_class}",
        "-s", "FEED_FORMAT=json",
        "-s", "FEED_URI=stdout:"
    ]

    try:
        # 非同期でScrapyを実行
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # 非同期で出力を待機
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise HTTPException(status_code=500, detail={"stdout": stdout, "stderr": stderr})

        try:
            scraped_data = json.loads(stdout.strip())
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Failed to decode JSON from Scrapy output")

        return {"scraped_data": scraped_data, "stderr": stderr}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
