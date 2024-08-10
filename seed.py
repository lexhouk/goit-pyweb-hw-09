from json import dump

from bs4 import BeautifulSoup
from requests import get


def main() -> None:
    if (response := get('https://quotes.toscrape.com')).status_code == 200:
        ATTRIBUTES = {
            field: {key: field for key in ('class', 'itemprop')}
            for field in ('author', 'text')
        }

        nodes = BeautifulSoup(response.text, 'lxml').find_all(
            'div',
            {
                'class': 'quote',
                'itemtype': 'http://schema.org/CreativeWork'
            }
        )

        quotes = []

        for quote in nodes:
            phrase = quote.find('span', ATTRIBUTES['text'])

            wrapper = phrase.find_next_sibling('span')
            author = wrapper.find('small', ATTRIBUTES['author']).text

            if wrapper.text.replace('\n', '') == f'by {author}(about)':
                tags = quote.find('div', class_='tags') \
                    .select('a.tag[href^="/tag/"]')

                quotes.append({
                    'tags': [tag.text for tag in tags],
                    'author': author,
                    'quote': phrase.text
                })

        with open('quotes.json', 'w', encoding='utf-8') as file:
            dump(quotes, file, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    main()
