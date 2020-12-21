import argparse
import requests

from bs4 import BeautifulSoup

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape Yahoo Finance for articles related to a Stock symbol')
    parser.add_argument('symbol', metavar='S', type=str, help='The stock symbol to be scraped for')

    args = parser.parse_args()
    print("running webscrape for " + args.symbol)

    URL = "https://finance.yahoo.com/quote/" + args.symbol + "?p=" + args.symbol
    press_URL = "https://finance.yahoo.com/quote/" + args.symbol + "/press-releases?p=" + args.symbol

    page = requests.get(URL)
    press_page = requests.get(press_URL)
    print("Checking on: " + press_URL)

    soup = BeautifulSoup(page.content, 'html.parser')
    press_soup = BeautifulSoup(page.content, 'html.parser')

    press_results = press_soup.find_all(id='Main')
    for result in press_results:
        press_elements = result.find_all('li', class_='js-stream-content Pos(r)')
        elems = 0
        for elem in press_elements:
            elems += 1
            title_elem = elem.find('h3', class_='Mb(5px)')

            print(title_elem)
        print(elems)