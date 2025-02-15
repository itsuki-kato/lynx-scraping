import os
import subprocess
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

SCRAPY_PROJECT_PATH = "/usr/src/app/app"  # Scrapy プロジェクトのルート

class CrawlRequest(BaseModel):
    start_url: str
    target_class: str

@app.post("/crawl/")
def run_scrapy(request: CrawlRequest):
    os.chdir(SCRAPY_PROJECT_PATH)  # Scrapy のプロジェクトディレクトリに移動

    # Scrapy を適切な引数で実行（リアルタイムに標準出力を取得）
    process = subprocess.Popen(
        [
            "scrapy", "crawl", "internallinks",
            "-a", f"start_url={request.start_url}",
            "-a", f"target_class={request.target_class}",
            "-s", "FEED_FORMAT=json",
            "-s", "FEED_URI=stdout:"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    stdout, stderr = process.communicate()  # Scrapy の実行が終わるまで待機

    if process.returncode != 0:
        raise HTTPException(status_code=500, detail={"stdout": stdout, "stderr": stderr})

    try:
        scraped_data = json.loads(stdout.strip())  # Scrapy の標準出力から JSON データを読み込む
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to decode JSON from Scrapy output")

    return {"scraped_data": scraped_data, "stderr": stderr}