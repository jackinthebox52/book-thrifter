#Tools for writing object to json "database"
import json
import os
import datetime
from typing import List, Dict

from src.scrape import Book, Edition, Condition

def data_dir():
    '''Locate and return the data directory for the application. If it does not exist, create it.'''
    if 'HOME' not in os.environ:
        raise ValueError("HOME environment variable not found")
    data_dir = os.path.join(os.environ['HOME'], '.bookthrifter', 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir

#RECORD PRICES
def record_prices_filepath():
    '''Return the filepath for the record prices database.'''
    return os.path.join(data_dir(), 'record_prices.json')
    
def read_record_prices() -> Dict[int, List[float]]:
    '''Read the record prices database from the data directory. Returns a dict of uid (int) keys and high/low price (float) values (Dollars only).'''
    filepath = record_prices_filepath()
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)
    
def write_record_prices(data: Dict[int, List[float]]):
    filepath = record_prices_filepath()
    print(data)
    print(filepath)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)
#END RECORD PRICES 


#BOOKS JSON
def current_datetime_filepath():
    '''Compile a filepath with a datetime timestamp, using the current date and time.'''
    filename = f"scrape-{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    return os.path.join(data_dir(), filename)

def datetime_filepath_to_date(filepath: str) -> datetime.datetime:
    '''Extract the datetime from a filepath and return it as a datetime object.'''
    return datetime.datetime.strptime(filepath.split('/')[-1].split('.json')[0].split('_')[-1], '%Y-%m-%d_%H-%M-%S')
    
def write_books_json(data: list[Book]):
    '''Write a Book object to a JSON file in the data directory, with a timestamped filename.'''
    books_dict = [b.to_dict() for b in data]
    filepath = current_datetime_filepath()
    with open(filepath, 'w') as f:
        json.dump(books_dict, f, indent=4)
        
def read_books_json() -> list[Book]:
    '''Read a Book object from the most recent JSON file.'''
    data_files = [os.path.join(data_dir(), f) for f in os.listdir(data_dir()) if f.startswith('scrape-')]
    if data_files == []:
        return []
    recent_file = max([os.path.join(data_dir(), f) for f in data_files], key=os.path.getctime)
    with open(recent_file, 'r') as f:
        data = json.load(f)
        return [obj_handler(b) for b in data]

def obj_handler(d):
    if 'isbn' in d:  # or another unique key for Edition
        conditions = [Condition(**c) for c in d.pop('conditions', [])]
        return Edition(conditions=conditions, **d)
    elif 'condition' in d:  # or another unique key for Condition
        return Condition(**d)
    else:
        editions = [obj_handler(e) for e in d.pop('editions', [])]
        return Book(editions=editions, **d)
#END BOOKS JSON