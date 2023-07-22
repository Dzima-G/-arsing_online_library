import requests
import os
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filepath, sanitize_filename
import argparse
import sys
from urllib.parse import urljoin
import logging
import time

logger = logging.getLogger(__name__)


class BookError(requests.HTTPError):
    """Если отсутствует книга"""
    pass


def get_book_page(url):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    return response


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


def check_for_redirect(response):
    if response.history:
        raise BookError


def download_txt(book_id, filename, folder='books/'):
    """Функция для скачивания текстовых файлов.
    Args:
        url (str): Cсылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """
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
    with open(file_path, 'w') as file:
        file.write(book_text)
    return file_path


def download_image(url, folder='images/'):
    fpath = sanitize_filepath(folder)
    os.makedirs(fpath, exist_ok=True)
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    filename = sanitize_filename(url.split('/')[-1])
    file_path = os.path.join(folder, filename)
    with open(file_path, 'wb') as file:
        file.write(response.content)


def create_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=('''\
Скрипт скачивает книги с сайта https://tululu.org/
--------------------------------------------------
Для скачивания необходимо указать параметры:
--start_id - первое значение интервала (id книги)
--end_id - последнее значение интервала (id книги)'''))
    parser.add_argument('--start_id', default=1, nargs='?', type=int,
                        help='Введите первое значение интервала (id книги)')
    parser.add_argument('--end_id', default=11, nargs='?', type=int,
                        help="Введите второе значение интервала (id книги)")
    return parser


if __name__ == "__main__":
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)

    parser = create_parser()
    args = parser.parse_args(sys.argv[1:])
    books_folder_name = 'books'
    url = 'https://tululu.org/'
    sequence_number = 1

    for book_id in range(args.start_id, args.end_id + 1):
        page_url = f'{url}b{book_id}/'
        try:
            book_page = get_book_page(page_url)
            soup = BeautifulSoup(book_page.text, 'lxml')
            book_poster = parse_book_page(soup, book_id)
            book_name = f'{sequence_number}. {book_poster["book_title"]}'
            download_txt(book_id, book_name)
            download_image(book_poster['book_image_url'])
        except BookError:
            logger.warning(f'Книга #{book_id} отсутствует в библиотеке.')
            continue
        except requests.exceptions.HTTPError as error:
            print(error, file=sys.stderr)
        except requests.exceptions.ConnectionError:
            logger.warning(f'Не удается подключиться к серверу! Повторное подключение через 10 секунд.')
            time.sleep(10)
            continue

        print(f'{sequence_number} Название:', book_poster['book_title'])
        print(f'  Автор:', book_poster['book_author'])
        print(f'  Ссылка на обложку книги:', book_poster['book_image_url'])

        if book_poster['book_comments']:
            print(f'  Комментарии:', *book_poster['book_comments'])
        print(f'  Жанр книги:', *book_poster['book_genre'])
        print('')
        sequence_number += 1
