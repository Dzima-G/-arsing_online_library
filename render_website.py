import json
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
        rendered_page = template.render(books_desc=range_books, pages=pages, current_page=page_id)

        with open(f'pages/index{page_id}.html', 'w', encoding="utf8") as file:
            file.write(rendered_page)


if __name__ == "__main__":
    with open("content_books.json", "r", encoding='utf8') as file:
        books_desc = json.load(file)
    books_desc = list(chunked(books_desc, NUMBER_BOOKS_PER_PAGE))

    on_reload()

    server = Server()
    server.watch('template/template.html', on_reload)
    server.serve(root='pages')
