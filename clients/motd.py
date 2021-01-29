from clients.baseclient import BaseClient
import requests


class Client(BaseClient):

    url = 'http://quotes.rest/qod'
    type_ = 'MOTD'
    sleep_time = 3600

    @property
    def data(self):
        data = requests.get(self.url).json()
        if 'error' in data:
            return dict(
                    quote=data['error']['message'],
                    author=data['error']['code']
                )
        quote = data['contents']['quotes'][0]
        return dict(
            quote=quote['quote'],
            author=quote['author']
        )
