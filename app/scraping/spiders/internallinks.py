import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

class InternalLinksSpider(CrawlSpider):
    name = 'internallinks'

    def __init__(self, start_url=None, target_class=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not start_url:
            raise ValueError("start_url is required")
        if not target_class:
            raise ValueError("target_class is required")

        self.allowed_domains = [start_url.split("//")[-1].split("/")[0]]
        self.start_urls = [start_url]
        self.target_class = target_class  # クラス名をインスタンス変数として保持

    rules = (
        Rule(LinkExtractor(allow=()), callback='parse_item', follow=True),
    )

    def parse_item(self, response):
        # 指定したクラスがページ内に存在するかチェック
        if not response.xpath(f"//div[contains(@class, '{self.target_class}')]"):
            return  # クラスがなければスキップ

        current_url = response.url
        title = response.xpath('//title/text()').get(default='').strip()
        description = response.xpath('//meta[@name="description"]/@content').get(default='').strip()

        # meta robots を取得し、index/noindex を判定
        robots_meta = response.xpath('//meta[@name="robots"]/@content').get(default='').strip()
        index_status = 'noindex' if 'noindex' in robots_meta.lower() else 'index'

        # 指定クラス内の内部リンクを取得
        internal_links = response.xpath(f"//div[contains(@class, '{self.target_class}')]//a/@href").getall()
        internal_links = [response.urljoin(link) for link in internal_links]

        yield {
            'current_url': current_url,
            'title': title,
            'description': description,
            'index_status': index_status,
            'internal_links': internal_links,
        }