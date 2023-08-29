import json
from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked


def on_reload():
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template('website/template/template.html')
    for i, range_books in enumerate(list(chunked(books_desc, 10)), 1):
        rendered_page = template.render(books_desc=range_books)

        with open(f'website/pages/index{i}.html', 'w', encoding="utf8") as file:
            file.write(rendered_page)


if __name__ == "__main__":
    with open("website/content_books.json", "r", encoding='utf8') as file:
        books_desc = json.load(file)

    on_reload()

    server = Server()
    server.watch('website/template/template.html', on_reload)
    server.serve(root='website/pages')
