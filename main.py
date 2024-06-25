import yaml
import os
import argparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Config:
    def __init__(self, email, password, price_threshold, notification_rate, notification_methods, notification_email, notification_phone):
        self.email = email
        self.password = password
        self.price_threshold = price_threshold
        self.notification_rate = notification_rate
        self.notification_methods = notification_methods
        self.notification_email = notification_email
        self.notification_phone = notification_phone

    @classmethod
    def read_file(cls, filename):
        with open(filename, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def write_file(self, filename):
        with open(filename, 'w') as f:
            yaml.safe_dump(self.__dict__, f)

class Book:
    def __init__(self, uid, title, author, thrift_price, url, list_price):
        self.uid = uid
        self.title = title
        self.author = author
        self.thrift_price = thrift_price
        self.list_price = list_price
        self.url = url

    def __str__(self):
        return f"Book: {self.title} by {self.author} - Thrift price: ${self.thrift_price} - List price: ${self.list_price}"



def load_configs() -> list[Config]:
    '''Locates all configuration files in the user's home directory. If the directory does not exist, it is created, and None is returned. Returns data as Config objects.'''
    if 'HOME' not in os.environ:
        raise ValueError("HOME environment variable not found")
    configs = []
    config_dir = os.path.join(os.environ['HOME'], '.config', 'bookthrifter')
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        return None
    for path in os.listdir():
        if path.endswith('.conf'):
            data = Config.read_file(path)
            configs.append(data)
    return configs

def scrape_books(driver: webdriver, config: Config, **kwargs) -> list[Book]:
    driver.get("https://www.thriftbooks.com/list/")
    el = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".WishList-Root"))
    )
    list_items = el.find_elements(By.CSS_SELECTOR, ".WishList-ListItem")
    print(f"Parsed {len(list_items)} books in wishlist, grabbing list-price.") if kwargs['verbose'] else None

    books = []
    for item in list_items:
        link = item.find_element(By.CSS_SELECTOR, ".WishList-ItemTitle a").get_attribute('href')
        driver.get(link)
        uid = link.split('/')[-2]
        el_title = driver.find_element(By.CSS_SELECTOR, ".WorkMeta-title")
        title = el_title.text
        print(f"Scraping book with ID: {uid} - Name: {title}") if kwargs['verbose'] else None
        el_price = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".WorkSelector-price"))
        )
        thrift_price = float(el_price.text.split('$')[1])
        print(f"Thrift price: ${thrift_price}") if kwargs['verbose'] else None
        el_price = driver.find_element(By.CSS_SELECTOR, ".WorkSelector-strike")
        list_price = float(el_price.text.split('$')[1])
        print(f"List price: ${list_price}\n") if kwargs['verbose'] else None

        book = Book(uid, title, author, thrift_price, link, list_price)
        books.append(book)

    return books
            

def execute(config: Config, **kwargs):
    '''Executes the program with the given configuration.'''
    driver = None
    match kwargs['browser']:
        case 'chrome':
            options = webdriver.ChromeOptions()
            driver = webdriver.Chrome(options=options)
        case 'firefox':
            options = webdriver.FirefoxOptions()
            driver = webdriver.Firefox(options=options)

    driver.get("https://www.thriftbooks.com/account/login/")

    el = driver.find_element(By.CSS_SELECTOR, "#ExistingAccount_EmailAddress")
    assert el.is_enabled()
    el.send_keys(config.email)

    el = driver.find_element(By.CSS_SELECTOR, "#ExistingAccount_Password")
    assert el.is_enabled()
    el.send_keys(config.password)
    el.submit()
    el = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".HomepageContentBlocks-Container"))
    )
    print("Logged in successfully.") if kwargs['verbose'] else None

    books = scrape_books(driver, config, **kwargs)

    driver.quit()
    return

def main(args: argparse.Namespace):
    if args.version:
        print("Bookthrifter v0.1")
        return
    if args.verbose:
        print("Verbose mode enabled.")
    if args.config:
        config = Config.read_file(args.config)
        execute(config)
        return

    configs = load_configs()
    print(f"Load {len(configs)} configuration files.") if args.verbose else None
    if configs is None:
        print("No configuration files found. Please create a configuration file in the ~/.config/bookthrifter directory.")
        return
    for c in configs:
        execute(c, browser=args.browser, dry_run=args.dry_run, verbose=args.verbose, debug=args.debug)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Bookthrifter: A tool to monitor book prices and notify you when they drop.")
    parser.add_argument('--config', type=str, help="Path to configuration file.")
    parser.add_argument('--browser', type=str, default='chrome', help="Run the programusing the specified browser, e.g. 'chrome', 'firefox'.")
    parser.add_argument('--dry-run', action='store_true', default=False, help="Run the program without sending notifications.")
    parser.add_argument('--version', action='store_true', help="Print the version of the program.")
    parser.add_argument('--verbose', action='store_true', help="Print verbose output.")
    parser.add_argument('--debug', action='store_true', help="Run in debug mode, showing the browser window.")
    main(parser.parse_args())