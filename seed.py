from collections import defaultdict
from json import dump
from logging import basicConfig, INFO, info
from re import search

from bs4 import BeautifulSoup
from requests import get


def scrape(path: str) -> BeautifulSoup | None:
    path = 'https://quotes.toscrape.com' + path

    info(f'Parsing {path}')

    response = get(path)

    return BeautifulSoup(response.text, 'lxml') \
        if response.status_code == 200 else None


def main() -> None:
    basicConfig(level=INFO, format='%(message)s')

    ATTRIBUTES = {
        field: {key: field for key in ('class', 'itemprop')}
        for field in ('author', 'text')
    }

    results = defaultdict(list)
    path = '/'

    while (page := scrape(path)):
        nodes = page.find_all(
            'div',
            {
                'class': 'quote',
                'itemtype': 'http://schema.org/CreativeWork'
            },
        )

        for quote in nodes:
            phrase = quote.find('span', ATTRIBUTES['text'])

            wrapper = phrase.find_next_sibling('span')
            author_name = wrapper.find('small', ATTRIBUTES['author']).text
            author_link = wrapper.select('a[href^="/author/"]')[0]

            author_info = f'by {author_name}{author_link.text}'

            if wrapper.text.replace('\n', '') != author_info:
                continue

            results['authors'].append(author_link['href'])

            tags = quote.find('div', class_='tags') \
                .select('a.tag[href^="/tag/"]')

            results['quotes'].append({
                'tags': [tag.text for tag in tags],
                'author': author_name,
                'quote': phrase.text,
            })

        if (not (
            (nodes := page.select('nav > ul.pager > li.next > a')) and
            search(r'^/page/\d+/$', path := nodes[0]['href'])
        )):
            break

    paths = set(results['authors'])
    results['authors'] = []

    for path in paths:
        if not (page := scrape(path)):
            continue

        wrapper = page.find('div', class_='author-details')
        author = {}

        for name in ('title', 'born-date', 'born-location', 'description'):
            field = 'fullname' if name == 'title' else name.replace('-', '_')
            author[field] = wrapper.select(f'.author-{name}')[0].text.strip()

        results['authors'].append(author)

    for type, result in results.items():
        with open(f'{type}.json', 'w', encoding='utf-8') as file:
            dump(result, file, indent=2, ensure_ascii=False)

        info(f'Found {len(result)} {type}.')


if __name__ == '__main__':
    main()
