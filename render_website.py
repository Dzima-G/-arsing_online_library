import argparse
import json
import os
import sys

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked

NUMBER_BOOKS_PER_PAGE = 10


def on_reload():
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template('template/template.html')

    pages = range(1, len(books_desc) + 1)

    for page_id, range_books in enumerate(books_desc, 1):
        rendered_page = template.render(books_desc=range_books,
                                        pages=pages,
                                        current_page=page_id
                                        )

        with open(f'pages/index{page_id}.html', 'w', encoding='utf8') as file:
            file.write(rendered_page)


def create_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=('''\
            Скрипт формирует веб-сайт из скачанных книг с сайта https://tululu.org/
            --------------------------------------------------
            Для формирования страниц веб-сайта необходимо указать параметры:
            --json_path - путь к файлу content_books.json сформированного скриптом parse_tululu_category.py
            '''
                     )
    )
    parser.add_argument('--json_path', default='', nargs='?',
                        help='Введите путь к файлу content_books.json')
    return parser


if __name__ == '__main__':
    os.makedirs('pages', exist_ok=True)
    parser = create_parser()
    args = parser.parse_args(sys.argv[1:])
    file_json_path = os.path.join(args.json_path, 'content_books.json')

    with open(file_json_path, 'r', encoding='utf8') as file:
        books_desc = json.load(file)
    books_desc = list(chunked(books_desc, NUMBER_BOOKS_PER_PAGE))

    on_reload()

    server = Server()
    server.watch('template/template.html', on_reload)
    server.serve(root='.')
