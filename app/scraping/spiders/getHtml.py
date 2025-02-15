import scrapy
import os


class GethtmlSpider(scrapy.Spider):
    name = "getHtml"
    allowed_domains = ["zenn.dev"]
    start_urls = ["https://zenn.dev/elletech/articles/nextjs_microcms"]

    def parse(self, response):
        output_path = "/usr/src/app/downloads/"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path + "index.html", "w", encoding="utf-8") as f:
            f.write(response.text)
