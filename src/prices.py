from src.database import write_record_prices, read_record_prices
from src.scrape import Book

from pprint import pprint

def check_record_prices(books: list[Book]):
    '''Check the high and low price of a book, by reading from record prices "database". For each new record, write it to the database.
    Replace the old record with the new record if the price is lower or higher.
    Return a dict of the high and low prices, with uid as the key.'''
    records: dict[int, list[float]] = read_record_prices()
    for book in books:
        print(f"Checking book: {book.title}")
        for edition in book.editions:
            isbn = str(edition.isbn)
            print(book.title, isbn)
            for condition in edition.conditions:    #TODO add a check for the condition name, e.g. "Good" or "Acceptable"
                price = condition.thrift_price
                print(records.keys())
                if isbn not in records.keys():
                    print(f"New record found: {isbn} - {price}")
                    records[isbn] = [price, price]
                else:
                    min_price, max_price = records[isbn]
                    if price < min_price:
                        min_price = price
                    if price > max_price:
                        max_price = price
                    records[isbn] = [min_price, max_price]
    pprint(records)
    write_record_prices(records)
    