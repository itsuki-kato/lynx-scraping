import os
import subprocess
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

SCRAPY_PROJECT_PATH = "/usr/src/app/app"  # Scrapy プロジェクトのルート

# API のリクエストデータ用の Pydantic モデル
class CrawlRequest(BaseModel):
    start_url: str
    target_class: str

@app.post("/crawl/")
def run_scrapy(request: CrawlRequest):
    os.chdir(SCRAPY_PROJECT_PATH)  # Scrapy のプロジェクトディレクトリに移動

    # Scrapy を適切な引数で実行（Popen でリアルタイムに標準出力を取得）
    process = subprocess.Popen(
        [
            "scrapy", "crawl", "internallinks",
            "-a", f"start_url={request.start_url}",
            "-a", f"target_class={request.target_class}",
            "-o", "output.json",  # 結果を JSON ファイルに保存
            "-t", "json"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    stdout, stderr = process.communicate()  # Scrapy の実行が終わるまで待機

    if process.returncode != 0:
        raise HTTPException(status_code=500, detail={"stdout": stdout, "stderr": stderr})

    # Scrapy が生成した JSON を読み込む
    output_path = os.path.join(SCRAPY_PROJECT_PATH, "output.json")
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            scraped_data = json.load(f)  # Scraped データを取得
    else:
        scraped_data = []

    return {"scraped_data": scraped_data, "stdout": stdout, "stderr": stderr}
