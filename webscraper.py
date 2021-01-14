import argparse
import requests
import re
import pandas as pd
import json
import os
import selenium
from selenium import webdriver
import time
from PIL import Image
import io
import preprocessing
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from article import Article


def newswire_scrape(symbol):
    '''
    webscraping function going through articles related to ticker symbol passed and stores textual results in folder.
    :param symbol: String of ticker symbol
    :return: Saves textual data direclty to the folder
    '''
    URL = "https://www.prnewswire.com/search/news/?keyword=" + symbol
    print("Checking on: " + URL)
    page_number = 0

    # Creating folder structure and setting output path
    module_path = os.path.dirname(os.path.realpath(__file__))
    output_dir = os.path.join(module_path, 'data/articles/' + symbol)
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

            info = clean_missing(title, subtitle, date)
            art = Article(preprocessing.clean_text(info[0]), preprocessing.clean_text(info[1]), info[2], preprocessing.clean_text(clean_body))

            # Saving the article to the specified output path
            output_path = os.path.join(output_dir, 'article_' + str(article_number) + '.txt')
            article_number += 1
            with open(output_path, 'w+') as article_file:
                json.dump(art.to_dict(), article_file)


def yahoo_scrape(symbol):
    '''
    Webscraper for the yahoo finance press reports page, goes through all linked reports of the ticker symbol
    :param symbol: String of the ticker symbol
    :return: Saves the reports directly in a folder
    '''
    driver = webdriver.Chrome(ChromeDriverManager().install())

    opts = webdriver.ChromeOptions()
    opts.headless = True
    URL = 'https://finance.yahoo.com/quote/'+ symbol + '/press-releases?p=' + symbol
    print("Checking on: " + URL)
    page_number = 0

    # Creating folder structure and setting output path
    module_path = os.path.dirname(os.path.realpath(__file__))
    output_dir = os.path.join(module_path, 'data/articles/' + symbol)
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    article_number = 0

    page_number += 1
    try:
        page = driver.get(URL)
    except ValueError:
        print('URL not found')
    driver.maximize_window()

    articles = driver.find_elements_by_xpath('//h3[@class="Mb(5px)"]')
    article_links = [art.find_element_by_xpath(".//a").get_attribute('href') for art in articles]

    for link in article_links:
        article_number += 1
        driver.get(link)
        title = driver.find_element_by_xpath('//header[@class = "caas-header"]')
        date = driver.find_element_by_xpath('//time')
        content_wrapper = driver.find_element_by_xpath('//div[@class="caas-content-wrapper"]')
        try:
            read_more = driver.find_element_by_xpath(
                '//button[@class="link rapid-noclick-resp caas-button collapse-button"]')
            read_more.click()
        except:
            print('short article only')
        paragraphs = content_wrapper.find_elements_by_xpath('.//p')
        print('Found article: ' + title.text + 'published on ' + date.text)
        clean_body = ''
        for para in paragraphs:
            if para.text:
                clean_body += para.text + ' '

        art = Article(title.text, 'N.A', date.text, clean_body)

        # Saving the article to the specified output path
        output_path = os.path.join(output_dir, 'article_' + str(article_number) + '.txt')
        article_number += 1
        with open(output_path, 'w+') as article_file:
            json.dump(art.to_dict(), article_file)

    print("number articles found: " + str(len(articles)))
    print('linkes checked: ' + str(len(article_links)))

    driver.close()


def scroll_down(driver):
    html = driver.find_element_by_tag_name('html')
    html.send_keys(Keys.END)


def scroll_to_end(driver):
    SCROLL_PAUSE_TIME = 0.5

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def clean_missing(title, subtitle, date):
    info_list = [title, subtitle, date]
    for i, info in enumerate(info_list):
        info_list[i] = info.string if info else 'N.A.'
        try:
            info_list[i] = ' '.join(info_list[i].split())
        except AttributeError:
            info_list[i] = 'N.A.'

    return [info_list[0], info_list[1], info_list[2]]


def main():
    parser = argparse.ArgumentParser(description='Scrape on news channel for articles related to a Stock')
    parser.add_argument('symbol', metavar='S', type=str, help='The stock symbol or Company name to be scraped for')
    parser.add_argument('channel', metavar='C', type=str, help='The news channel to scrape, choose between: PR-Newswire, yahoo')

    args = parser.parse_args()
    print("running webscrape for " + args.symbol + " on " + args.channel)

    if args.symbol == 'SP500':
        table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
        df = table[0]
        symbols = df['Symbol'].to_numpy()

        for symbol in symbols:
            if not symbol in os.listdir(os.getcwd()+ '/data'):
                try:
                    yahoo_scrape(symbol)
                except:
                    print('article scraping caused issues')

    elif args.channel == 'PR-Newswire':
        newswire_scrape(args.symbol)

    elif args.channel == 'yahoo':
        try:
            yahoo_scrape(args.symbol)
        except:
            print('article scraping caused issues')


if __name__ == '__main__':
    main()
