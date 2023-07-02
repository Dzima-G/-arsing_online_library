import requests
import os
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filepath, sanitize_filename


def get_books(url):
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    check_for_redirect(response)
    return response.text


def get_book_name(url):
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


if __name__ == "__main__":
    books_folder_name = 'books'
    url = 'https://tululu.org/'
    i = 1
    for book_id in range(1, 11):
        book_url = f'{url}/txt.php?id={book_id}'
        page_url = f'{url}/b{book_id}/'
        try:
            book_poster = get_book_name(page_url)
            book_name = f'{i}. {book_poster[0]}'
            download_txt(book_url, book_name)
            download_image(book_poster[2])
        except requests.HTTPError:
            # print("Книга отсутствует с id ==", book_id)
            continue
        print(f'Заголовок:{book_name}', book_poster[2], book_poster[3], book_poster[4], '', sep='\n', end='\n')
        i += 1
