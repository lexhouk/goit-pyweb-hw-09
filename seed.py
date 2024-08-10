from collections import defaultdict
from json import dump
from re import search

from bs4 import BeautifulSoup
from requests import get


def main() -> None:
    DOMAIN = 'https://quotes.toscrape.com'

    ATTRIBUTES = {
        field: {key: field for key in ('class', 'itemprop')}
        for field in ('author', 'text')
    }

    results = defaultdict(list)
    path = '/'

    while True:
        if (response := get(DOMAIN + path)).status_code != 200:
            break

        page = BeautifulSoup(response.text, 'lxml')

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

    results['authors'] = list(set(results['authors']))

    for type, result in results.items():
        with open(f'{type}.json', 'w', encoding='utf-8') as file:
            dump(result, file, indent=2, ensure_ascii=False)

        print(f'Found {len(result)} {type}.')


if __name__ == '__main__':
    main()
