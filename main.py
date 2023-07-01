import requests
import os
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filepath, sanitize_filename


def get_books(url):
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    check_for_redirect(response)
    return response.text


def check_for_redirect(response):
    if response.status_code == 302:
        raise requests.HTTPError


def get_book_name(book_id):
    url = f'https://tululu.org/b{book_id}'
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    soup = BeautifulSoup(response.text, 'lxml')
    title_tag = soup.find('h1')
    title_text = title_tag.text.split('   ::   ')
    return title_text[0], title_text[1]


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


if __name__ == "__main__":
    books_folder_name = 'books'
    url = 'https://tululu.org/'

    for i in range(1, 2):
        book_url = f'{url}/txt.php?id={i}'
        try:
            book_name = get_book_name(i)[0]
            print(book_name)
            download_txt(book_url, book_name)
        except requests.HTTPError:
            print("Книга отсутствует с id ==", i)
            continue
