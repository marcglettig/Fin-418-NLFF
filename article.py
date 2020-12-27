import re


class Article:
    def __init__(self, title: str, subtitle: str, date: str, text: str):
        # Initializing instance of article. Directly cleaning out missing information
        info_list = [title, subtitle, date]
        for i, info in enumerate(info_list):
            info_list[i] = info.string if info else 'N.A.'
            try:
                info_list[i] = ' '.join(info_list[i].split())
            except AttributeError:
                info_list[i] = 'N.A.'

        self._title = info_list[0]
        self._subtitle = info_list[1]
        self._date = info_list[2]
        self._text = text

    def __str__(self):
        # To String method to print nicely to file
        out = '{title} - {subtitle} ({date}) \n {text}'
        return out.format(title=self._title, subtitle=self._subtitle, date=self._date, text=self._text)