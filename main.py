import requests
import os
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filepath, sanitize_filename
import argparse
import sys


def get_books(url):
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    check_for_redirect(response)
    return response.text


def parse_book_page(url):
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    check_for_redirect(response)
    soup = BeautifulSoup(response.text, 'lxml')
    page_data = soup.find('h1').text.split('   ::   ')
    image_url = f"https://tululu.org/{soup.find('div', class_='bookimage').find('img')['src']}"
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
    if response.status_code == 302:
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
    book_data = get_books(url)
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


def createParser():
    parser = argparse.ArgumentParser(description='Введите интервал через пробел для скачивания книг')
    parser.add_argument('--start_id', default=1, nargs='?', type=int, help="Введите первое значение интервала")
    parser.add_argument('--end_id', default=5, nargs='?', type=int, help="Введите второе значение интервала")
    return parser

if __name__ == "__main__":
    parser = createParser()
    namespace = parser.parse_args(sys.argv[1:])
    books_folder_name = 'books'
    url = 'https://tululu.org/'
    i = 1
    for book_id in range(namespace.start_id, namespace.end_id + 1):
        book_url = f'{url}/txt.php?id={book_id}'
        page_url = f'{url}/b{book_id}/'
        try:
            book_poster = parse_book_page(page_url)
            book_name = f'{i}. {book_poster[0]}'
            download_txt(book_url, book_name)
            download_image(book_poster[2])
        except requests.HTTPError:
            continue

        print(f'{i} Название:', book_poster[0])
        print(f'  Автор:', book_poster[1])
        print(f'  Ссылка на обложку книги:', book_poster[2])
        if len(book_poster[3]) > 0:
            print(f'  Комментарии:', *book_poster[3])
        print(f'  Жанр книги:', *book_poster[4])
        print('')
        i += 1
