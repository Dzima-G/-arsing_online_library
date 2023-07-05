import requests
import os
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filepath, sanitize_filename
import argparse
import sys
from urllib.parse import urlsplit, urlunsplit, urljoin


def get_books(url, book_id):
    payload = {'id': book_id}
    response = requests.get(url, params=payload)
    response.raise_for_status()
    check_for_redirect(response)
    return response.text


def parse_book_page(url):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    return response


def get_page_data(response):
    soup = BeautifulSoup(response.text, 'lxml')
    page_data = soup.find('h1').text.split('   ::   ')
    image_url = urljoin('https://tululu.org/', soup.find('div', class_='bookimage').find('img')['src'])
    page_data.append(image_url)
    comments_tag = soup.find_all('div', class_='texts')
    comments_list = []
    if len(comments_tag) > 0:
        for item_comment in comments_tag:
            comment_tag = item_comment.find_all('span')
            comment_text = comment_tag[0].text
            comments_list.append(comment_text)
    page_data.append(comments_list)
    genres_tag = soup.find('span', class_='d_book')
    genres_tag = genres_tag.find_all('a')
    genres_list = []
    if len(genres_tag) > 0:
        for item_genre in genres_tag:
            genre_text = item_genre.text
            genres_list.append(genre_text)
    page_data.append(genres_list)

    return page_data


def check_for_redirect(response):
    if len(response.history) > 0:
        raise requests.HTTPError


def download_txt(url, filename, folder='books/'):
    """Функция для скачивания текстовых файлов.
    Args:
        url (str): Cсылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """
    book_id = urlsplit(url).path.strip('/')[1:]
    url_parts = list(urlsplit(url))
    url_parts[2] = 'txt.php'
    book_url = urlunsplit(url_parts)
    book_data = get_books(book_url, book_id)
    filename = sanitize_filename(f'{filename}.txt')
    fpath = sanitize_filepath(folder)
    os.makedirs(fpath, exist_ok=True)
    file_path = os.path.join(fpath, filename)
    with open(file_path, 'w') as file:
        file.write(book_data)
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


def createparser():
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
    parser = createparser()
    args = parser.parse_args(sys.argv[1:])
    books_folder_name = 'books'
    url = 'https://tululu.org/'
    sequence_number = 1
    for book_id in range(args.start_id, args.end_id + 1):
        page_url = f'{url}b{book_id}/'
        try:
            book_page_data = parse_book_page(page_url)
        except requests.HTTPError:
            continue
        book_poster = get_page_data(book_page_data)
        book_name = f'{sequence_number}. {book_poster[0]}'
        try:
            download_txt(page_url, book_name)
            download_image(book_poster[2])
        except requests.HTTPError:
            continue

        print(f'{sequence_number} Название:', book_poster[0])
        print(f'  Автор:', book_poster[1])
        print(f'  Ссылка на обложку книги:', book_poster[2])
        if len(book_poster[3]) > 0:
            print(f'  Комментарии:', *book_poster[3])
        print(f'  Жанр книги:', *book_poster[4])
        print('')
        sequence_number += 1
