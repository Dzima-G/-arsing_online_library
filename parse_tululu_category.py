import requests
import logging
import sys
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathvalidate import sanitize_filepath, sanitize_filename
import os
import json
import argparse

logger = logging.getLogger(__name__)


class BookError(requests.HTTPError):
    """Если отсутствует книга"""
    pass


def check_for_redirect(response):
    if response.history:
        raise BookError


def get_book_page(url):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    return response


def get_categories(response):
    soup = BeautifulSoup(response.text, 'lxml')
    book_category = [' '.join(i.text.split()) for i in (soup.select('#leftnavmenu dt b'))]
    category_url = [i.get('href') for i in (soup.select('#leftnavmenu dt a'))]
    return dict(zip(book_category, category_url))


def get_subcategories(response, subcategory):
    soup = BeautifulSoup(response.text, 'lxml')
    book_subcategories = [' '.join(i.text.split())[1:].strip() for i in (soup.select('#leftnavmenu dd a'))]
    subcategories_url = [i.get('href') for i in (soup.select('#leftnavmenu dd a'))]
    subcategories = dict(zip(book_subcategories, subcategories_url))
    return subcategories.get(subcategory)


def get_book_id(response):
    soup = BeautifulSoup(response.text, 'lxml')
    books_id = [x.get('href').strip('/')[1:] for x in (soup.select('.bookimage a'))]
    return books_id


def parse_book_page(soup, book_id):
    book_title, book_author = [i.strip() for i in (soup.find('h1').text.split('   ::   '))]
    book_image_url = urljoin(f'https://tululu.org/{book_id}',
                             soup.find('div', class_='bookimage').find('img')['src'])
    comments_tags = soup.select('.texts .black')
    book_comments = [item_comment.text for item_comment in comments_tags]
    genres_tags = soup.select('span.d_book a')
    book_genres = [genre.text for genre in genres_tags]
    return {
        'book_title': book_title,
        'book_author': book_author,
        'book_image_url': book_image_url,
        'book_comments': book_comments,
        'book_genre': book_genres
    }


def download_txt(book_id, filename, folder):
    book_url = 'https://tululu.org/txt.php'
    payload = {'id': book_id}
    response = requests.get(book_url, params=payload)
    response.raise_for_status()
    check_for_redirect(response)
    book_text = response.text

    filename = sanitize_filename(f'{filename}.txt')
    fpath = sanitize_filepath(folder)
    os.makedirs(fpath, exist_ok=True)
    file_path = os.path.join(fpath, filename)
    with open(file_path, 'w', encoding="utf-8") as file:
        file.write(book_text)
    return file_path


def download_image(url, folder):
    fpath = sanitize_filepath(folder)
    os.makedirs(fpath, exist_ok=True)
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    filename = sanitize_filename(url.split('/')[-1])
    file_path = os.path.join(folder, filename)
    with open(file_path, 'wb') as file:
        file.write(response.content)


def get_books_content(book_poster, content_json):
    content = {
        "title": book_poster['book_title'],
        "autor": book_poster['book_author'],
        "img_src": f"images/{sanitize_filename(book_poster['book_image_url'].split('/')[-1])}",
        "book_path": f'/books/{book_name}.txt',
    }
    if book_poster['book_comments']:
        content["comments"] = book_poster['book_comments']
    content["genres"] = book_poster['book_genre']
    content_json.append(content)
    return content_json


def get_content_json(content, folder):
    file_path = os.path.join(folder, 'content.json')
    with open(file_path, "w", encoding='utf8') as my_file:
        content_json = json.dumps(content, indent=4, ensure_ascii=False)
        my_file.write(content_json)


def create_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=('''\
Скрипт скачивает книги с сайта https://tululu.org/
--------------------------------------------------
Для скачивания необходимо указать параметры:
--start_page - первая скачиваемая страница
--end_page - страница по которую скачиваются книги (не включительно)
--dest_folder — путь к каталогу с результатами парсинга: картинкам, книгам, JSON.
--skip_imgs — не скачивать картинки
--skip_txt — не скачивать книги'''))

    parser.add_argument('--start_page', default=700, nargs='?', type=int,
                        help='Введите первую скачиваемую страницу')
    parser.add_argument('--end_page', default=None, nargs='?', type=int,
                        help="Введите последнюю скачиваемую страницу (не включительно)")
    parser.add_argument('--dest_folder', default='books',
                        help="Введите каталог куда сохранять результаты парсинга: картинки, книги, JSON")
    parser.add_argument('--skip_imgs', default=False, action='store_true',
                        help="Используйте если необходимо не скачивать картинки")
    parser.add_argument('--skip_txt', default=False, action='store_true',
                        help="Используйте если необходимо не скачивать книги")


    return parser


if __name__ == "__main__":
    input_category = 'Фантастика - фэнтези'
    input_subcategory = 'Научная фантастика'

    books_page_id = []
    content_json = []

    parser = create_parser()
    args = parser.parse_args(sys.argv[1:])

    try:
        home_page = get_book_page('https://tululu.org/')
        categories = get_categories(home_page)
        subcategory_page = get_book_page(urljoin('https://tululu.org/', categories.get(input_category)))
        subcategory_url = get_subcategories(subcategory_page, input_subcategory)
        path = urlparse(subcategory_url).path

        last_page = args.end_page
        if not last_page:
            subcategory_page = get_book_page(subcategory_url)
            soup = BeautifulSoup(subcategory_page.text, 'lxml')
            last_page = int(soup.select('.npage')[-1]['href'].split('/')[2]) + 1

        for page in range(args.start_page, last_page):
            subcategory_page = get_book_page(urljoin('https://tululu.org/', f'{path}/{page}/'))
            books_page_id = books_page_id + get_book_id(subcategory_page)
    except requests.exceptions.HTTPError as error:
        print(error, file=sys.stderr)

    if args.dest_folder:
        os.makedirs(args.dest_folder, exist_ok=True)
        dest_folder = args.dest_folder

    for book_id in books_page_id:
        page_url = urljoin('https://tululu.org/', f'b{book_id}/')

        try:
            book_page = get_book_page(page_url)
            soup = BeautifulSoup(book_page.text, 'lxml')
            book_poster = parse_book_page(soup, book_id)
            book_name = f'{book_id}-я книга. {book_poster["book_title"]}'
            if not args.skip_txt:
                download_txt(book_id, book_name,  dest_folder)
            if not args.skip_imgs:
                download_image(book_poster['book_image_url'],  dest_folder)
        except BookError:
            logger.warning(f'Книга #{book_id} отсутствует в библиотеке.')
            continue
        except requests.exceptions.HTTPError as error:
            print(error, file=sys.stderr)
            continue
        except requests.exceptions.ConnectionError:
            logger.warning(f'Не удается подключиться к серверу! Повторное подключение через 10 секунд.')

        books_content = get_books_content(book_poster, content_json)
        get_content_json(books_content, dest_folder)
