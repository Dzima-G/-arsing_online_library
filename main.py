import requests
import os
from bs4 import BeautifulSoup


def save_book(data_book, book_name, books_folder_name):
    file_path = os.path.join(books_folder_name, book_name)
    with open(file_path, 'w') as file:
        file.write(data_book)


def get_books(book_id):
    payload = {'id': book_id}
    url = 'https://tululu.org/txt.php'
    response = requests.get(url, params=payload, allow_redirects=False)
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
    print('Заголовок:', title_text[0])
    print('Автор:', title_text[1])


if __name__ == "__main__":
    books_folder_name = 'books'
    os.makedirs(books_folder_name, exist_ok=True)
    for i in range(1, 2):
        try:
            book_data = get_books(i)
            get_book_name(i)
        except requests.HTTPError:
            print("Книга отсутствует с id ==", i)
            continue
        # save_book(book_data, f'id_{i}.txt', books_folder_name)
