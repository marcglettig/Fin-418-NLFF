import argparse
import requests
import re
import os
from bs4 import BeautifulSoup

from article import Article


def main():
    parser = argparse.ArgumentParser(description='Scrape on PR Newswire for articles related to a Stock')
    parser.add_argument('symbol', metavar='S', type=str, help='The stock symbol or Company name to be scraped for')

    args = parser.parse_args()
    print("running webscrape for " + args.symbol)

    URL = "https://www.prnewswire.com/search/news/?keyword=" + args.symbol
    print("Checking on: " + URL)
    page_number = 0

    # Creating folder structure and setting output path
    module_path = os.path.dirname(os.path.realpath(__file__))
    output_dir = os.path.join(module_path, 'data/' + args.symbol)
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    article_number = 0

    # Loop over articles until no more found.
    while True:
        page_number += 1
        try:
            page = requests.get(URL + '&pagesize=25&page=' + str(page_number))
        except ValueError:
            print('URL not found')
            break

        soup = BeautifulSoup(page.content, 'html.parser')
        press_results = soup.find(class_='container search-results-text')
        press_results = press_results.find_all('a', 'news-release', 'href')
        print("result on page: " + str(len(press_results)))
        if len(press_results) == 0:
            break

        # Checking every single article in search results
        for result in press_results:
            print("Checking: " + result['href'])

            # Initializing article information values
            URL_ = "https://www.prnewswire.com" + result['href']
            page_ = requests.get(URL_)
            soup_ = BeautifulSoup(page_.content, 'html.parser')
            info = soup_.find(class_='container release-header')
            title = info.find('h1')
            subtitle = info.find('p', 'subtitle')
            date = info.find('p', 'mb-no')

            # Stripping additional content from webpage and only keeping text paragraphs
            body = soup_.find(class_='release-body container')
            paragraphs = body.find_all('p')

            # Cumulatively building article content string
            clean_body = ''
            for para in paragraphs:
                if para.string:
                    clean_body += para.string

            art = Article(title, subtitle, date, clean_body)

            # Saving the article to the specified output path
            output_path = os.path.join(output_dir, 'article_' + str(article_number) + '.txt')
            article_number += 1
            with open(output_path, 'w+') as article_file:
                article_file.write(str(art))


if __name__ == '__main__':
    main()
