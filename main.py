import argparse
import time
from pprint import pprint

from src.database import data_dir, write_books_json, read_books_json
from src.scrape import login, scrape_books, initialize_driver
from src.config import Config, load_configs
from src.prices import check_record_prices

#TODO check against language whitelist or blacklist in profile  


def execute(config: Config, **kwargs):
    '''Given a configuration, execute the scraping, analysis, and notification process.'''
    #loaded_books: list[Book] = read_books_json()
    #check_record_prices(loaded_books)
    #quit()
    
    
    #previous_books = read_books_json()
    #if previous_books == []:
        #print("No previous data found, will not compare prices or notify on this run.")    
    driver = initialize_driver(kwargs['browser'], kwargs['debug'])
    login(driver, config.email, config.password, **kwargs)
    books = scrape_books(driver, config, **kwargs)
    #write_books_json(books)
    #loaded_books: list[Book] = read_books_json()
    #PLAN: maintain a list of ISBNs and their min and max prices, and compare to the current list of books ISBNs and prices
    check_record_prices(books)
    
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
    if args.debug:
        args.verbose = True
        print("Debug mode enabled.")
        
    configs = load_configs()
    print(f"Loaded {len(configs)} configuration files.") if args.verbose else None
    if configs == [] or configs == None:
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