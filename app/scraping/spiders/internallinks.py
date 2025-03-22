import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import Request
import requests
import json
from urllib.parse import urlparse


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
        if not response.xpath(f"//*[contains(@class, '{self.target_class}')]"):
            return  # クラスがなければスキップ

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

        # 指定クラス内の内部リンクを取得（URLとアンカーテキスト）
        internal_links = []
        link_elements = response.xpath(
            f"//*[contains(@class, '{self.target_class}')]//a"
        )
        
        for link in link_elements:
            href = link.xpath("@href").get()
            if href:
                full_url = response.urljoin(href)
                anchor_text = link.xpath("string(.)").get().strip()
                
                # 同一ドメインかどうかを判定
                is_same_domain = self.is_same_domain(full_url)
                
                # 同一ドメインの場合はステータス情報を取得、異なるドメインの場合はデフォルト値を設定
                status_info = self.get_link_status(full_url) if is_same_domain else {"code": -1, "redirectUrl": ""}
                
                internal_links.append({
                    "linkUrl": full_url,
                    "anchorText": anchor_text,
                    "status": status_info
                })

        # 階層構造を持たせた h タグの取得
        headings = self.get_structured_headings(response)

        # JSON-LD形式の構造化データを取得
        jsonld_data = self.extract_jsonld(response)

        yield {
            "articleUrl": current_url,
            "metaTitle": title,
            "metaDescription": description,
            "isIndexable": index_status == "index",
            "internalLinks": internal_links,
            "headings": headings,  # 階層構造の h タグ
            "jsonLd": jsonld_data  # JSON-LD形式の構造化データ
        }

    def is_same_domain(self, url):
        """URLが同一ドメインかどうかを判定する"""
        try:
            domain = urlparse(url).netloc
            return domain in self.allowed_domains
        except:
            return False
            
    def get_link_status(self, url):
        """リンクのHTTPステータスコードとリダイレクト先を取得する"""
        try:
            # リダイレクトを追跡しないようにする
            response = requests.head(url, timeout=5, allow_redirects=False)
            status_code = response.status_code
            
            # リダイレクト先URLを取得（存在する場合）
            redirect_url = response.headers.get('Location', '') if 300 <= status_code < 400 else ''
            
            # 相対URLの場合は絶対URLに変換
            if redirect_url and not redirect_url.startswith(('http://', 'https://')):
                # URLの基本部分を取得
                parsed_url = urlparse(url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                
                # 相対URLが / で始まる場合はドメインルートからの相対パス
                if redirect_url.startswith('/'):
                    redirect_url = f"{base_url}{redirect_url}"
                # そうでない場合は現在のパスからの相対パス
                else:
                    # 現在のパスのディレクトリ部分を取得
                    path_parts = parsed_url.path.split('/')
                    if len(path_parts) > 1:
                        path_parts.pop()  # 最後の部分（ファイル名）を削除
                    current_dir = '/'.join(path_parts)
                    redirect_url = f"{base_url}{current_dir}/{redirect_url}"
            
            return {
                "code": status_code,
                "redirectUrl": redirect_url
            }
        except:
            # 例外が発生した場合は0を返す（接続エラーなど）
            return {
                "code": 0,
                "redirectUrl": ""
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
            # string(.)を使用して子要素内のテキストも含めて取得
            text = element.xpath("string(.)").get("").strip()
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
        
    def extract_jsonld(self, response):
        """ページからJSON-LD形式の構造化データを抽出する"""
        # JSON-LDスクリプトタグを検索
        jsonld_scripts = response.xpath('//script[@type="application/ld+json"]/text()').getall()
        
        result = []
        for script in jsonld_scripts:
            try:
                # JSONとして解析
                data = json.loads(script)
                result.append(data)
            except json.JSONDecodeError:
                # 解析エラーの場合はスキップ
                continue
                
        return result
