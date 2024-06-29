from src.config import Config
from pprint import pprint

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

class Condition:
    def __init__(self, name: str, thrift_price: float, available: int, list_price: float=None):
        self.name = name
        self.thrift_price = thrift_price
        self.available = available
        self.list_price = list_price
        
    def __str__(self):
        return f"Condition: {self.name} - Price: {self.thrift_price} - Available: {self.available}"
    
    def to_dict(self):
        return {
            'name': self.name,
            'thrift_price': self.thrift_price,
            'available': self.available,
            'list_price': self.list_price
        }
            
class Edition:
    def __init__(self, isbn: int, form: str, pub_date: str, language: str, publisher: str, conditions: list[Condition], isbn13: int):
        self.isbn = isbn
        self.form = form
        self.isbn13 = isbn13
        self.pub_date = pub_date #TODO convert to datetime
        self.language = language
        self.publisher = publisher
        self.conditions = conditions

    def __str__(self):
        return f"Edition: {self.title} by {self.author} - Format: {self.form} - Author: {self.author} - ISBN: {self.isbn}"
    
    def to_dict(self):
        return {
            'isbn': self.isbn,
            'form': self.form,
            'isbn13': self.isbn13,
            'pub_date': self.pub_date,
            'language': self.language,
            'publisher': self.publisher,
            'conditions': [c.to_dict() for c in self.conditions]
        }

class Book:
    def __init__(self, uid: int, title: str, author: str, url: str, editions: list[Edition]=[]):
        self.uid = uid
        self.title = title
        self.author = author
        self.url = url
        self.editions = editions
        self.editions_url = f"{url.split('/#')[0]}/all-editions/"
        
    def add_edition(self, edition):
        if not isinstance(edition, Edition):
            raise ValueError("Edition must be an instance of the Edition class.")
        self.editions.append(edition)

    def __str__(self):
        return f"Book: {self.title} by {self.author} - {len(self.editions)} editions available."
            
    
    def to_dict(self):
        return {
            'uid': self.uid,
            'title': self.title,
            'author': self.author,
            'url': self.url,
            'editions': [e.to_dict() for e in self.editions]
        }

def initialize_driver(browser: str, debug: bool) -> webdriver:
    '''Initializes the webdriver based on the browser argument.'''
    driver = None
    match browser:
        case 'chrome':
            options = webdriver.ChromeOptions()
            if not debug:
                options.add_argument('--headless')
            driver = webdriver.Chrome(options=options)
        case 'firefox':
            options = webdriver.FirefoxOptions()
            if not debug:
                options.add_argument('--headless')
            driver = webdriver.Firefox(options=options)
    return driver

def scrape_editions(driver: webdriver, book: Book, **kwargs) -> list[Edition]:
    '''Scrapes the editions of a book and returns a list of Edition objects.'''
    print(f"Attempting to visit: {book.editions_url}") if kwargs['verbose'] else None
    driver.get(book.editions_url)
    el_header = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".AllEditionsHeader"))   #Presence or visibility
    )

    el_editions = driver.find_elements(By.CSS_SELECTOR, ".AllEditionsItem-work")
    editions = []
    for el in el_editions:
        details = {}
        for detail in el.find_elements(By.CSS_SELECTOR, '.AllEditionsItem-details-item, .AllEditionsItem-details-item.hidden'):   #Extract details into dict
            text = detail.get_attribute('textContent')
            if text == '': #Skip empty elements
                print("Skipping empty element.")
                continue
            name = text.split(':')[0].lstrip().lower().replace(' ', '_')
            value = text.split(':')[1].lstrip().lower()
            details[name] = value
            #print(f"Name: {name} - Value: {value}") if kwargs['verbose'] else None
            
        conditions = []
        try:
            el_conditions = Select(el.find_element(By.CSS_SELECTOR, ".AllEditions-selectCondition"))
        except:
            continue
        for condition in el_conditions.options:
            name = condition.text.split(' $')[0]
            el_conditions.select_by_visible_text(condition.text)
            el_cart = el.find_element(By.CSS_SELECTOR, ".AllEditionsItem-addToCart")
            el_thrift_price = el.find_element(By.CSS_SELECTOR, ".AllEditionsItem-amount")
            available: int = None
            list_price: float = None
            try:            #Extract available quantity
                el_available = el.find_element(By.CSS_SELECTOR, ".AllEditionsItem-quantity")
                available = int(el_available.text.split(' ')[0])
            except:
                el_available = el.find_element(By.CSS_SELECTOR, ".AllEditionsItem-quantity-available.AllEditions-redFont")
                available = el_available.text.split(' ')[3]
            
            try:            #Extract list price
                el_list_price = el.find_element(By.CSS_SELECTOR, ".AllEditionsItem-savings-list-price s")
                list_price = el_list_price.text.split('$')[1]
            except:
                pass
            
            conditions.append(Condition(name=name, thrift_price=el_thrift_price.text, list_price=list_price, available=available))
            
        #pprint(details) if kwargs['verbose'] else None
        edition = Edition(
            isbn=int(details.get('isbn', 0)), 
            form=details.get('format', None), 
            pub_date=details.get('release_date', None), 
            language=details.get('language', None), 
            publisher=details.get('publisher', None), 
            conditions=conditions, 
            isbn13=int(details.get('isbn13', 0))
        )
        editions.append(edition)
    print('\n')
    return editions

def scrape_books(driver: webdriver, config: Config, **kwargs) -> list[Book]:
    driver.get("https://www.thriftbooks.com/list/")
    el = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".WishList-Root"))
    )
    list_items = el.find_elements(By.CSS_SELECTOR, ".WishList-ListItem")
    print(f"Parsed {len(list_items)} books in wishlist, grabbing list-price.") if kwargs['verbose'] else None

    #Unpack list_items into a list of directives for scraping {title_str: title, href_str: href}
    scrape_directives = []
    for item in list_items:
        title = item.find_element(By.CSS_SELECTOR, ".WishList-ItemTitle a").text
        href = item.find_element(By.CSS_SELECTOR, ".WishList-ItemTitle a").get_attribute('href')
        scrape_directives.append({'title': title, 'href': href})

    books = []
    for item in scrape_directives:
        driver.get(item['href'])
        uid = int(item['href'].split('/')[-2])
        el_author = driver.find_element(By.CSS_SELECTOR, ".WorkMeta-authors")
        author = ', '.join([a.text for a in el_author.find_elements(By.XPATH, ".//a")]) #CSV of authors
        
        print(f"ID: {uid} - Name: {item['title']} - Author: {author}") if kwargs['verbose'] else None
        book = Book(uid, item['title'], author, item['href'])
        
        editions = scrape_editions(driver, book, **kwargs)
        for e in editions:
            book.add_edition(e)
        
        books.append(book)
    return books

def login(driver: webdriver, email: str, password: str, **kwargs):
    '''Logs into the Thriftbooks website using the provided credentials.'''
    driver.get("https://www.thriftbooks.com/account/login/")
    el = driver.find_element(By.CSS_SELECTOR, "#ExistingAccount_EmailAddress")
    assert el.is_enabled()
    el.send_keys(email)

    el = driver.find_element(By.CSS_SELECTOR, "#ExistingAccount_Password")
    assert el.is_enabled()
    el.send_keys(password)
    el.submit()
    el = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".HomepageContentBlocks-Container"))
    )
    print("Logged in successfully.") if kwargs['verbose'] else None