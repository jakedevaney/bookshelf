import argparse
import json
import os
import requests
from difflib import get_close_matches

# manual fetching of environment variables from .env file
def load_env_file(filepath):
    if os.path.exists(filepath):
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env_file(".env")
GOOGLE_BOOKS_API_KEY = os.environ.get("GOOGLE_BOOKS_API_KEY")

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
    parser.add_argument('--new', type=str, help='add a new book to the bookshelf')
    parser.add_argument('--list', action='store_true', help='list all books in the bookshelf')
    parser.add_argument('--remove', type=str, help='remove a book from the bookshelf')
    parser.add_argument('--clear', action='store_true', help='clear the entire bookshelf')
    parser.add_argument('--spr', nargs=2, metavar=('TITLE', 'PAGES'), help='set pages read: TITLE PAGES')
    parser.add_argument('--add', action='store_true', help='when setting pages read, add to the current pages read instead of replacing it')
    parser.add_argument('--subtract', action='store_true', help='when setting pages read, subtract from the current pages read instead of replacing it')
    parser.add_argument('--description', type=str, help='show the description of a book')
    parser.add_argument('--status', type=str, help='show the status of a book')
    parser.add_argument('--complete', type=str, help='mark a book as completed')

    args = parser.parse_args()

    if args.new:
        add_book(args.new)
    elif args.list:
        list_books()
    elif args.remove:
        remove_book(args.remove)
    elif args.spr:
        title, pages = args.spr
        pages = int(pages)
        if args.add:
            set_pages_read(title, pages, mode='add')
        elif args.subtract:
            set_pages_read(title, pages, mode='subtract')
        else:
            set_pages_read(title, pages)
    elif args.status:
        show_status(args.status)
    elif args.description:
        show_description(args.description)
    elif args.complete:
        complete_book(args.complete)
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
            "author(s)": "Unknown",
            "published_date": "Unknown",
            "pages": "Unknown",
            "description": "No description available.",
            "pages_read": 0,
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
        print(f'"{book["title"]}" by {book["author"]} ({book["published_date"]}) - {book["pages_read"]}/{book["pages"]} pages read ({book["pages_read"]/book["pages"]*100:.2f}%) - {"Completed" if book["completed"] else "Not Completed"}')

def find_book(search_term, bookshelf):
    search_term = search_term.lower()
    exact = [book for book in bookshelf if book['title'].lower() == search_term]
    if exact:
        return exact

    substring_matches = [book for book in bookshelf if search_term in book['title'].lower()]
    if substring_matches:
        return substring_matches

    titles = [book['title'] for book in bookshelf]
    close = get_close_matches(search_term, [t.lower() for t in titles], n=3, cutoff=0.6)
    if close:
        return [book for book in bookshelf if book['title'].lower() in close]

    return []

def resolve_single_book(search_term, bookshelf):
    matches = find_book(search_term, bookshelf)

    if not matches:
        print(f'No books found matching "{search_term}".')
        return None 

    if len(matches) == 1:
        return matches[0]

    print(f'Multiple books found matching "{search_term}":')
    for i, book in enumerate(matches, start=1):
        print(f'  {i}. {book["title"]}')
    choice = input('Enter number of the book to select, or press Enter to cancel: ')
    if not choice.isdigit() or not (1 <= int(choice) <= len(matches)):
        print('Selection cancelled.')
        return None
    return matches[int(choice) - 1]

def remove_book(title):
    bookshelf = load_books()
    book = resolve_single_book(title, bookshelf)
    if book is None:
        return
    bookshelf.remove(book)
    save_books(bookshelf)
    print(f'Removed "{book["title"]}" from the bookshelf.')

def set_pages_read(title, pages, mode='set'):
    bookshelf = load_books()
    book = resolve_single_book(title, bookshelf)
    if book is None:
        print(f'No book found matching "{title}".')
        return

    current = book.get('pages_read', 0)

    if mode == 'add':
        new_pages = current + pages
    elif mode == 'subtract':
        new_pages = max(0, current - pages)
    else:
        new_pages = pages

    book['pages_read'] = new_pages

    if isinstance(book['pages'], int) and new_pages >= book['pages']:
        book['completed'] = True
        book['pages_read'] = book['pages']
        print(f'Set pages read for "{book["title"]}" to {book["pages"]}. Marked as completed.')
        save_books(bookshelf)
        return
    save_books(bookshelf)
    print(f'Set pages read for "{book["title"]}" to {new_pages}.')

def show_description(title):
    bookshelf = load_books()
    book = resolve_single_book(title, bookshelf)
    if book is None:
        print(f'No book found matching "{title}".')
        return
    description = book.get('description', 'No description available.')
    print(f'"{book["title"]}" by {book["author"]}:\n{description}')

def show_status(title):
    bookshelf = load_books()
    book = resolve_single_book(title, bookshelf)
    if book is None:
        print(f'No book found matching "{title}".')
        return
    percentage = (book['pages_read'] / book['pages'] * 100) if isinstance(book['pages'], int) and book['pages'] > 0 else "Unknown"
    print(f'Status of "{book["title"]}" by {book["author"]}:')
    print(f'Read {book["pages_read"]}/{book["pages"]} pages ({percentage:.2f}%).')
    print(f'Completed: {"Yes" if book["completed"] else "No"}')


def complete_book(title):
    bookshelf = load_books()
    book = resolve_single_book(title, bookshelf)
    if book is None:
        return
    if book['completed']:
        print(f'"{book["title"]}" is already marked as completed.')
        print('Would you like to mark it as not completed? (y/n)')
        response = input().lower()
        if response == 'y':
            book['completed'] = False
            save_books(bookshelf)
            print(f'Marked "{book["title"]}" as not completed.')
        return
    book['completed'] = True
    save_books(bookshelf)
    print(f'Marked "{book["title"]}" as completed.')

def clear_bookshelf():
    print('Are you sure you want to clear the entire bookshelf? This action cannot be undone. (y/n)')
    response = input().lower()
    if response == 'y':
        save_books([])
        print('Cleared the bookshelf.')
    else:
        print('Clearing cancelled.')

def fetch_book_info(title):
    url = "https://www.googleapis.com/books/v1/volumes"
    try:
        response = requests.get(
            url,
            params={'q': title, 'key': GOOGLE_BOOKS_API_KEY},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return None

    if "items" not in data:
        return None

    # Look for the first result that actually has author info
    for item in data["items"]:
        book = item["volumeInfo"]
        if book.get("authors"):
            return {
                "title": book.get("title", title),
                "author": ", ".join(book["authors"]),
                "published_date": book.get("publishedDate", "Unknown"),
                "pages": book.get("pageCount", "Unknown"),
                "description": book.get("description", "No description available."),
                "pages_read": 0,
                "completed": False
            }

    # fallback: no result had author info, just use the first one
    book = data["items"][0]["volumeInfo"]
    return {
        "title": book.get("title", title),
        "author": ", ".join(book.get("authors", ["Unknown"])),
        "published_date": book.get("publishedDate", "Unknown"),
        "pages": book.get("pageCount", "Unknown"),
        "description": book.get("description", "No description available."),
        "pages_read": 0,
        "completed": False
    }

if __name__ == '__main__':
    main()