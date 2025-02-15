import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class InternalLinksSpider(CrawlSpider):
    name = 'internallinks'
    allowed_domains = ['naresome-matome.com']
    start_urls = ['https://naresome-matome.com/']

    # 取得対象のクラス名を指定
    target_class = "post_content"  # 取得したいコンテンツエリアのクラスを指定

    rules = (
        Rule(LinkExtractor(allow=()), callback='parse_item', follow=True),
        Rule(LinkExtractor(restrict_xpaths="//a[contains(text(),'次へ') or contains(text(),'Next')]"), follow=True),
    )

    def parse_item(self, response):
        # 指定したクラスがページ内に存在するかチェック
        if not response.xpath(f"//div[contains(@class, '{self.target_class}')]"):
            return  # クラスがなければスキップ

        # 現在のページのURL
        current_url = response.url

        # ページのタイトルを取得
        title = response.xpath('//title/text()').get(default='').strip()

        # meta descriptionを取得
        description = response.xpath('//meta[@name="description"]/@content').get(default='').strip()

        # meta robotsを取得し、index/noindexを判定
        robots_meta = response.xpath('//meta[@name="robots"]/@content').get(default='').strip()
        index_status = 'noindex' if 'noindex' in robots_meta.lower() else 'index'

        # 特定のクラス内にある内部リンクのみ取得
        internal_links = response.xpath(f"//div[contains(@class, '{self.target_class}')]//a/@href").getall()

        # 相対URLを絶対URLに変換
        internal_links = [response.urljoin(link) for link in internal_links]

        yield {
            'current_url': current_url,
            'title': title,
            'description': description,
            'index_status': index_status,
            'internal_links': internal_links,
        }
