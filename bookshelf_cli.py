import argparse
import json
import os
import requests

# Storing the bookshelf data in a JSON file
DATA_FILE = 'bookshelf.json'

def load_books():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_books(books):
    with open(DATA_FILE, 'w') as f:
        json.dump(books, f, indent=2)

# Main function to handle command-line arguments
def main():
    parser = argparse.ArgumentParser(description='books CLI')
    parser.add_argument('--add', type=str, help='add a book to the bookshelf')
    parser.add_argument('--list', action='store_true', help='list all books in the bookshelf')
    parser.add_argument('--remove', type=str, help='remove a book from the bookshelf')
    parser.add_argument('--clear', action='store_true', help='clear the entire bookshelf')

    args = parser.parse_args()

    if args.add:
        add_book(args.add)
    elif args.list:
        list_books()
    elif args.remove:
        remove_book(args.remove)
    elif args.clear:
        clear_bookshelf()
    else:
        parser.print_help()

def add_book(title):
    bookshelf = load_books()

    if any(book['title'].lower() == title.lower() for book in bookshelf):
        print(f'"{title}" is already in the bookshelf.')
        return

    book_info = fetch_book_info(title)

    if book_info is None:
        print(f'Could not fetch information for "{title}". Adding with title only.')
        book_info = {
            "title": title,
            "author": "Unknown",
            "published_date": "Unknown",
            "pages": "Unknown",
            "completed": False
        }

    bookshelf.append(book_info)
    save_books(bookshelf)
    print(f'Added "{title}" to the bookshelf.')

def list_books():
    bookshelf = load_books()
    if not bookshelf:
        print('The bookshelf is empty.')
        return
    for book in bookshelf:
        print(book)

def remove_book(title):
    bookshelf = load_books()
    
    matching_book = next(
        (book for book in bookshelf if book['title'].lower() == title.lower()),
        None
    )

    if matching_book is None:
        print(f'"{title}" is not in the bookshelf.')
        return

    bookshelf.remove(matching_book)
    save_books(bookshelf)
    print(f'Removed "{title}" from the bookshelf.')

def clear_bookshelf():
    print('Are you sure you want to clear the entire bookshelf? This action cannot be undone. (yes/no)')
    response = input().lower()
    if response == 'yes':
        save_books([])
        print('Cleared the bookshelf.')
    else:
        print('Clearing cancelled.')

def fetch_book_info(title):
    url = "https://www.googleapis.com/books/v1/volumes"
    try:
        response = requests.get(
            url,
            params={'q': title},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return None

    if "items" not in data:
        return None

    book = data["items"][0]["volumeInfo"]
    return {
        "title": book.get("title", title),
        "author(s)": ", ".join(book.get("authors", ["Unknown"])),
        "published_date": book.get("publishedDate", "Unknown"),
        "pages": book.get("pageCount", "Unknown"),
        "completed": False
    }

if __name__ == '__main__':
    main()