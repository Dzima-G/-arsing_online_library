import json
from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server


def on_reload():
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template('template/template.html')
    rendered_page = template.render(books_desc=books_desc)

    with open('index.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)


if __name__ == "__main__":
    with open("books/content.json", "r", encoding='utf8') as file:
        books_desc = json.load(file)

    on_reload()

    server = Server()
    server.watch('template/template.html', on_reload)
    server.serve(root='.')
