import re
import json


class Article:
    def __init__(self, title: str, subtitle: str, date: str, text: str):
        # Initializing instance of article.
        self._title = title
        self._subtitle = subtitle
        self._date = date
        self._text = text

    def __str__(self):
        # To String method to print nicely to file
        out = '{title} - {subtitle} ({date}) \n {text}'
        return out.format(title=self._title, subtitle=self._subtitle, date=self._date, text=self._text)

    def to_dict(self):
        # To dict method to dump in json file
        article = {'title': self._title,
                   'subtitle': self._subtitle,
                   'date': self._date,
                   'text': self._text
                   }
        return article


def load_from_json(path: str):
    with open(path, 'r') as article_file:
        article = json.load(article_file)
    art = Article(article['title'], article['subtitle'], article['date'], article['text'])
    return art
