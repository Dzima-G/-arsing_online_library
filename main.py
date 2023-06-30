import requests
import os


def save_book(data_book, book_name, books_folder_name):
    file_path = os.path.join(books_folder_name, book_name)
    with open(file_path, 'w') as file:
        file.write(data_book)


def get_books(books_folder_name, first_book_id, last_book_id):
    books_id = [i for i in range(first_book_id, last_book_id + 1)]
    for book_id in books_id:
        payload = {'id': book_id}
        url = 'https://tululu.org/txt.php'
        response = requests.get(url, params=payload)
        response.raise_for_status()
        save_book(response.text, f'id_{book_id}.txt', books_folder_name)


if __name__ == "__main__":
    books_folder_name = 'books'
    os.makedirs(books_folder_name, exist_ok=True)
    get_books(books_folder_name, 1, 10)
