import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import datetime
import dateutil
import nltk
import string
import contractions
import inflect
import article
import json
import unicodedata
import re

import pandas as pd
import yfinance as yf
from yahoofinancials import YahooFinancials


def clean_text(text: str):
    # removing indents, tabs and linebreaks
    text = ' '.join(text.split())

    # removing quotation marks
    text = text.replace('"', '')

    # remove non-ASCII chars
    printable = set(string.printable)
    text = ''.join(filter(lambda x: x in printable, text))

    # all lowercase characters
    text = text.lower()
    return text


def text_sizes(path: str):
    article_names = os.listdir(path)

    articles = []
    art_sizes = np.zeros(len(article_names))

    for i, name in enumerate(article_names):
        with open(path + '/' + name, 'r') as article_file:
            article = json.load(article_file)
        text = article['text']
        art_sizes[i] = len(text)
    return art_sizes


def convert_to_class(value: float):
    '''
    Converts delta found on day of the article to one of the following classes: [increase, not relevant, decrease] with
    defined threshold values found by analysis of changes on all trading days in the last year.
    :param value: the relative delta found on the trading day
    :return: the class of the article as a string
    '''
    if value > 0.05:
        return 'increase'
    elif value < -0.05:
        return 'decrease'
    else:
        return 'not relevant'


def convert_numeric(value: str):
    if type(value) == str:
        value.replace(',', '')
    try:
        return float(value)
    except:
        return None


def convert_date(date: str):
    try:
        return dateutil.parser.parse(date)
    except:
        new_date = date.split(',')[1] + date.split(',')[2]
        return dateutil.parser.parse(new_date)


def get_companies_in_folder(path: str):
    """
    collects all available folders in found in path
    :param path: Where to search for companies
    :return: List of strings with company name
    """
    available_cmps = os.listdir(path)
    available_cmps.remove('.DS_Store')
    return available_cmps


def clean_returns(returns: pd.DataFrame):
    """
    Takes returns and converts date type and closing values to required formats. Fills missing values and calculates the daily return delta
    :param returns: Requires a Dataframe with columns "Date" and "Close Value"
    :return: returns cleaned dataframe instance, with the date as index
    """
    returns['Date'] = returns['Date'].apply(lambda x: dateutil.parser.parse(x))
    returns['Close Value'] = returns['Close Value'].apply(lambda x: convert_numeric(x))
    returns = returns.fillna(method='ffill')
    returns['Delta'] = returns['Close Value'].diff(1)
    returns = returns.set_index('Date')
    return returns


def find_label(snp: pd.DataFrame, returns: pd.DataFrame, date: datetime.date, max_iter: int, adj_ts_model: pd.DataFrame):
    '''
    Takes the date of an article together with the returns
    :param snp:
    :param returns:
    :param date:
    :param max_iter:
    :return:
    '''
    returns['Delta'] = -returns['Adj Close'].diff(-2) / returns['Adj Close']
    try:
        returns['Delta'] = returns['Delta'] - adj_ts_model['Delta']
    except:
        pass
    returns['rel_Delta'] = returns['Delta'] - snp['Delta']
    i = max_iter
    while i > 0:
        try:
            label = returns['rel_Delta'].loc[date - datetime.timedelta(days=1)]
            break
        except:
            # increase days until found
            date = date + datetime.timedelta(days=1)
            i -= 1
    return label


def to_float(string: str):
    if type(string)==str:
        string = string.strip('[').strip(']')
    return float(string)


def format_to_bert(adj_ts_model: str = '', path: str = os.getcwd()):
    """
    Takes all article files in ticker symbol folders to convert them to a single dataframe stored as tsv file.
    Adds labels to the articles to facilitate supervised learning by comparing the returns to the S&P500 returns.
    :param path: the dir. where the folders of each ticker symbols are stored, containing txt files for the articles
    :return: the training dataframe, additionally stored as tsv file
    """
    input_dir = path + '/data/articles'
    output_dir = path + '/data/tabular_data'
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    available_cmps = get_companies_in_folder(input_dir)

    df = pd.DataFrame(columns=['text', 'label', 'date'])
    oldest_article = datetime.date.today()

    start_date = '2020-01-01'
    end_date = '2021-01-05'
    adj_data = None

    if adj_ts_model == 'LSTM':
        lstm_data = pd.read_csv('data/tabular_data/lstm_pred.csv')
        lstm_data['Date'] = lstm_data['Date'].apply(lambda x: dateutil.parser.parse(x))
        lstm_data.set_index('Date', inplace=True)
        adj_data = lstm_data
        start_date = str(lstm_data.index.min().date())
        end_date = str(lstm_data.index.max().date())

    if adj_ts_model == 'ARIMA':
        arima_data = pd.read_csv('data/tabular_data/prediction_arima_withdate.csv')
        arima_data['Date'] = arima_data['Date'].apply(lambda x: dateutil.parser.parse(x))
        arima_data.set_index('Date', inplace=True)
        for col in arima_data.columns:
            arima_data[col] = arima_data[col].apply(lambda x: to_float(x))
        adj_data = arima_data
        start_date = str(arima_data.index.min().date())
        end_date = str(arima_data.index.max().date())

    snp = yf.download('SNP', start=start_date, end=end_date, progress=False)
    snp['Delta'] = -snp['Adj Close'].diff(-2) / (snp['Adj Close'])

    for stock in available_cmps:
        input_path = input_dir + '/' + stock
        article_names = os.listdir(input_path)
        try:
            returns = yf.download(stock, start=start_date, end=end_date, progress=False)
        except:
            print('Could not download returns properly for: ' + stock)
            continue
        for name in article_names:
            art = article.load_from_json(input_path + '/' + name)
            date = convert_date(art._date)
            if date.date() < oldest_article:
                oldest_article = date.date()
            title = clean_text(art._title)
            text = title + clean_text(art._text)
            try:
                if adj_ts_model:
                    adj_data['Delta'] = adj_data[stock]
                label = find_label(snp, returns, date, 5, adj_data)
            except:
                if not adj_ts_model:
                    print('Could not find matching trading Delta for ' + str(date) +
                          '.Check if returns are well defined and if '
                          'maxIter is sufficiently high. Stock: ' + stock)
                continue

            df = df.append({'text' : text,
                            'label': convert_to_class(label),
                            'date' : date},
                            ignore_index=True)
    bert_df = pd.DataFrame({'label': df['label'],
                            'text': df['text'].replace(r'\n', ' ', regex=True),
    })

    print('Train DF of size ' + str(bert_df.shape[0]))
    print('oldest article: ' + str(oldest_article))
    print('save DF to: ' + output_dir + '/data_' + adj_ts_model + '.tsv')
    bert_df.to_csv(output_dir + '/data_' + adj_ts_model + '.tsv', sep='\t', index=False, header=False)

    return df
