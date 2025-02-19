import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import Request


class InternalLinksSpider(CrawlSpider):
    name = "internallinks"

    def __init__(self, start_url=None, target_class=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not start_url:
            raise ValueError("start_url is required")
        if not target_class:
            raise ValueError("target_class is required")

        self.allowed_domains = [start_url.split("//")[-1].split("/")[0]]
        self.start_urls = [start_url]
        self.target_class = target_class  # クラス名をインスタンス変数として保持

    rules = (Rule(LinkExtractor(allow=()), callback="parse_item", follow=True),)

    def parse_item(self, response):
        # 指定クラスがページ内に存在するかチェック
        # if not response.xpath(f"//div[contains(@class, '{self.target_class}')]"):
        #     return  # クラスがなければスキップ

        current_url = response.url
        title = response.xpath("//title/text()").get(default="").strip()
        description = (
            response.xpath('//meta[@name="description"]/@content')
            .get(default="")
            .strip()
        )

        # meta robots を取得し、index/noindex を判定
        robots_meta = (
            response.xpath('//meta[@name="robots"]/@content').get(default="").strip()
        )
        index_status = "noindex" if "noindex" in robots_meta.lower() else "index"

        # 指定クラス内の内部リンクを取得
        internal_links = response.xpath(
            f"//div[contains(@class, '{self.target_class}')]//a/@href"
        ).getall()
        internal_links = [response.urljoin(link) for link in internal_links]

        # 階層構造を持たせた h タグの取得
        headings = self.get_structured_headings(response)

        yield {
            "current_url": current_url,
            "title": title,
            "description": description,
            "index_status": index_status,
            "internal_links": internal_links,
            "headings": headings,  # 階層構造の h タグ
        }

    def get_structured_headings(self, response):
        """h1~h4 タグをサイト内の配置に基づいて階層構造で取得"""
        headings = []
        stack = []  # 階層管理用のスタック
        prev_level = 0  # 直前の見出しのレベル

        # h1~h4 の要素を順番に取得
        heading_elements = response.xpath("//h1 | //h2 | //h3 | //h4")

        for element in heading_elements:
            tag_name = element.root.tag  # h1, h2, h3, h4 のタグ名
            text = element.xpath("text()").get("").strip()
            level = int(tag_name[1])  # h1, h2, h3, h4 の数値部分を取得（例: h2 -> 2）

            heading_item = {"tag": tag_name, "text": text, "children": []}

            # スタックが空ならルート要素として追加
            if not stack:
                stack.append(heading_item)
                headings.append(heading_item)
            else:
                # 直前のレベルと比較して適切な階層構造を作る
                if level > prev_level:
                    # 直前の見出しの子要素として追加
                    stack[-1]["children"].append(heading_item)
                    stack.append(heading_item)
                else:
                    # スタックを遡って適切な位置に配置
                    while stack and int(stack[-1]["tag"][1]) >= level:
                        stack.pop()
                    if stack:
                        stack[-1]["children"].append(heading_item)
                    else:
                        headings.append(heading_item)
                    stack.append(heading_item)

            prev_level = level  # 現在のレベルを更新

        return headings
