from collections import defaultdict
from json import dump
from re import search

from itemadapter import ItemAdapter
from scrapy import Request, Spider
from scrapy.http.response import Response
from scrapy.crawler import CrawlerProcess
from scrapy.item import Field, Item


class QuoteItem(Item):
    tags = Field()
    author = Field()
    quote = Field()


class AuthorItem(Item):
    fullname = Field()
    born_date = Field()
    born_location = Field()
    description = Field()


class DataPipline:
    def __init__(self) -> None:
        self.__results = defaultdict(list)

    def process_item(self, item, spider) -> None:
        adapter = ItemAdapter(item)
        type = 'authors' if 'fullname' in adapter.keys() else 'quotes'
        self.__results[type].append(dict(adapter))

    def close_spider(self, spider):
        for type, result in self.__results.items():
            with open(f'{type}.json', 'w', encoding='utf-8') as file:
                dump(result, file, indent=2, ensure_ascii=False)


class QuotesSpider(Spider):
    name = 'quotes'
    allowed_domains = ['quotes.toscrape.com']
    start_urls = ['https://' + domain for domain in allowed_domains]
    custom_settings = {'ITEM_PIPELINES': {DataPipline: 300}}

    def parse(self, response: Response):
        QUERIES = {
            'tags': (
                "div[@class='tags']/a[@class='tag']"
                "[starts-with(@href, '/tag/')]"
            ),
            'author': "span/small[@class='author'][@itemprop='author']",
            'quote': "span[@class='text'][@itemprop='text']",
        }

        AUTHOR = (
            "span/a[starts-with(@href, '/author/')][text()='(about)']/@href"
        )

        NEXT = (
            "/html//nav/ul[@class='pager']/li[@class='next']"
            "/a[starts-with(@href, '/page/')]/@href"
        )

        nodes = response.xpath(
            "/html//div[@class='quote']"
            "[@itemtype='http://schema.org/CreativeWork']",
        )

        for quote in nodes:
            yield QuoteItem(**{
                field: getattr(
                    quote.xpath(query + '/text()'),
                    'extract' if field == 'tags' else 'get',
                )()
                for field, query in QUERIES.items()
            })

            yield response.follow(
                self.start_urls[0] + quote.xpath(AUTHOR).get(),
                self.parse_author,
            )

        next = response.xpath(NEXT).get()

        if next and search(r'^/page/\d+/$', next):
            yield Request(self.start_urls[0] + next)

    @staticmethod
    def parse_author(response: Response):
        wrapper = response.xpath("/html//div[@class='author-details']")
        author = {}

        for name in ('title', 'born-date', 'born-location', 'description'):
            field = 'fullname' if name == 'title' else name.replace('-', '_')
            query = f"*[@class='author-{name}']/text()"

            if name.startswith('born-'):
                query = 'p/' + query

            author[field] = wrapper.xpath(query).get().strip()

            if name == 'born-location':
                author[field] = author[field][3:]

        yield AuthorItem(**author)


def main() -> None:
    process = CrawlerProcess()
    process.crawl(QuotesSpider)
    process.start()


if __name__ == '__main__':
    main()
